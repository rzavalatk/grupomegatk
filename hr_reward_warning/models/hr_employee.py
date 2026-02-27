# -*- coding: utf-8 -*-
from odoo import fields, models, _


class HrEmployee(models.Model):
    """Extensión del modelo de Empleado para incluir anuncios.
    
    Agrega funcionalidad para que los empleados puedan ver los anuncios
    que les corresponden según diferentes criterios (generales, por empleado,
    por departamento o por posición de trabajo).
    """
    _inherit = 'hr.employee'

    # ===== CAMPOS ADICIONALES =====
    
    announcement_count = fields.Integer(
        compute='_compute_announcement_count',
        string='# Anuncios',
        help="Conteo de Anuncios disponibles para el empleado")

    # ===== MÉTODOS COMPUTADOS =====

    def _compute_announcement_count(self):
        """Calcula el número total de anuncios para un empleado.
        
        Cuenta todos los anuncios aprobados y activos que aplican al empleado:
        - Anuncios generales (para toda la empresa)
        - Anuncios específicos para este empleado
        - Anuncios para el departamento del empleado
        - Anuncios para la posición de trabajo del empleado
        """
        for employee in self:
            # Cuenta anuncios generales aprobados y vigentes
            announcement_ids_general = self.env[
                'hr.announcement'].sudo().search_count(
                [('is_announcement', '=', True),
                 ('state', '=', 'approved'),
                 ('date_start', '<=', fields.Date.today())])
            
            # Cuenta anuncios dirigidos específicamente a este empleado
            announcement_ids_emp = (self.env['hr.announcement'].
            sudo().search_count(
                [('employee_ids', 'in', self.id),
                 ('state', '=', 'approved'),
                 ('date_start', '<=', fields.Date.today())]))
            
            # Cuenta anuncios dirigidos al departamento del empleado
            announcement_ids_dep = (self.env['hr.announcement'].
            sudo().search_count(
                [('department_ids', 'in', self.department_id.id),
                 ('state', '=', 'approved'),
                 ('date_start', '<=', fields.Date.today())]))
            
            # Cuenta anuncios dirigidos a la posición del empleado
            announcement_ids_job = (self.env['hr.announcement'].
            sudo().search_count(
                [('position_ids', 'in', self.job_id.id),
                 ('state', '=', 'approved'),
                 ('date_start', '<=', fields.Date.today())]))
            
            # Suma todos los anuncios aplicables
            employee.announcement_count = (announcement_ids_general +
                                           announcement_ids_emp +
                                           announcement_ids_dep +
                                           announcement_ids_job)

    # ===== ACCIONES DE BOTONES =====

    def action_open_announcements(self):
        """Abre una vista mostrando los anuncios relacionados con el empleado.
        
        Busca todos los anuncios aprobados que aplican al empleado según
        los diferentes criterios y abre una vista para visualizarlos.
        
        Returns:
            dict: Acción de ventana para mostrar los anuncios
        """
        # Busca anuncios generales
        announcement_ids_general = self.env[
            'hr.announcement'].sudo().search(
            [('is_announcement', '=', True),
             ('state', '=', 'approved'),
             ('date_start', '<=', fields.Date.today())])
        
        # Busca anuncios específicos para este empleado
        announcement_ids_emp = self.env['hr.announcement'].sudo().search(
            [('employee_ids', 'in', self.id),
             ('state', '=', 'approved'),
             ('date_start', '<=', fields.Date.today())])
        
        # Busca anuncios del departamento
        announcement_ids_dep = self.env['hr.announcement'].sudo().search(
            [('department_ids', 'in', self.department_id.id),
             ('state', '=', 'approved'),
             ('date_start', '<=', fields.Date.today())])
        
        # Busca anuncios de la posición de trabajo
        announcement_ids_job = self.env['hr.announcement'].sudo().search(
            [('position_ids', 'in', self.job_id.id),
             ('state', '=', 'approved'),
             ('date_start', '<=', fields.Date.today())])
        
        # Combina todos los IDs de anuncios
        announcement_ids = (announcement_ids_general.ids +
                            announcement_ids_emp.ids +
                            announcement_ids_job.ids + 
                            announcement_ids_dep.ids)
        
        # Obtiene la vista de formulario
        view_id = self.env.ref('hr_reward_warning.hr_announcement_view_form').id
        
        if announcement_ids:
            if len(announcement_ids) > 1:
                # Si hay múltiples anuncios, muestra una lista
                value = {
                    'domain': [('id', 'in', announcement_ids)],
                    'view_mode': 'list,form',
                    'res_model': 'hr.announcement',
                    'type': 'ir.actions.act_window',
                    'name': _('Anuncios'),
                }
            else:
                # Si hay solo un anuncio, abre directamente el formulario
                value = {
                    'view_mode': 'form',
                    'res_model': 'hr.announcement',
                    'view_id': view_id,
                    'type': 'ir.actions.act_window',
                    'name': _('Anuncios'),
                    'res_id': announcement_ids and announcement_ids[0],
                }
            return value

    def announcement_view(self):
        """Alias para compatibilidad con vistas antiguas.

        Mantiene funcionando el botón que llama a ``announcement_view``
        reutilizando la lógica nueva de ``action_open_announcements``.
        """
        return self.action_open_announcements()
