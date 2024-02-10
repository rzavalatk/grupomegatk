from odoo import models, fields

class SorteoProducts(models.Model):
    _name = 'sorteo.products'
    _description = 'Productos cuentan como doble'

    product = fields.Many2one('product.product',string='Producto', required=True)
    fecha_inicial = fields.Date(string='Fecha Inicial', required=True)
    fecha_final = fields.Date(string='Fecha Final', required=True)