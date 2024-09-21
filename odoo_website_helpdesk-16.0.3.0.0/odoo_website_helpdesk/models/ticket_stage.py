# -*- coding: utf-8 -*-
from odoo import fields, models, _
from odoo.exceptions import UserError


class TicketStage(models.Model):
    """Este modelo representa las etapas de un ticket de asistencia técnica. Se utiliza una etapa para
    indicar el estado actual de un ticket, como "Nuevo", "En curso",
    "Resuelto" o "Cerrado". Las etapas se utilizan para organizar y seguir el
    progreso de los tickets a lo largo de su ciclo de vida."""

    _name = 'ticket.stage'
    _description = 'Ticket Stage'
    _order = 'sequence, id'
    _fold_name = 'fold'

    name = fields.Char(string='Nombre', help='El nombre del escenario. Este campo se utiliza para '
                       'identificar la etapa y se muestra en varias vistas e informes.')
    active = fields.Boolean(default=True,
                            string='Activo',
                            help='Si el escenario está activo o no.s '
                                 'Si este campo se establece en Falso '
                                 'la etapa no se mostrará en varias vistas e informes.')
    sequence = fields.Integer(string='Secuencia',
                              default=50,
                              help='El número de secuencia de la etapa. Este campo se utiliza para' 
                              'especificar el orden en el que se muestran las etapas en varias vistas e informes.', )
    closing_stage = fields.Boolean(string='Etapa de cierre',
                                   help='Si la etapa es una etapa de cierre o no.  '
                                        'Una etapa de cierre es una etapa '
                                        'que indica que el ticket de la mesa '
                                        'de ayuda ha sido resuelto o cerrado.'
                                        ' Este campo se utiliza para identificar la etapa de cierre '
                                        'y se utiliza en varios cálculos e informes. ')
    cancel_stage = fields.Boolean(string='Etapa de cancelación',)
                              
    starting_stage = fields.Boolean(string='Etapa de inicio',)
    folded = fields.Boolean(string='Folded in Kanban',)
                            
    template_id = fields.Many2one('mail.template',
                                  string='Plantilla',
                                  domain="[('model', '=', 'help.ticket')]")
    group_ids = fields.Many2many('res.groups',
                                 string='Grupos',
                                 help='Choose the group ID')
    fold = fields.Boolean(string='Fold', )

    def unlink(self):
        """Eliminar los tickets del servicio de asistencia técnica de varias etapas."""
        for rec in self:
            tickets = rec.search([])
            sequence = tickets.mapped('sequence')
            lowest_sequence = tickets.filtered(
                lambda x: x.sequence == min(sequence))
            if self.name == "Draft":
                raise UserError(_("No se puede eliminar esta etapa"))
            if rec == lowest_sequence:
                raise UserError(_("No se puede eliminare '%s'" % (rec.name)))
            else:
                res = super().unlink()
                return res
