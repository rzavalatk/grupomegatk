# -*- coding: utf-8 -*-
from odoo import fields, models

class XRayReport(models.TransientModel):
    """Añadir el reporte de rayos X del paciente."""
    _name = 'xray.report'
    _description = 'Reporte de Rayos X'
    
    patient_id = fields.Many2one('res.partner',
                                 string='Paciente', required=True,
                                 help="nombre del paciente")
    report_date = fields.Date(string='Fecha de Reporte',
                              default=lambda self: fields.Date.context_today(self),
                              required=True,
                              help="fecha de adición del reporte")
    report_file = fields.Binary(string='Archivo de Reporte', required=True,
                                help="Archivo para subir")
    file_name = fields.Char(string="Nombre del Archivo",
                            help="Nombre del archivo")
    description = fields.Text(string='Descripción',
                              help="Para agregar la descripción del reporte de rayos X")
