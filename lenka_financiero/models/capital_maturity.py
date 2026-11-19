"""Explicit capital receivable maturity; never rewrite historical entries on upgrade."""
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, ValidationError


class LenkaDisbursementMaturity(models.Model):
    _inherit = 'lenka.disbursement'

    capital_due_date = fields.Date(
        string='Vencimiento contable del capital', copy=False, tracking=True,
        help='Fecha pactada para esta CxC. No cambia las cuotas, los intereses ni la mora del plan. '
             'Si ya existe partida, utilice Definir vencimiento CxC para revisarla expresamente.')
    capital_plan_due_date = fields.Date(
        string='Ultima cuota del plan', compute='_compute_capital_plan_due_date')

    @api.depends('operation_id.schedule_line_ids.date')
    def _compute_capital_plan_due_date(self):
        for rec in self:
            rec.capital_plan_due_date = max(rec.operation_id.schedule_line_ids.mapped('date'), default=False)

    def _require_capital_maturity_manager(self):
        self.check_access('write')
        self.mapped('operation_id').check_access('read')
        if not self.env.user.has_group('lenka_financiero.group_lenka_manager'):
            raise AccessError(_('Se requiere Gerente de Lenka para definir vencimientos contables.'))

    @api.model_create_multi
    def create(self, vals_list):
        if any(vals.get('capital_due_date') for vals in vals_list):
            self._require_capital_maturity_manager()
        return super().create(vals_list)

    def write(self, vals):
        if 'capital_due_date' in vals:
            self._require_capital_maturity_manager()
            if self.filtered(lambda d: d.move_id or d.payment_method == 'refinance_entry' or d.state == 'cancelled'):
                raise ValidationError(_('Use Definir vencimiento CxC para revisar una partida existente.'))
        return super().write(vals)

    @api.constrains('capital_due_date', 'date')
    def _check_capital_due_date(self):
        for rec in self:
            if rec.capital_due_date and rec.capital_due_date < rec.date:
                raise ValidationError(_('El vencimiento del capital no puede ser anterior al desembolso.'))

    def _capital_maturity_lines(self, move):
        self.ensure_one()
        move.check_access('read')
        company = self.operation_id.company_id
        if move.company_id != company or move.move_type != 'entry' or move.state not in ('draft', 'posted'):
            raise ValidationError(_('Revise la empresa, el tipo y el estado de la partida vinculada.'))
        if move.reversed_entry_id or move.reversal_move_ids.filtered(lambda m: m.state == 'posted'):
            raise ValidationError(_('No se puede modificar el vencimiento de una partida revertida.'))
        portfolio = company.lenka_portfolio_account_id
        if portfolio.account_type != 'asset_receivable':
            raise ValidationError(_('La cartera debe ser de tipo Por cobrar para usar vencimientos de CxC.'))
        lines = move.line_ids.filtered(lambda l: l.account_id == portfolio)
        if (not lines or any(l.partner_id != self.operation_id.partner_id or l.debit <= 0 or l.credit
                             or l.currency_id != self.currency_id for l in lines)
                or self.currency_id.compare_amounts(sum(lines.mapped('amount_currency')), self.amount)):
            raise ValidationError(_('La partida debe contener exactamente el capital y cliente de este desembolso.'))
        if self.payment_method == 'refinance_entry':
            self._validate_refinance_entry()
            if lines != self.refinance_line_id:
                raise ValidationError(_('Seleccione exclusivamente el apunte de capital del refinanciamiento.'))
        lines.check_access('write')
        return lines

    def _link_disbursement_move(self, move):
        # All generators, including native Treasury checks, pass through this hook.
        # Only an explicitly selected date changes a newly generated draft.
        if self.capital_due_date:
            if move.state != 'draft':
                raise ValidationError(_('La nueva partida debe estar en borrador.'))
            move.check_access('write')
            lines = self._capital_maturity_lines(move)
            lines.write({'date_maturity': self.capital_due_date})
        return super()._link_disbursement_move(move)

    def action_open_capital_maturity(self):
        self.ensure_one()
        self._require_capital_maturity_manager()
        if self.state != 'posted':
            raise ValidationError(_('Aplique el desembolso antes de revisar su vencimiento contable.'))
        return {
            'type': 'ir.actions.act_window', 'name': _('Definir vencimiento CxC'),
            'res_model': 'lenka.capital.maturity.wizard', 'view_mode': 'form', 'target': 'new',
            'context': {'default_disbursement_id': self.id},
        }

    def _apply_capital_maturity(self, due_date, reason):
        self.ensure_one()
        self._require_capital_maturity_manager()
        if not due_date or not (reason or '').strip():
            raise ValidationError(_('Indique la fecha pactada y el motivo del vencimiento.'))
        due_date = fields.Date.to_date(due_date)
        with self.env.cr.savepoint():
            self._lock_operations()
            if self.state != 'posted':
                raise ValidationError(_('El desembolso debe seguir aplicado.'))
            move = self.move_id or self.refinance_move_id
            if due_date < self.date or (move and due_date < move.date):
                raise ValidationError(_('El vencimiento no puede ser anterior al desembolso o a su partida.'))
            before = []
            if move:
                move.check_access('write')
                self.env.cr.execute('SELECT id FROM account_move WHERE id = %s FOR UPDATE', [move.id])
                move.invalidate_recordset()
                lines = self._capital_maturity_lines(move)
                self.env.cr.execute('SELECT id FROM account_move_line WHERE id IN %s ORDER BY id FOR UPDATE',
                                    [tuple(lines.ids)])
                lines.invalidate_recordset()
                if any(l.reconciled or l.matched_debit_ids or l.matched_credit_ids for l in lines):
                    raise ValidationError(_('El capital tiene conciliaciones; revise su vencimiento con Contabilidad.'))
                before = [(l.id, fields.Date.to_string(l.date_maturity) or _('Sin fecha')) for l in lines]
                lines.write({'date_maturity': due_date})
            # Internal method, not a forgeable context flag; normal ACLs still apply.
            super(LenkaDisbursementMaturity, self).write({'capital_due_date': due_date})
            self.message_post(body=_('Vencimiento contable del capital: %s. Partida: %s. '
                                     'Apuntes y fechas anteriores: %s. Motivo: %s. '
                                     'No se modifican importes, cuotas ni intereses.') % (
                due_date, move.name if move else _('Pendiente de crear'), before, reason.strip()))
        return True


