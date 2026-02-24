# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

#CAMPOS EN VENTAS/PRESUPUESTOS
class Saleorder(models.Model):
    _inherit = "sale.order"

    pricelist_id = fields.Many2one('product.pricelist', copy=False)
    
    #CAMPO EN PRESUPUESTO
    x_valido = fields.Selection([('5','5 días'),('10','10 días'),('15','15 días'),('30','30 días'),('90','90 días'),('nunca','No vence')], string='Días Válidos', default='5')
    #CAMPO EN OTRA INFORMACIÓN
    x_consignacion = fields.Selection([('si','SI'),('no','NO')], string='Consignación', default='no')
    
    x_contacto = fields.Char('Contacto de referencia')
    
    sorteo_id = fields.Many2one('sorteo.sorteo', string='Sorteo', ondelete='set null')
    x_student = fields.Boolean(string='Es Estudiante', default=False)

    def action_confirm(self):
        res = super(Saleorder, self).action_confirm()
        
        if self.payment_term_id.id:
            quote_term =self.env['account.payment.term'].search([('id', '=', self.payment_term_id.id)])
            if quote_term.credit:
                if not self.env.user.has_group('fields_megatk.factura_credito_manager'):
                    raise UserError(_("No tienes permiso para confirmar cotizaciones."))
        
        return res

class SaleorderLine(models.Model):
    _inherit = "sale.order.line"

    x_user_id = fields.Many2one('res.users', default=lambda self: self.env.user, string='Responsable')
    obj_padre = fields.Many2one('res.users', related="order_id.user_id", string="ResponsableTem", readonly=True)
    x_series = fields.Text("Series")
    tax_editable = fields.Boolean('tax e.')
    price_unit = fields.Float(digits=(16, 2))

    def _prepare_invoice_line(self, **optional_values):
        invoice_item_sequence = 0
        values = super(SaleorderLine, self)._prepare_invoice_line(**optional_values)
        values['x_user_id'] = self.x_user_id.id
        values['x_series'] = self.x_series
        return values
       

    """@api.model_create_multi"""
    @api.onchange('product_id')
    def product_id_change1(self):
        self.x_user_id = self.obj_padre
        
