# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CierreConfig(models.Model):
    _name = 'account.cierre.config'
    _description = 'Configuracion de cierre diario'

    company_id = fields.Many2one(
        'res.company',
        string='Compania',
        required=True,
        default=lambda self: self.env.company.id,
    )
    journal_ids = fields.Many2many(
        'account.journal',
        'crons_mega_cfg_journal_rel',
        'config_id',
        'journal_id',
        string='Diarios de cierre',
    )
    account_ids_cron_mega = fields.Many2many(
        'account.account',
        'crons_mega_cfg_account_rel',
        'config_id',
        'account_id',
        string='Cuentas CXC para cierre',
    )
    marca_ids = fields.Many2many(
        'product.marca',
        'crons_mega_cfg_marca_rel',
        'config_id',
        'marca_id',
        string='Marcas',
    )

    _sql_constraints = [
        (
            'crons_mega_unique_company_config',
            'unique(company_id)',
            'Solo puede existir una configuracion de cierre por compania.',
        )
    ]

    @api.model
    def _normalize_company_id(self, company):
        if hasattr(company, 'id'):
            return company.id
        if company:
            return int(company)
        return self.env.company.id

    @api.model
    def _get_config(self, company):
        company_id = self._normalize_company_id(company)
        return self.search([('company_id', '=', company_id)], limit=1)

    @api.model
    def get_journal_ids(self, company=None):
        config = self._get_config(company)
        return config.journal_ids.ids if config else []

    @api.model
    def get_account_ids(self, company=None):
        config = self._get_config(company)
        return config.account_ids_cron_mega.ids if config else []

    @api.model
    def get_marca_ids(self, company=None):
        config = self._get_config(company)
        return config.marca_ids.ids if config else []


class Settings(models.TransientModel):
    _inherit = 'res.config.settings'

    journal_ids = fields.Many2many(
        'account.journal',
        'crons_mega_config_journal_rel',
        'config_id', 'journal_id',
        string='Diarios de cierre')
    teams_sps = fields.Char('Canales de SPS')
    account_ids_cron_mega = fields.Many2many(
        'account.account',
        'crons_mega_config_account_rel',
        'config_id', 'account_id',
        string='Cuentas Cxc para cierre')
    marca_ids = fields.Many2many(
        'product.marca',
        'crons_mega_config_marca_rel',
        'config_id', 'marca_id',
        string='Marcas')

    def _company_id_from_input(self, company):
        if hasattr(company, 'id'):
            return company.id
        if company:
            return int(company)
        return self.env.company.id

    def get_values_journal_ids(self, company):
        company_id = self._company_id_from_input(company)
        return self.env['account.cierre.config'].sudo().get_journal_ids(company_id)

    def get_values_account_ids_cron_mega(self, company):
        company_id = self._company_id_from_input(company)
        return self.env['account.cierre.config'].sudo().get_account_ids(company_id)

    def get_values_teams_sps(self):
        return []

    def get_values(self):
        res = super(Settings, self).get_values()
        company_id = self.env.company.id
        config = self.env['account.cierre.config'].sudo().search([
            ('company_id', '=', company_id)
        ], limit=1)
        res.update(
            journal_ids=[(6, 0, config.journal_ids.ids)] if config else [],
            account_ids_cron_mega=[(6, 0, config.account_ids_cron_mega.ids)] if config else [],
            marca_ids=[(6, 0, config.marca_ids.ids)] if config else [],
        )
        return res

    def set_values(self):
        super(Settings, self).set_values()
        company_id = self.env.company.id
        config = self.env['account.cierre.config'].sudo().search([
            ('company_id', '=', company_id)
        ], limit=1)
        values = {
            'company_id': company_id,
            'journal_ids': [(6, 0, self.journal_ids.ids)],
            'account_ids_cron_mega': [(6, 0, self.account_ids_cron_mega.ids)],
            'marca_ids': [(6, 0, self.marca_ids.ids)],
        }
        if config:
            config.write(values)
        else:
            self.env['account.cierre.config'].sudo().create(values)

