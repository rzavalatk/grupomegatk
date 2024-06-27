from odoo import models,fields

class ofertas(models.Model):
    _name = "offers.property"
    _description = "Oferta"

    price = fields.Float('Precio')
    status = fields.Selection([
        ('accepted', 'Aceptado'),
        ('refused','Rechazado')
    ], copy = False, string='Estatus')
    partner_identification = fields.Many2one('res.partner', string='Identificacion de socio', required=True)
    property_id = fields.Many2one('test.model', string='ID de propiedad', required=True)
