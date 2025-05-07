
from odoo import http
from odoo.http import request

class LeafletMapController(http.Controller):

    @http.route('/leaflet_map', type='http', auth='user', website=False)
    def leaflet_map(self, **kw):
        return request.render('leaflet_map_demo.leaflet_map_template')
