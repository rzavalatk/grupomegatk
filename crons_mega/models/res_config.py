# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import Warning

import logging

_logger = logging.getLogger(__name__)


class Settings(models.TransientModel):
    _inherit = 'res.config.settings'

    company_cierre = 0
    puntero = 0
    journal_ids = fields.Many2many(
        "account.journal", "alias_id", string="Diarios de cierre")
    teams_sps = fields.Char("Canales de SPS")
    account_ids_cron_mega = fields.Many2many(
        "account.account", "code", string="Cuentas Cxc para cierre")
    marca_ids = fields.Many2many(
        "product.marca", "setting_id", string="Marcas")
    
    def get_values_journal_ids(self, company):
        
        _logger.warning("Este es el ID: "+str(company))
        _logger.warning("Este es el ID de company_cierre: "+str(self.company_cierre))
        
       
        self.write({'company_cierre': company})
        
        obj = self.get_values()
        _logger.warning("Este es el ID de company_cierre 2: "+str(self.company_cierre))
        _logger.warning("Este es journal_ids: "+str(obj['journal_ids']))   
        
        
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
        
    #@api.model_create_multi
    def get_values(self):
        try:
            res = super(Settings, self).get_values()
            IrValues = self.env['ir.config_parameter'].sudo()
            marca_ids = IrValues.get_param('crons_mega.marca_ids'+str(self.env.user.company_id.id))
            journal_ids = IrValues.get_param('crons_mega.journal_ids_'+str(self.company_cierre[0]))
            account_ids_cron_mega = IrValues.get_param('crons_mega.account_ids_cron_mega_'+str(self.company_cierre[0])) 
            lines = []
            lines_account = []
            marcas = []
            marcas_ids = []
            
            #_logger.warning("Este es el ID en get_values: "+str(company))
            
            
            
            try:
                marca_ids = marca_ids.replace('[','')
                marca_ids = marca_ids.replace(']','')
                marca_ids = marca_ids.split(',')
                for item in marca_ids:
                    marcas_ids.append(int(item))
                    _logger.warning(item)
                if marcas_ids:
                    marcas = [(6, 0, marcas_ids)]
            except:
                pass
            
            account_ids = []
            if not account_ids_cron_mega:
                account_ids_cron_mega = IrValues.get_param('crons_mega.account_ids_cron_mega_'+str(self.env.user.company_id.id)) 
            try:
                account_ids_cron_mega = account_ids_cron_mega.replace('[','')
                account_ids_cron_mega = account_ids_cron_mega.replace(']','')
                account_ids_cron_mega = account_ids_cron_mega.split(',')
                for item in account_ids_cron_mega:
                    account_ids.append(int(item))
                if account_ids:
                    lines_account = [(6, 0, account_ids)]
            except:
                pass
                
            ids = []
            if not journal_ids:
                journal_ids = IrValues.get_param('crons_mega.journal_ids_'+str(self.env.user.company_id.id))    
            try:
                journal_ids = journal_ids.replace('[','')
                journal_ids = journal_ids.replace(']','')
                journal_ids = journal_ids.split(',')
                for item in journal_ids:
                    ids.append(int(item))
                if ids:
                    lines = [(6, 0, ids)]
            except:
                pass
            res.update(journal_ids=lines,account_ids_cron_mega=lines_account,marca_ids=marcas)
        except Exception as e:
            pass
            # raise Warning(_(f'Error: {e}'))
        
        if self.company_cierre:
            self.company_cierre.pop(0)
            
        #self.company_cierre.append(1)
        return res

    #@api.model_create_multi
    def set_values(self):
        IrValues = self.env['ir.config_parameter'].sudo()
        IrValues.set_param('crons_mega.marca_ids'+str(self.env.user.company_id.id), self.marca_ids.ids)
        IrValues.set_param('crons_mega.account_ids_cron_mega_'+str(self.env.user.company_id.id), self.account_ids_cron_mega.ids)
        IrValues.set_param('crons_mega.journal_ids_'+str(self.env.user.company_id.id), self.journal_ids.ids)
        IrValues.set_param('crons_mega.teams_sps', self.teams_sps)
        super(Settings, self).set_values()

