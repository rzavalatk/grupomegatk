# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class Account_invoice(models.Model):
    _inherit = "account.invoice"

    x_comision = fields.Selection([('1','SI'),('2','NO')], string='Comisión Pagada', required=True, default='2')
    
class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    x_user_id = fields.Many2one('res.users', default=lambda self: self.env.user, string='Responsable')
    obj_padre = fields.Many2one(related="invoice_id.user_id", string="ResponsableTem")
    x_series = fields.Text("Series")

    @api.multi
    @api.onchange('product_id')
    def product_id_change1(self):
        self.x_user_id = self.obj_padre.id