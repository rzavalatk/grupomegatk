from datetime import datetime, timedelta, time
from odoo import models, fields
import pytz
import math
import logging

import base64
import io
from odoo.tools.misc import xlsxwriter

_logger = logging.getLogger(__name__)
honduras_tz = pytz.timezone('America/Tegucigalpa')


class AttendanceRuleInput(models.Model):
    _inherit = 'hr.payslip'

    def calcular_llegadat(self, in_time, dia_permiso, calendario_id, salario):
        costo_dia = salario / 30
        costo_hora = costo_dia / 8
        deduccion = 0

        working_hours = self.env['resource.calendar.attendance'].search([
            ('calendar_id', '=', calendario_id),
            ('dayofweek', '=', str(dia_permiso)),
            ('day_period', '=', 'morning')
        ])

        for hours in working_hours:
            start_time = datetime.strptime(f"{int(hours.hour_from)}:00:00", '%H:%M:%S').time()
            start_datetime = datetime.combine(datetime.today(), start_time)

            # Rango de deducción según minutos de retraso
            diff_minutes = (datetime.combine(datetime.today(), in_time) - start_datetime).total_seconds() / 60

            if 7 < diff_minutes <= 15:
                deduccion = costo_hora / 2
            elif 15 < diff_minutes <= 30:
                deduccion = costo_hora
            elif 30 < diff_minutes <= 60:
                deduccion = costo_hora * 2
            elif 60 < diff_minutes <= 90:
                deduccion = costo_hora * 4

        return deduccion

    def get_inputs(self, contract_ids, date_from, date_to):
        res = super().get_inputs(contract_ids, date_from, date_to)
        contract_id = contract_ids[0]
        employee = contract_id.employee_id

        costo_dia = contract_id.wage / 30
        costo_hora = costo_dia / 8
        costo_minuto = costo_hora / 60

        # Obtener permisos (leaves)
        leaves = employee.list_leaves(
            datetime.combine(fields.Date.from_string(date_from), time.min),
            datetime.combine(fields.Date.from_string(date_to), time.max),
            calendar=contract_id.resource_calendar_id
        )

        # Agregar deducciones por permisos con marca 'deducciones'
        for day, hours, leave_list in leaves:
            for leave in leave_list:
                if leave.holiday_id.holiday_status_id.deducciones:
                    for result in res:
                        if result.get('code') == 'DED_PRM':
                            total = leave.holiday_id.dias * costo_dia + leave.holiday_id.horas * costo_hora + leave.holiday_id.minutos * costo_minuto
                            result['amount'] += total

        # Obtener asistencias
        attendances = self.env['hr.attendance'].search([
            ('employee_id', '=', employee.id),
            ('check_in', '>=', date_from),
            ('check_out', '<=', date_to)
        ])

        for attendance in attendances:
            check_in_local = attendance.check_in.astimezone(honduras_tz)
            in_date = check_in_local.date()
            in_time = check_in_local.time()
            dia_semana = in_date.weekday()

            # Verificamos si ese día tiene permisos
            permiso_encontrado = False
            for day, hours, leave_list in leaves:
                if day == in_date:
                    for leave in leave_list:
                        permiso_encontrado = True
                        # Día completo: no calcular deducción
                        if leave.holiday_id.request_unit_half and leave.holiday_id.request_date_from_period == 'am':
                            # Permiso por la mañana: no calcular deducción
                            _logger.info("Permiso por la mañana, no se aplica deducción")
                            continue
                        elif leave.holiday_id.request_unit_half and leave.holiday_id.request_date_from_period == 'pm':
                            # Permiso por la tarde: sí aplica si llegó tarde en la mañana
                            amount = self.calcular_llegadat(in_time, dia_semana, contract_id.resource_calendar_id.id, contract_id.wage)
                        elif leave.holiday_id.request_unit_hours:
                            # Permiso por horas
                            permiso_inicio = datetime.combine(day, time(hour=int(float(leave.holiday_id.request_hour_from_1))))
                            permiso_fin = datetime.combine(day, time(hour=int(float(leave.holiday_id.request_hour_to_1))))

                            entrada_datetime = datetime.combine(day, in_time)
                            # Si entró antes del permiso, no se deduce
                            if entrada_datetime < permiso_inicio:
                                amount = self.calcular_llegadat(in_time, dia_semana, contract_id.resource_calendar_id.id, contract_id.wage)
                            else:
                                _logger.info("Entró durante el permiso por horas, no se aplica deducción")
                                continue
                        else:
                            # Día completo
                            _logger.info("Permiso por el día completo, no se aplica deducción")
                            continue

                        for result in res:
                            if result.get('code') == 'DED_LLT':
                                result['amount'] += amount
            if not permiso_encontrado:
                # No hay permiso → aplicar lógica de llegada tarde
                amount = self.calcular_llegadat(in_time, dia_semana, contract_id.resource_calendar_id.id, contract_id.wage)
                for result in res:
                    if result.get('code') == 'DED_LLT':
                        result['amount'] += amount

        return res
    
    def exportar_excel_deducciones(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        data_ded_prm = []
        data_ded_ast = []
        
        # Crear hojas de Excel
        worksheet_asistencias = workbook.add_worksheet('Deducciones de asistencias')
        worksheet_permisos = workbook.add_worksheet('Deducciones de permisos')
        
        # Definir formatos
        currency_format = workbook.add_format({'num_format': 'L#,##0.00', 'align': 'center'})
        number_format = workbook.add_format({'num_format': '#,##0', 'align': 'center'})
        header_format = workbook.add_format({'bold': True, 'align': 'center'})
        date_format = workbook.add_format({'num_format': 'dd-mm-yyyy', 'align': 'center'})
        datetime_format = workbook.add_format({'num_format': 'hh:mm:ss', 'align': 'center'})
        
        # Función para escribir encabezados y datos en una hoja y ajustar el tamaño de las columnas
        def escribir_hoja(worksheet, encabezados, datos, col_widths, formatos):
            # Ajustar el tamaño de las columnas
            for col, width in enumerate(col_widths):
                worksheet.set_column(col, col, width)
            
            # Escribir los encabezados
            for col, encabezado in enumerate(encabezados):
                worksheet.write(0, col, encabezado, header_format)
            
            # Escribir los datos
            row = 1
            for record in datos:
                for col, value in enumerate(record):
                    worksheet.write(row, col, value, formatos[col])
                row += 1

        # Encabezados y anchos de columnas
        encabezados_asistencias_reports = ['Empleado', 'Fecha de asistencia', 'Hora de asistencia', 'Dia de asistencia' 'Deducción']
        col_widths_asistencias_reports = [50, 25, 25, 25, 20]  # Ajusta estos valores según sea necesario
        formatos_asistencias_reports = [None, date_format, datetime_format, None, currency_format]  # Formatos para cada columna
        
        encabezados_reports_permisos = ['Empleado', 'fecha inicio', 'fecha final', 'jornada', 'Hora inicio', 'Hora final', 'deduccion', 'Monto']
        col_widths_reports_permisos = [50,25, 25, 20, 25, 25, 25, 25]  # Ajusta estos valores según sea necesario
        formatos_reports_permisos = [None,date_format,date_format, None, datetime_format, datetime_format, None, number_format]  # Formatos para cada columna
        
        # Preparar los datos 
        for slip_id in self.slip_ids:
            employee = slip_id.employee_id
            contract_id = slip_id.contract_id
            date_from = slip_id.date_from
            date_to = slip_id.date_to
            costo_dia = contract_id.wage / 30
            costo_hora = costo_dia / 8
            costo_minuto = costo_hora / 60
            
            # Obtener permisos (leaves)
            leaves = employee.list_leaves(
                datetime.combine(fields.Date.from_string(date_from), time.min),
                datetime.combine(fields.Date.from_string(date_to), time.max),
                calendar=contract_id.resource_calendar_id
            )

            # Agregar deducciones por permisos con marca 'deducciones'
            for day, hours, leave_list in leaves:
                for leave in leave_list:
                    if leave.holiday_id.holiday_status_id.deducciones:
                        total = leave.holiday_id.dias * costo_dia + leave.holiday_id.horas * costo_hora + leave.holiday_id.minutos * costo_minuto
                        permiso = {
                            'Empleado': leave.holiday_id.employee_id.name,
                            'fecha inicio': leave.holiday_id.request_date_from,
                            'fecha final': leave.holiday_id.request_date_to,
                            'jornada' : leave.holiday_id.request_date_from_period if leave.holiday_id.request_unit_half else 'N/A',
                            'Hora inicio' : leave.holiday_id.request_hour_from_1 if leave.holiday_id.request_unit_hours else 'N/A',
                            'Hora final' : leave.holiday_id.request_hour_to_1 if leave.holiday_id.request_unit_hours else 'N/A',
                            'deduccion': leave.holiday_id.holiday_status_id.name,
                            'Monto': total,
                            }
                        data_ded_prm.append(permiso)
                    

            # Obtener asistencias
            attendances = self.env['hr.attendance'].search([
                ('employee_id', '=', employee.id),
                ('check_in', '>=', date_from),
                ('check_out', '<=', date_to)
            ])

            for attendance in attendances:
                check_in_local = attendance.check_in.astimezone(honduras_tz)
                in_date = check_in_local.date()
                in_time = check_in_local.time()
                dia_semana = in_date.weekday()

                # Verificamos si ese día tiene permisos
                permiso_encontrado = False
                for day, hours, leave_list in leaves:
                    if day == in_date:
                        for leave in leave_list:
                            permiso_encontrado = True
                            # Día completo: no calcular deducción
                            if leave.holiday_id.request_unit_half and leave.holiday_id.request_date_from_period == 'am':
                                # Permiso por la mañana: no calcular deducción
                                _logger.info("Permiso por la mañana, no se aplica deducción")
                                continue
                            elif leave.holiday_id.request_unit_half and leave.holiday_id.request_date_from_period == 'pm':
                                # Permiso por la tarde: sí aplica si llegó tarde en la mañana
                                amount = self.calcular_llegadat(in_time, dia_semana, contract_id.resource_calendar_id.id, contract_id.wage)
                                asistencia = {
                                    'Empleado': attendance.employee_id.name,
                                    'fecha': in_date,
                                    'Hora': in_time,
                                    'dia': dia_semana,
                                    'deducción': amount
                                }
                                data_ded_ast.append(asistencia)
                            elif leave.holiday_id.request_unit_hours:
                                # Permiso por horas
                                permiso_inicio = datetime.combine(day, time(hour=int(float(leave.holiday_id.request_hour_from_1))))
                                permiso_fin = datetime.combine(day, time(hour=int(float(leave.holiday_id.request_hour_to_1))))

                                entrada_datetime = datetime.combine(day, in_time)
                                # Si entró antes del permiso, no se deduce
                                if entrada_datetime < permiso_inicio:
                                    amount = self.calcular_llegadat(in_time, dia_semana, contract_id.resource_calendar_id.id, contract_id.wage)
                                    asistencia = {
                                        'Empleado': attendance.employee_id.name,
                                        'fecha': in_date,
                                        'Hora': in_time,
                                        'dia': dia_semana,
                                        'deducción': amount
                                    }
                                    data_ded_ast.append(asistencia)
                                else:
                                    _logger.info("Entró durante el permiso por horas, no se aplica deducción")
                                    continue
                            else:
                                # Día completo
                                _logger.info("Permiso por el día completo, no se aplica deducción")
                                continue

                if not permiso_encontrado:
                    # No hay permiso → aplicar lógica de llegada tarde
                    amount = self.calcular_llegadat(in_time, dia_semana, contract_id.resource_calendar_id.id, contract_id.wage)
                    asistencia = {
                        'Empleado': attendance.employee_id.name,
                        'fecha': in_date,
                        'Hora': in_time,
                        'dia': dia_semana,
                        'deducción': amount
                    }
                    data_ded_ast.append(asistencia)
        
        datos_lines_asistencias = [
            (
                record['Empleado'],
                record['fecha'],
                record['Hora'],
                record['dia'],
                record['deducción'],
            )
            for record in data_ded_ast
        ]
        
        datos_lines_permisos = [
            (
                record['Empleado'],
                record['fecha inicio'],
                record['fecha final'],
                record['jornada'],
                record['Hora inicio'],
                record['Hora final'],
                record['deduccion'],
                record['Monto']
                
            )
            for record in self.report_lines_to
        ]
        
        # Escribir datos en las hojas correspondientes y ajustar el tamaño de las columnas
        escribir_hoja(worksheet_asistencias, encabezados_asistencias_reports, datos_lines_asistencias, col_widths_asistencias_reports, formatos_asistencias_reports)
        escribir_hoja(worksheet_permisos, encabezados_reports_permisos, datos_lines_permisos, col_widths_reports_permisos, formatos_reports_permisos)
        
        workbook.close()
        output.seek(0)

        # Crear el adjunto
        attachment = self.env['ir.attachment'].create({
            'name': f'reporte_de_deducciones_de_planilla_del_{self.date_start}_{self.date_end}.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(output.getvalue()),
            'store_fname': f'reporte_de_deducciones_de_planilla_del_{self.date_start}_{self.date_end}.xlsx',
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        # Devolver la acción para descargar el archivo
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
