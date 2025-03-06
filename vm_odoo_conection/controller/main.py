from odoo import http
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)

class EmployeeController(http.Controller):

    @http.route('/api/validate_card', type='json', auth='public', methods=['POST'])
    def validate_card(self, **kwargs):
        try:
            # Obtener el cuerpo de la solicitud JSON
            data = json.loads(request.httprequest.data)
            _logger.info("Datos recibidos: %s", data)

            # Extraer el código de la tarjeta
            cardCode = data.get('cardCode')
            if not cardCode:
                _logger.error("Código de tarjeta no proporcionado")
                return {'error': 'Código de tarjeta no proporcionado'}

            # Buscar el empleado por el número de tarjeta
            employee = request.env['hr.employee'].sudo().search([('numero_tarjeta', '=', cardCode)], limit=1)
            if not employee:
                _logger.error("Empleado no encontrado para el código de tarjeta: %s", cardCode)
                return {'error': 'Empleado no encontrado'}

            # Devolver la información del empleado
            _logger.info("Empleado encontrado: %s", employee.name)
            response_data = {
                'name': employee.name,
                'credito': float(employee.credito),
                'credito_disponible': float(employee.credito_disponible)
            }
            _logger.info("Respuesta JSON enviada: %s", response_data)
            return response_data  # Devolver el diccionario directamente
        except Exception as e:
            _logger.error("Error en el controlador: %s", str(e))
            return {'error': str(e)}