class LenkaCapitalMaturityWizard(models.TransientModel):
    _name = 'lenka.capital.maturity.wizard'
    _description = 'Revision explicita del vencimiento contable del capital Lenka'

    disbursement_id = fields.Many2one('lenka.disbursement', required=True, readonly=True)
    operation_id = fields.Many2one(related='disbursement_id.operation_id')
    plan_due_date = fields.Date(related='disbursement_id.capital_plan_due_date')
    due_date = fields.Date(string='Vencimiento pactado de esta CxC', required=True)
    reason = fields.Text(string='Motivo / referencia contractual', required=True)
    confirmed = fields.Boolean(string='Confirmo que esta fecha corresponde al capital pactado')

    @api.model
    def default_get(self, fields_list):
        vals = super().default_get(fields_list)
        if vals.get('disbursement_id'):
            rec = self.env['lenka.disbursement'].browse(vals['disbursement_id'])
            rec._require_capital_maturity_manager()
            if 'due_date' in fields_list:
                vals['due_date'] = rec.capital_due_date or rec.capital_plan_due_date
        return vals

    def action_apply(self):
        self.ensure_one()
        if not self.confirmed:
            raise ValidationError(_('Confirme que el vencimiento corresponde al capital pactado.'))
        self.disbursement_id._apply_capital_maturity(self.due_date, self.reason)
        return {'type': 'ir.actions.act_window_close'}
