# -*- encoding: utf-8 -*-
from odoo import fields, models, api


class CreateSale(models.TransientModel):
    _name = "invoice.consignacion.sale"
    
    options = fields.Selection([
        (0, 'Presupuestar lineas'),
        (1, 'Presupuestar lineas y editar fecha'),
    ])