# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class WizardSign(models.TransientModel):
    _name = 'sign_documents.sign.wizard'
    _description = "description"


    def print_report(self):
        return self.env['stock.picking'].print_report()
