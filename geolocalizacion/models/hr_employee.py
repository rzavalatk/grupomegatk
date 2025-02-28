# from odoo import models, fields, api, exceptions
# from geopy.geocoders import Nominatim
# import logging
# from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
# from datetime import datetime, timedelta

# _logger = logging.getLogger(__name__)

# class HrEmployee(models.Model):
#     _inherit = 'hr.employee'

#     tracking_active = fields.Boolean('Tracking', default=False)
    
#     def start_tracking(self):
#         self.ensure_one()
#         if not self.tracking_active:
#             self.tracking_active = True
            
#     def stop_tracking(self):
#         self.ensure_one()
#         self.tracking_active = False
        
#     def _start_tracking_loop(self):
#         self.ensure_one()
#         if self.tracking_active:
#             self._get_current_location()
#             self.env.cr.commit()
#             self.env['ir.cron'].sudo().create({
#                 'name': 'Geolocalizacion',
#                 'user_id': self.env.user.id,
#                 'model_id': self.env.ref('geolocalizacion.model_hr_employee').id,
#                 'state': 'code',
#                 'code': 'model._start_tracking_loop(%d)' % self.id,
#                 'interval_number': 5,
#                 'interval_type': 'minutes',
#                 'numbercall': -1,
#                 'doall': True
#             })
    
#     def _get_current_location(self, latitude, longitude):
#         self.ensure_one()
#         if self.location_tracking_active:
#             self._geolocate(latitude, longitude)

#     def _update_location(self, latitude, longitude):
#         self.ensure_one()
#         self._geolocate(latitude, longitude)
        
#     def _geolocate(self, latitude, longitude):
#         geolocator = Nominatim(user_agent='my-app')
#         location = geolocator.reverse(f"{latitude}, {longitude}")
#         self.env['hr.attendance'].create({
#             'employee_id': self.id,
#             'checkin_latitude': latitude,
#             'checkin_longitude': longitude,
#             'checkin_location': f"https://www.google.com/maps/search/?api=1&query={latitude},{longitude}",
#         })