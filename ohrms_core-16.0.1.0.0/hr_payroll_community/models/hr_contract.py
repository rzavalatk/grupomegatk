# -*- coding:utf-8 -*-

from odoo import api, fields, models


class HrContract(models.Model):
    _inherit = 'hr.contract'
    _description = 'Contrato del Empleado'

    struct_id = fields.Many2one('hr.payroll.structure', string='Estructura Salarial')
    schedule_pay = fields.Selection([
        ('monthly', 'Mensual'),
        ('quarterly', 'Trimestral'),
        ('semi-annually', 'Semi Anual'),
        ('annually', 'Anual'),
        ('weekly', 'Semanal'),
    ], string='Pago Programado', index=True, default='monthly',
        help="Define la frecuencia de pago del salario.")
    resource_calendar_id = fields.Many2one(
        required=True, help="Horario de trabajo del empleado.")
    medical_allowance = fields.Monetary(
        string="Subsidio Médico", help="Subsidio médico otorgado al empleado.")
    other_allowance = fields.Monetary(
        string="Otras Indemnizaciones", help="Indemnizaciones adicionales otorgadas al empleado.")

    def get_all_structures(self):
        """
        @return: las estructuras vinculadas a los contratos dados, ordenadas por jerarquía 
                 (primero las que no tienen padre, luego las de primer nivel y así sucesivamente), 
                 y sin duplicados.
        """
        structures = self.mapped('struct_id')
        if not structures:
            return []
        # YTI TODO: retornar registros navegables
        return list(set(structures._get_parent_structure().ids))

    def get_attribute(self, code, attribute):
        """
        @param code: Código del atributo a buscar.
        @param attribute: Nombre del atributo que se desea recuperar.
        @return: el valor del atributo encontrado en la plantilla de ventajas.
        """
        return self.env['hr.contract.advantage.template'].search([('code', '=', code)], limit=1)[attribute]

    def set_attribute_value(self, code, active):
        """
        @param code: Código del atributo a actualizar.
        @param active: Booleano para activar o desactivar el atributo.
        """
        for contract in self:
            if active:
                value = self.env['hr.contract.advantage.template'].search(
                    [('code', '=', code)], limit=1).default_value
                contract[code] = value
            else:
                contract[code] = 0.0


class HrContractAdvandageTemplate(models.Model):
    _name = 'hr.contract.advantage.template'
    _description = "Ventajas del Contrato del Empleado"

    name = fields.Char('Nombre', required=True)
    code = fields.Char('Código', required=True)
    lower_bound = fields.Float(
        'Límite Inferior', help="Límite inferior autorizado por el empleador para esta ventaja.")
    upper_bound = fields.Float(
        'Límite Superior', help="Límite superior autorizado por el empleador para esta ventaja.")
    default_value = fields.Float('Valor por Defecto', help="Valor por defecto para esta ventaja.")
