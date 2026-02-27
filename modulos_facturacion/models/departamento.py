# -*- coding: utf-8 -*-

from odoo import models, api, fields
import requests


class Departamentos(models.Model):
    _name = 'departamentos.departamentos'
    _description = 'Información para el modulo de departamentos y ciudades'

    name = fields.Char(string='Nombre', required=True, copy=False,)
    #compañia = fields.Many2one('res.company', string='Compañia', required=True)
    codigo_postal = fields.Char(string='Codigo postal', required=True, copy=False,)
    
    ciudades = fields.One2many('departamentos.ciudad', 'departamento', string='Ciudades', help='Ciudades relacionados con este departamento')
    
    

class DepartamentosCiudad(models.Model):
    _name = 'departamentos.ciudad'
    _description = 'Información para el modulo de ciudades importantes de cada departamento'

    name = fields.Char(string='Nombre', required=True, copy=False,)
    #compañia = fields.Many2one('res.company', string='Compañia', required=True)
    departamento = fields.Many2one('departamentos.departamentos', string='Departamento', store=True) 