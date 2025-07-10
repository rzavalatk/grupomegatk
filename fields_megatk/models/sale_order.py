# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

#CAMPOS EN VENTAS/PRESUPUESTOS
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
    pricelist_id = fields.Many2one(copy=False)

    #CAMPO EN PRESUPUESTO
    x_valido = fields.Selection([('5','5 días'),('10','10 días'),('15','15 días'),('30','30 días'),('90','90 días'),('nunca','No vence')], string='Días Válidos', default='5')
    #CAMPO EN OTRA INFORMACIÓN
    x_consignacion = fields.Selection([('si','SI'),('no','NO')], string='Consignación', default='no')
    
    x_contacto = fields.Char('Contacto de referencia')
    
    sorteo_id = fields.Many2one('sorteo.sorteo', string='Sorteo')
    x_student = fields.Boolean(string='Es Estudiante', default=False)

    def action_confirm(self):
        res = super(Saleorder, self).action_confirm()
        if not self.env.user.has_group('fields_megatk.factura_credito_manager'):
            raise UserError(_("No tienes permiso para confirmar cotizaciones."))
        return res
    
#CAMPOS EN SECCION INFERIOR EN PAGE LINEAS DEL PEDIDO
class SaleorderLine(models.Model):
    _inherit = "sale.order.line"

    x_user_id = fields.Many2one('res.users', default=lambda self: self.env.user, string='Responsable')
    obj_padre = fields.Many2one(related="order_id.user_id", string="ResponsableTem")
    x_series = fields.Text("Series")
    tax_editable = fields.Boolean('tax e.')
    price_unit = fields.Float(digits=(16, 2))

    def _prepare_invoice_line(self, **optional_values):
        invoice_item_sequence = 0
        values = super(SaleorderLine, self)._prepare_invoice_line(**optional_values)
        values['x_user_id'] = self.x_user_id.id
        values['x_series'] = self.x_series
        return values
        

    """@api.onchange('x_user_id')
    def onchange_x_user_id(self):
        # Puedes realizar acciones adicionales aquí si es necesario
        self.x_user_id = x_user_id"""
    

    """@api.model_create_multi"""
    @api.onchange('product_id')
    def product_id_change1(self):
        self.x_user_id = self.obj_padre.id
        
