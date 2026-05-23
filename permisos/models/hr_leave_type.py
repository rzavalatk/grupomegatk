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
            # Solo cambiar requires_allocation en nuevos registros
            if not self.id or not self._origin.id:
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
                # Solo establecer requires_allocation para nuevos registros
                if 'id' not in vals:
                    vals['requires_allocation'] = 'no'
        return super().create(vals_list)

    def write(self, vals):
        # Si hay permisos validados, NO permitir cambio de requires_allocation
        if 'requires_allocation' in vals and self._has_validated_leaves():
            # Remover requires_allocation de los valores a actualizar
            vals = dict(vals)  # Crear copia para no modificar el original
            vals.pop('requires_allocation')
        
        # Si se está activando el checkbox de vacaciones, ajustar allow_negative_balance
        if vals.get('vacaciones'):
            vals['allow_negative_balance'] = True
            # Solo intentar cambiar requires_allocation si no hay permisos validados
            if not self._has_validated_leaves():
                vals['requires_allocation'] = 'no'
        
        return super().write(vals)
    
    def _has_validated_leaves(self):
        """Verifica si este tipo de permiso tiene permisos validados"""
        for leave_type in self:
            validated_leaves = self.env['hr.leave'].search_count([
                ('holiday_status_id', '=', leave_type.id),
                ('state', 'in', ['validate', 'validate1'])
            ], limit=1)
            if validated_leaves:
                return True
        return False

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
            # Si el tipo de permiso ya existe, NO modificar requires_allocation
            # para evitar conflictos con permisos validados
            safe_vals = {k: v for k, v in vals.items() if k != 'requires_allocation'}
            leave_type.write(safe_vals)
            if 'active' in leave_type._fields and not leave_type.active:
                leave_type.active = True
            return leave_type

        # Para nuevos tipos, usar todos los valores
        return self.create(vals)

    def init(self):
        # Asegura consistencia en registros existentes al actualizar el modulo.
        # Solo actualizar allow_negative_balance (siempre es seguro de modificar)
        # NO tocar requires_allocation para evitar conflictos con permisos validados
        self.env.cr.execute(
            """
            UPDATE hr_leave_type
               SET allow_negative_balance = TRUE
             WHERE vacaciones IS TRUE
            """
        )
        self._ensure_overtime_leave_type()