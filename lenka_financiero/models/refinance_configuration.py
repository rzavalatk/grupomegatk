"""Company-specific recognition of an explicitly designated internal bridge."""
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, ValidationError


class ResCompanyLenkaRefinance(models.Model):
    _inherit = 'res.company'

    lenka_refinance_clearing_journal_id = fields.Many2one(
        'account.journal', string='Lenka: Diario puente interno de refinanciamiento',
        ondelete='restrict',
        help='Diario confirmado como puente interno, sin cuenta bancaria real. Permite reconocer '
             'sus asientos existentes sin cambiar su clasificacion historica ni generar dinero.')

    @api.constrains('lenka_refinance_clearing_journal_id', 'lenka_portfolio_account_id')
    def _check_lenka_refinance_bridge(self):
        for company in self:
            journal = company.lenka_refinance_clearing_journal_id
            if not journal:
                continue
            account = journal.default_account_id
            if (journal.company_id != company or journal.type not in ('general', 'bank')
                    or journal.bank_account_id or not account
                    or company not in account.company_ids
                    or account == company.lenka_portfolio_account_id
                    or account.account_type not in ('asset_current', 'asset_cash')):
                raise ValidationError(_('Seleccione un diario puente de esta empresa, con cuenta propia '
                                        'de intercambio y sin cuenta bancaria real vinculada.'))

    @api.model_create_multi
    def create(self, vals_list):
        if (any(vals.get('lenka_refinance_clearing_journal_id') for vals in vals_list)
                and not self.env.user.has_group('lenka_financiero.group_lenka_manager')):
            raise AccessError(_('Solo un gerente de Lenka puede designar el diario puente interno.'))
        return super().create(vals_list)

    def write(self, vals):
        if 'lenka_refinance_clearing_journal_id' in vals:
            changing = self.filtered(lambda c: c.lenka_refinance_clearing_journal_id.id !=
                                     vals['lenka_refinance_clearing_journal_id'])
            if changing and not self.env.user.has_group('lenka_financiero.group_lenka_manager'):
                raise AccessError(_('Solo un gerente de Lenka puede designar el diario puente interno.'))
            for company in changing.filtered('lenka_refinance_clearing_journal_id'):
                if self.env['lenka.disbursement'].sudo().search_count([
                    ('operation_id.company_id', '=', company.id), ('state', '=', 'posted'),
                    ('payment_method', '=', 'refinance_entry'),
                    ('refinance_move_id.journal_id', '=', company.lenka_refinance_clearing_journal_id.id),
                ]):
                    raise ValidationError(_('El diario puente tiene refinanciamientos aplicados. '
                                            'Conserve la configuracion mientras existan esos vinculos.'))
        return super().write(vals)


class ResConfigSettingsLenkaRefinance(models.TransientModel):
    _inherit = 'res.config.settings'

    lenka_refinance_clearing_journal_id = fields.Many2one(
        related='company_id.lenka_refinance_clearing_journal_id', readonly=False)
    lenka_refinance_clearing_account_id = fields.Many2one(
        related='company_id.lenka_refinance_clearing_journal_id.default_account_id', readonly=True)
