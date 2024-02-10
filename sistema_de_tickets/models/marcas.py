from odoo import models, fields

class SorteoMarcas(models.Model):
    _name = 'sorteo.marcas'
    _description = 'Marcas cuentan como doble'

    marcas = fields.Many2one('product.marca',string='Marcas', required=True)
    fecha_inicial = fields.Date(string='Fecha Inicial', required=True)
    fecha_final = fields.Date(string='Fecha Final', required=True)