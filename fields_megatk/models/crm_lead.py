# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError

class CrmLead(models.Model):
    _inherit = "crm.lead"

    serie = fields.Char(string='Numero de serie',)
    marca_id = fields.Many2one('crm.lead.marca', string='Marca', domain=[('active', '=', True)])
    categoria_id = fields.Many2one('crm.lead.categoria', string='Categoria', domain=[('active', '=', True)])
    modelo_id = fields.Many2one('crm.lead.modelo', string='Modelo', domain=[('active', '=', True)])
    accesorio_ids = fields.Many2many('crm.lead.accesorios', string='Accesorios',)
    fallas = fields.Text("Fallas")
    informe_tecnico = fields.Text("Informe técnico")
    tipo_id = fields.Many2one('crm.lead.tipo', string='Título de oportunidad',)
    tipo_soporte = fields.Selection([('llamada','Llamada'),('interno','Interno'),('visita','Visita'),('visita_sin_costo','Visita sin costo'),('taller','Taller'),('sin_costo','Sin Costo')], string='Tipo de Soporte', default='llamada')
    estado_taller = fields.Selection([('sinrevision','Sin Revisión'),('enreparacion','En Reparación'),('diagnostico','Diagnóstico'),('pendaprov','Pend. Aprobación'),('rma','RMA'),('reparado','Reparado'),('equipo_x_entregar','Equipo por entregar'),('entregado','Entregado')], string='Estado del Equipo', default='sinrevision')
    tipo_visita = fields.Selection([('cortesia','Cortesía'),('contado','Contado'),('garantia','Garantía'),('capacitacion','Capacitación'),('instalacion','Instalación')], string='Tipo de Visita')
    tipo_visita_sin_costo = fields.Selection([('cortesia','Cortesía'),('garantia','Garantía'),('capacitacion','Capacitación'),('instalacion','Instalación')], string='Tipo de Visita.')
    tipo_venta = fields.Selection([('llamada','Llamada'),('visitac','Visita Calle'),('visitat','Visita Tienda')], string='Venta', default='llamada')
    reporto = fields.Char(string='Persona que reporto',)
    repor_tel = fields.Char(string='Telefono',)
    repor_email = fields.Char(string='Correo electrónico',)
    proposito = fields.Char(string='Propósito de la visita',)
    observacion_visita = fields.Html(string='Observaciones')
    producto1 = fields.Char(string='Producto',)
    producto2 = fields.Char(string='Producto',)
    producto3 = fields.Char(string='Producto',)
    fecha_movimiento = fields.Datetime(string='Fecha primer movimiento',)


    @api.onchange('marca_id')
    def _onchange_marca_id(self):
        self.categoria_id=False
        self.modelo_id=False

    @api.multi
    def write(self, values):
        if not self.fecha_movimiento:
            if self.create_uid.id != self.env.user.id:
                #self.fecha_movimiento = datetime.now()  
                values['fecha_movimiento'] = datetime.now()
        return super(CrmLead, self).write(values)

    @api.multi
    def _message_post_after_hook(self, message, *args, **kwargs):
        self.observacion_visita = message.body
        return super(CrmLead, self)._message_post_after_hook(message,*args, **kwargs)

    @api.onchange('categoria_id')
    def _onchange_categoria_id(self):
        self.modelo_id=False

    @api.onchange('tipo_id')
    def _onchange_tipo_id(self):
        self.name=self.tipo_id.name

    def imprimir_soporte(self):
        self.ensure_one()
        if self.tipo_soporte == 'taller':
            self.send_email_with_attachment()
            return self.env.ref('fields_megatk.crm_orden_ingreso').report_action(self)
        elif self.tipo_soporte == 'visita':
            return self.env.ref('fields_megatk.crm_visita_tecnica').report_action(self)
    
    def send_email_with_attachment(self):
        template = self.env.ref('fields_megatk.email_template_ingreso_taller')
        email_values = {'email_to': self.email_from ,
            'email_from': self.env.user.email}
        template.send_mail(self.id, email_values=email_values, force_send=True)
        return True

class CrmLeadTipo(models.Model):
    _name = 'crm.lead.tipo'
    _order = 'name asc'

    name = fields.Char(string='nombre',)
    active = fields.Boolean(string='Activo', default=True)

class CrmLeadMarca(models.Model):
    _name = 'crm.lead.marca'
    _order = 'name asc'

    name = fields.Char(string='Nombre',)
    categoria_ids = fields.One2many('crm.lead.categoria', 'marca_id', string='categoria',)
    active = fields.Boolean(string='Activo', default=True)

class CrmLeadCategoria(models.Model):
    _name = 'crm.lead.categoria'
    _order = 'name asc'

    name = fields.Char(string='Nombre',)
    marca_id = fields.Many2one('crm.lead.marca', string='Marca', ondelete='cascade')
    modelo_ids = fields.One2many('crm.lead.modelo', 'categoria_id',  string='Modelo',)
    active = fields.Boolean(string='Activo', default=True)

class CrmLeadModelo(models.Model):
    _name = 'crm.lead.modelo'
    _order = 'name asc'
    
    name = fields.Char(string='Nombre',)
    categoria_id = fields.Many2one('crm.lead.categoria', string='Categoria', ondelete='cascade')
    active = fields.Boolean(string='Activo', default=True)
    
class CrmLeadAccesorios(models.Model):
    _name = 'crm.lead.accesorios'
    _order = 'name asc'
    
    name = fields.Char(string='Nombre',)
    active = fields.Boolean(string='Activo', default=True)