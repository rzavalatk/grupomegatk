from odoo import models, fields, api
import datetime
import pytz


class HrLeave(models.Model):
    _inherit = "hr.leave.type"
    _description = "Tipos de permiso"
    
    vacaciones = fields.Boolean('Vacaciones')