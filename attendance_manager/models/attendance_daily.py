from odoo import models, fields, api
from datetime import datetime

import logging
class AttendanceDaily(models.Model):
    _name = 'attendance.daily'
    _description = 'Modelo de asistencias diarias'

    id_marcaciones = fields.Integer(string='ID marcaciones', required=True)
    fecha = fields.Date(string='Fecha de asistencia', required=True)
    company_id = fields.Many2one('res.company', string='Compañia')
    employee_id = fields.Many2one('hr.employee', string='Empleado', required=True)
    check_in = fields.Char(string="Hora", required=True)
    check_type = fields.Selection([
        ('in', 'Hora entrada'),
        ('out', 'Hora salida'),
        ('late', 'Llegada tarde'),
        ('in_perm', 'Permiso Entrada'),
        ('out_perm', 'Permiso salida'),
        ('late_out', 'Marco salida antes de hora'),
        ('late_perm', 'Permiso llegada tarde'),
        ('break', 'Hora de descanso'),
    ])
    
    
    attendance_record = fields.Many2one('attendance.record', string='Asistencias entradas', )
    attendance_record_exists = fields.Many2one('attendance.record', string='Asistencias salidas',)

    def time_to_milliseconds(self, time_str):
        """Convierte una hora en formato HH:MM:SS:FFF a milisegundos desde las 00:00:00:000"""
        hours, minutes, seconds = map(int, time_str.split(':')[:3])
        milliseconds = int(time_str.split(':')[3]) if len(time_str.split(':')) == 4 else 0
        total_milliseconds = ((hours * 60 * 60) + (minutes * 60) + seconds) * 1000 + milliseconds
        return total_milliseconds

    def create(self, vals):
        """Update the registry when existing rules are updated."""
        
        logging.warning("1")
        if "id_marcaciones" in vals:
            logging.warning("2")
            if vals["id_marcaciones"]:
                logging.warning("3")
                empleado = self.env['attendance.users'].sudo().search([('id_marcaciones', '=', vals["id_marcaciones"])])
                vals["employee_id"] = empleado.employee_id.id
                vals["company_id"] = empleado.company_id.id
                
                #LOGICA PARA CALCULAR LAS HORAS DE TRABAJO SI ES ENTRADA O SALIDA
                
                hora_marcacion = self.time_to_milliseconds(vals["check_in"])
                hora_max_entrada = self.time_to_milliseconds("07:05:00:000")
                rango_max_entrada = self.time_to_milliseconds("08:05:00:000")
                hora_min_salida = self.time_to_milliseconds("16:05:00:000")
                
                #Esto busca las marcaciones del mismo usuario en un mismo dia para verificar si hubo entrada o porque marcan como 10 veces solo la entrada
                marcaciones = self.env['attendance.daily'].sudo().search([('id_marcaciones', '=', vals["id_marcaciones"]) and ('fecha', '=', vals["fecha"])])
                
                #Buscamos los permisos para este dia
                permisos = self.env['hr.employee.permisos'].sudo().search([('employe_id', '=', empleado.employee_id.id) and ('fecha_inicio', '>=', vals["fecha"]) and
                                                                          ('fecha_fin', '<=', vals["fecha"])], limit=1)
                
                hora_init_permiso = permisos.fecha_inicio.time()
                hora_fin_permiso = permisos.fecha_fin.time()
                
                logging.warning("Permisos:")
                logging.warning(permisos)
                #Esto es para saber si es entrada o salida
                marcacion_temp = hora_max_entrada
                if not marcaciones:
                    logging.warning("No hay marcaciones")
                    if hora_marcacion <= hora_max_entrada:
                        vals["check_type"] = "in"
                    elif permisos:
                        if hora_marcacion <= hora_init_permiso and hora_fin_permiso <= hora_min_salida:
                            vals["check_type"] = "in_perm"
                        else:    
                            vals["check_type"] = "late_perm"
                    elif hora_marcacion > hora_max_entrada:
                        vals["check_type"] = "late"
                elif marcaciones:
                    for asistencia in marcaciones:
                        marcacion_activ = self.time_to_milliseconds(asistencia.check_in)
                        if marcacion_activ > marcacion_temp:
                            marcacion_temp = marcacion_activ
                    
                    if permisos:
                        logging.warning("Hasta aqui llega")
                        logging.warning(hora_marcacion)
                        if hora_marcacion <= hora_min_salida and hora_fin_permiso >= hora_min_salida:
                            logging.warning("EL PROBLEMA")
                            vals["check_type"] = "out_perm"
                    elif marcacion_temp < hora_min_salida and marcacion_temp >= rango_max_entrada:
                        vals["check_type"] = "late_out"
                    elif marcacion_temp >= hora_min_salida:
                        vals["check_type"] = "out"
                    

                return super().create(vals)