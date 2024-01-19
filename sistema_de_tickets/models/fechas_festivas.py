from odoo import models, fields

class FechaFestiva(models.Model):
    _name = 'sorteo.fecha_festiva'
    _description = 'Fechas Festivas para el Sorteo'

    name = fields.Char(string='Nombre', required=True)
    fecha = fields.Date(string='Fecha', required=True)