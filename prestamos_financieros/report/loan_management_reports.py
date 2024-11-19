# -*- coding: utf-8 -*-

from odoo import api, models


class LoanDetails(models.AbstractModel):
    
    _name = 'report.prestamos_financieros.loan_report_template'

    @api.model
    def _get_report_values(self, doc_ids, data=None):
        loan_id = self.env['prestamo'].browse(doc_ids)
        data = {
            'Loan_id': loan_id.id,
            'Customer': loan_id.partner_id.name,
            'CustomerAddress': f"{loan_id.partner_id.street} "
                               f"{loan_id.partner_id.city}" if loan_id.partner_id.city
            else '',
            'CustomerAddress2': f"{loan_id.partner_id.city}, "
                                f"{loan_id.partner_id.state_id.name}" if
            loan_id.partner_id.city and loan_id.partner_id.state_id.name
            else '',
            'CustomerContact': loan_id.partner_id.phone,
            'Loan_Type': loan_id.loan_type_id.name,
            'Tenure': loan_id.meses_seleccion,
            'Tenure_type': loan_id.loan_type_id.payment_frequency,
            'Interest_Rate': str(loan_id.interest_rate),
            'Loan_Amount': str(loan_id.amount_borrowed),
        }
       
        query = """SELECT name as Name, date_due as Date, amount_capital_quota as Amount,
         interest_generated as Interest_amount,state as State, 
         amount as Total_amount FROM cuota"""
        check = """WHERE"""
        condition = """prestamo_id='{cust}'""".format(cust=loan_id.id)
        query = """{} {} {}""".format(query, check, condition)
        self.env.cr.execute(query)
        record = self.env.cr.dictfetchall()
        record_sort = sorted(record, key=lambda x: x['date_due'])
        return {
            'docs': record_sort,
            'doc_ids': doc_ids,
            'data': data,
        }
