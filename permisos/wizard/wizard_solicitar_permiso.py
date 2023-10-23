# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import Warning
import datetime
import pytz

class WizardSolicitarPermiso(models.TransientModel):
    _name = 'hr.employee.permisos.wizard'

    fecha_inicio = fields.Datetime(string='Desde', required=True, ) 
    fecha_fin = fields.Datetime(string='Hasta', required=True, )
    cargo = fields.Selection([('vaciones', 'Vacaciones'),('deduccion', 'Dedución de sueldo'),('sincargo', 'Sin cargo'),('incapacidad', 'Incapacidad')], default= 'vaciones', copy=False, required=True, track_visibility='onchange')
    reporto = fields.Selection([('anticipado', 'Anticipado'),('llamada', 'Llamada'),('mensaje', 'Mensaje'),('noreporto', 'No reporto')], default= 'anticipado', copy=False, required=True, track_visibility='onchange')
    employe_ids = fields.Many2many(comodel_name='hr.employee', string='Solicitantes', required=True, relation='x_permisos_empleados', column1="employe_id", column2="permiso_id")
    stock_pick_ids = fields.Many2many(comodel_name="stock.picking",relation="x_stockpicking_impor_product_mega",column1="stock_picking_id", column2="import_mega_id", string="Transferencias",required=True,)
    justificacion = fields.Text('Motivo' ,copy=False,)
    dias = fields.Integer(string='Días', default=1,)
    horas = fields.Integer(string='Horas', default=0,)
    minutos = fields.Integer(string='Minutos', default=0,)

    @api.onchange('fecha_fin','fecha_inicio')
    def _onchange_fechafin(self):
        if self.fecha_fin and self.fecha_inicio:
            user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz)
            fecha_inicial = pytz.utc.localize(self.fecha_inicio).astimezone(user_tz)
            fecha_fin = pytz.utc.localize(self.fecha_fin).astimezone(user_tz)
            
            if fecha_fin > fecha_inicial:
                permiso = self.calcularPermisos(fecha_inicial,fecha_fin)
                if not isinstance(permiso,str):
                    self.dias = permiso['D']
                    self.horas = permiso['H']
                    self.minutos = permiso['M']
                    self.fecha_inicio_txt = str(fecha_inicial.strftime("%d-%m-%Y %H:%M:%S"))
                    self.fecha_fin_txt = str(fecha_fin.strftime("%d-%m-%Y %H:%M:%S"))
            else:
                self.dias = 0
                self.horas = 0
                self.minutos = 0
                self.env.user.notify_warning(message='La fecha final debe ser mayor a la fecha inicial')

    def rangeDate(self, dateInit, dateEnd):
        dates = [
            dateInit + datetime.timedelta(n) for n in range(int((dateEnd - dateInit).days))
        ]
        datesClear = []
        for date in dates:
            if date.weekday() != 6:
                datesClear.append(date)
        return len(datesClear)

    def calcularPermisos(self, datetimeInit, datetimeEnd):
        dateInit = datetimeInit.date()
        dateEnd = datetimeEnd.date()
        timeInit = datetimeInit.time()
        timeEnd = datetimeEnd.time()
        res = {
            'D': 0,
            'H': 0,
            'M': 0
        }
        if dateInit == dateEnd and timeInit == timeEnd:
            return res
        if dateInit == dateEnd and timeInit != timeEnd:
            days = 0
            hour = timeEnd.hour - timeInit.hour
            if timeEnd.hour > 12:
                hour = hour - 1
            if hour < 0:
                return "Error en las Horas."
            else:
                hour = hour - 1
                minutes = timeEnd.minute - timeInit.minute
                if minutes < 0 and hour >= 0:
                    minutesInit = 60 - timeInit.minute
                    minutes = timeEnd.minute + minutesInit
                elif minutes < 0 and hour < 0:
                    return "Error en los Minutos."
                else:
                    hour = hour + 1
                if dateInit.weekday() == 5:
                    hour = hour * 2
                    minutes = minutes * 2
                    while minutes >= 60:
                        minutes = minutes - 60
                        hour = hour + 1
                while hour >= 8:
                    hour = hour - 8
                    days = days + 1
                if timeEnd.hour == 12:
                    minutes = 0
                res['D'],res['H'],res['M'] = days,hour,minutes
        if dateInit != dateEnd and timeInit == timeEnd:
            rang = self.rangeDate(dateInit=dateInit, dateEnd=dateEnd)
            if rang == 0:
                return "Error en las fechas."
            else:
                res['D'],res['H'],res['M'] = rang,0,0
        if dateInit != dateEnd and timeInit != timeEnd:
            rang = self.rangeDate(dateInit=dateInit, dateEnd=dateEnd) - 1
            if rang < 0:
                return "Error en las fechas."
            sab = 0
            if (dateEnd.weekday() == 5 or dateEnd.weekday() == 6) and timeEnd.hour > 12:
                sab = timeEnd.hour - 12
            sab = timeEnd.hour - sab
            H1 = 17 - timeInit.hour
            H2 = sab - 8
            if timeInit.hour <= 12:
                H1 = H1 - 1
            if sab > 12:
                H2 = H2 - 1
            time = H1 + H2
            while time >= 8:
                rang = rang + 1
                time = time - 8
                if (dateEnd.weekday() == 5 or dateEnd.weekday() == 6) and time < 8:
                    time = time * 2
            time = time - 1
            minutes = timeEnd.minute - timeInit.minute
            if minutes < 0:
                minutesInit = 60 - timeInit.minute
                minutes = timeEnd.minute + minutesInit
            else:
                time = time + 1
            if dateEnd.weekday() == 6:
                rang = rang - 1
            if rang < 0:
                return "Error en las Fechas"
            else:
                res['D'],res['H'],res['M'] = rang,time,minutes
        return res

    def crear_permisos(self):
        if self.fecha_fin > self.fecha_inicio:
            obj_sequence = self.env["ir.sequence"].search([('name','=','permisos')])
            user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz)
            fecha_inicial = pytz.utc.localize(self.fecha_inicio).astimezone(user_tz)
            fecha_fin = pytz.utc.localize(self.fecha_fin).astimezone(user_tz)
            obj_permiso = self.env["hr.employee.permisos"]
            for employe in self.employe_ids:
                valores = {
                    'name': obj_sequence.with_context().next_by_id(),
                    'fecha_inicio': self.fecha_inicio,
                    'fecha_inicio_txt': str(fecha_inicial.strftime("%d-%m-%Y %H:%M:%S")),
                    'fecha_fin': self.fecha_fin,
                    'fecha_fin_txt': str(fecha_fin.strftime("%d-%m-%Y %H:%M:%S")),
                    'cargo': self.cargo,
                    'reporto': self.reporto,
                    'employe_id': employe.id,
                    'justificacion': self.justificacion,
                    'state': 'aprobado',
                    'dias': self.dias,
                    'horas': self.horas,
                    'minutos': self.minutos,
                    'department_id': employe.department_id.id,
                    'sequence_id': obj_sequence.id,
                    'por_empresa': True,
                }
                permiso_id = obj_permiso.create(valores)
                permiso_id.aprobar('general')
        else:
            raise Warning(_('Las fechas no deben ser iguales'))
