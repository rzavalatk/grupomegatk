#-*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import UserError
from datetime import date
import logging

import base64
import io
from odoo.tools.misc import xlsxwriter

_logger = logging.getLogger(__name__)


class Visitas_Record(models.Model):
    _name = 'registro.visitas'
    _description = 'Modelo de visitas diarias a las sucursales'
    
    fecha_reporte = fields.Date(string='Fecha Inicial:', required=True, readonly=True,  states={'borrador': [('readonly', False)]})
    fecha_final = fields.Date(string='Fecha Final:', required=True, readonly=True, states={'borrador': [('readonly', False)]})

    def _compute_name(self):
        for record in self:
            if record.fecha_final and record.fecha_reporte:
                if record.fecha_final < record.fecha_reporte:
                    record.name_reporte = f"Reporte de Visitas"
                elif record.fecha_final == record.fecha_reporte:
                    record.name_reporte = f"Reporte de Visitas {str(record.fecha_reporte)}"
                else:
                    record.name_reporte = f"Reporte de Visitas {str(record.fecha_reporte)} - {str(record.fecha_final)}"
            else:
                record.name_reporte = f"Reporte de Visitas"
                
    name_reporte = fields.Char(string='Reporte', compute='_compute_name')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id, required=True)
    
    visita_diaria = fields.One2many('control.visitas', 'registro_visita', string='Registro Visitas')
    
    state = fields.Selection([
        ('borrador', 'Borrador'),
        ('aprobado', 'Aprobado'),
        ], default='borrador')
    
    def agrupar_registros(self):
            
        if self.fecha_final and self.fecha_reporte:
            if self.fecha_final < self.fecha_reporte:
                self.write({'state': 'borrador'})
                raise UserError("La fecha final debe ser mayor a la fecha inicial")
            elif self.fecha_final == self.fecha_reporte:
                visitas = self.env['control.visitas'].search([('fecha', '=', self.fecha_reporte),('region', 'in', ['TGU', 'SPS'])])
            else:
                 visitas = self.env['control.visitas'].search([('fecha', '>=', self.fecha_reporte),('fecha', '<=', self.fecha_final),('region', 'in', ['TGU', 'SPS'])])
        
        for visita in visitas:
            _logger.warning(f"Visita ID desde Master {visita.id} - Región: {visita.region}")
        
        if not visitas:
            raise UserError("No hay registros de visitas en esa fecha")
        else:
            self.visita_diaria = visitas
            
        self.write({'state': 'aprobado'})
                    
        return visitas
    
    def editar_reporte(self):
        self.write({'state': 'borrador'})
    
    def exportar_excel(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        # Crear hojas de Excel
        worksheet = workbook.add_worksheet('Visitas')
        
        #Definir formatos
        currency_format = workbook.add_format({'num_format': 'L#,##0.00', 'align': 'center'})
        number_format = workbook.add_format({'num_format': '#,##0', 'align': 'center'})
        header_format = workbook.add_format({'bold': True, 'align': 'center'})
        
        #Funcion para escribir encabezados y datos en una hoja y ajustar el tamano de las columnas
        def escribir_hoja(worksheet,encabezados, datos, col_widths, formatos):
            #Ajustar tamanio de las columnas
            for col, width in enumerate(col_widths):
                worksheet.set_column(col, col, width)
            
            #Escribir los encabezados
            for col, encabezado in enumerate(encabezados):
                worksheet.write(0, col, encabezado, header_format)
                
            # Escribir los datos
            row = 1
            for record in datos:
                for col, value in enumerate(record):
                    worksheet.write(row, col, value, formatos[col])
                row += 1
                
        #Encabezados y anchos de columnas
        encabezados_report_visita = ['Nombre', 'Fecha', 'Hora', 'Región', 'Usuario']
        col_widths_report_visita = [25, 20, 20, 20, 20]  # Ajusta estos valores según sea necesario
        formatos_report_visitas = [None, None, None, None, None]  # Formatos para cada columna
        
        datos = [
            (
              record.name,
              str(record.fecha),
              record.hora,
              record.region,
              record.user_id.name
            )
            for record in self.visita_diaria
        ]
        
        _logger.warning(f'Datos de archivo xlsx {datos}')
        
        #Escribir datos en las hojas correspondientes y ajustar tamanio de las columnas
        escribir_hoja(worksheet, encabezados_report_visita, datos, col_widths_report_visita, formatos_report_visitas)
        
        workbook.close()
        output.seek(0)
        
        #Crear el adjunto
        if self.fecha_final and self.fecha_reporte:
            if self.fecha_reporte < self.fecha_final:
                attachment = self.env["ir.attachment"].create({
                    'name':f'reporte_control_visitas_{self.fecha_reporte}_{self.fecha_final}.xlsx',
                    'type':'binary',
                    'datas':base64.b64encode(output.getvalue()),
                    'store_fname':f'reporte_control_visitas_{self.fecha_reporte}_{self.fecha_final}.xlsx',
                    'mimetype':'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                })
            else:
                attachment = self.env["ir.attachment"].create({
                    'name':f'reporte_control_visitas_{self.fecha_reporte}.xlsx',
                    'type':'binary',
                    'datas':base64.b64encode(output.getvalue()),
                    'store_fname':f'reporte_control_visitas_{self.fecha_reporte}.xlsx',
                    'mimetype':'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                })
                
        #Devolver la accion para descargar el archivo
        return {
            'type':'ir.actions.act_url',
            'url':f'/web/content/{attachment.id}?download=true',
            'target':'self',
        }
            