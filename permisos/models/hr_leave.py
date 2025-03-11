# -*- coding: utf-8 -*-
from odoo import models, fields, api


class HrLeave(models.Model):
    _inherit = "hr.leave"
    _description = "Permisos Generales"
    
    datetm_from = fields.Datetime('datetm_from')
    datetm_to = fields.Datetime('datetm_to')
    cubierto_employe_id = fields.Many2one('hr.employee', string='Ausencia cubierta', copy=False,)
    reporto = fields.Selection([('anticipado', 'Anticipado'),('llamada', 'Llamada'),('mensaje', 'Mensaje'),('noreporto', 'No reporto')], default= 'anticipado', copy=False, required=True, track_visibility='onchange')
    justificacion = fields.Text('Motivo' ,copy=False,)

