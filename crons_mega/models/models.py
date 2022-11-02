# -*- coding: utf-8 -*-

from odoo import models, api
from datetime import datetime
# import datetime
import pytz


class Pagos(models.Model):
    _inherit = "account.payment"
    
    
    def send_email(self,values,to):
        template = self.env.ref(
            'crons_mega.email_template_cierre_diario_2')
        email_values = {
            'email_from': 'azelaya@megatk.com',
            'email_to': to,
            'email_cc': 'azelaya@megatk.com'
        }
        template.with_context(values).send_mail(self.id, email_values=email_values, force_send=True)
        return True

    def _exist_index(self, dictionary, key):
        try:
            dictionary[key]
            return True
        except:
            return False
        
    def _reoder_data(self,obj):
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
        return mydict
    
    def _check_only_currency(self,amount,current,current_final):
        if current.name == current_final:
            return amount
        else:
            return amount/current.rate


    def get_payments_today(self):
        pass
        # tz = pytz.timezone("America/Guatemala")
        # today_datetime = datetime.now(tz)
        # if today_datetime.weekday() != 6:        
        #     today = today_datetime.strftime('%Y-%m-%d')
        #     value = {}
        #     value['date'] = today_datetime.strftime('%d/%m/%Y')
        #     mega = self.env['res.company'].search([('name','=','MEGATK')])
        #     meditek = self.env['res.company'].search([('name','=','MEDITEK')])
        #     mediteksa = self.env['res.company'].search([('name','=','MEDITEKSA NIC')])
        #     for item in mega:
        #         mega_id = item.id
        #     for item in meditek:
        #         medi_id = item.id
        #     for item in mediteksa:
        #         medisa_id = item.id     
        #     payments_mega = self.env['account.payment'].search(
        #         ['&',('payment_date', '=', today),
        #         ('company_id', '=', mega_id)
        #         ])
        #     payments_medi = self.env['account.payment'].search(
        #         ['&',('payment_date', '=', today),
        #         ('company_id', '=', medi_id)
        #         ])
        #     payments_medisa = self.env['account.payment'].search(
        #         ['&',('payment_date', '=', today),
        #         ('company_id', '=', medisa_id)
        #         ])
        #     obj_mega = []
        #     obj_medi = []
        #     obj_medisa = []
        #     for item in payments_mega:
        #         amount = self._check_only_currency(item.amount,item.currency_id,'HNL')
        #         obj_mega.append((item.region, item.journal_id.name, amount))
        #     for item in payments_medi:
        #         amount = self._check_only_currency(item.amount,item.currency_id,'HNL')
        #         obj_medi.append((item.region, item.journal_id.name, amount))
        #     for item in payments_medisa:
        #         amount = self._check_only_currency(item.amount,item.currency_id,'USD')
        #         obj_medisa.append((item.region, item.journal_id.name, amount))
        #     dict_mega = self._reoder_data(obj_mega)
        #     dict_medi = self._reoder_data(obj_medi)
        #     dict_medisa = self._reoder_data(obj_medisa)
        #     value['accounts'] = {**dict_mega,**dict_medisa}
        #     value['company'] = "MegaTK y Mediteksa NIC"
        #     # self.send_email(value,"azelaya@megatk.com")
        #     self.send_email(value,"lmoran@megatk.com")
        #     value['company'] = "Mediteksa"
        #     value['accounts'] = dict_medi
        #     # self.send_email(value,"azelaya@megatk.com")
        #     self.send_email(value,"jmoran@meditekhn.com")
