# -*- coding: utf-8 -*-
import pandas as pd
from collections import defaultdict
from datetime import timedelta, datetime, date
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.http import request
from odoo.tools import float_utils
from odoo.tools import format_duration
from pytz import utc

ROUNDING_FACTOR = 16


class HrEmployee(models.Model):
    """Extiende hr.employee para el dashboard con métodos de estadísticas.
    
    Añade funcionalidad para:
    - Control de asistencia manual
    - Obtención de detalles de empleados para dashboard
    - Gráficos de ausencias por departamento
    - Tendencias de contratación y renuncias
    - Cálculo de tasa de desgaste
    - Habilidades de empleados
    """
    _inherit = 'hr.employee'

    birthday = fields.Date(string='Fecha de Nacimiento', groups="base.group_user",
                           help="Fecha de nacimiento del empleado")

    def attendance_manual(self):
        """Crea y actualiza asistencia para el empleado usuario.
        
        Registra la asistencia del empleado incluyendo datos de geolocalización,
        navegador y dirección IP cuando se registra manualmente.
        
        Returns:
            hr.employee: Registro del empleado actualizado
        """
        employee = request.env['hr.employee'].sudo().browse(
            self.env.user.employee_id.id)
        employee.sudo()._attendance_action_change({
            'city': request.geoip.city.name or _('Desconocido'),
            'country_name': request.geoip.country.name or
                            request.geoip.continent.name or _('Desconocido'),
            'latitude': request.geoip.location.latitude or False,
            'longitude': request.geoip.location.longitude or False,
            'ip_address': request.geoip.ip,
            'browser': request.httprequest.user_agent.browser,
            'mode': 'kiosk'
        })
        return employee

    @api.model
    def check_user_group(self):
        """Verifica si el usuario es gerente de RRHH.
        
        Returns:
            bool: True si el usuario tiene el grupo hr.group_hr_manager
        """
        uid = request.session.uid
        user = self.env['res.users'].sudo().search([('id', '=', uid)], limit=1)
        if user.has_group('hr.group_hr_manager'):
            return True
        else:
            return False

    @api.model
    def get_user_employee_details(self):
        """Obtiene detalles completos del empleado para el dashboard.
        
        Recupera información de:
        - Asistencias con horas trabajadas
        - Ausencias con estados y colores
        - Gastos con estados y colores
        - Estadísticas generales (ausencias pendientes, hoy, este mes)
        - Factor amplio del empleado
        - Edad y experiencia calculadas
        
        Returns:
            dict: Diccionario con todos los detalles del empleado o False
        """
        uid = request.session.uid
        employee = self.env['hr.employee'].sudo().search_read(
            [('user_id', '=', uid)], limit=1)
        # Obtener asistencias del empleado
        attendance = self.env['hr.attendance'].sudo().search_read(
            [('employee_id', '=', employee[0]['id'])],
            fields=['id', 'check_in', 'check_out', 'worked_hours'])
        attendance_line = []
        for line in attendance:
            if line['check_in'] and line['check_out']:
                val = {
                    'id':line['id'],
                    'date': line['check_in'].date(),
                    'sign_in': line['check_in'].time().strftime('%H:%M'),
                    'sign_out': line['check_out'].time().strftime('%H:%M'),
                    'worked_hours': format_duration(line['worked_hours'])
                }
                attendance_line.append(val)
        # Obtener ausencias del empleado
        leaves = self.env['hr.leave'].sudo().search_read(
            [('employee_id', '=', employee[0]['id'])],
            fields=['request_date_from', 'request_date_to', 'state',
                    'holiday_status_id'])
        for line in leaves:
            line['type'] = line.pop('holiday_status_id')[1]
            if line['state'] == 'confirm':
                line['state'] = 'Por Aprobar'
                line['color'] = 'orange'
            elif line['state'] == 'validate1':
                line['state'] = 'Segunda Aprobación'
                line['color'] = '#7CFC00'
            elif line['state'] == 'validate':
                line['state'] = 'Aprobado'
                line['color'] = 'green'
            elif line['state'] == 'cancel':
                line['state'] = 'Cancelado'
                line['color'] = 'red'
            else:
                line['state'] = 'Rechazado'
                line['color'] = 'red'
        # Obtener gastos del empleado
        expense = self.env['hr.expense'].sudo().search_read(
            [('employee_id', '=', employee[0]['id'])],
            fields=['name', 'date', 'state', 'total_amount'])
        for line in expense:
            if line['state'] == 'draft':
                line['state'] = 'Para Reportar'
                line['color'] = '#17A2B8'
            elif line['state'] == 'reported':
                line['state'] = 'Para Enviar'
                line['color'] = '#17A2B8'
            elif line['state'] == 'submitted':
                line['state'] = 'Enviado'
                line['color'] = '#FFAC00'
            elif line['state'] == 'approved':
                line['state'] = 'Aprobado'
                line['color'] = '#28A745'
            elif line['state'] == 'done':
                line['state'] = 'Hecho'
                line['color'] = '#28A745'
            else:
                line['state'] = 'Rechazado'
                line['color'] = 'red'
        # Contar ausencias pendientes de aprobación
        leaves_to_approve = self.env['hr.leave'].sudo().search_count(
            [('state', 'in', ['confirm', 'validate1'])])
        today = datetime.strftime(datetime.today(), '%Y-%m-%d')
        # Consultar ausencias de hoy
        query = """
        select count(id)
        from hr_leave
        WHERE (hr_leave.date_from::DATE,hr_leave.date_to::DATE) 
        OVERLAPS ('%s', '%s') and
        state='validate'""" % (today, today)
        cr = self._cr
        cr.execute(query)
        leaves_today = cr.fetchall()
        # Consultar ausencias de este mes
        first_day = date.today().replace(day=1)
        last_day = (date.today() + relativedelta(months=1, day=1)) - timedelta(
            1)
        query = """
                select count(id)
                from hr_leave
                WHERE (hr_leave.date_from::DATE,hr_leave.date_to::DATE) 
                OVERLAPS ('%s', '%s')
                and  state='validate'""" % (first_day, last_day)
        cr = self._cr
        cr.execute(query)
        leaves_this_month = cr.fetchall()
        # Contar asignaciones de ausencias pendientes
        leaves_alloc_req = self.env['hr.leave.allocation'].sudo().search_count(
            [('state', 'in', ['confirm', 'validate1'])])
        # Contar hojas de tiempo del empleado
        timesheet_count = self.env['account.analytic.line'].sudo().search_count(
            [('project_id', '!=', False), ('user_id', '=', uid)])
        timesheet_view_id = self.env.ref(
            'hr_timesheet.hr_timesheet_line_search')
        # Contar solicitudes de empleo
        job_applications = self.env['hr.applicant'].sudo().search_count([])
        if employee:
            # Obtener factor amplio del empleado
            sql = """select broad_factor from hr_employee_broad_factor 
            where id =%s"""
            self.env.cr.execute(sql, (employee[0]['id'],))
            result = self.env.cr.dictfetchall()
            broad_factor = result[0]['broad_factor'] if result[0][
                'broad_factor'] else False
            # Calcular edad del empleado
            if employee[0]['birthday']:
                diff = relativedelta(datetime.today(), employee[0]['birthday'])
                age = diff.years
            else:
                age = False
            # Calcular experiencia del empleado
            if employee[0]['joining_date']:
                diff = relativedelta(datetime.today(),
                                     employee[0]['joining_date'])
                years = diff.years
                months = diff.months
                days = diff.days
                experience = '{} años {} meses {} días'.format(years, months,
                                                                 days)
            else:
                experience = False
            if employee:
                data = {
                    'broad_factor': broad_factor if broad_factor else 0,
                    'leaves_to_approve': leaves_to_approve,
                    'leaves_today': leaves_today,
                    'leaves_this_month': leaves_this_month,
                    'leaves_alloc_req': leaves_alloc_req,
                    'emp_timesheets': timesheet_count,
                    'job_applications': job_applications,
                    'timesheet_view_id': timesheet_view_id,
                    'experience': experience,
                    'age': age,
                    'attendance_lines': attendance_line,
                    'leave_lines': leaves,
                    'expense_lines': expense
                }
                employee[0].update(data)
            return employee
        else:
            return False

    @api.model
    def get_upcoming(self):
        """Obtiene próximos eventos, anuncios y cumpleaños.
        
        Devuelve información sobre:
        - Próximos cumpleaños de empleados (próximos 4)
        - Anuncios aprobados y vigentes
        - Eventos próximos con ubicación
        
        Returns:
            dict: Diccionario con birthday, event, announcement
        """
        cr = self._cr
        uid = request.session.uid
        employee = self.env['hr.employee'].search([('user_id', '=', uid)],
                                                  limit=1)
        today = fields.Date.today()
        # Buscar próximos cumpleaños
        birthday_employees = self.env['hr.employee'].search_read(
            [('birthday', '!=', False)], fields=['id', 'name', 'birthday'], order='birthday ASC', limit=4)

        for emp in birthday_employees:
            if emp['birthday'].month == today.month and emp[
                'birthday'].day == today.day:
                emp['is_birthday'] = True
            else:
                emp_birthday = emp['birthday'].replace(year=today.year)
                emp['days'] = (emp_birthday - today).days
        # Buscar anuncios aprobados y vigentes
        announcements = self.env['hr.announcement'].search_read(
            [('state', '=', 'approved'),
             ('date_start', '<=', fields.Date.today()),
             '|', ('is_announcement', '=', True),
             '|', '|',
             ('employee_ids', 'in', employee.id),
             ('department_ids', 'in', employee.department_id.id),
             ('position_ids', 'in', employee.job_id.id),
             ], fields=['announcement_reason', 'date_start', 'date_end'])

        lang = f"'{self.env.context['lang']}'"
        # Buscar próximos eventos
        cr.execute("""select e.id, e.name ->> e.lang as name, e.date_begin,
         e.date_end,rp.name as location
        from event_event e
        inner join res_partner rp 
        on e.address_id = rp.id
        and (e.date_begin >= now())
        order by e.date_begin""")
        event = cr.fetchall()
        return {
            'birthday': birthday_employees,
            'event': event,
            'announcement': announcements
        }

    @api.model
    def get_dept_employee(self):
        """Obtiene detalles de empleados por departamento.
        
        Cuenta el número de empleados en cada departamento para
        mostrar en gráficos del dashboard.
        
        Returns:
            list: Lista de diccionarios con label (nombre depto) y value (cantidad)
        """
        cr = self._cr
        cr.execute("""select department_id, hr_department.name,count(*)
        from hr_employee join hr_department on 
        hr_department.id=hr_employee.department_id
        group by hr_employee.department_id,hr_department.name""")
        dat = cr.fetchall()
        data = []
        for i in range(0, len(dat)):
            data.append(
                {'label': list(dat[i][1].values())[0], 'value': dat[i][2]})
        return data

    @api.model
    def get_department_leave(self):
        """Devuelve información mensual de ausencias por departamento.
        
        Genera un gráfico con ausencias de los últimos 6 meses agrupadas
        por departamento. Solo accesible para gerentes de RRHH.
        
        Returns:
            tuple: (graph_result, department_list) con datos mensuales y lista de deptos
        """
        user = self.env.user
        if not user.has_group('hr.group_hr_manager'):
            return [], []
        month_list = []
        graph_result = []
        # Generar lista de últimos 6 meses
        for i in range(5, -1, -1):
            last_month = datetime.now() - relativedelta(months=i)
            text = format(last_month, '%B %Y')
            month_list.append(text)
        # Obtener lista de departamentos activos
        self.env.cr.execute(
            """select id, name from hr_department where active=True """)
        departments = self.env.cr.dictfetchall()
        department_list = [list(x['name'].values())[0] for x in departments]
        # Inicializar estructura de datos
        for month in month_list:
            leave = {}
            for dept in departments:
                leave[list(dept['name'].values())[0]] = 0
            vals = {
                'l_month': month,
                'leave': leave
            }
            graph_result.append(vals)
        # Consulta SQL para obtener ausencias por mes y departamento
        sql = """
        SELECT h.id, h.employee_id,h.department_id
             , extract('month' FROM y)::int AS leave_month
             , to_char(y, 'Month YYYY') as month_year
             , GREATEST(y                    , h.date_from) AS date_from
             , LEAST   (y + interval '1 month', h.date_to)   AS date_to
        FROM  (select * from hr_leave where state = 'validate') h
             , generate_series(date_trunc('month', date_from::timestamp)
                             , date_trunc('month', date_to::timestamp)
                             , interval '1 month') y
        where date_trunc('month', GREATEST(y , h.date_from)) >= 
        date_trunc('month', now()) - interval '6 month' and
        date_trunc('month', GREATEST(y , h.date_from)) <= 
        date_trunc('month', now())
        and h.department_id is not null
        """
        self.env.cr.execute(sql)
        results = self.env.cr.dictfetchall()
        leave_lines = []
        # Procesar resultados y calcular días trabajados
        for line in results:
            employee = self.browse(line['employee_id'])
            from_dt = fields.Datetime.from_string(line['date_from'])
            to_dt = fields.Datetime.from_string(line['date_to'])
            days = employee.get_work_days_dashboard(from_dt, to_dt)
            line['days'] = days
            vals = {
                'department': line['department_id'],
                'l_month': line['month_year'],
                'days': days
            }
            leave_lines.append(vals)
        # Agrupar datos usando pandas
        if leave_lines:
            df = pd.DataFrame(leave_lines)
            rf = df.groupby(['l_month', 'department']).sum()
            result_lines = rf.to_dict('index')
            # Mapear resultados a la estructura de gráfico
            for month in month_list:
                for line in result_lines:
                    if month.replace(' ', '') == line[0].replace(' ', ''):
                        match = list(filter(lambda d: d['l_month'] in [month],
                                            graph_result))[0]['leave']
                        dept_name = self.env['hr.department'].browse(
                            line[1]).name
                        if match:
                            match[dept_name] = result_lines[line]['days']
        # Formatear nombres de meses (Ene 2024)
        for result in graph_result:
            result['l_month'] = result['l_month'].split(' ')[:1][0].strip()[
                                :3] + " " + \
                                result['l_month'].split(' ')[1:2][0]

        return graph_result, department_list

    def get_work_days_dashboard(self, from_datetime, to_datetime,
                                compute_leaves=False, calendar=None,
                                domain=None):
        """Calcula horas/días trabajados del empleado.
        
        Calcula los días trabajados efectivos considerando el calendario
        del empleado y los intervalos de asistencia. Utiliza un factor de
        redondeo para precisar el cálculo.
        
        Args:
            from_datetime: Fecha/hora de inicio
            to_datetime: Fecha/hora de fin
            compute_leaves: Si debe considerar ausencias
            calendar: Calendario a usar (por defecto el del empleado)
            domain: Dominio adicional para filtrar
            
        Returns:
            float: Número de días trabajados
        """
        resource = self.resource_id
        calendar = calendar or self.resource_calendar_id
        # Asegurar que las fechas tengan zona horaria
        if not from_datetime.tzinfo:
            from_datetime = from_datetime.replace(tzinfo=utc)
        if not to_datetime.tzinfo:
            to_datetime = to_datetime.replace(tzinfo=utc)
        # Ampliar rango para capturar días completos
        from_full = from_datetime - timedelta(days=1)
        to_full = to_datetime + timedelta(days=1)
        # Obtener intervalos de asistencia del calendario
        intervals = calendar._attendance_intervals_batch(from_full, to_full,
                                                         resource)
        # Calcular total de horas por día
        day_total = defaultdict(float)
        for start, stop, meta in intervals[resource.id]:
            day_total[start.date()] += (stop - start).total_seconds() / 3600
        # Calcular horas efectivas considerando ausencias si se requiere
        if compute_leaves:
            intervals = calendar._work_intervals_batch(from_datetime,
                                                       to_datetime, resource,
                                                       domain)
        else:
            intervals = calendar._attendance_intervals_batch(from_datetime,
                                                             to_datetime,
                                                             resource)
        day_hours = defaultdict(float)
        for start, stop, meta in intervals[resource.id]:
            day_hours[start.date()] += (stop - start).total_seconds() / 3600
        # Calcular días proporcionales
        days = sum(
            float_utils.round(ROUNDING_FACTOR * day_hours[day] / day_total[
                day]) / ROUNDING_FACTOR
            for day in day_hours
        )
        return days

    @api.model
    def employee_leave_trend(self):
        """Información mensual de ausencias del empleado logueado.
        
        Genera un gráfico con las ausencias del empleado actual
        durante los últimos 6 meses.
        
        Returns:
            list: Lista de diccionarios con mes y días de ausencia
        """
        leave_lines = []
        month_list = []
        graph_result = []
        # Generar lista de últimos 6 meses
        for i in range(5, -1, -1):
            last_month = datetime.now() - relativedelta(months=i)
            text = format(last_month, '%B %Y')
            month_list.append(text)
        uid = request.session.uid
        employee = self.env['hr.employee'].sudo().search_read(
            [('user_id', '=', uid)], limit=1)
        # Inicializar estructura de datos
        for month in month_list:
            vals = {
                'l_month': month,
                'leave': 0
            }
            graph_result.append(vals)
        # Consulta SQL para ausencias del empleado por mes
        sql = """
                SELECT h.id, h.employee_id
                     , extract('month' FROM y)::int AS leave_month
                     , to_char(y, 'Month YYYY') as month_year
                     , GREATEST(y                    , h.date_from) AS date_from
                     , LEAST   (y + interval '1 month', h.date_to)   AS date_to
                FROM  (select * from hr_leave where state = 'validate') h
                     , generate_series(date_trunc('month', date_from::timestamp)
                                     , date_trunc('month', date_to::timestamp)
                                     , interval '1 month') y
                where date_trunc('month', GREATEST(y , h.date_from)) >= 
                date_trunc('month', now()) - interval '6 month' and
                date_trunc('month', GREATEST(y , h.date_from)) <= 
                date_trunc('month', now()) and h.employee_id = %s """
        self.env.cr.execute(sql, (employee[0]['id'],))
        results = self.env.cr.dictfetchall()
        # Procesar resultados y calcular días
        for line in results:
            employee = self.browse(line['employee_id'])
            from_dt = fields.Datetime.from_string(line['date_from'])
            to_dt = fields.Datetime.from_string(line['date_to'])
            days = employee.get_work_days_dashboard(from_dt, to_dt)
            line['days'] = days
            vals = {
                'l_month': line['month_year'],
                'days': days
            }
            leave_lines.append(vals)
        # Agrupar usando pandas
        if leave_lines:
            df = pd.DataFrame(leave_lines)
            rf = df.groupby(['l_month']).sum()
            result_lines = rf.to_dict('index')
            for line in result_lines:
                match = list(filter(
                    lambda d: d['l_month'].replace(' ', '') == line.replace(' ',
                                                                            ''),
                    graph_result))
                if match:
                    match[0]['leave'] = result_lines[line]['days']
        # Formatear nombres de meses
        for result in graph_result:
            result['l_month'] = result['l_month'].split(' ')[:1][0].strip()[
                                :3] + " " + \
                                result['l_month'].split(' ')[1:2][0]
        return graph_result

    @api.model
    def join_resign_trends(self):
        """Devuelve detalles de contrataciones/renuncias por mes.
        
        Genera un gráfico de líneas con dos series:
        - Contrataciones por mes (últimos 12 meses)
        - Renuncias por mes (últimos 12 meses)
        
        Returns:
            list: Lista con dos diccionarios (Join y Resign) con valores mensuales
        """
        cr = self._cr
        month_list = []
        join_trend = []
        resign_trend = []
        # Generar lista de últimos 12 meses
        for i in range(11, -1, -1):
            last_month = datetime.now() - relativedelta(months=i)
            text = format(last_month, '%B %Y')
            month_list.append(text)
        # Inicializar tendencia de contrataciones
        for month in month_list:
            vals = {
                'l_month': month,
                'count': 0
            }
            join_trend.append(vals)
        # Inicializar tendencia de renuncias
        for month in month_list:
            vals = {
                'l_month': month,
                'count': 0
            }
            resign_trend.append(vals)
        # Consultar contrataciones de los últimos 12 meses
        cr.execute('''select to_char(joining_date, 'Month YYYY') as l_month,
         count(id) from hr_employee
        WHERE joining_date BETWEEN CURRENT_DATE - INTERVAL '12 months'
        AND CURRENT_DATE + interval '1 month - 1 day'
        group by l_month''')
        join_data = cr.fetchall()
        # Consultar renuncias de los últimos 12 meses
        cr.execute('''select to_char(resign_date, 'Month YYYY') as l_month,
         count(id) from hr_employee
        WHERE resign_date BETWEEN CURRENT_DATE - INTERVAL '12 months'
        AND CURRENT_DATE + interval '1 month - 1 day'
        group by l_month;''')
        resign_data = cr.fetchall()

        # Mapear datos de contrataciones
        for line in join_data:
            match = list(filter(
                lambda d: d['l_month'].replace(' ', '') == line[0].replace(' ',
                                                                           ''),
                join_trend))
            if match:
                match[0]['count'] = line[1]
        # Mapear datos de renuncias
        for line in resign_data:
            match = list(filter(
                lambda d: d['l_month'].replace(' ', '') == line[0].replace(' ',
                                                                           ''),
                resign_trend))
            if match:
                match[0]['count'] = line[1]
        # Formatear nombres de meses (abreviados)
        for join in join_trend:
            join['l_month'] = join['l_month'].split(' ')[:1][0].strip()[:3]
        for resign in resign_trend:
            resign['l_month'] = resign['l_month'].split(' ')[:1][0].strip()[:3]
        # Estructura final para gráfico de líneas
        graph_result = [{
            'name': 'Contratación',
            'values': join_trend
        }, {
            'name': 'Renuncia',
            'values': resign_trend
        }]
        return graph_result

    @api.model
    def get_attrition_rate(self):
        """Devuelve tasa de desgaste mensual.
        
        Calcula la tasa de desgaste (attrition rate) para cada mes de los
        últimos 12 meses. La fórmula es:
        Tasa = (Renuncias del mes / Promedio de empleados) * 100
        
        El promedio de empleados considera:
        - Empleados al inicio del mes
        - Contrataciones del mes
        - Renuncias del mes
        
        Returns:
            list: Lista de diccionarios con mes y tasa de desgaste
        """
        month_attrition = []
        # Obtener datos de contrataciones y renuncias
        monthly_join_resign = self.join_resign_trends()
        month_join = monthly_join_resign[0]['values']
        month_resign = monthly_join_resign[1]['values']
        # Generar fechas de inicio de los últimos 12 meses
        sql = """
        SELECT (date_trunc('month', CURRENT_DATE))::date - interval '1' 
        month * s.a AS month_start
        FROM generate_series(0,11,1) AS s(a);"""
        self._cr.execute(sql)
        month_start_list = self._cr.fetchall()
        # Calcular tasa de desgaste para cada mes
        for month_date in month_start_list:
            # Contar empleados activos al inicio del mes
            self._cr.execute("""select count(id), 
            to_char(date '%s', 'Month YYYY') as l_month from hr_employee
            where resign_date> date '%s' or resign_date is null and 
            joining_date < date '%s'
            """ % (month_date[0], month_date[0], month_date[0],))
            month_emp = self._cr.fetchone()
            # Obtener contrataciones del mes
            match_join = \
                list(filter(
                    lambda d: d['l_month'] == month_emp[1].split(' ')[:1][
                                                  0].strip()[:3], month_join))[
                    0][
                    'count']
            # Obtener renuncias del mes
            match_resign = \
                list(filter(
                    lambda d: d['l_month'] == month_emp[1].split(' ')[:1][
                                                  0].strip()[:3],
                    month_resign))[0][
                    'count']
            # Calcular promedio de empleados: (inicio + fin) / 2
            month_avg = (month_emp[0] + match_join - match_resign + month_emp[
                0]) / 2
            # Calcular tasa de desgaste
            attrition_rate = (match_resign / month_avg) * 100 \
                if month_avg != 0 else 0
            vals = {
                'month': month_emp[1].split(' ')[:1][0].strip()[:3],
                'attrition_rate': round(float(attrition_rate), 2)
            }
            month_attrition.append(vals)
        return month_attrition

    @api.model
    def get_employee_skill(self):
        """Obtiene habilidades del empleado y su progreso.
        
        Devuelve las habilidades registradas del empleado actual
        con su nivel de progreso para mostrar en el dashboard.
        
        Returns:
            list: Lista de diccionarios con habilidades y progreso
        """
        employee = self.env['hr.employee'].sudo().search(
            [('user_id', '=', request.session.uid)], limit=1)
        skills = self.env['hr.employee.skill'].sudo().search_read(
            [('employee_id', '=', employee.id)])
        dataset = []
        for rec in skills:
            vals = {
                'skills': rec['skill_type_id'][1] + '-' + rec['skill_id'][1],
                'progress': rec['level_progress']
            }
            dataset.append(vals)
        return dataset

    @api.model
    def get_employee_project_tasks(self):
        """Obtiene tareas de proyectos del empleado.
        
        Devuelve las tareas de proyectos asignadas al usuario actual,
        ordenadas por fecha límite y limitadas a las 10 más próximas.
        
        Returns:
            list: Lista de diccionarios con información de tareas
        """
        employee = self.env['hr.employee'].sudo().browse(self.env.uid)
        if not employee:
            return []

        # Obtener tareas asignadas al usuario actual
        tasks = self.env['project.task'].sudo().search([
            ('user_ids', 'in', self.env.uid),
            ('active', '=', True)
        ], order='date_deadline asc', limit=10)

        task_data = []
        for task in tasks:
            task_data.append({
                'id': task.id,
                'task_name': task.name,
                'project_name': task.project_id.name if task.project_id else 'Sin Proyecto',
                'date_deadline': task.date_deadline.strftime('%Y-%m-%d') if task.date_deadline else '',
                'stage_name': task.stage_id.name if task.stage_id else 'Sin Etapa',
            })

        return task_data

