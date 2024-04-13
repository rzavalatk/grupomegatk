# -*- coding: utf-8 -*-

from odoo import models, api, fields
from odoo.exceptions import Warning
import requests


class SorteoSorteo(models.Model):
    _name = 'sorteo.sorteo'
    _description = 'Información para el sorteo'

    name = fields.Char(string='Nombre', required=True, copy=False,)
    #compañia = fields.Many2one('res.company', string='Compañia', required=True)
    encargado_id = fields.Many2one('hr.employee', string='Encargado', store=True, ondelete='set null')
    sequence_id = fields.Many2one("ir.sequence", "Secuencia de Ticket")
    fecha_inicio = fields.Date(string='fecha de inicio', help='Fecha desde donde se empezara a contabilizar los tickets')
    fecha_final = fields.Date(string='fecha de cierre', help='Fecha desde donde se terminara de contabilizar los tickets')
    fecha_sorteo = fields.Date(string='fecha de sorteo', help='Fecha donde se hara el sorteo')
    premios = fields.Char(string='Premios')
    
    tickets = fields.One2many('sorteo.ticket', 'sorteo', string='Tickets del Sorteo', help='Tickets relacionados con este sorteo')
    
    fechas_festivas = fields.Many2many('sorteo.fecha_festiva', string='Fechas Festivas')
    productos = fields.Many2many('sorteo.products', string='Productos')
    marcas = fields.Many2many('sorteo.marcas', string='Marcas')

    
