from odoo import http
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)

class EmployeeController(http.Controller):

    @http.route('/api/validate_card', type='json', auth='user', methods=['POST'])
    def validate_card(self, **kwargs):
        try:
            # Obtener el cuerpo de la solicitud JSON
            data = json.loads(request.httprequest.data)
            _logger.info("Datos recibidos: %s", data)

            # Extraer el código de la tarjeta
            cardCode = data.get('cardCode')
            if not cardCode:
                _logger.error("Código de tarjeta no proporcionado")
                return {
                    "jsonrpc": "2.0",
                    "id": None,
                    "result": {
                        "status": "error",
                        "status_msg": "Código de tarjeta no proporcionado"
                    }
                }

            # Buscar el empleado por el número de tarjeta
            employee = request.env['hr.employee'].sudo().search([('numero_tarjeta', '=', cardCode)], limit=1)
            if not employee:
                _logger.error("Empleado no encontrado para el código de tarjeta: %s", cardCode)
                return {
                    "jsonrpc": "2.0",
                    "id": None,
                    "result": {
                        "status": "error",
                        "status_msg": "Empleado no encontrado"
                    }
                }

            # Devolver la información del empleado en formato JSON-RPC2
            response_data = {
                "jsonrpc": "2.0",
                "id": None,
                "result": {
                    "status": "success",
                    "status_msg": "Success",
                    "data": {
                        "name": employee.name,
                        "credito": float(employee.credito),
                        "credito_disponible": float(employee.credito_disponible)
                    }
                }
            }

            _logger.info("Respuesta JSON enviada: %s", response_data)
            return response_data

        except Exception as e:
            _logger.error("Error en el controlador: %s", str(e))
            return {
                "jsonrpc": "2.0",
                "id": None,
                "result": {
                    "status": "error",
                    "status_msg": str(e)
                }
            }