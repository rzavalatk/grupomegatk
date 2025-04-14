# -*- coding: utf-8 -*-
from odoo import api, fields, models


class OHRMSConfiguration(models.TransientModel):
    _inherit = 'res.config.settings'

    module_hr_custody = fields.Boolean(
    string='Gestionar los bienes de la empresa cuando están en custodia de un empleado',
    help='Ayuda a gestionar las solicitudes de custodia.\n'
         '- Esto instala el módulo Gestión de Custodia.')
    module_oh_employee_check_list = fields.Boolean(
        string='Gestiona el proceso de entrada y salida de los empleados',
        help='Ayuda a gestionar la lista de verificación del empleado.\n'
            '- Esto instala el módulo Lista de Verificación del Empleado.')
    module_hr_employee_shift = fields.Boolean(
        string='Gestionar diferentes tipos de turnos',
        help='Ayuda a gestionar los turnos de los empleados.\n'
            '- Esto instala el módulo Turnos de Empleados.')
    module_hr_insurance = fields.Boolean(
        string='Gestionar seguros para empleados',
        help='Ayuda a gestionar los seguros de los empleados.\n'
            '- Esto instala el módulo Seguros para Empleados.')
    module_oh_hr_lawsuit_management = fields.Boolean(
        string='Gestionar acciones legales',
        help='Ayuda a gestionar la gestión de demandas.\n'
            '- Esto instala el módulo Gestión de Demandas.')
    module_hr_resignation = fields.Boolean(
        string='Gestionar el proceso de renuncia del empleado',
        help='Ayuda a gestionar el proceso de renuncia.\n'
            '- Esto instala el módulo Proceso de Renuncia.')
    module_hr_vacation_mngmt = fields.Boolean(
        string='Gestionar vacaciones de empleados',
        help='Ayuda a gestionar la gestión de vacaciones.\n'
            '- Esto instala el módulo Gestión de Vacaciones.')
    module_oh_hr_zk_attendance = fields.Boolean(
        string='Gestionar la integración del dispositivo biométrico (Modelo: ZKteco uFace 202) con la asistencia de RRHH (Rostro + Huella)',
        help='Ayuda a gestionar la integración del dispositivo biométrico.\n'
            '- Esto instala el módulo Integración de Dispositivo Biométrico.')

    test_module_hr_custody = fields.Boolean(default=False, invisible=True)
    test_oh_employee_check_list = fields.Boolean(default=False, invisible=True)
    test_module_hr_employee_shift = fields.Boolean(default=False, invisible=True)
    test_module_hr_insurance = fields.Boolean(default=False, invisible=True)
    test_module_oh_hr_lawsuit_management = fields.Boolean(default=False, invisible=True)
    test_module_hr_resignation = fields.Boolean(default=False, invisible=True)
    test_module_hr_vacation_mngmt = fields.Boolean(default=False, invisible=True)
    test_module_oh_hr_zk_attendance = fields.Boolean(default=False, invisible=True)

    @api.onchange('module_hr_custody')
    def onchange_module_hr_custody(self):
        for each in self:
            if each.module_hr_custody:
                if not self.env['ir.module.module'].search([('name', '=', 'hr_custody')]):
                    each.test_module_hr_custody = True
                    each.module_hr_custody = False
                else:
                    each.test_module_hr_custody = False

    @api.onchange('module_oh_employee_check_list')
    def onchange_module_oh_employee_check_list(self):
        for each in self:
            if each.module_oh_employee_check_list:
                if not self.env['ir.module.module'].search([('name', '=', 'oh_employee_check_list')]):
                    each.test_oh_employee_check_list = True
                    each.module_oh_employee_check_list = False
                else:
                    each.test_oh_employee_check_list = False

    @api.onchange('module_hr_employee_shift')
    def onchange_module_hr_employee_shift(self):
        for each in self:
            if each.module_hr_employee_shift:
                if not self.env['ir.module.module'].search([('name', '=', 'hr_employee_shift')]):
                    each.test_module_hr_employee_shift = True
                    each.module_hr_employee_shift = False
                else:
                    each.test_module_hr_employee_shift = False

    @api.onchange('module_hr_insurance')
    def onchange_module_hr_insurance(self):
        for each in self:
            if each.module_hr_insurance:
                if not self.env['ir.module.module'].search([('name', '=', 'hr_insurance')]):
                    each.test_module_hr_insurance = True
                    each.module_hr_insurance = False
                else:
                    each.test_module_hr_insurance = False

    @api.onchange('module_oh_hr_lawsuit_management')
    def onchange_module_oh_hr_lawsuit_management(self):
        for each in self:
            if each.module_oh_hr_lawsuit_management:
                if not self.env['ir.module.module'].search([('name', '=', 'oh_hr_lawsuit_management')]):
                    each.test_module_oh_hr_lawsuit_management = True
                    each.module_oh_hr_lawsuit_management = False
                else:
                    each.test_module_oh_hr_lawsuit_management = False

    @api.onchange('module_hr_resignation')
    def onchange_module_hr_resignation(self):
        for each in self:
            if each.module_hr_resignation:
                if not self.env['ir.module.module'].search([('name', '=', 'hr_resignation')]):
                    each.test_module_hr_resignation = True
                    each.module_hr_resignation = False
                else:
                    each.test_module_hr_resignation = False

    @api.onchange('module_hr_vacation_mngmt')
    def onchange_module_hr_vacation_mngmt(self):
        for each in self:
            if each.module_hr_vacation_mngmt:
                if not self.env['ir.module.module'].search([('name', '=', 'hr_vacation_mngmt')]):
                    each.test_module_hr_vacation_mngmt = True
                    each.module_hr_vacation_mngmt = False
                else:
                    each.test_module_hr_vacation_mngmt = False

    @api.onchange('module_oh_hr_zk_attendance')
    def onchange_module_oh_hr_zk_attendance(self):
        for each in self:
            if each.module_oh_hr_zk_attendance:
                if not self.env['ir.module.module'].search([('name', '=', 'oh_hr_zk_attendance')]):
                    each.test_module_oh_hr_zk_attendance = True
                    each.module_oh_hr_zk_attendance = False
                else:
                    each.test_module_oh_hr_zk_attendance = False


