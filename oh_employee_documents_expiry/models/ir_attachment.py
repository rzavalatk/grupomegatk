# -*- coding: utf-8 -*-
from odoo import fields, models


class IrAttachment(models.Model):
    """Extensión del modelo de Adjuntos para documentos de RRHH.
    
    Esta clase hereda de 'ir.attachment' e introduce dos relaciones many-to-many:
    - 'doc_attach_rel': Para asociar documentos de empleados de RRHH
    - 'attach_rel': Para adjuntar plantillas de documentos generales de RRHH
    
    Permite vincular archivos adjuntos con documentos de empleados y plantillas,
    facilitando la gestión centralizada de archivos relacionados con RRHH.
    """
    _inherit = 'ir.attachment'

    # ===== RELACIONES CON DOCUMENTOS DE RRHH =====
    
    doc_attach_rel = fields.Many2many('hr.employee.document',
                                      'doc_attachment_ids',
                                      'attach_id3', 'doc_id',
                                      string="Adjunto", invisible=1,
                                      help='Este campo le permite asociar'
                                           'documentos de empleados de RRHH con el '
                                           'registro.')
    attach_rel = fields.Many2many('hr.document',
                                  'attach_ids', 'attachment_id3',
                                  'document_id',
                                  string="Adjunto", invisible=1,
                                  help='Este campo le permite adjuntar '
                                       'plantillas de documentos de RRHH al registro.')
