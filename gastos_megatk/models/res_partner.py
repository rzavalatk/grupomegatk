# -*- encoding: utf-8 -*-
from odoo import models, fields, api

class PartnerAnticipo(models.Model):
    _inherit = "res.partner"

    account_id = fields.Many2one("account.account", "Cuenta de anticipos")
    es_empleado = fields.Boolean("Es empleado")
