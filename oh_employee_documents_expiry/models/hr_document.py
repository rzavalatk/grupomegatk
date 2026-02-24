# -*- coding: utf-8 -*-
from odoo import fields, models


class HrDocument(models.Model):
    """Plantillas de Documentos de RRHH.
    
    Este modelo permite crear plantillas de documentos reutilizables
    que pueden ser utilizadas como base para documentos de empleados.
    Útil para estandarizar formatos de documentos comunes en la empresa.
    
    Ejemplos de plantillas:
    - Formato de solicitud de vacaciones
    - Plantilla de certificado laboral
    - Formato de declaración jurada
    """
    _name = 'hr.document'
    _description = 'Plantilla de Documento de RRHH'

    # ===== CAMPOS DE LA PLANTILLA =====
    
    name = fields.Char(string='Nombre del Documento', required=True, copy=False,
                       help='Puede ingresar el nombre de su documento aquí.')
    note = fields.Text(string='Nota', copy=False, 
                       help="Nota o descripción del documento.")
    attach_ids = fields.Many2many('ir.attachment',
                                  'attach_rel', 'doc_id',
                                  'attach_id3', string="Adjunto",
                                  help='Puede adjuntar la copia de su'
                                       ' documento.', copy=False)
