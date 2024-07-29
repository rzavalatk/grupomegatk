# -*- coding: utf-8 -*-

from odoo import fields, models


class LoanDocuments(models.Model):
    """Documentos necesarios para aprobar el préstamo, por ejemplo:-DNI, Constancia de trabajo ..."""
    _name = 'loan.documents'
    _description = 'Loan Documents'
    _rec_name = 'loan_proofs'

    loan_proofs = fields.Char(string="Documentos", help="Nombre del documento ")
    company_id = fields.Many2one('res.company', string='Compañia',
                                 readonly=True,
                                 help="Nombre de la compañia",
                                 default=lambda self:
                                 self.env.company)

