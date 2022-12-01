# -*- coding: utf-8 -*-

from odoo import models, api,fields

class Facturas(models.Model):
    _inherit="account.invoice"
    
    
    de_consignacion = fields.Boolean(default=False)
    
    @api.model
    def create(self,val):
        context = self.env.context
        if context.get('de_consignacion'):
            data = self.env['res.config.settings'].get_data_consignacion()
            val['journal_id'] = data['journal_id']
            val['account_id'] = data['account_id']
            val['de_consignacion'] = context.get('de_consignacion')
        return super(Facturas,self).create(val)
    
    @api.onchange('sequence_ids')
    def _onchange_sequence_ids(self):
        context = self.env.context
        data = self.env['res.config.settings'].get_data_consignacion()
        journal_ids = self.env['account.journal'].search([('type','=','sale'),('company_id','=',self.env.user.company_id.id)])
        journal_id = [i.id for i in journal_ids]
        if context.get('de_consignacion'):
            self.journal_id = int(data['journal_id'])
        else:
            for item in journal_id:
                if item != int(data['journal_id']):
                    self.journal_id = item
            
        
        