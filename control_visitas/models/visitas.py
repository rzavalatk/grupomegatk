from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime
import logging
import base64

_logger = logging.getLogger(__name__)

class Visitas(models.Model):
    _name = 'control.visitas'
    _description = 'Control de Visitas'
    
    name = fields.Char(string='Nombre')
    fecha = fields.Datetime(string='Fecha y Hora', compute='_compute_fecha', store=True)
    region = fields.Char(string='Region', compute='_compute_region', store=True)
    user_id = fields.Many2one('res.users', string='Usuario', default=lambda self: self.env.user, store=True)
    
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
            record.fecha = datetime.now()
 
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
        
    def enviar_correo_con_reporte(self):
        """
        Envía un correo electrónico con el reporte adjunto.
        """
        # Obtener el template de correo
        template = self.env.ref('control_visitas.email_template_reporte_visitas', raise_if_not_found=False)
        if not template:
            _logger.error("Plantilla de correo no encontrada.")
            return

        # Obtener el reporte PDF
        report = self.env['ir.actions.report']._get_report_from_name('control_visitas.report_pdf')
        pdf_content, _ = report._render_qweb_pdf(self.ids)

        # Adjuntar el PDF al correo
        attachment = self.env['ir.attachment'].create({
            'name': f"Reporte_Visitas_{self.name}.pdf",
            'type': 'binary',
            'datas': base64.b64encode(pdf_content),
            'res_model': 'control.visitas',
            'res_id': self.id,
            'mimetype': 'application/pdf',
        })

        # Enviar el correo
        if self.user_id.email:
            template.send_mail(self.id, force_send=True, email_values={
                'attachment_ids': [attachment.id],
                'email_to': 'alexdreyesmt@gmail.com',
            })
            _logger.warning(f"Correo enviado a alexdreyesmt@gmail.com")
        else:
            _logger.warning(f"No se encontró un correo para el usuario ar")   