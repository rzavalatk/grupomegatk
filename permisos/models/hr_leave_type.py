from odoo import models, fields, api
import datetime
import pytz


class HrLeave(models.Model):
    _inherit = "hr.leave.type"
    _description = "Tipos de permiso"
    
    vacaciones = fields.Boolean('Vacaciones')
    deducciones = fields.Boolean('Deducción de sueldo')
    sin_cargo = fields.Boolean('Sin cargo')
    incapacidad = fields.Boolean('Incapacidad')
    
    @api.onchange('vacaciones')
    def _onchange_vacaciones(self):
        self.deducciones = False
        self.sin_cargo = False
        self.incapacidad = False
    
    @api.onchange('deducciones')
    def _onchange_deducciones(self):
        self.vacaciones = False
        self.sin_cargo = False
        self.incapacidad = False
    
    @api.onchange('sin_cargo')
    def _onchange_sin_cargo(self):
        self.vacaciones = False
        self.deducciones = False
        self.incapacidad = False
    
    @api.onchange('incapacidad')
    def _onchange_incapacidad(self):
        self.vacaciones = False
        self.deducciones = False
        self.sin_cargo = False