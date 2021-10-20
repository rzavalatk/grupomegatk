# -*- coding: utf-8 -*-

from odoo import models, api, fields


class ModelCompras(models.Model):
    _inherit = 'purchase.order'

    cubing = fields.Float("Cubicaje total")
    weight = fields.Float("Peso total")
    code_reference = fields.Char("Código de Referencia")
    origin_city = fields.Char("Ciudad de origen")


class ModelImport(models.Model):
    _inherit = 'import.product.mega'

    @api.one
    def _brand_produt(self):
        self.brand_produt = self.import_line_id[0].product_id.marca_id.id
        self.write({
            "brand_name": self.import_line_id[0].product_id.marca_id.name
        })

    brand_produt = fields.Many2one('product.marca',"Marca", compute=_brand_produt)
    brand_name = fields.Char()
