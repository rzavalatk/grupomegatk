from odoo import models, fields, api


class HrLeave(models.Model):
    _inherit = "hr.leave.type"
    _description = "Tipos de permiso"
    
    vacaciones = fields.Boolean('Vacaciones')
    deducciones = fields.Boolean('Deducción de sueldo')
    sin_cargo = fields.Boolean('Sin cargo')
    incapacidad = fields.Boolean('Incapacidad')
    is_overtime_compensation = fields.Boolean(
        string='Compensación de horas extra',
        help='Identifica el tipo de tiempo personal usado para convertir y descontar horas extra.'
    )
    
    allow_negative_balance = fields.Boolean(
        string="Permitir saldo negativo",
        help="Permite que los empleados soliciten permisos incluso si no tienen días disponibles asignados."
    )
    
    @api.onchange('vacaciones')
    def _onchange_vacaciones(self):
        self.deducciones = False
        self.sin_cargo = False
        self.incapacidad = False
        if self.vacaciones:
            self.allow_negative_balance = True
            self.requires_allocation = 'no'
    
    @api.onchange('deducciones')
    def _onchange_deducciones(self):
        self.vacaciones = False
        self.sin_cargo = False
        self.incapacidad = False
    
    @api.onchange('sin_cargo')
    def _onchange_sin_cargo(self):
        self.vacaciones = False
        self.deducciones = False
        self.incapacidad = False
    
    @api.onchange('incapacidad')
    def _onchange_incapacidad(self):
        self.vacaciones = False
        self.deducciones = False
        self.sin_cargo = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('vacaciones'):
                vals['allow_negative_balance'] = True
                vals['requires_allocation'] = 'no'
        return super().create(vals_list)

    def write(self, vals):
        result = super().write(vals)
        vacation_types = self.filtered(
            lambda leave_type: leave_type.vacaciones and (
                not leave_type.allow_negative_balance or leave_type.requires_allocation != 'no'
            )
        )
        if vacation_types:
            vacation_types.write({
                'allow_negative_balance': True,
                'requires_allocation': 'no',
            })
        return result

    def _selection_has(self, field_name, value):
        field = self._fields.get(field_name)
        return bool(field and any(option[0] == value for option in field.selection))

    def _get_overtime_leave_type_vals(self):
        vals = {
            'name': 'Horas extra',
            'vacaciones': False,
            'deducciones': False,
            'sin_cargo': False,
            'incapacidad': False,
            'is_overtime_compensation': True,
        }

        if 'requires_allocation' in self._fields and self._selection_has('requires_allocation', 'yes'):
            vals['requires_allocation'] = 'yes'

        if 'employee_requests' in self._fields and self._selection_has('employee_requests', 'yes'):
            vals['employee_requests'] = 'yes'

        if 'leave_validation_type' in self._fields and self._selection_has('leave_validation_type', 'hr'):
            vals['leave_validation_type'] = 'hr'

        if 'request_unit' in self._fields and self._selection_has('request_unit', 'hour'):
            vals['request_unit'] = 'hour'
        elif 'request_unit_hours' in self._fields:
            vals['request_unit_hours'] = True

        if 'allow_negative_balance' in self._fields:
            vals['allow_negative_balance'] = False

        if 'overtime_deductible' in self._fields:
            vals['overtime_deductible'] = True

        return vals

    def _ensure_overtime_leave_type(self):
        leave_type = self.search([
            ('is_overtime_compensation', '=', True),
            ('active', 'in', [True, False]),
        ], limit=1)

        if not leave_type:
            leave_type = self.search([
                ('name', 'ilike', 'hora'),
                ('name', 'ilike', 'extra'),
                ('active', 'in', [True, False]),
            ], limit=1)

        vals = self._get_overtime_leave_type_vals()

        if leave_type:
            leave_type.write(vals)
            if 'active' in leave_type._fields and not leave_type.active:
                leave_type.active = True
            return leave_type

        return self.create(vals)

    def init(self):
        # Asegura consistencia en registros existentes al actualizar el modulo.
        self.env.cr.execute(
            """
            UPDATE hr_leave_type
               SET allow_negative_balance = TRUE,
                   requires_allocation = 'no'
             WHERE vacaciones IS TRUE
            """
        )
        self._ensure_overtime_leave_type()