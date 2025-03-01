from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class EmployeeController(http.Controller):

    @http.route('/api/validate_card', type='json', auth='public', methods=['POST'])
    def validate_card(self, **kwargs):
        _logger.info("Datos recibidos: %s", kwargs)  # Log para ver los datos recibidos
        _logger.info("Tipo de datos recibidos: %s", type(kwargs))  # Log para ver el tipo de datos
        card_code = kwargs.get('card_code')
        if not card_code:
            _logger.error("Código de tarjeta no proporcionado")
            return {'error': 'Código de tarjeta no proporcionado'}

        # Buscar el empleado por el número de tarjeta
        employee = request.env['hr.employee'].sudo().search([('numero_tarjeta', '=', card_code)], limit=1)
        if not employee:
            _logger.error("Empleado no encontrado para el código de tarjeta: %s", card_code)
            return {'error': 'Empleado no encontrado'}

        # Devolver la información del empleado
        _logger.info("Empleado encontrado: %s", employee.name)
        return {
            'name': employee.name,
            'credito': employee.credito,
            'credito_disponible': employee.credito_disponible,
            'numero_tarjeta': employee.numero_tarjeta,
        }