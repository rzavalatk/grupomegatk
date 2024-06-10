from odoo import http
from odoo.http import request

import base64
import io
from odoo.tools.misc import xlsxwriter

class StockReportHistoryController(http.Controller):

    @http.route('/stock_report_history/export_excel', type='http', auth='user')
    def exportar_excel(self, **kwargs):
        records = request.env['stock.report.history'].search([])
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet()

        # Escribir los encabezados
        worksheet.write(0, 0, 'Producto')
        worksheet.write(0, 1, 'Inventario Inicial')
        worksheet.write(0, 2, 'Inventario Final')
        worksheet.write(0, 3, 'Movimiento de producto')

        # Escribir los datos
        row = 1
        for record in records:
            worksheet.write(row, 0, record.report_differences.product_id)
            worksheet.write(row, 1, record.report_differences.quantity_from)
            worksheet.write(row, 2, record.report_differences.quantity_to)
            worksheet.write(row, 2, record.report_differences.quantity_difference)
            row += 1

        workbook.close()
        output.seek(0)

        
        return request.make_response(
            output.getvalue(),
            headers=[
                ('Content-Disposition', 'attachment; filename=stock_report_history_export.xlsx'),
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            ]
        )
