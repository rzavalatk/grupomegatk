# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)


class Settings(models.TransientModel):
    _inherit = 'res.config.settings'

    #company_cierre = []
    company_cierre = {"company": 0}
    puntero = 0
    journal_ids = fields.Many2many(
        "account.journal",
        "crons_mega_config_journal_rel",
        "config_id", "journal_id",
        string="Diarios de cierre")
    teams_sps = fields.Char("Canales de SPS")
    account_ids_cron_mega = fields.Many2many(
        "account.account",
        "crons_mega_config_account_rel",
        "config_id", "account_id",
        string="Cuentas Cxc para cierre")
    marca_ids = fields.Many2many(
        "product.marca",
        "crons_mega_config_marca_rel",
        "config_id", "marca_id",
        string="Marcas")
    
    def get_values_journal_ids(self, company):
        self.company_cierre["company"] = company
        obj = self.get_values()
        journal_ids = obj.get('journal_ids', [])
        if journal_ids:
            return journal_ids[0][2]
        return []
    
    def get_values_account_ids_cron_mega(self,company):
        try:
            self.write({'company_cierre': company})
            obj = self.get_values()
            return obj['account_ids_cron_mega'][0][2]
        except:
            return []
        
    def get_values_teams_sps(self):
        obj = self.get_values()
        res = []
        l = obj['teams_sps'].split(',')
        for item in l:
            res.append(int(item))
        return res
        
    def get_values(self):
        res = super(Settings, self).get_values()
        IrValues = self.env['ir.config_parameter'].sudo()
        lines = []
        lines_account = []
        marcas = []

        try:
            marca_ids = IrValues.get_param('crons_mega.marca_ids' + str(self.env.user.company_id.id))
            marcas_ids = []
            if marca_ids:
                for item in marca_ids.replace('[', '').replace(']', '').split(','):
                    item = item.strip()
                    if item:
                        marcas_ids.append(int(item))
            if marcas_ids:
                marcas = [(6, 0, marcas_ids)]
        except Exception:
            pass

        try:
            account_ids_cron_mega = IrValues.get_param(
                'crons_mega.account_ids_cron_mega_' + str(self.company_cierre["company"])
            ) or IrValues.get_param(
                'crons_mega.account_ids_cron_mega_' + str(self.env.user.company_id.id)
            )
            account_ids = []
            if account_ids_cron_mega:
                for item in account_ids_cron_mega.replace('[', '').replace(']', '').split(','):
                    item = item.strip()
                    if item:
                        account_ids.append(int(item))
            if account_ids:
                lines_account = [(6, 0, account_ids)]
        except Exception:
            pass

        try:
            journal_ids = IrValues.get_param(
                'crons_mega.journal_ids_' + str(self.company_cierre["company"])
            ) or IrValues.get_param(
                'crons_mega.journal_ids_' + str(self.env.user.company_id.id)
            )
            ids = []
            if journal_ids:
                for item in journal_ids.replace('[', '').replace(']', '').split(','):
                    item = item.strip()
                    if item:
                        ids.append(int(item))
            if ids:
                lines = [(6, 0, ids)]
        except Exception:
            pass

        res.update(journal_ids=lines, account_ids_cron_mega=lines_account, marca_ids=marcas)
        return res

    def set_values(self):
        IrValues = self.env['ir.config_parameter'].sudo()
        IrValues.set_param('crons_mega.marca_ids'+str(self.env.user.company_id.id), self.marca_ids.ids)
        IrValues.set_param('crons_mega.account_ids_cron_mega_'+str(self.env.user.company_id.id), self.account_ids_cron_mega.ids)
        IrValues.set_param('crons_mega.journal_ids_'+str(self.env.user.company_id.id), self.journal_ids.ids)
        IrValues.set_param('crons_mega.teams_sps', self.teams_sps)
        super(Settings, self).set_values()

