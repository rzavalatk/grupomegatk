# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class Purchase(models.Model):
    _inherit = "purchase.order"

    x_enviar = fields.Text("Enviar a")