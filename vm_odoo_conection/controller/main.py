from odoo import http
from odoo.http import request
import logging
_logger = logging.getLogger(__name__)

class EmployeeController(http.Controller):

    @http.route('/api/validate_card', type='json', auth='public', methods=['POST'])
    def validate_card(self, **kwargs):
        _logger.info("Datos recibidos: %s", kwargs)  # Log para ver los datos recibidos
        card_code = kwargs.get('card_code')
        if not card_code:
            return {'error': 'Código de tarjeta no proporcionado'}

        # Buscar el empleado por el número de tarjeta
        employee = request.env['hr.employee'].sudo().search([('numero_tarjeta', '=', card_code)], limit=1)
        if not employee:
            return {'error': 'Empleado no encontrado'}

        # Devolver la información del empleado
        return {
            'name': employee.name,
            'credito': employee.credito,
            'credito_disponible': employee.credito_disponible,
            'numero_tarjeta': employee.numero_tarjeta,
        }