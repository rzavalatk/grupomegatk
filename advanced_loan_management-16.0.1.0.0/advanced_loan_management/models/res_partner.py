# -*- coding: utf-8 -*-

from odoo import fields, models


class ResPartner(models.Model):
    """Añadir nueva pestaña para mostrar el recuento de préstamos de los clientes"""
    _inherit = "res.partner"

    def _compute_partner_loans(self):
        """Calcula el importe del préstamo y el número total de préstamos de un socio.."""
        self.loan_count = self.env['loan.request'].search_count(
            [('partner_id', '=', self.id),
             ('state', 'in', ('pro_pago', 'pagado'))])

    loan_count = fields.Integer(string="Loan Count",
                                compute='_compute_partner_loans',
                                help="Displays numbers of loans "
                                     "ongoing and closed by the employee")

    def action_view_loans(self):
        """Returns loan records of current employee"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Loans',
            'view_mode': 'tree',
            'res_model': 'loan.request',
            'domain': [('partner_id', '=', self.id)],
            'context': "{'create': False}"
        }
