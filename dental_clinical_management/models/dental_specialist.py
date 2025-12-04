# -*- coding: utf-8 -*-

from odoo import fields, models


class DentalSpecialist(models.Model):
    """médicos Campo especializado"""
    _name = 'dental.specialist'
    _description = "Especialista dental"

    name = fields.Char(string="Nombre", help="Nombre del especialista dental")
    code = fields.Char(string="Código", help="Agregar el código para el nombre")