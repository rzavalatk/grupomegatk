# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Extensión de Configuración para alias de solicitudes de ausencias.
    
    Permite configurar los parámetros necesarios para la creación automática
    de solicitudes de ausencias desde correos electrónicos:
    - Prefijo: Texto que debe aparecer en el asunto del correo
    - Dominio: Dominio de correo electrónico válido para solicitudes
    """
    _inherit = 'res.config.settings'

    # ===== CONFIGURACIÓN DE ALIAS DE CORREO =====
    
    alias_prefix = fields.Char(string='Prefijo',
                               help='Nombre de alias predeterminado para ausencias '
                                    '(ej: "SOLICITUD DE AUSENCIA")',
                               config_parameter='hr_holidays.alias_prefix')
    alias_domain = fields.Char(string='Dominio',
                               help='Dominio de alias predeterminado para ausencias '
                                    '(ej: "@empresa.com")',
                               config_parameter='hr_holidays.alias_domain')
