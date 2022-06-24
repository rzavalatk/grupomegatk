# -*- coding: utf-8 -*-

from odoo import models, fields, api

class VideoWeb(models.Model):
    _name = 'video.web'
    
    name = fields.Char("Nombre")
    url = fields.Char("URL del video")
    position = fields.Char("Posición", readonly=True)
    path = fields.Char("Vista", readonly=True)
    website = fields.Many2one('website', string="Página web", readonly=True)
    width = fields.Char("Anchura (px)")
    height = fields.Char("Altura (px)")
    
    