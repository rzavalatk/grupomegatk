# -*- coding: utf-8 -*-

from odoo import models, api, fields
from odoo.exceptions import Warning
from datetime import datetime as dt
import datetime
import pytz


class Lots(models.Model):
    _inherit = "stock.production.lot"

    company_id = fields.Many2one("res.company", "Compañia")

    def write(self, vals):
        res = super(Lots, self).write(vals)
        if self.company_id.id != self.product_id.company_id.id:
            raise Warning(
                "El cambio que intenta hacer es invalido, El producto no pertenece a la compañia que tiene seleccionada.")
        else:
            return res

    @api.onchange('product_id')
    def _onchange_product_id(self):
        self.company_id = self.product_id.company_id.id

    @api.onchange('company_id')
    def _onchange_company_id(self):
        if self.product_id:
            if self.company_id.id != self.env.user.company_id.id:
                raise Warning(
                    "La compañia que seleccionó no es permitida, cambie de compañia para que sea valido el cambio")

    def rangeDate(self, dateInit, dateEnd):
        dates = [
            dateInit + datetime.timedelta(n) for n in range(int((dateEnd - dateInit).days))
        ]
        datesClear = []
        for date in dates:
            datesClear.append(date)
        return len(datesClear)
    
    def send_email(self, email, cc="",contexto={}):
        template = self.env.ref(
            'crons_mega.email_template_product_expirated')
        email_values = {
            'email_from': 'azelaya@megatk.com',
            'email_to': email,
            'email_cc': cc
        }
        template.with_context(contexto).send_mail(self.id, email_values=email_values, force_send=True)
        return True

    def review_date_expired(self):
        html = ""
        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz)
        today = dt.now(user_tz)
        lots = self.env['stock.production.lot'].search([])
        products = []
        products_by_expired = []
        for item in lots:
            try:
                days = self.rangeDate(today.date(),item.life_date.date())
                if  days == 0:
                    products.append({
                        'product': item.product_id.sudo().name,
                        'code': item.product_id.sudo().default_code,
                        'company': item.company_id.name,
                        'life_date':item.life_date.date(),
                        'by_expired': self.rangeDate(item.life_date.date(),today.date()) * -1,
                    })
                else:
                    products.append({
                        'product': item.product_id.sudo().name,
                        'code': item.product_id.sudo().default_code,
                        'company': item.company_id.name,
                        'life_date':item.life_date.date(),
                        'by_expired': days
                    })
            except:
                pass
        for item in products:
            if item['by_expired'] <= 45:
                products_by_expired.append(item)
        if len(products_by_expired) > 0:
            contexto = {}
            for item in products_by_expired:
                html += "<tr>"
                html += f"""
                    <th>{item['code']}</th>
                    <th>{item['product']}</th>
                    <th>{item['company']}</th>
                    <th>{item['life_date']}</th>
                    <th>{item['by_expired']}</th>
                """
                html += "</tr>"
            contexto['body'] = html
            to = "azelaya@megatk.com"
            cc = "rzavala@megatk.com"
            self.send_email(to,cc,contexto)