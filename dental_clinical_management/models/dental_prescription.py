# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class DentalPrescription(models.Model):
    """Prescripción del paciente de la clínica dental"""
    _name = 'dental.prescription'
    _description = "Prescripción Dental"
    _inherit = ['mail.thread']
    _rec_name = "sequence_no"

    sequence_no = fields.Char(string='No. de Secuencia', required=True,
                              readonly=True, default=lambda self: _('Nuevo'),
                              help="Número de secuencia de la prescripción dental")
    appointment_ids = fields.Many2many('dental.appointment',
                                       string="Cita",
                                       compute="_compute_appointment_ids",
                                       help="Para obtener todas las citas creadas")
    appointment_id = fields.Many2one('dental.appointment',
                                     string="Cita",
                                     domain="[('id','in',appointment_ids)]",
                                     required=True,
                                     help="Citas creadas")
    patient_id = fields.Many2one(related="appointment_id.patient_id",
                                 string="Paciente",
                                 required=True,
                                 help="Nombre del paciente")
    token_no = fields.Integer(related="appointment_id.token_no",
                              string="No. de Turno",
                              help="Número de turno del paciente")
    treatment_id = fields.Many2one('dental.treatment',
                                   string="Tratamiento",
                                   help="Nombre del tratamiento realizado al paciente")
    cost = fields.Float(related="treatment_id.cost",
                        string="Costo del Tratamiento",
                        help="Costo del tratamiento")
    currency_id = fields.Many2one('res.currency', 'Moneda',
                                  default=lambda self: self.env.user.company_id.currency_id,
                                  required=True,
                                  help="Agregar el tipo de moneda en el costo")
    prescribed_doctor_id = fields.Many2one(related="appointment_id.doctor_id",
                                           string='Doctor que prescribe',
                                           required=True,
                                           help="Doctor que prescribe")
    prescription_date = fields.Date(related="appointment_id.date",
                                    string='Fecha de Prescripción',
                                    required=True,
                                    help="Fecha de la prescripción")
    state = fields.Selection([('new', 'Nueva'),
                              ('done', 'Prescrita'),
                              ('invoiced', 'Facturada')],
                             default="new",
                             string="Estado",
                             help="Estado de la cita")
    medicine_ids = fields.One2many('dental.prescription_lines',
                                   'prescription_id',
                                   string="Medicamento",
                                   help="Medicamentos")
    invoice_data_id = fields.Many2one(comodel_name="account.move",
                                      string="Datos de Factura",
                                      help="Datos de la factura")
    grand_total = fields.Float(compute="_compute_grand_total",
                               string="Total General",
                               help="Obtener el monto total general")

    @api.model
    def create(self, vals):
        """Función declarada para crear el número de secuencia para pacientes"""
        if vals.get('sequence_no', _('Nuevo')) == _('Nuevo'):
            vals['sequence_no'] = self.env['ir.sequence'].next_by_code(
                'dental.prescriptions') or _('Nuevo')
        res = super(DentalPrescription, self).create(vals)
        return res

    @api.depends('appointment_id')
    def _compute_appointment_ids(self):
        """Calcula y asigna el campo `appointment_ids` para cada registro.
        Este método busca todos los registros `dental.appointment` que tengan
        estado `new` y fecha igual a la fecha de hoy. Luego actualiza el campo
        `appointment_ids` de cada registro `DentalPrescription` con los IDs encontrados."""
        for rec in self:
            rec.appointment_ids = self.env['dental.appointment'].search(
                [('state', '=', 'new'), ('date', '=', fields.Date.today())]).ids

    def action_prescribed(self):
        """Marca la prescripción y su cita asociada como `done`.
        Este método actualiza el estado tanto de la instancia DentalPrescription
        como de su instancia vinculada 'dental.appointment' a `done`, indicando
        que la prescripción ha sido finalizada y la cita completada."""
        self.state = 'done'
        self.appointment_id.state = 'done'

    def create_invoice(self):
        """Crear una factura basada en la factura del paciente."""
        self.ensure_one()
        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.patient_id.id,
            'invoice_line_ids': [
                fields.Command.create({
                    'name': self.treatment_id.name,
                    'quantity': 1,
                    'price_unit': self.cost,
                })
            ]
        }
        invoice = self.env['account.move'].create(invoice_vals)
        for rec in self.medicine_ids:
            product_id = self.env['product.product'].search([
                ('product_tmpl_id', '=', rec.medicament_id.id)])
            invoice['invoice_line_ids'] = [(0, 0, {
                'product_id': product_id.id,
                'name': rec.display_name,
                'quantity': rec.quantity,
                'price_unit': rec.price,
            })]
        self.invoice_data_id = invoice.id
        invoice.action_post()
        self.state = 'invoiced'
        return {
            'name': _('Factura de Cliente'),
            'view_mode': 'form',
            'view_id': self.env.ref('account.view_move_form').id,
            'res_model': 'account.move',
            'context': "{'move_type':'out_invoice'}",
            'type': 'ir.actions.act_window',
            'res_id': self.invoice_data_id.id,
        }

    def action_view_invoice(self):
        """Vista de la factura"""
        return {
            'name': _('Factura de Cliente'),
            'view_mode': 'form',
            'view_id': self.env.ref('account.view_move_form').id,
            'res_model': 'account.move',
            'context': "{'move_type':'out_invoice'}",
            'type': 'ir.actions.act_window',
            'res_id': self.invoice_data_id.id,
        }

    def _compute_grand_total(self):
        """Calcula el costo total general de la prescripción dental.

        Este método inicializa el total general con el costo del tratamiento
        y luego recorre todos los medicamentos prescritos, sumando su costo total
        al total general. El total general se almacena en el campo `grand_total`
        del modelo `DentalPrescription`."""
        self.grand_total = self.cost
        for rec in self.medicine_ids:
            self.grand_total += rec.total


