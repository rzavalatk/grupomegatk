from odoo import models, fields, api

class CustomAccountMove(models.Model):
    _inherit = 'account.move'
    
    """@api.model_create_multi
    def write(self, vals):
        for move in self:
            if 'line_ids' in vals:
                # Comenta o elimina el bloque de código que deseas desactivar
                # if self._context.get('check_move_validity', False):
                #     move._check_balanced()
                move.update_lines_tax_exigibility()
        return super(CustomAccountMove, self).write(vals)"""
    
    