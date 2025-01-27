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
    tipo_soporte = fields.Selection([('llamada','Llamada'),('interno','Interno'),('visita','Visita'),('visita_sin_costo','Visita sin costo'),('taller','Taller'),('sin_costo','Sin Costo')], string='Tipo de Soporte', default='sin_costo')
    estado_taller = fields.Selection([('sinrevision','Sin Revisión'),('enreparacion','En Reparación'),('diagnostico','Diagnóstico'),('pendaprov','Pend. Aprobación'),('rma','RMA'),('reparado','Reparado'),('equipo_x_entregar','Equipo por entregar'),('entregado','Entregado')], string='Estado del Equipo', default='sinrevision')
    tipo_visita = fields.Selection([('cortesia','Cortesía'),('contado','Contado'),('garantia','Garantía'),('capacitacion','Capacitación'),('instalacion','Instalación')], string='Tipo de Visita')
    tipo_visita_sin_costo = fields.Selection([('cortesia','Cortesía'),('garantia','Garantía'),('capacitacion','Capacitación'),('instalacion','Instalación')], string='Tipo de Visita.')
    tipo_venta = fields.Selection([('llamada','Llamada'),('visitac','Visita Calle'),('visitat','Visita Tienda')], string='Venta', default='llamada')
    reporto = fields.Char(string='La persona que reporto',)
    repor_tel = fields.Char(string='Telefono',)
    repor_email = fields.Char(string='Correo electrónico',)
    repor_direction = fields.Char(string='Direccion de la visita')
    proposito = fields.Char(string='Propósito de la visita',)
    proposito_llamada = fields.Text("Proposito de la llamada")
    observacion_visita = fields.Html(string='Observaciones')
    producto1 = fields.Char(string='Campaña',)
    producto2 = fields.Char(string='Media',)
    producto3 = fields.Char(string='Origen',)
    fecha_movimiento = fields.Datetime(string='Fecha primer movimiento',)
    

    marca_spt = fields.Many2one('crm.lead.marca', string='Marca servicio', domain=[('spt', '=', True), ('active', '=', True)])
    tipo_servicio = fields.Selection([('taller','Taller'),('visita','Visita'),('llamada','Llamada')], string='Tipo de Servicio', default='taller')
    servicio_spt = fields.Many2one('crm.servicio', string='Servicio')
   
    
    tecnico_asistente_1 = fields.Many2one('res.users', string='1er Asistente')
    tecnico_asistente_2 = fields.Many2one('res.users', string='2do Asistente')
    tecnico_asistente_3 = fields.Many2one('res.users', string='3er Asistente')
    
    puntuado = fields.Boolean('Puntuado', default=False, readonly=True)


    @api.onchange('marca_spt')
    def onchange_marca_spt(self):
        if self.marca_spt:
            return {'domain': {'servicio_spt': [('marca_id', '=', self.marca_spt.id)]}}
        else:
            return {'domain': {'servicio_spt': []}}
    
    @api.onchange('marca_id')
    def _onchange_marca_id(self):
        self.categoria_id=False
        self.modelo_id=False

    @api.onchange('partner_id','company_id')
    def _onchange_name_opportunity(self):
        if self.partner_id and self.company_id:
            if self.tipo_id.id == 6:
                self.name = "Proyectos / " + self.partner_id.name
            if self.tipo_id.id == 37:
                self.name = "MDTKSA / " + self.partner_id.name
            if self.tipo_id.id == 5:
                self.name = "SPCHINE / " + self.partner_id.name
            if self.tipo_id.id == 1:
                self.name = "MGTK / " + self.partner_id.name
            if self.tipo_id.id == 2:
                self.name = "PRTX / " + self.partner_id.name
            if self.tipo_id.id == 3:
                self.name = "SPT / " + self.partner_id.name
            if self.tipo_id.id == 4:
                self.name = "MDTK / " + self.partner_id.name
  
    def write(self, values):
        if not self.fecha_movimiento:
            if self.create_uid.id != self.env.user.id:
                #self.fecha_movimiento = datetime.now()  
                values['fecha_movimiento'] = datetime.now()
        return super(CrmLead, self).write(values)

 
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
    spt = fields.Boolean(string='SPT', default=False, help='Sistema de puntaje spt si esta disponible')

class CrmLeadCategoria(models.Model):
    _name = 'crm.lead.categoria'
    _order = 'name asc'

    name = fields.Char(string='Nombre:',)
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


class CrmServicio(models.Model):
    _name = 'crm.servicio'
    
    name = fields.Char(string='Nombre', required=True)
    marca_id = fields.Many2one('crm.lead.marca', string='Marca', ondelete='cascade', required=True, domain=[('spt', '=', True)])
    puntaje_taller = fields.Integer(string='Puntaje Taller', required=True)
    puntaje_llamada = fields.Integer(string='Puntaje Llamada', required=True)
    puntaje_visita = fields.Integer(string='Puntaje Visita', required=True) 
    active = fields.Boolean(string='Activo', default=True)