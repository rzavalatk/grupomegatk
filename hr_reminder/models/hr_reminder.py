# -*- coding: utf-8 -*-
from odoo import models, fields


class HrReminder(models.Model):
    """Modelo de Recordatorios de RRHH.
    
    Permite crear recordatorios configurables basados en fechas de modelos
    de Recursos Humanos. Los recordatorios pueden configurarse para aparecer:
    - Hoy (hoy mismo)
    - Por período (rango de fechas)
    - Por fecha específica (con días de anticipación)
    
    Los recordatorios aparecen en la barra superior del sistema (systray)
    y pueden tener fechas de expiración opcionales.
    """
    _name = 'hr.reminder'
    _description = "Recordatorio de RRHH"

    # ===== CAMPOS BÁSICOS =====
    
    name = fields.Char(string='Título', required=True,
                       help="Título del recordatorio")
    model_id = fields.Many2one('ir.model', help="Elija el nombre del modelo",
                               string="Modelo", required=True,
                               ondelete='cascade',
                               domain="[('model', 'like','hr')]")
    field_id = fields.Many2one('ir.model.fields', string='Campo',
                               help="Elija el campo de fecha",
                               domain="[('model_id', '=',model_id),"
                                      "('ttype', 'in', ['datetime','date'])]"
                               , required=True, ondelete='cascade')
    
    # ===== CONFIGURACIÓN DE BÚSQUEDA =====
    
    search_by = fields.Selection([('today', 'Hoy'),
                                  ('set_period', 'Establecer Período'),
                                  ('set_date', 'Establecer Fecha'), ],
                                 required=True, string="Buscar Por",
                                 help="Buscar por el campo especificado")
    days_before = fields.Integer(string='Recordar antes',
                                 help="Número de días antes de que se muestre "
                                      "el recordatorio")
    
    # ===== CAMPOS DE FECHA =====
    
    date_set = fields.Date(string='Seleccionar Fecha',
                           help="Seleccione la fecha del recordatorio")
    date_from = fields.Date(string="Fecha de Inicio",
                            help="Fecha de inicio para mostrar el recordatorio")
    date_to = fields.Date(string="Fecha Final",
                          help="Fecha final para dejar de mostrar el recordatorio")
    expiry_date = fields.Date(string="Fecha de Expiración del Recordatorio",
                              help="Fecha de expiración para que caduque el recordatorio")
    
    # ===== OTROS CAMPOS =====
    
    company_id = fields.Many2one('res.company', string='Compañía',
                                 required=True, help="Compañía del registro",
                                 default=lambda self: self.env.user.company_id)
