# -*- coding: utf-8 -*-

from odoo import fields, models


class DentalTreatment(models.Model):
    """Para agregar detalles del tratamiento dental de los pacientes"""
    _name = 'dental.treatment'
    _description = "Tratamiento Dental"
    _inherit = ['mail.thread']

    name = fields.Char(string='Nombre del Tratamiento', help="Fecha del tratamiento")
    treatment_categ_id = fields.Many2one('treatment.category',
                                         string="Categoría",
                                         help="Nombre del tratamiento")
    cost = fields.Float(string='Costo',
                        help="Costo del Tratamiento")
