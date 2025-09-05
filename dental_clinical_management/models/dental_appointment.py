from odoo import api, fields, models, _

class DentalAppointment(models.Model):
    """Detalles de la cita dental del paciente"""
    _name = 'dental.appointment'
    _description = "Cita dental para pacientes"
    _inherit = "mail.thread"
    _rec_name = 'sequence_no'

    sequence_no = fields.Char(string='No. de Secuencia', readonly=True,
                              default=lambda self: _('New'),
                              copy=False,
                              help="Número de secuencia de la cita")
    token_no = fields.Integer(string='No. de Turno', copy=False,
                              readonly=True,
                              help="Número de turno de las citas")
    patient_id = fields.Many2one('res.partner',
                                 string="Nombre del Paciente",
                                 domain="[('is_patient', '=', True)]",
                                 copy=False,
                                 required=True,
                                 help="Agregar el paciente")
    patient_phone = fields.Char(related="patient_id.phone", string="Teléfono",
                                help="Número de teléfono del paciente")
    patient_age = fields.Integer(related="patient_id.patient_age", string="Edad",
                                 help="Edad del paciente")
    specialist_id = fields.Many2one('dental.specialist',
                                    string="Departamento Médico",
                                    help='Elegir el departamento médico')
    doctor_ids = fields.Many2many('hr.employee',
                                  compute='_compute_doctor_ids',
                                  string="Datos de los Doctores", help="Datos de los doctores",
                                  )
    doctor_id = fields.Many2one('hr.employee', string="Doctor",
                                required=True,
                                domain="[('id', 'in', doctor_ids)]",
                                help="Nombre del doctor")
    time_shift_ids = fields.Many2many('dental.time.shift',
                                      string="Turno",
                                      help="Elegir el turno",
                                      compute='_compute_time_shifts')
    shift_id = fields.Many2one('dental.time.shift',
                               string="Hora de Reserva",
                               domain="[('id','in',time_shift_ids)]",
                               help="Elegir el turno")
    date = fields.Date(string="Fecha", required=True,
                       default=fields.date.today(),
                       help="Fecha para tomar la cita con el doctor")
    reason = fields.Text(string="Describa el motivo",
                         help="Explique el motivo para tomar la cita médica")
    state = fields.Selection([('draft', 'Borrador'),
                              ('new', 'Nueva Cita'),
                              ('done', 'Prescrito'),
                              ('cancel', 'Cancelado')],
                             default="draft",
                             string="Estado", help="Estado de la cita")

    @api.model
    def create(self, vals):
        """Función declarada para crear el número de secuencia para las citas"""
        if vals.get('sequence_no', _('New')) == _('New'):
            vals['sequence_no'] = self.env['ir.sequence'].next_by_code(
                'dental.appointment') or _('New')
        last_token = self.search(
            [('doctor_id', '=', int(vals['doctor_id'])),
             ('date', '=', vals['date']),
             ('shift_id', '=', int(vals['shift_id']))],
            order='id desc', limit=1)
        vals['token_no'] = last_token.token_no + 1 if last_token else 1
        res = super(DentalAppointment, self).create(vals)
        res.state = 'new'
        return res

    def action_create_appointment(self):
        """Cambiar el estado de la cita al hacer clic en el botón crear"""
        self.state = 'new'

    @api.depends('doctor_id')
    def _compute_time_shifts(self):
        """Obtener el turno del doctor"""
        for record in self:
            record.time_shift_ids = self.env['dental.time.shift'].search(
                [('id', 'in', record.doctor_id.time_shift_ids.ids)]).ids

    @api.depends('specialist_id')
    def _compute_doctor_ids(self):
        """Buscar doctores según su especialización"""
        for record in self:
            if record.specialist_id:
                record.doctor_ids = self.env['hr.employee'].search(
                    [('specialised_in_id', '=', record.specialist_id.id)]).ids
            else:
                record.doctor_ids = self.env['hr.employee'].search([]).ids

    def action_cancel(self):
        """Cambiar el estado de la cita al hacer clic en el botón cancelar"""
        self.state = 'cancel'

    def action_prescription(self):
        """Acción creada para ver las prescripciones
        de las citas en estado 'Prescrito'"""
        return {
            'type': 'ir.actions.act_window',
            'target': 'inline',
            'name': 'Prescripción',
            'view_mode': 'form',
            'res_model': 'dental.prescription',
            'res_id': self.env['dental.prescription'].search([
                ('appointment_id', '=', self.id)], limit=1).id,
        }
