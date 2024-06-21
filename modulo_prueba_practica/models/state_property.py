from odoo import models,fields
from datetime import date, timedelta

class TestModel(models.Model):
    _name = "test.model"
    _description = "Propiedades"

    def tres_meses_futuro():
        fecha_actual = date.today()
        fecha_futura = fecha_actual + timedelta(days=30 * 3)
        return fecha_futura.strftime("%Y-%m-%d")  
    
    tag_ids = fields.Char('Etiqueta')
    name = fields.Char('Nombre', required=True)
    description = fields.Text('Descripcion')
    postcode = fields.Char('Codigo postal')
    date_availability = fields.Date('fecha_disponibilidad', default = tres_meses_futuro() ,copy=False)
    expected_price = fields.Float('Precio esperado',required=True)
    selling_price = fields.Float('Precio de venta', readonly=True, copy=False)
    bedrooms = fields.Integer('Dormitorios', default=2)
    living_area = fields.Integer('Sala de estar')
    facades = fields.Integer('Fachadas')
    garage = fields.Boolean('Garage')
    garden = fields.Boolean('Jardin')
    garden_area = fields.Integer('Zona de jardin')
    garden_orientation = fields.Selection([
        ('north', 'Norte'),
        ('sout', 'Sur'),
        ('est', 'Este'),
        ('west', 'Oeste')
    ], string='orientacion jardin')
    active = fields.Boolean(string='Activo', default = 'True')
    state = fields.Selection([
        ('New', 'Nuevo'),
        ('offer_received', 'Oferta recibida'),
        ('offer_acepted', 'Oferta aceptada'),
        ('sold','Vendido'),
        ('canceled', 'Cancelado')
    ], string='Estado', default = 'draft')
    #property_type_id = fields.Many2one('comodel_name', string='Tipo de propiedad')
    salesman = fields.Many2one('res.partner', string='Comprador')
    buyer = fields.Many2one('res.users', string='Vendedor')

