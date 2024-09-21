# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError

class CrmServiciosSPT(models.Model):
    _name = "crm.lead.servicio"

    name = fields.Char(string='Servicio', required=True)
    marca_id = fields.Many2one('crm.lead.marca', string='Marca', domain=[('active', '=', True), ('spt', '=', True)], required=True)
    puntaje = fields.One2many('crm.lead.puntaje', 'lead_id', string='Puntaje')

class CrmTipoServicio(models.Model):
    _name = 'crm.tipo.servicio'
    _order = 'name asc'

    name = fields.Char(string='nombre',)
    active = fields.Boolean(string='Activo', default=True)
    spt_active = fields.Boolean(string='SPT', default=False, help='Sistema de puntaje spt si esta disponible')

class CRMpuntajeSPT(models.Model):
    _name = 'crm.lead.puntaje'
    _order = 'name asc'

    
    puntaje = fields.Integer(string='Puntaje', required=True)
    lead_id = fields.Many2one('crm.lead.servicio', string='Servicio', required=True)
    id_tipo = fields.Many2one('crm.lead.tipo', string='Tipo', required=True)
    active = fields.Boolean(string='Activo', default=True)
    spt_active = fields.Boolean(string='SPT', default=False, help='Sistema de puntaje spt si esta disponible')