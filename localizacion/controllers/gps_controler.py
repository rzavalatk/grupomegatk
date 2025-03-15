from odoo import http
from odoo.http import request
import json

class GpsController(http.Controller):

    @http.route('/gps/save_location', type='json', auth='user', methods=['POST'])
    def save_location(self, **kwargs):
        data = json.loads(request.httprequest.data)
        latitude = data.get('latitude')
        longitude = data.get('longitude')

        if latitude and longitude:
            location = request.env['gps.location'].create({
                'name': f"Ubicación de {request.env.user.name}",
                'latitude': latitude,
                'longitude': longitude,
            })
            return {'status': 'success', 'location_id': location.id}
        else:
            return {'status': 'error', 'message': 'Datos de ubicación no válidos'}