from odoo import api, fields, models, _
from odoo.exceptions import AccessError, ValidationError


class LenkaBankDisbursement(models.Model):
    _inherit = 'lenka.disbursement'

    bank_check_ids = fields.One2many('banks.check', 'lenka_disbursement_id', string='Cheques de Tesoreria', readonly=True)

    def _require_treasury_manager(self):
        self.check_access('write')
        if not self.env.user.has_group('lenka_financiero.group_lenka_manager'):
            raise AccessError(_('Se requiere el permiso Gerente de Lenka.'))
        if not self.env.user.has_group('banks.banks_check_manager'):
            raise AccessError(_('Se requiere el permiso existente Cheques Usuario Avanzado de Tesoreria.'))

    def _check_sequence(self, journal):
        sequences = journal.secuencia_ids.filtered(lambda s: s.move_type == 'check' or s.code == 'check')
        if len(sequences) != 1 or sequences.use_date_range:
            raise ValidationError(_('Configure una sola secuencia de cheques sin rangos de fecha para el banco seleccionado.'))
        sequence = sequences[0]
        if sequence.company_id and sequence.company_id != self.operation_id.company_id:
            raise ValidationError(_('La secuencia de cheques pertenece a otra empresa.'))
        sequence.check_access('read')
        return sequence

    def _native_check_values(self, journal, amount):
        self.ensure_one()
        company = self.operation_id.company_id
        return {
            'journal_id': journal.id, 'company_id': company.id, 'date': self.date,
            'currency_id': self.currency_id.id,
            'currency_rate': self.currency_id._convert(1, company.currency_id, company, self.date, round=False),
            'es_moneda_base': self.currency_id == company.currency_id,
            'doc_type': 'check', 'total': amount,
            'name': (self.destination_partner_id or self.operation_id.partner_id).name,
            'memo': '%s - %s' % (self.operation_id.name, self.name),
            'check_lines': [(0, 0, {
                'account_id': company.lenka_portfolio_account_id.id,
                'partner_id': self.operation_id.partner_id.id,
                'name': _('Capital financiado - %s') % self.operation_id.name,
                'amount': amount, 'move_type': 'debit', 'currency_id': self.currency_id.id,
            })],
        }

    def action_create_account_move(self):
        self.check_access('write')
        self._lock_operations()
        checks = self.filtered(lambda d: d.payment_method == 'check' and not d.move_id)
        for rec in checks:
            rec._require_treasury_manager()
            if rec.state != 'posted' or not rec.disbursement_journal_id:
                raise ValidationError(_('Aplique el desembolso con su banco de salida antes de registrar el cheque.'))
            journal, _portfolio, _account = rec._disbursement_accounts()
            sequence = rec._check_sequence(journal)
            # Serialize with all native consumers of this same ir.sequence.
            sequence.flush_recordset()
            self.env.cr.execute('SELECT id FROM ir_sequence WHERE id = %s FOR UPDATE', [sequence.id])
            sequence.invalidate_recordset()
            check = self.env['banks.check'].create(rec._native_check_values(journal, rec.amount))
            check.action_validate()  # Native numbering and ONE native draft accounting entry.
            sequence.invalidate_recordset(['number_next_actual'])
            if not check.move_id or check.move_id.state != 'draft':
                raise ValidationError(_('Tesoreria no genero el borrador contable esperado.'))
            rec._link_disbursement_move(check.move_id)
            check._attach_lenka(rec, historical=False)
            rec.reference = check.number
            rec.message_post(body=_('Cheque registrado en Tesoreria: %s.') % check.number)
        return super(LenkaBankDisbursement, self - checks).action_create_account_move()

    def action_open_bank_checks(self):
        self.ensure_one()
        self.bank_check_ids.check_access('read')
        return {'type': 'ir.actions.act_window', 'name': _('Cheques del desembolso'),
                'res_model': 'banks.check', 'view_mode': 'list,form',
                'domain': [('id', 'in', self.bank_check_ids.ids)], 'target': 'current'}

    def action_register_historical_checks(self):
        self.ensure_one()
        self._require_treasury_manager()
        if self.payment_method != 'check' or self.state != 'posted' or not self.move_id or self.move_id.state != 'posted' or self.bank_check_ids:
            raise ValidationError(_('Esta accion es para un desembolso por cheque ya contabilizado, sin cheques vinculados.'))
        return {'type': 'ir.actions.act_window', 'name': _('Registrar cheques ya emitidos'),
                'res_model': 'lenka.historical.check.wizard', 'view_mode': 'form', 'target': 'new',
                'context': {'default_disbursement_id': self.id}}

    def action_cancel(self):
        if self.filtered('bank_check_ids'):
            raise ValidationError(_('El desembolso tiene cheques emitidos. Gestione su anulacion con Tesoreria y revise la contabilidad; no se borrara el correlativo.'))
        return super().action_cancel()


