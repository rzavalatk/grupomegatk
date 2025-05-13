from odoo import http
from odoo.http import request

class GpsTrackingController(http.Controller):

    @http.route('/gps/tracking/menu', type='http', auth='user', website=True)
    def tracking_menu(self):
        # Buscar viaje actual en curso para el usuario (o cualquier criterio)
        viaje = request.env['gps.device.trip'].sudo().search([('state', '=', 'ongoing')], limit=1)

        values = {
            'check_in': viaje.check_in if viaje else False,
        }
        return request.render('gps_tracking.TrackingCardMenu', values)
