# -*- coding: utf-8 -*-

from odoo import models, fields, api

class BreadcumCustom(models.Model):
    _name = 'breadcum_custom.images'

    name = fields.Char(string="Nombre")
    image = fields.Binary(string="Imagen")
    website_id = fields.Many2one("website","Sitio web")

    _sql_constraints = [
        ('website_id_uniq', 'unique (website_id)', 'El Sitio web no debe repetirce!')
    ]


class CarouselCustom(models.Model):
    _name = 'carousel.images'


    @api.one
    @api.depends('active')
    def _color(self):
        if self.active:
           self.color = 4
        else:
            self.color = 1

    
    @api.one
    @api.depends('website')
    def _company(self):
        self.company = self.website.company_id

    
    @api.one
    @api.depends('product')
    def _name_product_trunc(self):
        textTrunc = ""
        length = 15
        i = 0
        for char in self.product.name:
            if i < length:
                textTrunc += char
            if i == length:
                textTrunc += "..."
            i += 1
        self.name_product_trunc = textTrunc



    name = fields.Char(string="Nombre")
    description = fields.Text(string="Descripción")
    image = fields.Binary(string="Imagen")
    website = fields.Many2one("website","Sitio web")
    company = fields.Many2one("res.company", compute=_company)
    product = fields.Many2one("product.template","Producto")
    name_product_trunc = fields.Char(compute=_name_product_trunc)
    font_color_name = fields.Char(string="Color del nombre",default='white')
    font_color_description = fields.Char(string="Color de la descripción",default='white')
    label_button = fields.Char(string="Text del boton",default='Ver')
    active = fields.Boolean("Imagen activa", default=True)
    color = fields.Integer(compute=_color,default=4)
    style = fields.Selection([('1', 'Estilo 1'),('2', 'Estilo 2'),],'Estilo',default='1')
    stroke_name = fields.Boolean("Contorno para el nombre", default=False)
    color_stroke_name = fields.Char("Color del contorno")
    size_stroke_name = fields.Integer("Tamaño del contorno")
    stroke_description = fields.Boolean("Contorno para la descripción", default=False)
    color_stroke_description = fields.Char("Color del contorno")


    @api.onchange('stroke_name')
    def _stroke_name(self):
        if self.stroke_name:
           self.color_stroke_name = "white"
           self.size_stroke_name = 1
        else:
            self.color_stroke_name = ""
            self.size_stroke_name = 0


    @api.onchange('stroke_description')
    def _stroke_description(self):
        if self.stroke_description:
           self.color_stroke_description = "white"
        else:
            self.color_stroke_description = ""
    
