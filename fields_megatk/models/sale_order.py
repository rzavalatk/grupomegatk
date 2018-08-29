# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class Saleorder(models.Model):
    _inherit = "sale.order"

    # tipo_lead = fields.Selection([('arrendamiento', 'Arrendamiento'), ('venta', 'Venta Directa'), 
    #     ('ventaarenta', 'Venta/Arrendamiento')], string='Tipo de Venta', required=True, default='arrendamiento')

    # monocromaticas_fijas = fields.Char("Impresiones Fijas Monocromaticas")
    # color_fijas = fields.Char("Impresiones Fijas Color")
    # mensualidad_total = fields.Monetary("Renta Mensual")

    # # Costos adicionales
    # monocromaticas_adicional = fields.Float("Costo Adicional Monocromaticas", digits=(12, 4))
    # color_adicional = fields.Float("Costo Adicional Color", digits=(12, 4))
    # imagen_digitalizada = fields.Monetary("Costo imagen digitalizada")
    # deposito = fields.Monetary("Deposito")
    # adicional_software = fields.Monetary("Software de administración")
    # corte_software = fields.Monetary("Sistema automatización de cortes de facturación")

    # tiempo_contrato = fields.Char("Tiempo de contrato")
    # inicio_proyecto = fields.Integer("Inicio de proyecto")
    # tiempo_mantenimiento = fields.Integer("Tiempo de mantenimiento")
    # aplica_color = fields.Boolean("Apllica color")

    x_valido = fields.Selection([('5','5 días'),('10','10 días'),('15','15 días'),('90','90 días')], string='Días Válidos', default='5')

class SaleorderLine(models.Model):
    _inherit = "sale.order.line"

    x_user_id = fields.Many2one('res.users', default=lambda self: self.env.user, string='Responsable')
    obj_padre = fields.Many2one(related="order_id.user_id", string="ResponsableTem")
    x_series = fields.Text("Series")
    

    @api.multi
    def _prepare_invoice_line(self, qty):
        values = super(SaleorderLine, self)._prepare_invoice_line(qty)
        values['x_user_id'] = self.x_user_id.id
        values['x_series'] = self.x_series
        return values

    @api.multi
    @api.onchange('product_id')
    def product_id_change1(self):
        self.x_user_id = self.obj_padre.id
        
