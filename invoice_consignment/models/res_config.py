# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Settings(models.TransientModel):
    _inherit = 'res.config.settings'

    journal_id = fields.Many2one("account.journal",string="Diario consignación")
    account_id = fields.Many2one("account.account",string="Cuenta consignación")
    
    def get_data_consignacion(self):
        data=self.get_values()
        return {
            "journal_id": data['journal_id'],
            "account_id": data['account_id'],
        }

    #@api.model
    def get_values(self):
        res = super(Settings, self).get_values()
        IrValues = self.env['ir.config_parameter'].sudo()
        journal_id = int(IrValues.get_param('invoice_consignment.journal_id_'+str(self.env.user.company_id.id)))
        account_id = int(IrValues.get_param('invoice_consignment.account_id_'+str(self.env.user.company_id.id)))
        res.update(journal_id=journal_id,account_id=account_id)
        return res

    #@api.model_create_multi
    def set_values(self):
        IrValues = self.env['ir.config_parameter'].sudo()
        IrValues.set_param('invoice_consignment.journal_id_'+str(self.env.user.company_id.id), self.journal_id.id)
        IrValues.set_param('invoice_consignment.account_id_'+str(self.env.user.company_id.id), self.account_id.id)
        super(Settings, self).set_values()