# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

#CAMPOS EN FORMULARIO CONTACTO/VENTAS Y COMPRAS/VARIOS
class ResParnertIndustry(models.Model):
    _inherit = "res.partner.industry"

    company_id = fields.Many2one('res.company', string='Company', change_default=True, required=True, default=lambda self: self.env.user.company_id)

