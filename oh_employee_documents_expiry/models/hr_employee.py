# -*- coding: utf-8 -*-
from odoo import fields, models, _


class HrEmployee(models.Model):
    """Extensión del modelo de Empleado para gestión de documentos.
    
    Agrega funcionalidad para que los empleados puedan:
    - Ver el conteo de sus documentos
    - Acceder a la lista completa de sus documentos
    - Gestionar documentos con vencimientos
    """
    _inherit = 'hr.employee'

    # ===== CAMPO COMPUTADO =====
    
    document_count = fields.Integer(compute='_compute_document_count',
                                    string='Documentos',
                                    help='Conteo de documentos.')

    # ===== MÉTODOS COMPUTADOS =====
    
    def _compute_document_count(self):
        """Calcula el número total de documentos del empleado.
        
        Cuenta todos los documentos asociados al empleado actual,
        útil para mostrar en smart buttons y estadísticas.
        """
        for rec in self:
            rec.document_count = self.env[
                'hr.employee.document'].sudo().search_count(
                [('employee_ref_id', '=', rec.id)])

    # ===== ACCIONES DE BOTONES =====
    
    def action_document_view(self):
        """Abre una vista para listar todos los documentos del empleado actual.
        
        Permite al empleado o al gerente de RRHH acceder rápidamente a todos
        los documentos asociados, pudiendo ver su estado de vencimiento y
        gestionar renovaciones.
        
        Returns:
            dict: Acción de ventana con la vista de documentos filtrada
        """
        self.ensure_one()
        return {
            'name': _('Documentos'),
            'domain': [('employee_ref_id', '=', self.id)],
            'res_model': 'hr.employee.document',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'list,form',
            'help': _('''<p class="oe_view_nocontent_create">
                           Click to Create for New Documents
                        </p>'''),
            'limit': 80,
            'context': "{'default_employee_ref_id': %s}" % self.id
        }
