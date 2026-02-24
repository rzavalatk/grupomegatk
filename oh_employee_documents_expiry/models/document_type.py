# -*- coding: utf-8 -*-
from odoo import fields, models


class DocumentType(models.Model):
    """Modelo de Tipos de Documentos.
    
    Este modelo se utiliza para categorizar y gestionar varios tipos de
    documentos en el sistema. Permite definir categorías personalizadas
    como: Pasaportes, Licencias, Certificados, Permisos, etc.
    
    Ejemplos de uso:
    - Pasaporte
    - Licencia de Conducir
    - Certificado Profesional
    - Permiso de Trabajo
    - Contrato Laboral
    """
    _name = 'document.type'
    _description = 'Tipo de Documento'

    # ===== CAMPO PRINCIPAL =====
    
    name = fields.Char(string="Nombre", required=True,
                       help="Nombre del tipo de documento")
