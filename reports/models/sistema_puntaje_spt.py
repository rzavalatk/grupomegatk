from itertools import groupby

from odoo import models, fields, api
from datetime import datetime
import time
import pytz

import base64
import io
from odoo.tools.misc import xlsxwriter

import logging

_logger = logging.getLogger(__name__)

class Usuarios(models.Model):
    _inherit = "res.users"

    puntaje_id = fields.Many2one("sistema.puntaje.soporte")

class SistemaPuntajeSoporte(models.Model):
    _name = 'sistema.puntaje.soporte'
    _description = 'Sistema de puntaje para comisiones de soporte tecnico'
    
    def _name_(self):
        
            if len(self.users_ids) > 1:
                    self.name = self.company_id.name + " - " + self.users_ids
            else:
                user_id = {}
                for item in self.users_ids:
                    user_id = item

                self.name = user_id.name

    
    name = fields.Char("Nombre", compute=_name_)
    company_id = fields.Many2one(
        "res.company", "Compañia", default=lambda self: self.env.user.company_id.id)
    users_ids = fields.Many2many("res.users", "puntaje_id", string="Usuarios")
    fecha_inicio = fields.Date('Fecha inicial')
    fecha_final = fields.Date('Fecha final')
    
    state = fields.Selection([
        ("draft", "Borrador"),
        ("init", "Iniciado"),
        ("proccess", "Proceso"),
        ("done", "Hecho"),
        ("cancel", "Cancelado")
    ], string="Estado", default="draft")
    
    Tabla_puntaje = fields.One2many(
        'sistema.tabla.puntaje', 'sistema_puntaje', string="Tabla de puntos", readonly=True)
    
    Tabla_detalle = fields.One2many(
        'sistema.detalles.puntaje', 'sistema_puntaje', string="Detalles", readonly=True)
    
    marcas = ["evolis", "zebra", "pos", "etiquetas", "ploter", "traslados"]
    
    servicios = ["evl_1", "evl_2", "evl_3", "evl_4", "evl_5", "evl_6",
                 "zeb_1", "zeb_2",
                 "pos_1", 
                 "etq_1",
                 "plt_1", "plt_2", "plt_3",
                 "tls_1"
                 ]
    
    tipos = ["taller", "visita", "llamada"]
    
    lines_total = []
    lines_detallado = []
    
    """def generate_report(self):
    
        domain = ['&', '&', '&',
                ('create_date', '>=', self.fecha_inicio),
                ('create_date', '<=', self.fecha_final),
                ('contabilizado', '=', False),
                ('user_id', 'in', self.users_ids)
            ]
            
        tickets = self.env['crm.lead'].search(domain)
        
        if tickets:
            for ticket in tickets:
                for marca in self.marcas:
                    if ticket.marca == marca:
                        for servicio in self.servicios:
                            if ticket."""
                    
                        
        
    
    
    
class TablaPuntaje(models.Model):
    _name = "sistema.tabla.puntaje"
    _description = "Tabla de puntaje del sistema para puntuar comisiones a soporte"
    
    sistema_puntaje = fields.Many2one(
        'sistema.puntaje.soporte', string="Tabla de puntos", ondelete='cascade')
    
    tecnico_id = fields.Many2one('res.users', string='Tecnico')
    marcas_id = fields.Char('Marca mas puntuada')
    servicio_id = fields.Char('Servicio mas puntuado')
    taller_id = fields.Integer('Puntos taller')
    visita_id = fields.Integer('Puntos visita')
    llamada_id = fields.Integer('Puntos llamada')
    total = fields.Integer('Total')
    
    

class PuntajeDetalles(models.Model):
    _name = "sistema.detalles.puntaje"
    _description = "Resumen detallado de los tickets puntuados"
    
    sistema_puntaje = fields.Many2one(
        'sistema.puntaje.soporte', string="Detalles", ondelete='cascade')
    
    tecnico_id = fields.Many2one('res.users', string='Tecnico')
    marcas_id = fields.Char('Marca ')
    servicio_id = fields.Char('Servicio')
    taller_id = fields.Integer('Puntos taller')
    visita_id = fields.Integer('Puntos visita')
    llamada_id = fields.Integer('Puntos llamada')
    