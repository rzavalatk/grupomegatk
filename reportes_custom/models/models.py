# -*- coding: utf-8 -*-

from odoo import models, api, fields
import base64


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def print_report(self):
        context = self.env.context
        id = context['active_id']
        ids = context['active_ids']
        self = self.browse(id)
        try:
            pdf_pos = self.env.ref(
                'reportes_custom.stock_picking_custom_pos').render_qweb_pdf(ids)
            pdf = self.env.ref(
                'reportes_custom.stock_picking_custom').render_qweb_pdf(ids)
            self.env['ir.attachment'].create({
                'name': f"Orden de entraga pos - {self.name}",
                'type': 'binary',
                'datas': base64.encodestring(pdf_pos[0]),
                'datas_fname': f'Orden de entraga pos -  {self.name}.pdf',
                'res_model': 'stock.picking',
                'res_id': id,
                'mimetype': 'application/x-pdf'
            })
            self.env['ir.attachment'].create({
                'name': f"Orden de entrega -  {self.name}",
                'type': 'binary',
                'datas': base64.encodestring(pdf[0]),
                'datas_fname': f'Orden de entrega -  {self.name}.pdf',
                'res_model': 'stock.picking',
                'res_id': id,
                'mimetype': 'application/x-pdf'
            })
        except:
            self.env.user.notify_danger(
                title="Se ha producido un error interno:",
                message="""La Firma no fue adjuntada correctamente, profavor intente nuevamente""")
            self.write({'passed': "No"})
            print("///////////Error al adjuntar el reporte//////////////")
        return True

    sign = fields.Binary()
    passed = fields.Char(string="Aprobado", default="No")
