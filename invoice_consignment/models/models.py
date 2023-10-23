# -*- coding: utf-8 -*-

from odoo import models, api,fields
from odoo.exceptions import Warning

class Facturas(models.Model):
    _inherit="account.invoice"
    
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
    
    @api.model
    def create(self,val):
        try:
            context = self.env.context
            data = self.env['res.config.settings'].sudo().get_data_consignacion()
            if context.get('de_consignacion'):
                val['journal_id'] = data['journal_id']
                val['account_id'] = data['account_id']
                val['de_consignacion'] = context.get('de_consignacion')
            else: 
                journal_ids = self.env['account.journal'].search([('type','=','sale'),('company_id','=',self.env.user.company_id.id)])
                journal_id = [i.id for i in journal_ids]
                for item in journal_id:
                    if item != int(data['journal_id']):
                        val['journal_id'] = item
                        
            res = super(Facturas,self).create(val)
            return res
        except:
            raise Warning('No hay Diario ni Cuenta de Consignacion en la configuración. Contacte a su administrador.')
    
    @api.onchange('sequence_ids')
    def _onchange_sequence_ids(self):
            context = self.env.context
            data = self.env['res.config.settings'].sudo().get_data_consignacion()
            journal_ids = self.env['account.journal'].search([('type','=','sale'),('company_id','=',self.env.user.company_id.id)])
            journal_id = [i.id for i in journal_ids]
            if context.get('de_consignacion'):
                    if int(data['journal_id']) == 0:
                        text = """No hay Diario ni Cuenta de Consignacion en la configuración para este tipo de Facturas: Porfavor no crear registros para evitar errores en el sistema
                            
                            Contacte a su Administrador inmediatamente despues de ver este Mensaje.
                        """
                        raise Warning(text)
                    self.journal_id = int(data['journal_id'])
            else:
                for item in journal_id:
                    if item != int(data['journal_id']):
                        self.journal_id = item

                    
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
    
    def create_invoices(self):
        res = super(CreateFacturas,self).create_invoices()
        return res
            
        

class LineasFacturas(models.Model):
    _inherit="account.invoice.line"
    
    @api.multi
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
