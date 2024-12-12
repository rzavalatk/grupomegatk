# -*- coding: utf-8 -*-

from odoo import fields, models


class ConfiguracionResSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    module_account_accountant = fields.Boolean(string='Contabilidad para Contadores')
    module_l10n_fr_hr_payroll = fields.Boolean(string='Nómina Francesa')
    module_l10n_be_hr_payroll = fields.Boolean(string='Nómina Belga')
    module_l10n_in_hr_payroll = fields.Boolean(string='Nómina India')
