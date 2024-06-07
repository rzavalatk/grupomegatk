# -*- coding: utf-8 -*-

from odoo import fields, models


class HrAttendances(models.Model):
    """Inherits HR Attendance model"""
    _inherit = 'hr.attendance'

    checkin_address = fields.Char(string='Dirección de registro', store=True,
                                  help="Dirección de registro del usuario")
    checkout_address = fields.Char(string='Dirección de salida', store=True,
                                   help="Dirección de salida del usuario")
    checkin_latitude = fields.Char(string='Verificar latitud', store=True,
                                   help="Verificar latitud del usuario")
    checkout_latitude = fields.Char(string='Latitud de salida', store=True,
                                    help="Longitud de salida del usuario")
    checkin_longitude = fields.Char(string='Longitud de entrada', store=True,
                                    help="Longitud de entrada del usuario")
    checkout_longitude = fields.Char(string='Longitud de salida', store=True,
                                     help="LOngitud de salida del usuario")
    checkin_location = fields.Char(string='Link de localización de entrada', store=True,
                                   help="Localización de entrada del usuario")
    checkout_location = fields.Char(string='Link de localización de salida', store=True,
                                    help="Link de localización de salida del usuario")
