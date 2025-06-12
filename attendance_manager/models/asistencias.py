from odoo import models, fields, api
#from sqlalchemy import create_engine

from odoo.exceptions import UserError
import logging
import pymssql


_logger = logging.getLogger(__name__)

class AttendanceRecord(models.Model):
    _name = 'attendance.record'
    _description = 'Modelo de asistencias para empleados y usuarios'
    
    def _compute_name(self):
        for record in self:
            record.name = f"Marcaciones de {record.company_id.name} a la fecha {str(record.fecha_reporte)}" if record.company_id.name else f"Marcaciones a la fecha {str(record.fecha_reporte)}"
    #Nombre del reporte
    name = fields.Char(string='Asistencia', compute='_compute_name')

    fecha_reporte = fields.Date(string='Fecha de reporte', required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id, required=True)
    
    attendance_daily_entries = fields.One2many('attendance.daily', 'attendance_record', string='Asistencias entradas')
    attendance_daily_exits = fields.One2many('attendance.daily', 'attendance_record_exists', string='Asistencias salidas')
    
    #attendance_permisos = fields.One2many('hr.employee.permisos', 'attendance_record_permiso', string='Permisos')
    #attendance_sync = fields.One2many('attendance.sync', 'attendance_record', string='Marcaciones', required=True)
    #attendance_administracion = fields.One2many('attendance.administration', 'attendance_record', string='Administración', required=True)
    
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('confirmed', 'Confirmado'),
    ], string='Estado', default='draft')

    def evaluar(self):
        
        asistencias_entradas = self.env['attendance.daily'].sudo().search([('fecha', '=', self.fecha_reporte), ('company_id', '=', self.company_id.id), 
                                                                           ('check_type', '=', 'in')])
        
        asistencias_salidas = self.env['attendance.daily'].sudo().search([('fecha', '=', self.fecha_reporte), ('company_id', '=', self.company_id.id), 
                                                                           ('check_type', '=', 'out')])
        
        #permisos_daily = self.env['hr.employee.permisos'].sudo().search([('fecha_inicio', '<=', self.fecha_reporte), ('fecha_fin', '>=', self.fecha_reporte), ('state', '=', 'aprobado')])  

        if not asistencias_entradas and not asistencias_salidas:
            raise UserError('No hay registros para evaluar')
        else:
            self.attendance_daily_entries = asistencias_entradas
            self.attendance_daily_exits = asistencias_salidas
            #self.attendance_permisos = permisos_daily
    
    """def conectar_sql_server():
        try:
            # Configuración de conexión
            connection = pymssql.connect(
                server="nombre_servidor_sql",  # Dirección o IP del servidor
                user="usuario",               # Usuario de la base de datos
                password="contraseña",        # Contraseña del usuario
                database="nombre_base"        # Nombre de la base de datos
            )
            cursor = connection.cursor()

            # Ejecutar una consulta
            cursor.execute("SELECT * FROM tabla_ejemplo;")
            registros = cursor.fetchall()

            for registro in registros:
                print(registro)

            # Cerrar la conexión
            cursor.close()
            connection.close()

        except Exception as e:
            print("Error al conectar a la base de datos SQL Server:", e)"""

        
class AttendanceSync(models.Model):
    _name = 'attendance.sync'
    _description = 'Modelo de sincronización de asistencias'
    
    attendance_record = fields.Many2one('attendance.record', string='Asistencia', required=True)

    id_marcaciones = fields.Integer(string='ID marcaciones', required=True)
    employee_id = fields.Many2one('hr.employee', string='Empleado', required=True)
    check_in = fields.Datetime(string='Hora entrada', required=True)
    check_out = fields.Datetime(string='Hora salida', required=True)
    attendance_type = fields.Selection([
        ('in', 'Hora entrada'),
        ('out', 'Hora salida'),
        ('break', 'Hora de descanso'),
    ], string='Tipo de asistencia', required=True)
    
    permiso = fields.Boolean(string='Permiso', default=False)
    
    """def obtener_asistencias(self):
        # Conectar a la base de datos de COSEC
        
        engine = create_engine('mssql+pymssql://sa:M3g@tK2012@192.168.10.12/COSEC')

        with engine.connect() as connection:
            result = connection.execute("SELECT * FROM [COSEC].[dbo].[Mx_ATDEventTrn]")
            for row in result:
                _logger.warning('row:  ' + str(row))

        
         conn = pymssql.connect(server='192.168.10.12', user='sa', password='M3g@tK2012', database='COSEC')
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM [COSEC].[dbo].[Mx_ATDEventTrn]")
        rows = cursor.fetchall()

        for row in rows:
            _logger.warning('row:  ' + str(row))

        conn.close()"""
        
class AttendanceAdministracion(models.Model):
    _name = 'attendance.administration'
    _description = 'Modelo de administración de asistencias'
    
    attendance_record = fields.Many2one('attendance.record', string='Asistencia', required=True)
    
    employee_id = fields.Many2one('hr.employee', string='Empleado', required=True)
    hora_entrada = fields.Datetime(string='Hora entrada', required=True)
    porcentaje_deduccion = fields.Float(string='Porcentaje dedúccion', required=True)
    deduccion_llegada_tarde = fields.Float(string='Deducción llegada tarde', required=True)
    permiso = fields.Boolean(string='Permiso', default=False)
    permiso_cargado = fields.Char(string='Permiso cargado a', required=True)
    deduccion_permiso = fields.Float(string='Deducción permiso', required=True)
    total_deducciones = fields.Float(string='Total deducciones', required=True)