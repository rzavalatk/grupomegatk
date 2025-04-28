from odoo import models, fields


class HrDocument(models.Model):
    _name = 'hr.document'
    _description = 'Documents Template '

    name = fields.Char(string='Nombre de documento', required=True, copy=False, )
    note = fields.Text(string='Nota', copy=False, help="Nota")
    attach_id = fields.Many2many('ir.attachment', 'attach_rel', 'doc_id', 'attach_id3', string="Adjunto",
                                 help='Puede subir una copia de tu documento', copy=False)
