# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class User(models.Model):
    _inherit = 'res.users'
    
    config_id = fields.Many2one("res.users")

class Settings(models.TransientModel):
    _inherit = 'res.config.settings'

    usuarios_vendedores = fields.Many2many("res.users", "config_id", string="Usuarios")
    

    def get_usuarios_vendedores(self):
        try:
            res = self.get_values()
            return res['usuarios_vendedores'][0][2]
        except Exception as e:
            pass
            #raise Warning(_(f'Error: {e}'))
        
    
    @api.model
    def get_values(self):
        res = super(Settings, self).get_values()
        IrValues = self.env['ir.config_parameter'].sudo()
        usuarios_vendedores = IrValues.get_param('grupos_accesos.usuarios_vendedores_sin_change_comercial')
        if usuarios_vendedores:
            usuarios_vendedores = usuarios_vendedores.replace('[','')
            usuarios_vendedores = usuarios_vendedores.replace(']','')
            usuarios_vendedores = usuarios_vendedores.split(',')
            ids = []
            for item in usuarios_vendedores:
                ids.append(int(item))
            lines = False
            if ids:
                lines = [(6, 0, ids)]
            res.update(usuarios_vendedores=lines)
        return res

    @api.multi
    def set_values(self):
        IrValues = self.env['ir.config_parameter'].sudo()
        IrValues.set_param('grupos_accesos.usuarios_vendedores_sin_change_comercial',self.usuarios_vendedores.ids)
        super(Settings, self).set_values()