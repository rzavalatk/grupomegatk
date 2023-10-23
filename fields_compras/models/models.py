# -*- coding: utf-8 -*-

from email.policy import default
from odoo import models, api, fields


class Payment(models.Model):
    _inherit = 'account.payment'
    
    
    regiones = [0,'Nicaragua','San Pedro Sula','Tegucigalpa']
    region = fields.Selection([
        ('Tegucigalpa','TGU'),
        ('San Pedro Sula','SPS'),
        ('Nicaragua','NIC'),
    ],string="Región",required=True,
    default=lambda self : self.regiones[int(self.env.user.ubicacion_vendedor)])



class ModelCompras(models.Model):
    _inherit = 'purchase.order'

    cubing = fields.Float("Cubicaje total")
    weight = fields.Float("Peso total")
    code_reference = fields.Char("Código de Referencia")
    origin_city = fields.Char("Ciudad de origen")
    
    
class Productos(models.Model):
    _inherit = 'product.template'

    ala = fields.Char("Ala")
    estante = fields.Char("Estante")
    nivel = fields.Char("Nivel")


class ModelImport(models.Model):
    _inherit = 'import.product.mega'

    @api.one
    def _brand_produt(self):
        try:
            self.brand_produt = self.import_line_id[0].product_id.marca_id.id
            self.write({
                "brand_name": self.import_line_id[0].product_id.marca_id.name
            })
        except :
            self.brand_produt = ""
            self.write({
                "brand_name": ""
            })

    brand_produt = fields.Many2one('product.marca',"Marca", compute=_brand_produt)
    brand_name = fields.Char()
    

