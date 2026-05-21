# -*- coding: utf-8 -*-
from odoo import fields, models


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    x_is_technical_area = fields.Boolean(
        related="team_id.x_is_technical_area",
        store=True,
        readonly=True,
    )
    x_tecnico_diagnostico = fields.Text(string="Diagnostico tecnico")
    x_tecnico_solucion = fields.Text(string="Solucion aplicada")

    def action_print_orden_ingreso(self):
        """Imprime la orden de ingreso del ticket"""
        return self.env.ref("helpdesk_custom_megatk.helpdesk_ticket_orden_ingreso").report_action(self)

    def action_print_visita_tecnica(self):
        """Imprime la visita técnica del ticket"""
        return self.env.ref("helpdesk_custom_megatk.helpdesk_ticket_visita_tecnica").report_action(self)

    def action_print_entrega_equipo(self):
        """Imprime la entrega de equipo del ticket"""
        return self.env.ref("helpdesk_custom_megatk.helpdesk_ticket_entrega_equipo").report_action(self)
