from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HistoricalCheckWizard(models.TransientModel):
    _name = 'lenka.historical.check.wizard'
    _description = 'Identificar cheques ya contabilizados sin otra salida'

    disbursement_id = fields.Many2one('lenka.disbursement', required=True)
    journal_id = fields.Many2one(related='disbursement_id.move_id.journal_id', readonly=True)
    currency_id = fields.Many2one(related='disbursement_id.currency_id')
    amount = fields.Monetary(related='disbursement_id.amount')
    line_ids = fields.One2many('lenka.historical.check.line', 'wizard_id', string='Cheques ya entregados')

    def action_register(self):
        self.ensure_one()
        disbursement = self.disbursement_id
        disbursement._require_treasury_manager()
        disbursement._lock_operations()
        if disbursement.payment_method != 'check' or disbursement.state != 'posted' or not disbursement.move_id or disbursement.move_id.state != 'posted' or disbursement.bank_check_ids:
            raise ValidationError(_('Seleccione un desembolso por cheque aplicado y contabilizado, sin cheques vinculados.'))
        move = disbursement.move_id
        move.check_access('read')
        self.env.cr.execute('SELECT id FROM account_move WHERE id = %s FOR UPDATE', [move.id])
        journal = move.journal_id
        company = disbursement.operation_id.company_id
        portfolio = company.lenka_portfolio_account_id
        if journal.type != 'bank' or journal.company_id != company or not portfolio:
            raise ValidationError(_('Revise el banco y la cuenta de cartera del asiento original.'))
        if self.currency_id != company.currency_id:
            raise ValidationError(_('La identificacion historica admite por ahora la moneda base de la empresa.'))
        debit = move.line_ids.filtered(lambda l: l.account_id == portfolio and l.partner_id == disbursement.operation_id.partner_id)
        credit = move.line_ids.filtered(lambda l: l.account_id == journal.default_account_id)
        if (len(move.line_ids) != 2 or not debit or not credit
                or company.currency_id.compare_amounts(sum(debit.mapped('balance')), disbursement.amount)
                or company.currency_id.compare_amounts(-sum(credit.mapped('balance')), disbursement.amount)):
            raise ValidationError(_('El asiento original debe representar exactamente la cartera y salida bancaria de este desembolso.'))
        if not self.line_ids or self.currency_id.compare_amounts(sum(self.line_ids.mapped('amount')), disbursement.amount):
            raise ValidationError(_('Los cheques deben sumar exactamente el desembolso ya contabilizado.'))
        sequence = disbursement._check_sequence(journal)
        self.env.cr.execute('SELECT id FROM ir_sequence WHERE id = %s FOR UPDATE', [sequence.id])
        sequence.invalidate_recordset()
        used = set()
        for line in self.line_ids:
            text = (line.check_number or '').strip()
            if not text.isascii() or not text.isdecimal() or int(text) <= 0 or line.amount <= 0:
                raise ValidationError(_('Indique numeros de cheque enteros positivos e importes mayores que cero.'))
            if int(text) >= sequence.number_next_actual:
                raise ValidationError(_('El cheque historico debe ser anterior al proximo numero de la chequera. No se modificara el correlativo.'))
            number = sequence.with_context(ir_sequence_date=disbursement.date).get_next_char(int(text))
            if number in used:
                raise ValidationError(_('No repita el mismo cheque en el desglose.'))
            used.add(number)
            if self.env['banks.check'].sudo().search_count([('journal_id', '=', journal.id), ('number', '=', number)]):
                raise ValidationError(_('El cheque %s ya existe en Tesoreria. Vincule o revise su registro antes de continuar.') % number)
            if self.env['account.move'].sudo().search_count([('journal_id', '=', journal.id), ('name', '=', number)]):
                raise ValidationError(_('Ya existe un asiento con el numero %s. No se creara un registro duplicado.') % number)
            vals = disbursement._native_check_values(journal, line.amount)
            vals.update({'number': number, 'state': 'validated', 'move_id': move.id, 'princhek': True})
            check = self.env['banks.check'].create(vals)
            check._attach_lenka(disbursement, historical=True)
        disbursement.message_post(body=_('Cheques historicos identificados sin crear asientos: %s.') % ', '.join(sorted(used)))
        return {'type': 'ir.actions.act_window_close'}


class HistoricalCheckLine(models.TransientModel):
    _name = 'lenka.historical.check.line'
    _description = 'Detalle de cheque ya entregado'

    wizard_id = fields.Many2one('lenka.historical.check.wizard', required=True, ondelete='cascade')
    check_number = fields.Char(string='Numero fisico del cheque', required=True)
    currency_id = fields.Many2one(related='wizard_id.currency_id')
    amount = fields.Monetary(required=True, string='Importe')
