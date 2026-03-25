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
        "account.journal", "alias_id", string="Diarios de cierre")
    teams_sps = fields.Char("Canales de SPS")
    account_ids_cron_mega = fields.Many2many(
        "account.account", "code", string="Cuentas Cxc para cierre")
    marca_ids = fields.Many2many(
        "product.marca", "setting_id", string="Marcas")
    
    def get_values_journal_ids(self, company):
        self.company_cierre["company"] = company
        
        obj = self.get_values()
        return obj['journal_ids'][0][2]
    
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
        company_id = self.env.user.company_id.id
        
        # Inicializar valores por defecto
        journal_ids = []
        account_ids_cron_mega = []
        marca_ids = []
        
        # Procesar journal_ids
        try:
            journal_ids_str = IrValues.get_param(f'crons_mega.journal_ids_{company_id}')
            if journal_ids_str:
                journal_ids_str = journal_ids_str.replace('[', '').replace(']', '')
                journal_ids_list = [int(x) for x in journal_ids_str.split(',') if x.strip()]
                if journal_ids_list:
                    journal_ids = [(6, 0, journal_ids_list)]
        except Exception as e:
            _logger.warning(f"Error al cargar journal_ids: {str(e)}")
        
        # Procesar account_ids_cron_mega
        try:
            account_ids_str = IrValues.get_param(f'crons_mega.account_ids_cron_mega_{company_id}')
            if account_ids_str:
                account_ids_str = account_ids_str.replace('[', '').replace(']', '')
                account_ids_list = [int(x) for x in account_ids_str.split(',') if x.strip()]
                if account_ids_list:
                    account_ids_cron_mega = [(6, 0, account_ids_list)]
        except Exception as e:
            _logger.warning(f"Error al cargar account_ids_cron_mega: {str(e)}")
        
        # Procesar marca_ids
        try:
            marca_ids_str = IrValues.get_param(f'crons_mega.marca_ids{company_id}')
            if marca_ids_str:
                marca_ids_str = marca_ids_str.replace('[', '').replace(']', '')
                marca_ids_list = [int(x) for x in marca_ids_str.split(',') if x.strip()]
                if marca_ids_list:
                    marca_ids = [(6, 0, marca_ids_list)]
        except Exception as e:
            _logger.warning(f"Error al cargar marca_ids: {str(e)}")
        
        # Actualizar res siempre con los campos, aunque sean vacíos
        res.update(
            journal_ids=journal_ids,
            account_ids_cron_mega=account_ids_cron_mega,
            marca_ids=marca_ids
        )
        
        return res

    def set_values(self):

        try:
            IrValues = self.env['ir.config_parameter'].sudo()
            company_id = self.env.user.company_id.id
            
            # Guardar journal_ids
            IrValues.set_param(f'crons_mega.journal_ids_{company_id}', self.journal_ids.ids)
            
            # Guardar account_ids_cron_mega
            IrValues.set_param(f'crons_mega.account_ids_cron_mega_{company_id}', self.account_ids_cron_mega.ids)
            
            # Guardar marca_ids
            IrValues.set_param(f'crons_mega.marca_ids{company_id}', self.marca_ids.ids)
            
            # Guardar teams_sps
            IrValues.set_param('crons_mega.teams_sps', self.teams_sps)
            
            super(Settings, self).set_values()
        except Exception as e:
            _logger.error(f"Error al guardar configuraciones de cierres: {str(e)}")
            raise

