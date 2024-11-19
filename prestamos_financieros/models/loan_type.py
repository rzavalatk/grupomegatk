# -*- coding: utf-8 -*-

from odoo import api, fields, models


class LoanTypes(models.Model):
    """Cree varios tipos de prestamos y luego se puedan elegir en la creacion del prestamo"""
    _name = 'loan.type'
    _inherit = ['mail.thread']
    _description = 'Tipo de prestamo'

    name = fields.Char(string='Nombre', help="Nombre del prestamo")
    loan_amount = fields.Integer(string='Monto del Préstamo', help="Cantidad a prestar")
    #company_id = fields.Many2one('res.company', string='Compañia',)
    meses_seleccion = fields.Selection(
        [
            ('12', '12 meses'),
            ('24', '24 meses'),
            ('36', '36 meses'),
            ('48', '48 meses'),
            ('60', '60 meses'),
        ],
        string='Duracion (meses)', required=True, default='12', readonly=True, states={'borrador': [('readonly', False)]})
    
    payment_frequency = fields.Selection([
        ('365', 'Diario'),
        ('52', 'Semanal'),
        ('24', 'Quincenal'),
        ('12', 'Mensual'),
        ('6', 'Bimestral'),
        ('4', 'Trimestral'),
        ('1', 'Anual')
    ], string='Frecuencia de Pago', default='12', required=True, readonly=True, states={'borrador': [('readonly', False)]},)
    
    loan_type = fields.Selection([
        ('personal', 'Personal'),
        ('financiamiento', 'Financiamiento')
    ], string='Tipo de Préstamo', default="personal", required=True, readonly=True, states={'borrador': [('readonly', False)]},)
    
    state = fields.Selection([
        ('borrador', 'Borrador'),
        ('aprobado', 'Aprobado')
    ], string='Estado', default='borrador', required=True)
    
    interest_rate = fields.Float(string='Tasa de interes',
                                 help="Tasa de interes del prestamo")
    disbursal_amount = fields.Float(string='Capital a pagar',
                                    compute='_compute_disbursal_amount',
                                    help="Valor total a pagar")
    documents_ids = fields.Many2many('loan.documents',
                                     string="Documentos requeridos",)
    processing_fee = fields.Integer(string="Prima de procesamiento",
                                    help="Importe para inicializar el préstamo")
    note = fields.Text(string="Notas")
    company_id = fields.Many2one('res.company', string='Compañia',
                                 help="Nombre de la compañia",
                                 default=lambda self:
                                 self.env.company, )
    
    producto_financiar = fields.Char('producto_financiar')
    precio_producto = fields.Integer('precio_producto')
    comercial = fields.Many2one('res.users', string='Comercial')
    
    @api.onchange('precio_producto')
    def _onchange_precio(self):
        for loan in self:
            loan.loan_amount = loan.precio_producto

    @api.depends('processing_fee')
    def _compute_disbursal_amount(self):
        """Calcular monto a pagar"""
        self.disbursal_amount = self.loan_amount - self.processing_fee
        
    def action_confirm(self):
        for prestamo in self:
            prestamo.state = 'aprobado'
            
    def action_cancel(self):
        for prestamo in self:
            prestamo.state = 'borrador'

