from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    enroll_id = fields.Integer(
        string='Enroll ID Biométrico',
        help='ID de inscripción en el dispositivo biométrico',
        index=True
    )
    biometric_person_id = fields.Many2one('biometric.person', string='Usuario Biométrico', compute='_compute_biometric_person', store=False)
    biometric_on_device = fields.Boolean(string='En Biometrico', compute='_compute_biometric_person', store=False)
    biometric_person_name = fields.Char(string='Nombre en Biométrico', compute='_compute_biometric_person', store=False)

    def _compute_biometric_person(self):
        for rec in self:
            rec.biometric_person_id = False
            rec.biometric_on_device = False
            rec.biometric_person_name = False
            if rec.enroll_id:
                person = self.env['biometric.person'].search([('enroll_id', '=', rec.enroll_id)], limit=1)
                if person:
                    rec.biometric_person_id = person
                    rec.biometric_on_device = bool(person and person.active)
                    rec.biometric_person_name = person.name
