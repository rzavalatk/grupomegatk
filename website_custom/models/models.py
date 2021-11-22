# -*- coding: utf-8 -*-

from odoo import models, fields, api


class BreadcumCustom(models.Model):
    _name = 'breadcum_custom.images'

    name = fields.Char(string="Nombre")
    image = fields.Binary(string="Imagen")
    website_id = fields.Many2one("website", "Sitio web")

    _sql_constraints = [
        ('website_id_uniq', 'unique (website_id)',
         'El Sitio web no debe repetirce!')
    ]
    
    def generate_report(self):
        sql = """
        SELECT  date_invoice as Fecha,
        (SELECT name FROM res_partner as r WHERE r.id = a.partner_id) as Cliente, 
        count(partner_id) as Numero_de_facturas FROM  account_invoice as a 
        WHERE state='paid' AND date_invoice BETWEEN '2021-01-01' AND '2021-12-31' 
        GROUP BY partner_id, date_invoice  
        ORDER BY  date_invoice asc
        """
        self.env.cr.execute(sql)
        data = self.env.cr.fetchall()
        csv = """'Fecha','Cliente','Numero de Facturas',\n"""
        if len(data) > 0:
            for row in data:
                csv_row = ""
                for item in row:
                    item = str(item)
                    item = item.replace('	', '')
                    temp = item.replace(',', '')
                    csv_row+= "{},".format(temp)
                csv+="{}\n".format(csv_row[:-1])
        return csv


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
        if self.product:
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
    website = fields.Many2one("website", "Sitio web",required=True)
    company = fields.Many2one("res.company", compute=_company)
    product = fields.Many2one("product.template", "Producto")
    name_product_trunc = fields.Char(compute=_name_product_trunc)
    font_color_name = fields.Char(string="Color del nombre", default='white')
    font_color_description = fields.Char(
        string="Color de la descripción", default='white')
    label_button = fields.Char(string="Text del boton", default='Ver')
    active = fields.Boolean("Imagen activa", default=True)
    color = fields.Integer(compute=_color, default=4)
    style = fields.Selection(
        [('1', 'Estilo 1 - Producto especifico'), ('2', 'Estilo 2 - Producto especifico'), ('3', 'Estilo 3 - Banner '), ], 'Estilo', default='1')
    stroke_name = fields.Boolean("Contorno para el nombre", default=False)
    color_stroke_name = fields.Char("Color del contorno")
    size_stroke_name = fields.Integer("Tamaño del contorno")
    stroke_description = fields.Boolean(
        "Contorno para la descripción", default=False)
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


class ProductTemplateCustom(models.Model):
    _inherit = 'product.template'

    def count_products(self):
        id = self.env['product.product'].search([('barcode', '=', self.barcode)])
        cant = self.env['stock.quant'].sudo().search(
            [('product_id', '=', id.id), ('quantity', '>', 0), ('company_id', '!=', None)])
        return cant

    @api.one
    def _quantity(self):
        cant = self.count_products()
        num = 0
        for item in cant:
            num = num + item.quantity
        self.quantity = num
        return num

    # quantity = fields.Float("Cantidad total", compute=_quantity)


    def get_quantity(self, product):
        self = self.browse(product)
        cant = self.count_products()
        num = 0
        for item in cant:
            num = num + item.quantity
        return {
            "quantity": num
        }