class DentalPrescriptionLines(models.Model):
    """Líneas de prescripción de la clínica dental"""
    _name = 'dental.prescription_lines'
    _description = "Líneas de Prescripción Dental"
    _rec_name = "medicament_id"

    medicament_id = fields.Many2one('product.template',
                                    domain="[('is_medicine', '=', True)]",
                                    string="Medicamento",
                                    help="Nombre del medicamento")
    generic_name = fields.Char(string="Nombre Genérico",
                               related="medicament_id.generic_name",
                               help="Nombre genérico del medicamento")
    dosage_strength = fields.Integer(string="Concentración",
                                     related="medicament_id.dosage_strength",
                                     help="Concentración del medicamento")
    medicament_form = fields.Selection([('tablet', 'Tabletas'),
                             ('capsule', 'Cápsulas'),
                             ('liquid', 'Líquido'),
                             ('injection', 'Inyecciones')],
                            string="Forma del Medicamento",
                            required=True,
                            help="Agregar la forma del medicamento")
    quantity = fields.Integer(string="Cantidad",
                              required=True,
                              help="Cantidad de medicamento")
    frequency_id = fields.Many2one('medicine.frequency',
                                   string="Frecuencia",
                                   required=True,
                                   help="Frecuencia del medicamento")
    price = fields.Float(related='medicament_id.list_price',
                         string="Precio",
                         help="Costo del medicamento")
    total = fields.Float(string="Precio Total",
                         help="Precio total del medicamento")
    prescription_id = fields.Many2one('dental.prescription',
                                      help="Relacionar el modelo con dental_prescription")

    @api.onchange('quantity')
    def _onchange_quantity(self):
        """Actualiza el precio total del medicamento según la cantidad.
        Este método se activa por un evento onchange del campo `quantity`.
        Calcula el precio total multiplicando la `cantidad` del medicamento por su `precio`
        y actualiza el campo `total` con el nuevo valor."""
        for rec in self:
            rec.total = rec.price * rec.quantity
