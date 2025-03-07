import json
import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

class EmployeeController(http.Controller):

    @http.route('/api/validate_card', type='json', auth='user', methods=['POST'])
    def validate_card(self, **kwargs):
        try:
            # Obtener el cuerpo de la solicitud JSON
            data = json.loads(request.httprequest.data)
            _logger.info("Datos recibidos: %s", data)

            # Verificar la API Key (si se usa autenticación basada en API Key)
            api_key = request.httprequest.headers.get('Authorization')
            if not api_key or not api_key.startswith('Bearer '):
                _logger.error("API Key no proporcionada o inválida")
                return self._json_response("error", "API Key no proporcionada o inválida")

            # Extraer el código de la tarjeta
            card_code = data.get('cardCode')
            if not card_code:
                _logger.error("Código de tarjeta no proporcionado")
                return self._json_response("error", "Código de tarjeta no proporcionado")

            # Buscar el empleado por número de tarjeta
            employee = request.env['hr.employee'].sudo().search([('numero_tarjeta', '=', card_code)], limit=1)
            if not employee:
                _logger.error("Empleado no encontrado para el código de tarjeta: %s", card_code)
                return self._json_response("error", "Empleado no encontrado")

            # Construir la respuesta con la información del empleado
            response_data = {
                "name": employee.name,
                "credito": float(employee.credito),
                "credito_disponible": float(employee.credito_disponible)
            }

            _logger.info("Respuesta JSON enviada: %s", response_data)
            return self._json_response("success", "Success", response_data)

        except Exception as e:
            _logger.exception("Error en el controlador")
            return self._json_response("error", str(e))

    def _json_response(self, status, status_msg, data=None):
        """
        Función auxiliar para construir respuestas JSON-RPC2 estándar.
        """
        return {
            "jsonrpc": "2.0",
            "id": None,
            "result": {
                "status": status,
                "status_msg": status_msg,
                "data": data if data else None
            }
        }
