# -*- coding: utf-8 -*-

from odoo import api, fields, models


class LoanTypes(models.Model):
    """Cree varios tipos de prestamos y luego se puedan elegir en la creacion del prestamo"""
    _name = 'loan.type'
    _inherit = ['mail.thread']
    _description = 'Loan Type'

    name = fields.Char(string='Nombre', help="Nombre del prestamo")
    loan_amount = fields.Integer(string='Monto del Préstamo', help="Cantidad a prestar")
    tenure = fields.Integer(string='Duración (meses)', default='1',
                            help="Periodo de amortización")
    tenure_plan = fields.Char(string="Frecuencia de pago", default='monthly',
                              readonly='True')
    interest_rate = fields.Float(string='Tasa de interes',
                                 help="Tasa de interes del prestamo")
    disbursal_amount = fields.Float(string='Importe de caítal',
                                    compute='_compute_disbursal_amount',
                                    help="Valor total a pagar")
    documents_ids = fields.Many2many('loan.documents',
                                     string="Documentos requeridos",)
    processing_fee = fields.Integer(string="Tasa de tramitación",
                                    help="Importe para inicializar el préstamo")
    note = fields.Text(string="Notas")
    company_id = fields.Many2one('res.company', string='Compañia',
                                 readonly=True,
                                 help="Nombre de la compañia",
                                 default=lambda self:
                                 self.env.company, )

    @api.depends('processing_fee')
    def _compute_disbursal_amount(self):
        """Calcular monto a pagar"""
        self.disbursal_amount = self.loan_amount - self.processing_fee

