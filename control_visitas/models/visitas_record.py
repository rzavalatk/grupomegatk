#-*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import UserError
from datetime import date
import logging

_logger = logging.getLogger(__name__)


class Visitas_Record(models.Model):
    _name = 'registro.visitas'
    _description = 'Modelo de visitas diarias a las sucursales'
    
  
            
    # fecha_act = fields.Date(string='Fecha', defau=date.today() ,store=True)
    fecha_reporte = fields.Date(string='Fecha', required=True)
    def _compute_name(self):
        for record in self:
            record.name_reporte = f"Reporte de Visitas {str(record.fecha_reporte)}"
        
    name_reporte = fields.Char(string='Reporte', compute='_compute_name')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id, required=True)
    
    visita_diaria = fields.One2many('control.visitas', 'registro_visita', string='Registro Visitas')
    
    def agrupar_registros(self):
        visitas = self.env['control.visitas'].sudo().search([('fecha', '=', self.fecha_reporte)])
       
        # visitas = self.env['control.visitas'].sudo().search([('fecha', '=', self.fecha_act)])
        if not visitas:
            raise UserError("No hay registros de visitas en esa fecha")
        else:
            self.visita_diaria = visitas
            
        return visitas
    
    @api.model    
    def send_email(self, email=None, cc=""):
        visitas = self.env['control.visitas'].sudo().search([('fecha', '=', date.today())])
        
        if not visitas:
            raise UserError("No hay registros de visitas en esa fecha")
        else:
            self.visita_diaria.env['control.visitas'].sudo().browse(428)
            _logger.warning(f"Registros encontrados: {self.visita_diaria}")
        
        template = self.env.ref(
            'control_visitas.email_template_registro_visitas')
        email_values = {

            'email_from': 'megatk.no_reply@megatk.com',
            'email_to': email,
            'email_cc': cc,  
        }
        template.send_mail(visitas.ids, email_values=email_values, force_send=True)
        self.write({
            'state': 'done'
        })
        return True
    
    @api.model
    def datos(self):
        registros = self.env['control.visitas'].search([('fecha', '=', date.today())])
        if not registros:
             raise UserError("No hay registros de visitas en esa fecha ")
         
        correo = "alexdreyesmt@gmail.com"
        
        self.send_email(correo)
    
    
    
   
    

     