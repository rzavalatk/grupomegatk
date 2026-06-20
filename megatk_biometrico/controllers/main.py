from odoo import http
from odoo.http import request
import json

class BiometricController(http.Controller):
    @http.route('/biometric/records/download', type='http', auth='user', methods=['GET'])
    def download_records(self, **kwargs):
        records = request.env['biometric.record'].search([])
        lines = [
            'device_serial_num,enroll_id,records_time_raw,mode,inout,event,temperature,image',
        ]
        for rec in records:
            lines.append(','.join([
                rec.device_serial_num or '',
                str(rec.enroll_id or ''),
                rec.records_time_raw or '',
                str(rec.mode or ''),
                str(rec.inout or ''),
                str(rec.event or ''),
                str(rec.temperature or ''),
                rec.image or ''
            ]))
        content = '\n'.join(lines)
        return request.make_response(content,
            headers=[
                ('Content-Type', 'text/csv'),
                ('Content-Disposition', 'attachment; filename=biometric_records.csv')
            ]
        )
