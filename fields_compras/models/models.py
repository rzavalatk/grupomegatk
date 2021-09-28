# -*- coding: utf-8 -*-

from odoo import models, api, fields


class ModelCompras(models.Model):
    _inherit = 'purchase.order'

    @api.one
    def _count_compute(self):
        self.write({
            "count": len(self.order_line) + 0.0
        })
        self.count_compute = len(self.order_line) + 0.0


    cubing = fields.Float("Cubicaje total")
    weight = fields.Float("Peso total")
    code_reference = fields.Char("Código de Referencia")
    count = fields.Float()
    count_compute = fields.Float("Total",compute=_count_compute)