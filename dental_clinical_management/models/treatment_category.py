# -*- coding: utf-8 -*-
from odoo import fields, models


class TreatmentCategory(models.Model):
    """Agregar la categoría de tratamiento"""
    _name = 'treatment.category'
    _description = "Categoría de Tratamiento"

    name = fields.Char(string="Nombre", help="Nombre de la categoría de tratamiento")