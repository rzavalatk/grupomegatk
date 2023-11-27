# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

#Campo de comisión pagada en las facturas
class Account_Move(models.Model):
    _inherit = "account.move"

    x_comision = fields.Selection([('1','SI'),('2','NO')], string='Comisión Pagada', required=True, default='2')
    invoice_payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms',
        check_company=True,
        readonly=False, required=False,)
    
    #mostrar boton en factura de borrados
    def go_draft(self):
        self.write({
            'state': 'draft'
        })
    
    
class AccountInvoiceLine(models.Model):
    _inherit = "account.move.line"

    x_user_id = fields.Many2one('res.users', default=lambda self: self.env.user, string='Responsible')
    obj_padre = fields.Many2one(related="move_id.user_id", string="ResponsibleTem")
    x_series = fields.Text("Series")

    @api.onchange('product_id')
    def product_id_change1(self):
        self.x_user_id = self.obj_padre.id
