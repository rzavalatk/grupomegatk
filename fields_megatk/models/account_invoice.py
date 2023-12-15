# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


#Campo de comisión pagada en las facturas
class Account_Move(models.Model):
    _inherit = "account.move"

    x_comision = fields.Selection([('1','SI'),('2','NO')], string='Comisión Pagada', required=True, default='2')
    invoice_payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms',
        check_company=True,
        readonly=False, required=False,)
    
    #mostrar boton en factura de borrados
    def go_draft(self):
        self.write({
            'state': 'draft'
        })
    
    @api.onchange('date_due')
    def update_move_lines(self):
        for move in self:
            for line in move.line_ids:
                line.date_maturity = move.date_due

    
class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    x_user_id = fields.Many2one('res.users', compute='_compute_responsable_cotizacion', string='Responsable')
    obj_padre = fields.Many2one(related="move_id.invoice_user_id", string="ResponsableTem")
    x_series = fields.Text("Series")
    fecha_vencimiento_report = fields.Char(string='referencia de factura/Fecha de vencimiento (Reporte)', compute='_compute_fecha_vencimiento', )
    terminos_pago_report = fields.Char(string='referencia de factura/Terminos pago (Reporte)', compute='_compute_terminos_pago', )
    referencia_pago_report = fields.Char(string='referencia de factura/pago (Reporte)', compute='_compute_ref_pago', )
    fecha_pago_report = fields.Char(string='referencia de factura/fecha de pago (Reporte)', compute='_compute_ref_pago', )
    nombre_empresa_report = fields.Char(string='referencia de factura/Empresa (Reporte)', compute='_compute_ref_empresa', )
    numero_interno_report = fields.Char(string='referencia de factura/Numero Interno (Reporte)', compute='_compute_ref_empresa', )
    
    @api.depends('move_id.invoice_origin')
    def _compute_responsable_cotizacion(self):
        for line in self:
            if line.move_id.invoice_origin and line.move_id.move_type == "out_invoice":
                cotizacion = self.env['sale.order'].search([('name', '=', line.move_id.invoice_origin)], limit=1)
                line.x_user_id = cotizacion.user_id if cotizacion.user_id else False
                """for lines in cotizacion.order_line:
                    line.x_user_id = lines.x_user_id if line.product_id.id == cotizacion.order_line.product_id.id else False"""
            else:
                line.x_user_id = self.env.user
                
    @api.depends('move_id.invoice_date_due')
    def _compute_fecha_vencimiento(self):
        for line in self:
            line.fecha_vencimiento_report = line.move_id.invoice_date_due
    
    @api.depends('move_id.invoice_payment_term_id')
    def _compute_terminos_pago(self):
        for line in self:
            line.terminos_pago_report = line.move_id.invoice_payment_term_id.display_name
    
    @api.depends('move_id.invoice_payments_widget')
    def _compute_ref_pago(self):
        
        for line in self:
            payments_ref = self.env['account.payment'].search([('ref', '=', line.move_id.name)], limit=1)
            line.referencia_pago_report = payments_ref.name
            line.fecha_pago_report = payments_ref.date
            
    @api.depends('move_id.partner_id')
    def _compute_ref_empresa(self):
        for line in self:
            line.nombre_empresa_report = line.move_id.partner_id.name
            line.numero_interno_report = line.move_id.internal_number
    
                
    '''@api.depends('move_id.invoice_origin')
    def _compute_serie(self):
        for line in self:
            if line.move_id.invoice_origin:
                cotizacion = self.env['sale.order'].search([('name', '=', line.move_id.invoice_origin)], limit=1)
                line.x_series = cotizacion.order_line.x_series if cotizacion.order_line.x_series else False
                """for lines in cotizacion.order_line:
                    line.x_series = lines.x_series if line.product_id.id == cotizacion.order_line.product_id.id else False"""
            else:
                line.x_series = "d"'''
    
    
    
    #date_maturity = fields.Date(string='Due Date', index=True, tracking=True, related='move_id.date_due',
    #    help="This field is used for payable and receivable journal entries. You can put the limit date for the payment of this line.")

    @api.onchange('product_id')
    def product_id_change1(self):
        self.x_user_id = self.obj_padre.id
        self.x_series = self.product_id.name

   