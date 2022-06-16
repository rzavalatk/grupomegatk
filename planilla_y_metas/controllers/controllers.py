# -*- coding: utf-8 -*-
from odoo import http


# class Controller(http.Controller):
#    pass
    
    # def create_excel(self):
    #     columns = ['meta_id', 'evaluator', 'point_meta']
    #     stream = StringIO.StringIO()
    #     book = xlwt.Workbook(encoding='utf-8')
    #     sheet = book.add_sheet(u'{}'.format(u'My Sheet'))

    #     row = 1
    #     cell = 0

    #     for norma in self.normas_ids:
    #         for item in columns:
    #             sheet.write(row, cell, norma[item])
    #             cell += 1
    #         row += 1
    #         # sheet.write(row, cell, norma.name)
    #         # row += 1

    #     book.save(stream)