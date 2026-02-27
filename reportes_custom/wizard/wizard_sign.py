# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class WizardSign(models.TransientModel):
    _name = 'sign_documents.sign.wizard'
    _description = "Wizard for signing documents"

    signature = fields.Binary(string="Firma", help="Firma digital del documento")

    def print_report(self):
        """Genera el reporte después de firmar"""
        active_id = self.env.context.get('active_id')
        if active_id:
            picking = self.env['stock.picking'].browse(active_id)
            # Aquí puedes agregar lógica para manejar la firma
            # picking.write({'signed': True, 'signature': self.signature})
            return picking.print_report()
        return {'type': 'ir.actions.act_window_close'}
