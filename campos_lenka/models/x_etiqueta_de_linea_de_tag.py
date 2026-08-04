# -*- coding: utf-8 -*-

from odoo import fields, models


class EtiquetaLineaDeTag(models.Model):
    _inherit = "x_etiqueta_de_linea_de_tag"

    partner_ids = fields.Many2many(
        "res.partner",
        string="Contactos",
    )