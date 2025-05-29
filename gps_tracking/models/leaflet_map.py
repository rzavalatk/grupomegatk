from odoo import models, fields, api

class LeafletMap(models.AbstractModel):
    _name = 'gps_tracking.leaflet_map'
    _description = 'Leaflet Map Widget'

    @api.model
    def get_locations(self, trip_id):
        locations = self.env['gps.device.location'].search_read(
            [('trip_id', '=', trip_id)],
            ['latitude', 'longitude', 'timestamp']
        )
        return locations