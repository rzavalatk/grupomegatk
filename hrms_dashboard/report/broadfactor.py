# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools


class EmployeeBroadFactor(models.Model):
    """
    Factor Amplio de Empleado.
    Calcula el factor amplio de empleados basado en sus ausencias y permisos.
    Este factor considera la frecuencia y duración de las ausencias para análisis de RRHH.
    """
    _name = "hr.employee.broad.factor"
    _description = "Factor Amplio de Empleado"
    _auto = False

    name = fields.Char(
        string="Nombre",
        help="Nombre del empleado para el registro."
    )
    no_of_occurrence = fields.Integer(
        string="Número de Ocurrencias",
        help="Cantidad de veces que el empleado ha tomado ausencias."
    )
    no_of_days = fields.Integer(
        string="Número de Días",
        help="Total de días de ausencias del empleado."
    )
    broad_factor = fields.Integer(
        string="Factor Amplio",
        help="Factor calculado basado en frecuencia y duración de ausencias (Ocurrencias² × Días)."
    )

    def init(self):
        """
        Calcula el factor amplio que depende de las ausencias del empleado.
        Crea una vista SQL que agrupa las ausencias validadas por empleado
        y calcula el factor amplio usando la fórmula: Ocurrencias² × Total de días.
        """
        tools.drop_view_if_exists(self._cr, 'hr_employee_broad_factor')
        self._cr.execute("""
            create or replace view hr_employee_broad_factor as (
                select
                    e.id, e.name, count(h.*) as no_of_occurrence,
                    sum(h.number_of_days) as no_of_days,
                    count(h.*)*count(h.*)*sum(h.number_of_days) as broad_factor
                from hr_employee e
                    full join (select * from hr_leave where state = 'validate' 
                    and date_to <= now()::timestamp) h
                    on e.id =h.employee_id
                group by e.id
               )""")


class ReportFactorAmplio(models.AbstractModel):
    """
    Reporte de Factor Amplio.
    Modelo abstracto para generar reportes del factor amplio de empleados.
    Proporciona datos para análisis de patrones de ausencias.
    """
    _name = 'report.hrms_dashboard.report_broadfactor'

    @api.model
    def get_report_values(self, docids=None, data=None):
        """
        Obtiene los valores para el reporte de factor amplio.
        
        Args:
            docids: IDs de los documentos (no usado en este reporte)
            data: Datos adicionales para el reporte
            
        Returns:
            dict: Diccionario con los datos del reporte incluyendo:
                - doc_model: Modelo de documento
                - lines: Líneas con datos de factores amplios
                - Date: Fecha actual del reporte
        """
        sql = """select * from hr_employee_broad_factor"""
        self.env.cr.execute(sql)
        lines = self.env.cr.dictfetchall()
        return {
            'doc_model': 'hr.employee.broad.factor',
            'lines': lines,
            'Date': fields.date.today(),
        }
