from odoo import http
from odoo.http import request

class AttendanceController(http.Controller):

    @http.route('/attendance/receive', type='json', auth='none', methods=['POST'], csrf=False)
    def receive_attendance(self, **kwargs):
        # Extraer los datos del cuerpo de la solicitud
        data = request.params

        # Procesar los datos y guardarlos en el modelo de asistencia
        employee_badge_id = data.get('employee_badge_id')
        timestamp = data.get('timestamp')
        event_type = data.get('event_type')

        employee = request.env['hr.employee'].sudo().search([('badge_id', '=', employee_badge_id)], limit=1)

        if employee:
            request.env['attendance.record'].sudo().create({
                'employee_id': employee.id,
                'check_in': timestamp,
                'name': event_type,
            })
            return {'status': 'success', 'message': 'Attendance recorded'}
        else:
            return {'status': 'error', 'message': 'Employee not found'}

