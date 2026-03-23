from odoo import models, fields, api


class HrLeave(models.Model):
    _inherit = "hr.leave.type"
    _description = "Tipos de permiso"
    
    vacaciones = fields.Boolean('Vacaciones')
    deducciones = fields.Boolean('Deducción de sueldo')
    sin_cargo = fields.Boolean('Sin cargo')
    incapacidad = fields.Boolean('Incapacidad')
    
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