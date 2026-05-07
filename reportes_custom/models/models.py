# -*- coding: utf-8 -*-
import logging
import math
import base64
from lxml import etree

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from odoo.tools import parse_date

_logger = logging.getLogger(__name__)


try:
    from num2words import num2words
except ImportError:
    _logger.warning("The num2words python library is not installed, amount-to-text features won't be fully available.")
    num2words = None


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    #@api.model_create_multi
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

class ResCurrencyInherit(models.Model):
    _inherit = 'res.currency'

    def amount_to_text(self, amount):
        self.ensure_one()
        
        def _num2words(number, lang):
            try:
                return num2words(number, lang=lang).title()
            except NotImplementedError:
                return num2words(number, lang='en').title()

        if num2words is None:
            logging.getLogger(__name__).warning("The library 'num2words' is missing, cannot render textual amounts.")
            return ""

        formatted = "%.{0}f".format(self.decimal_places) % amount
        parts = formatted.partition('.')
        integer_value = int(parts[0])
        fractional_value = int(parts[2] or 0)

        lang = tools.get_lang(self.env)
        amount_words = tools.ustr('{amt_value} {amt_word}').format(
                        amt_value=_num2words(integer_value, lang=lang.iso_code),
                        amt_word=self.currency_unit_label,
                        )
        if not self.is_zero(amount - integer_value):
            amount_words += ' ' + _('con') + tools.ustr(' {amt_value} {amt_word}').format(
                        amt_value=_num2words(fractional_value, lang=lang.iso_code),
                        amt_word=self.currency_subunit_label,
                        )
        return amount_words

    
class InvoiceOrder(models.Model):
    _inherit = 'account.move'

    # @api.multi
    def _compute_amount_in_word(self):
        for rec in self:
            rec.num_word = str(rec.currency_id.amount_to_text(rec.amount_total))

    num_word = fields.Char(string="Amount In Words:", compute='_compute_amount_in_word')    


        