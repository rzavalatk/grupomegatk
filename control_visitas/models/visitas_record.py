#-*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import UserError
from datetime import date
import logging

_logger = logging.getLogger(__name__)


class Visitas_Record(models.Model):
    _name = 'registro.visitas'
    _description = 'Modelo de visitas diarias a las sucursales'
    
    def _compute_name(self):
        for record in self:
            record.name_reporte = f"Reporte de Visitas {str(record.fecha_reporte)}"
            
   
            
    # fecha_act = fields.Date(string='Fecha', defau=date.today() ,store=True)
    name_reporte = fields.Char(string='Reporte', compute='_compute_name')
    fecha_reporte = fields.Date(string='Fecha', required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id, required=True)
    
    visita_diaria = fields.One2many('control.visitas', 'registro_visita', string='Registro Visitas')
    visitas_registradas = fields.One2many('control.visitas', 'registro_visita', string='Registro Visitas')
 

    
    def agrupar_registros(self):
        visitas = self.env['control.visitas'].sudo().search([('fecha', '=', self.fecha_reporte)])
        self.visitas_registradas = visitas
        _logger.warning(f"FECHA ACTUAL CORREO DESDE FUN AGRUPAR: {visitas}")
        # visitas = self.env['control.visitas'].sudo().search([('fecha', '=', self.fecha_act)])
        if not visitas:
            raise UserError("No hay registros de visitas en esa fecha")
        else:
            self.visita_diaria = visitas
            
        return visitas
    
   
    

    