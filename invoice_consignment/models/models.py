# -*- coding: utf-8 -*-

from odoo import models, api,fields
from odoo.exceptions import UserError

class Facturas(models.Model):
    _inherit="account.move"
    
    def _state_sale(self):
        try:
            if self.consig_sale_id.state == "cancel":
                self.state_sale = False
            else:
                if self.consig_sale_id:
                    self.state_sale = True
                else:
                    self.state_sale = False
        except:
            self.state_sale = False
        
    
    de_consignacion = fields.Boolean(default=False)
    consig_sale_id = fields.Many2one("sale.order","Presupuesto de consignación",default=None)
    state_sale = fields.Boolean(compute=_state_sale)
    
                    
    def create_sale(self):
        lines = []
        for line in self.invoice_line_ids:
            lines.append((0,0,{
                'name': line.product_id.display_name,
                'product_id': line.product_id.id,
                'product_uom_qty': line.quantity,
                'discount': 0.0,
                'price_unit': line.price_unit
            }))
        order = self.env['sale.order'].create({
            'partner_id': self.partner_id.id,
            'user_id': self.user_id.id,
            'validity_date': self.date_invoice,
            'order_line': lines
        })
        self.write({
            'consig_sale_id': order.id
        })
        action = order.env.ref('sale.action_quotations_with_onboarding').read()[0]
        form_view = [(order.env.ref('sale.view_order_form').id, 'form')]
        action['views'] = form_view
        action['res_id'] = order.id
        return action
        

class CreateFacturas(models.TransientModel):
    _inherit="sale.advance.payment.inv"
      

class LineasFacturas(models.Model):
    _inherit="account.move.line"

    @api.onchange('product_id')
    def _onchange_product_id(self):
        context = self.env.context
        self.name = self.product_id.display_name
        if context.get('de_consignacion'):
            data = self.env['res.config.settings'].sudo().get_data_consignacion()
            journal = self.env['account.journal'].browse(data['journal_id'])
            self.account_id = journal.default_debit_account_id.id
            self.invoice_line_tax_ids = None
            self.precio_id = None
