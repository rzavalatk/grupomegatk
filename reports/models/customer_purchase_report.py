from odoo import models, fields, api

import logging
from datetime import datetime
from datetime import date
import time

import io
import base64
import xlsxwriter

_logger = logging.getLogger(__name__)

class CustomerPurchaseReport(models.Model):
    _name = 'customer.purchase.report'
    _description = 'Customer No Purchase Report'

    @api.onchange('date_from','date_to','company_id')
    def _onchange_date_from(self):
        self.name = "Reporte de Clientes inactivos de " + str(self.company_id.name) + " del " +str(self.date_from) + " al " + str(self.date_to)
    
    
    report_lines_from_customer_purchase = fields.One2many(
        'customer.purchase.report.line', 'report_purchase_customers', string="Clientes que compraron en el intervalo de tiempo 1", readonly=True)
    
    report_lines_to_customer_purchase = fields.One2many(
        'customer.purchase.report.line', 'report_to_purchase_customer', string="Clientes que compraron en el intervalo de tiempo 2", readonly=True)

    report_differences = fields.One2many(
        'customer.purchase.report.line.difference', 'report_id', string="Report Differences", readonly=True)
    
    report_differences_OI = fields.One2many(
        'customer.purchase.report.line.difference', 'report_id_OI', string="Report Differences", readonly=True)
    
    name = fields.Char(string="Nombre de reporte", required=True, readonly=True, states={'borrador': [('readonly', False)]},)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id, readonly=True, states={'borrador': [('readonly', False)]},)
    date_from = fields.Date(string='Start Date', required=True, readonly=True, states={'borrador': [('readonly', False)]},)
    date_to = fields.Date(string='End Date', required=True, readonly=True, states={'borrador': [('readonly', False)]},)
    
    date_from_i2 = fields.Date(string='Fencha inicio', required=True, readonly=True, states={'borrador': [('readonly', False)]},)
    date_to_i2 = fields.Date(string='Fecha final', required=True, readonly=True, states={'borrador': [('readonly', False)]},)
    
    state = fields.Selection([
        ('borrador', 'Borrador'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
        ], default='borrador')
    
    def volver_borrador(self):
         self.write({'state': 'borrador'})   

    def generate_reports(self):
        time.sleep(4)
        line_from = self._get_customers_purchase( self.date_from, self.date_to, 'report_lines_from_customer_purchase')
        time.sleep(4)
        line_to = self._get_customers_purchase( self.date_from_i2, self.date_to_i2, 'report_lines_to_customer_purchase')
        #self._get_customers_no_purchase('report_lines_from_no_customer_purchase')
        time.sleep(4)
        if line_from and line_to:
            self._get_customers_difference(line_from, line_to)
        
        self.write({'state': 'aprobado'})
        
    def _get_customers_purchase(self,date1, date2, field_name):
        #Busqueda para todas las facturas en el periodo de tiempo 1 (Periodo de clientres que si han comprado)
        domain = ['&', '&', '&', '&',
            ('company_id', '=', self.company_id.id),
            ('invoice_date', '>=', date1),
            ('invoice_date', '<=', date2),
            ('state', '=', 'posted'),
            ('state', '!=', 'cancel'),
            ('move_type', '=', 'out_invoice'),
        ]
        account_orders = self.env['account.move'].search(domain)
        
        time.sleep(2)
        
        #Lista de todos los clientes y luego lista con todos los ids de los clientes
        customer_list = account_orders.mapped('partner_id')
        
        
        #Proceso para escribir los clientes que si han comprado en ese periodo de tiempo 1
        lines = []
        for customer_item in customer_list:
            n = True
            invoice_info = []
            valor_total = 0
            for invoice_item in customer_item.invoice_ids: #TODAS LAS FACTURAS DEL CLIENTE YA SEAN COMPRAS, VENTAS O COTIZACONES
                
                if invoice_item.move_type == 'out_invoice':
                    if invoice_item.state == 'posted':
                        if invoice_item.invoice_date and isinstance(invoice_item.invoice_date, date):
                            if invoice_item.invoice_date <= date2: 
                                if invoice_item.invoice_date >= date1:
                                    if n:
                                        invoice_info.append(invoice_item.id)
                                        invoice_info.append(invoice_item.invoice_date)
                                        invoice_info.append(invoice_item.invoice_payment_term_id.display_name)
                                        n = False
                                    
                                    valor_total = valor_total + invoice_item.amount_total     
                                
                                         
            if invoice_info:
                lines.append((0, 0, {
                    'partner_id': customer_item.id,
                    'last_purchase': invoice_info[0],
                    'purchase_date': invoice_info[1],
                    'purchase_comercial': customer_item.user_id.id,
                    'purchase_amount': valor_total,
                    'purchase_term_id': invoice_info[2],
                }))
        
        if lines:
            _logger.info(f"Writing lines to field {field_name}: {lines}")
            self.write({field_name: lines})
        
        return lines   
        
    
    def _get_customers_difference(self, list_from, list_to):
        self.ensure_one()
        differences = []
        differences_OI = []
        
        for _, _, item in list_from:
            
            no_encontrado = False
            
            for _, _, item_to in list_to:
                
                if item['partner_id'] == item_to['partner_id']:
                    no_encontrado = True
                    differences.append((0, 0, {
                        'partner_id': item['partner_id'],
                        'comercial': item['purchase_comercial'],
                        'amount_first': item['purchase_amount'],
                        'amount_second': item_to['purchase_amount'], 
                        'amount_total': item['purchase_amount'] + item_to['purchase_amount'],
                        
                    }))
                    
                    
            if not no_encontrado:
                differences_OI.append((0, 0, {
                    'partner_id': item['partner_id'],
                    'comercial': item['purchase_comercial'],
                    'amount_first': item['purchase_amount'],
                    'amount_second': '0', 
                    'amount_total': item['purchase_amount'],
                    
                }))
        
        _logger.info(f"Writing differences: {differences}, OI: {differences_OI}")
        self.report_differences = differences
        self.report_differences_OI = differences_OI
    

    def exportar_excel(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        # Crear hojas de Excel
        worksheet_lines_from_customer = workbook.add_worksheet('Clientes Intervalo 1')
        worksheet_lines_to_customer = workbook.add_worksheet('Clientes Intervalo 2')
        worksheet_differences = workbook.add_worksheet('Clientes que compraron en ambos')
        worksheet_differences_OIz9c = workbook.add_worksheet('Clientes que compraron en el primero pero no en el segundo')

        # Función para escribir encabezados y datos en una hoja y ajustar el tamaño de las columnas
        def escribir_hoja(worksheet, encabezados, datos, col_widths):
            # Ajustar el tamaño de las columnas
            for col, width in enumerate(col_widths):
                worksheet.set_column(col, col, width)
            
            # Escribir los encabezados
            for col, encabezado in enumerate(encabezados):
                worksheet.write(0, col, encabezado)
            
            # Escribir los datos
            row = 1
            for record in datos:
                for col, value in enumerate(record):
                    worksheet.write(row, col, value)
                row += 1

        # Encabezados y anchos de columnas
        encabezados_lines_customer = ['Customer', 'Ultima compra', 'Comercial del cliente', 'Total comprado', 'Termino de pago ultima compra']
        col_widths_lines_customer = [35, 20, 20, 25, 20, 25]  # Ajusta estos valores según sea necesario
        
        encabezados_differences = ['Customer', 'Comercial del cliente', 'Total comprado primer intervalo', 'Total comprado segundo intervalo', 'Total comprado']
        col_widths_differences = [35, 25, 30, 20, 25, 25, 25, 20]  # Ajusta estos valores según sea necesario

        # Preparar los datos
        datos_lines_from_customer = [
            (
                record.partner_id.name,
                record.last_purchase.name,
                record.purchase_comercial.name,
                record.purchase_amount,
                record.purchase_term_id
            )
            for record in self.report_lines_from_customer_purchase
        ]

        datos_lines_to_customer = [
            (
                record.partner_id.name,
                record.last_purchase.name,
                record.purchase_comercial.name,
                record.purchase_amount,
                record.purchase_term_id
            )
            for record in self.report_lines_to_customer_purchase
        ]

        datos_differences = [
            (
                record.partner_id.name,
                record.comercial.name,
                record.amount_first,
                record.amount_second,
                record.amount_total
            )
            for record in self.report_differences
        ]

        datos_differences_OIz9c = [
            (
                record.partner_id.name,
                record.comercial.name,
                record.amount_first,
                record.amount_second,
                record.amount_total
            )
            for record in self.report_differences_OI
        ]

        # Escribir datos en las hojas correspondientes y ajustar el tamaño de las columnas
        escribir_hoja(worksheet_lines_from_customer, encabezados_lines_customer, datos_lines_from_customer, col_widths_lines_customer)
        escribir_hoja(worksheet_lines_to_customer, encabezados_lines_customer, datos_lines_to_customer, col_widths_lines_customer)
        escribir_hoja(worksheet_differences, encabezados_differences, datos_differences, col_widths_differences)
        escribir_hoja(worksheet_differences_OIz9c, encabezados_differences, datos_differences_OIz9c, col_widths_differences)

        workbook.close()
        output.seek(0)

        # Crear el adjunto
        attachment = self.env['ir.attachment'].create({
            'name': 'reporte_de_actividad_clientes.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(output.getvalue()),
            'store_fname': 'reporte_de_actividad_clientes.xlsx',
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        # Devolver la acción para descargar el archivo
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
 
    def exportar_excel_intervalo(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        # Crear hojas de Excel
        worksheet_lines_from_customer = workbook.add_worksheet('Clientes que mas compraron')

        # Función para escribir encabezados y datos en una hoja y ajustar el tamaño de las columnas
        def escribir_hoja(worksheet, encabezados, datos, col_widths):
            # Ajustar el tamaño de las columnas
            for col, width in enumerate(col_widths):
                worksheet.set_column(col, col, width)
            
            # Escribir los encabezados
            for col, encabezado in enumerate(encabezados):
                worksheet.write(0, col, encabezado)
            
            # Escribir los datos
            row = 1
            for record in datos:
                for col, value in enumerate(record):
                    worksheet.write(row, col, value)
                row += 1

        # Encabezados y anchos de columnas
        encabezados_lines_customer = ['Customer', 'Ultima compra', 'Comercial del cliente', 'Total comprado', 'Termino de pago ultima compra']
        col_widths_lines_customer = [35, 20, 20, 25, 20, 25]  # Ajusta estos valores según sea necesario
    
        # Preparar los datos
        datos_lines_from_customer = [
            (
                record.partner_id.name,
                record.last_purchase.name,
                record.purchase_comercial.name,
                record.purchase_amount,
                record.purchase_term_id
            )
            for record in sorted(self.report_lines_from_customer_purchase, key=lambda x: x.purchase_amount, reverse=True)
        ]

       

        # Escribir datos en las hojas correspondientes y ajustar el tamaño de las columnas
        escribir_hoja(worksheet_lines_from_customer, encabezados_lines_customer, datos_lines_from_customer, col_widths_lines_customer)


        workbook.close()
        output.seek(0)

        # Crear el adjunto
        attachment = self.env['ir.attachment'].create({
            'name': 'reporte_de_compras_clientes.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(output.getvalue()),
            'store_fname': 'reporte_de_compras_clientes.xlsx',
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        # Devolver la acción para descargar el archivo
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

            
        

class CustomerReportLine(models.Model):
    _name = 'customer.purchase.report.line'
    _description = 'Customer purchase Report Line'
    
    
    report_purchase_customers = fields.Many2one(
        'customer.purchase.report', string="Clientes que compraron en el intervalo de tiempo 1", ondelete='cascade')
    
    report_to_purchase_customer = fields.Many2one(
        'customer.purchase.report', string="Clientes que compraron en el intervalo de tiempo 2", ondelete='cascade')
    
    partner_id = fields.Many2one('res.partner', string='Customer')
    last_purchase = fields.Many2one('account.move', string='Ultima compra')
    purchase_date = fields.Date('Fecha ultima compra')
    purchase_comercial = fields.Many2one('res.users', string='Comercial del cliente')
    purchase_amount = fields.Float('Total comprado')
    purchase_term_id = fields.Char('Termino de pago ultima compra')
    #location_id = fields.Many2one('stock.location', string="Location", required=True)
    #date_create = fields.Datetime(string="Create Date", required=True)
    
class CustomerReportLineDifference(models.Model):
    _name = 'customer.purchase.report.line.difference'
    _description = 'Customer purchase Report Line difference'

    report_id = fields.Many2one(
        'customer.purchase.report', string="Reporte", ondelete='cascade')
    
    report_id_OI = fields.Many2one(
        'customer.purchase.report', string="Reporte", ondelete='cascade')
    
    partner_id = fields.Many2one('res.partner', string='Customer')
    company_id = fields.Many2one('res.company', string='Compañia')
    email = fields.Text('email')
    phone = fields.Text('telefono')
    comercial = fields.Many2one('res.users', string='Comercial del cliente')
    amount_first = fields.Float('Total comprado primer intervalo')
    amount_second = fields.Float('Total comprado segundo intervalo')
    amount_total = fields.Float('Total comprado')
    