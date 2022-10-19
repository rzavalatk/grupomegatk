# -*- coding: utf-8 -*-

from odoo import models, api
from datetime import date


class Pagos(models.Model):
    _inherit = "account.payment"
    
    
    def send_email(self,values):
        template = self.env.ref(
            'crons_mega.email_template_cierre_diario')
        email_values = {
            'email_to': 'azelaya@megatk.com',
            'email_from': ['mmoran@megatk.com']
        }
        template.with_context(values).send_mail(self.id, email_values=email_values, force_send=True)
        return True

    def _exist_index(self, dictionary, key):
        try:
            dictionary[key]
            return True
        except:
            return False

    def get_payments_today(self):
        today = date.today()
        value = {}
        value['date'] = today.strftime('%Y-%m-%d')
        payments = self.env['account.payment'].search(
            [('payment_date', '=', today.strftime('%Y-%m-%d'))])
        obj = []
        for item in payments:
            obj.append((item.region, item.journal_id.name, item.amount))
        mydict = {}
        for item in obj:
            if self._exist_index(mydict, item[0]):
                if self._exist_index(mydict[item[0]], item[1]):
                    mydict[item[0]][item[1]] = mydict[item[0]][item[1]] + item[2]
                else:
                    mydict[item[0]][item[1]] = item[2]
            else:
                mydict[item[0]] = {
                    item[1]: item[2]
                }
        value['accounts'] = mydict
        self.send_email(value)
