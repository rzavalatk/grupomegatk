# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

#Campo de comisión pagada en las facturas
class Account_Move(models.Model):
    _inherit = "account.move"

    x_comision = fields.Selection([('1','SI'),('2','NO')], string='Comisión Pagada', required=True, default='2')
    
    #mostrar boton en factura de borrados
    def go_draft(self):
        self.write({
            'state': 'draft'
        })
    
    
class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    x_user_id = fields.Many2one('res.users', default=lambda self: self.env.user, string='Responsable')
    x_series = fields.Text("Series")

    @api.model_create_multi
    @api.onchange('product_id')
    def product_id_change1(self):
        if self.move_id:
            self.x_user_id = self.move_id.user_id.id
