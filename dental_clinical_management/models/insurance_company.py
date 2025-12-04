# -*- coding: utf-8 -*-
from odoo import fields, models


class InsuranceCompany(models.Model):
    """Para agregar los detalles del seguro"""
    _name = 'insurance.company'
    _description = "Compañía de Seguros"

    name = fields.Char(string="Nombre", help="Nombre de la compañía de seguros")
    phone = fields.Char(string="Teléfono", help="Número de teléfono de la compañía de seguros")
    email = fields.Char(string="Correo Electrónico", help="Correo electrónico de la compañía de seguros")