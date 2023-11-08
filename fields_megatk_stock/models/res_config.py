# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Settings(models.TransientModel):
    _inherit = 'res.config.settings'

    users_ids = fields.Many2many("res.users", "partner_id", string="Usuarios")
    
    @api.model_create_multi
    def get_values(self):
        res = super(Settings, self).get_values()
        IrValues = self.env['ir.config_parameter'].sudo()
        users_ids = IrValues.get_param('fields_megatk_stock.users_ids_foces_confirm_sales')
        if users_ids:
            users_ids = users_ids.replace('[','')
            users_ids = users_ids.replace(']','')
            users_ids = users_ids.split(',')
            ids = []
            for item in users_ids:
                ids.append(int(item))
            lines = False
            if ids:
                lines = [(6, 0, ids)]
            res.update(users_ids=lines)
        return res

    @api.model_create_multi
    def set_values(self):
        IrValues = self.env['ir.config_parameter'].sudo()
        IrValues.set_param('fields_megatk_stock.users_ids_foces_confirm_sales',self.users_ids.ids)
        super(Settings, self).set_values()