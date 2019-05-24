# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    rfq_id = fields.Many2one("purchase.requisition.diadema", "# Requisición")
