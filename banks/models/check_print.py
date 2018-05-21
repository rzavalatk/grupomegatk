from odoo import models, fields, api
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta


class reporte(models.AbstractModel):
    _name = 'report.banks.mcheck_print'

    def render_html(self, cr, uid, ids, data=None, context=None):
        self.cr = cr
        self. uid = uid
        report_obj = self.env["report"]
        report = report_obj._get_report_from_name('banks.check_print')
        docargs = {
            'doc_ids': ids,
            'doc_model': report.model,
            'docs': self,
            'conver_mont': self._convert_mont,
            'fecha_hoy': self._fh,
            # 'format': self._check_format,
            'mayuscula': self.mayusc,
            'cortar' : self.cortar_string
        }
        return report_obj.render('banks.check_print',docargs)

    def cortar_string(self, cadena):
        if cadena:
            return cadena[0:30]
        else:
            ''

    def mayusc(self, cadena):
        if cadena:
            return cadena.upper()
        else:
            return ''

    def _convert_mont(self, mont):
        if mont:
            return mont.upper()
        else:
            mes = ''
            mes = time.strftime('%B',time.strptime(datetime.now(),'%Y-%m-%d'))
            return mes.capitalize()

    def _fh(self):
        fecha = datetime.today() - relativedelta(hours=6)
        return datetime.strftime(fecha ,'%Y-%m-%d %H:%M:%S')

    def _check_format(self,journal_id):
        jour_pool = self.env['account.journal']
        check_book_pool = self.pool.get('banks.checkbook')
        check_book_obj = check_book_pool.browse(self.cr,self.uid,check_book_pool.search(self.cr,self.uid,[]))
        journal_obj = jour_pool.browse(self.cr,self.uid,journal_id)
        for j in journal_obj:
            for cb in check_book_obj:
                if j.id == cb.journal.id:
                    if cb.check_format == 'bac':
                        return 1
                    else:
                        return 99
        return  False