class BanksCheckLenka(models.Model):
    _inherit = 'banks.check'

    lenka_disbursement_id = fields.Many2one('lenka.disbursement', readonly=True, copy=False, ondelete='restrict')
    lenka_historical = fields.Boolean(string='Cheque historico ya contabilizado', readonly=True, copy=False)

    def _attach_lenka(self, disbursement, historical=False):
        self.ensure_one()
        disbursement._require_treasury_manager()
        if self.lenka_disbursement_id or self.move_id != disbursement.move_id:
            raise ValidationError(_('El cheque no corresponde al asiento del desembolso.'))
        super(BanksCheckLenka, self).write({'lenka_disbursement_id': disbursement.id, 'lenka_historical': historical})

    @api.model_create_multi
    def create(self, vals_list):
        if any(v.get('lenka_disbursement_id') or v.get('lenka_historical') for v in vals_list):
            raise AccessError(_('Vincule los cheques desde el desembolso autorizado.'))
        return super().create(vals_list)

    def write(self, vals):
        protected = {'lenka_disbursement_id', 'lenka_historical', 'state', 'move_id', 'number',
                     'journal_id', 'company_id', 'date', 'total', 'check_lines', 'currency_id', 'currency_rate', 'name', 'doc_type', 'cheque_anulado'}
        if {'lenka_disbursement_id', 'lenka_historical'}.intersection(vals) or (protected.intersection(vals) and self.filtered('lenka_disbursement_id')):
            raise ValidationError(_('El cheque esta vinculado a un prestamo. No puede alterarse, renumerarse ni regenerarse desde Tesoreria.'))
        return super().write(vals)

    def unlink(self):
        if self.filtered('lenka_disbursement_id'):
            raise ValidationError(_('Conserve el cheque y su correlativo vinculados al prestamo.'))
        return super().unlink()

    def generate_asiento(self):
        if self.filtered('lenka_disbursement_id'):
            raise ValidationError(_('Este cheque ya tiene asiento vinculado. No puede generar otra salida.'))
        return super().generate_asiento()


class BanksCheckLineLenka(models.Model):
    _inherit = 'banks.check.line'

    def write(self, vals):
        if self.mapped('check_id.lenka_disbursement_id'):
            raise ValidationError(_('No puede modificar el detalle de un cheque vinculado a Lenka.'))
        return super().write(vals)

    def unlink(self):
        if self.mapped('check_id.lenka_disbursement_id'):
            raise ValidationError(_('No puede eliminar el detalle de un cheque vinculado a Lenka.'))
        return super().unlink()

    @api.model_create_multi
    def create(self, vals_list):
        checks = self.env['banks.check'].browse([v['check_id'] for v in vals_list if v.get('check_id')])
        if checks.mapped('lenka_disbursement_id'):
            raise ValidationError(_('No puede agregar lineas a un cheque vinculado a Lenka.'))
        return super().create(vals_list)


class AccountMoveLenkaChecks(models.Model):
    _inherit = 'account.move'

    def _check_lenka_checks(self):
        if self.env['banks.check'].sudo().search_count([('move_id', 'in', self.ids), ('lenka_disbursement_id', '!=', False)]):
            raise ValidationError(_('El asiento tiene cheques de un prestamo Lenka. Solicite la correccion controlada; no lo revierta ni regenere directamente.'))

    def write(self, vals):
        if {'state', 'date', 'line_ids', 'journal_id', 'company_id'}.intersection(vals):
            # Allow the first publication of the generated draft, never a reset.
            if vals.get('state') == 'posted' and set(vals) == {'state'}:
                pass
            elif vals.get('state') == 'posted' and all(m.state == 'draft' for m in self):
                pass
            else:
                self._check_lenka_checks()
        return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        self.browse([v['reversed_entry_id'] for v in vals_list if v.get('reversed_entry_id')])._check_lenka_checks()
        return super().create(vals_list)

    def _post(self, soft=True):
        for move in self:
            checks = self.env['banks.check'].sudo().search([
                ('move_id', '=', move.id), ('lenka_disbursement_id', '!=', False)])
            if not checks:
                continue
            for disbursement in checks.mapped('lenka_disbursement_id'):
                company = disbursement.operation_id.company_id
                expected = disbursement.currency_id._convert(
                    disbursement.amount, company.currency_id, company, disbursement.date)
                capital = move.line_ids.filtered(lambda l: l.account_id == company.lenka_portfolio_account_id
                                                 and l.partner_id == disbursement.operation_id.partner_id)
                bank = move.line_ids.filtered(lambda l: l.account_id == move.journal_id.default_account_id)
                if (len(move.line_ids) != 2 or not capital or not bank
                        or company.currency_id.compare_amounts(sum(capital.mapped('balance')), expected)
                        or company.currency_id.compare_amounts(-sum(bank.mapped('balance')), expected)):
                    raise ValidationError(_('El asiento del cheque debe coincidir exactamente con la cartera y el banco del desembolso.'))
        return super()._post(soft=soft)


class AccountMoveLineLenkaChecks(models.Model):
    _inherit = 'account.move.line'

    def _protect_posted_checks(self):
        self.mapped('move_id').filtered(lambda m: m.state == 'posted')._check_lenka_checks()

    def write(self, vals):
        if {'move_id', 'account_id', 'partner_id', 'debit', 'credit', 'balance', 'amount_currency', 'currency_id', 'date'}.intersection(vals):
            self._protect_posted_checks()
        return super().write(vals)

    def unlink(self):
        self._protect_posted_checks()
        return super().unlink()

    @api.model_create_multi
    def create(self, vals_list):
        self.env['account.move'].browse([v['move_id'] for v in vals_list if v.get('move_id')]).filtered(lambda m: m.state == 'posted')._check_lenka_checks()
        return super().create(vals_list)
