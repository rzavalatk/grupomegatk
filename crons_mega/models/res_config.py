# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class Settings(models.TransientModel):
    _inherit = 'res.config.settings'

    company_cierre = 0
    journal_ids = fields.Many2many(
        "account.journal", "alias_id", string="Diarios de cierre")
    teams_sps = fields.Char("Canales de SPS")
    
    def get_values_journal_ids(self,company):
        self.company_cierre = company
        obj = self.get_values()
        return obj['journal_ids'][0][2]
        
    
    def get_values_teams_sps(self):
        obj = self.get_values()
        res = []
        l = obj['teams_sps'].split(',')
        for item in l:
            res.append(int(item))
        return res
        
    

    @api.model
    def get_values(self):
        res = super(Settings, self).get_values()
        IrValues = self.env['ir.config_parameter'].sudo()
        journal_ids = IrValues.get_param('crons_mega.journal_ids_'+str(self.company_cierre))
        # journal_ids = IrValues.get_param('crons_mega.journal_ids_'+str(self.env.user.company_id.id))
        teams_sps = IrValues.get_param('crons_mega.teams_sps')
        if journal_ids:
            journal_ids = journal_ids.replace('[','')
            journal_ids = journal_ids.replace(']','')
            journal_ids = journal_ids.split(',')
            ids = []
            for item in journal_ids:
                ids.append(int(item))
            lines = False
            if ids:
                lines = [(6, 0, ids)]
            res.update(journal_ids=lines,teams_sps=teams_sps)
        return res

    @api.multi
    def set_values(self):
        IrValues = self.env['ir.config_parameter'].sudo()
        IrValues.set_param('crons_mega.journal_ids_'+str(self.env.user.company_id.id), self.journal_ids.ids)
        IrValues.set_param('crons_mega.teams_sps', self.teams_sps)
        super(Settings, self).set_values()

