from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from odoo.tools import pdf
from datetime import date, datetime
import logging
import pytz

_logger = logging.getLogger(__name__)

class Visitas(models.Model):
    _name = 'control.visitas'
    _description = 'Control de Visitas'
    
    name = fields.Char(string='Nombre')
    fecha = fields.Date(string='Fecha', compute='_compute_fecha', store=True)
    hora = fields.Char(string='Hora', compute='_compute_hora', store=True)
    region = fields.Char(string='Region', compute='_compute_region', store=True)
    user_id = fields.Many2one('res.users', string='Usuario', default=lambda self: self.env.user, store=True)
    
    registro_visita = fields.Many2one('registro.visitas', string='Visitas Diarias')
    
    @api.depends('user_id')
    def _compute_region(self):
        for record in self:
            if record.user_id.ubicacion_vendedor == '3':
                record.region = 'TGU'
            if record.user_id.ubicacion_vendedor == '2':
                record.region = 'SPS'

    @api.depends('user_id')
    def _compute_fecha(self):
        for record in self:
            record.fecha = date.today()
            
    @api.depends('user_id')
    def _compute_hora(self):
        for record in self:
            hora_utc = datetime.now(pytz.utc)
            
            zona_horaria_usuario = self.env.user.tz or 'UTC'
            
            if hasattr(zona_horaria_usuario, 'zone'):
                zona_horaria = zona_horaria_usuario
            else:
                zona_horaria = pytz.timezone(zona_horaria_usuario)
            
            hora_local = hora_utc.astimezone(zona_horaria).strftime('%H:%M:%S')
            record.hora = hora_local
 
    @api.model
    def create(self, vals):
         user = self.env.user
         if user.ubicacion_vendedor == "2" and vals.get('name') in ["Visita Lenka", "Visita Clínica", "Visita Administración"]:
             raise ValidationError("No se puede registrar esta visita en SPS")
         return super(Visitas, self).create(vals)  
      
    @api.model   
    def visita_administracion(self, admin):
        self.create({'name': 'Visita Administración'})
            
    @api.model
    def visita_tienda_megatk(self, vals):
        self.create({'name': 'Visita Tienda Megatk'})

    @api.model
    def visita_tienda_meditek(self, vals):    
        self.create({'name': 'Visita Tienda Meditek'})
    
    @api.model
    def visita_lenka(self, vals):    
        self.create({'name': 'Visita Lenka'})
    
    @api.model
    def visita_clinica(self, vals):
        self.env['control.visitas'].create({'name': 'Visita Clínica'})
        
    def send_email(self, email=None, cc=""):
        registros = self.env['control.visitas'].search([('fecha', '=', self.fecha)])
        visitas = self.env['control.visitas'].browse([(registros)])
        _logger.warning(f"FECHA ACTUAL CORREO DESDE FUN SEND: {visitas}")
        if not visitas:
            raise UserError("No hay registros de visitas en esa fecha")
        else:
            self.visita_diaria = visitas
        
        template = self.env.ref(
            'control_visitas.email_template_registro_visitas')
        email_values = {

            'email_from': 'megatk.no_reply@megatk.com',
            'email_to': "alexdreyesmt@gmail.com",
            'email_cc': cc,
            'visitas_registradas':self.visita_diaria   
        }
        template.send_mail(self.id, email_values=email_values, force_send=True)
        self.write({
            'state': 'done'
        })
        return True
        
    # report = lambda self:self.env['ir.actions.report']._get_report_from_name('control_visitas.report_visita')
    # pdf = report._render_qweb_pdf(docids=[370, 371, 372])  # Pasar los IDs de los registros   
    
    # # def send_email(self,email,cc="",contexto={}):
    #     template = self.env.ref('control_visitas.email_template_visita')
    #     email_values = {
    #         'email_from': 'azelaya@megatk.com',
    #         'email_to': "alexdreyesmt@gmail.com",
    #         'email_cc': cc
    #     }
    #     template.with_context(contexto).send_mail(self.id, email_values=email_values, force_send=True)
    #     self.write({
    #         'state': 'done'
    #     })
    #     return True  
    # lista = self.env['control.visitas'].search([('id', '=', '370')])
    # rec = self.env['control.visitas'].browse(370)
    # _logger.warning(f"Registros obtenidos con browse: {rec.fecha}")
    