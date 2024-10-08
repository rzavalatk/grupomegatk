# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
import math

_logger = logging.getLogger(__name__)


#Campo de comisión pagada en las facturas
class Account_Move(models.Model):
    _inherit = "account.move"

    def _compute_contacto(self):
        cotizacion = self.env['sale.order'].search([('name', '=', self.invoice_origin)], limit=1)
        self.x_contacto = cotizacion.x_contacto
        self.sorteo_id = cotizacion.sorteo_id.id
        self.x_student = cotizacion.x_student
        
    x_comision = fields.Selection([('1','SI'),('2','NO')], string='Comisión Pagada', required=True, default='2')
    invoice_payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms',
        check_company=True,
        readonly=False, required=False,)
    
    sorteo_id = fields.Many2one('sorteo.sorteo', string='Sorteo')
    x_student = fields.Boolean(string='Es Estudiante', default=False)
    x_contacto = fields.Char('Contacto de referencia', compute='_compute_contacto')
    n_tickets_acum = fields.Integer('Tickets')
    mostrar_direccion = fields.Boolean(string='¿Mostrar Dirección de contacto?', default=False)
    certificado_deposito = fields.Boolean(string='¿Certificado de Deposito?', default=False)
    
    
    """departamentos = fields.Many2one('departamentos.departamentos', string='Departamentos')
    ciudad = fields.Many2one('departamentos.ciudad', string='Ciudad', domain="[('departamento.id', '=', departamentos.id)]")
    """
    
    @api.model_create_multi
    def create(self, vals_list):
        """Condicion que busca si la factura es al credito, si es asi busca el cliente si tiene numero y dirección, en caso de que no lo tenga no crea nada."""

        company_id = self.env.user.company_id.id
        for vals in vals_list:
            term_id = vals.get('invoice_payment_term_id')
            if term_id:
                term = self.env['account.payment.term'].browse(term_id)
                _logger.warning(term.line_ids)
                _logger.warning(term.line_ids.days)
                if term.line_ids and any(line.days > 0 for line in term.line_ids):
                    partner = self.env['res.partner'].browse(vals.get('partner_id'))
                    if partner:
                        if partner.mobile or partner.phone:
                            if partner.street and partner.city:
                                return super().create(vals_list)
                            else:
                                raise UserError(_("ERROR: Contacto no tiene el campo calle o ciudad de la dirección, agregar antes de crear facturas al credito."))
                        else:
                            raise UserError(_("ERROR: Contacto no tiene número de teléfono o móvil, agregar alguno de los dos antes de crear facturas al credito."))
        return super().create(vals_list)
        
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
                
    def action_post(self):
        res = super(Account_Move, self).action_post()
        
        self.generate_tickets()
        return res
    
    def enviar_email_qr(self):
        mail_template = self.env.ref('fields_megatk.mail_template_invoice_post')
        
        
        
        for invoice in self:
            if invoice.partner_id.email:
                qr_img_base64 = invoice.qr_image.decode('utf-8') if invoice.qr_image else ""
                email_values = {}

                if invoice.company_id.id == 8:
                    email_values = {
                        'email_from': 'megatk.no_reply@megatk.com',
                        #'email_to': 'dzuniga@megatk.com',
                        'email_to': invoice.partner_id.email,
                        #'email_cc': invoice.invoice_user_id.login
                    }
                elif invoice.company_id.id == 9:
                    email_values = {
                        'email_from': 'meditek.no_reply@megatk.com',
                        #'email_to': 'dzuniga@megatk.com',
                        'email_to': invoice.partner_id.email,
                        #'email_cc': invoice.invoice_user_id.login
                    }
                    
                email_context = {
                    'qr_image_base64': qr_img_base64
                }

                mail_template.sudo().with_context(email_context).send_mail(invoice.id, email_values=email_values, force_send=True)

    def generate_tickets(self):
        tickets = 0
        flag = False
        dia_festivo = False
        
        #if self.sorteo_id and self.sorteo_id.compañia.id == self.company_id.id:
        if self.sorteo_id:
            
            if self.sorteo_id.fecha_inicio <= self.invoice_date <= self.sorteo_id.fecha_final:
                
                if self.amount_total >= 1000:
                    #({'ticket': "ticket x1"})
                    
                    tickets = math.floor(self.amount_total / 1000)

                    
                    for fechas in self.sorteo_id.fechas_festivas:
                        if self.invoice_date == fechas.fecha:
                            #({'ticket': "ticket x2"})
                            tickets = tickets * 2
                            flag = True
                            dia_festivo = True
                            break
                    
                    #_logger.warning("Generando ticket 1")

                    for move_line in self.line_ids:
                        if not flag:
                            for marca in self.sorteo_id.marcas:
                                if not flag:
                                    if move_line.product_id.marca_id.name:
                                        if marca.marcas.name:
                                            if move_line.product_id.marca_id.name == marca.marcas.name:
                                                
                                                if marca.fecha_inicial <= self.invoice_date <= marca.fecha_final:
                                                    #({'ticket': "ticket x2"})
                                                    tickets = tickets* 2
                                                    flag = True
                                                    break
                                
                            for producto in self.sorteo_id.productos:
                                if not flag:
                                    if move_line.product_id.name == producto.product.name:
                                        if producto.fecha_inicial <= self.invoice_date <= producto.fecha_final:
                                            tickets = tickets* 2
                                            flag = True
                                            break
                                    
                    if self.x_student:
                        #({'ticket': "ticket 3"})
                        tickets = tickets * 3

                # Crear los registros de tickets
                for ticket_data in range(tickets):
                    # Cambiar 'move_line_id' por 'name' o algún otro campo significativo
                    self.env['sorteo.ticket'].create({
                        'move_id': self.id,
                        'name': self.sorteo_id.sequence_id.prefix + '%%0%sd' % self.sorteo_id.sequence_id.padding % self.sorteo_id.sequence_id.number_next_actual,
                        'sorteo': self.sorteo_id.id,
                        'customer_id': self.partner_id.id,
                        'fecha': self.invoice_date,
                    })
                    
                    # Incrementa el número de la secuencia para el próximo ticket
                    self.sorteo_id.sequence_id.sudo().write({'number_next_actual': self.sorteo_id.sequence_id.number_next_actual + 1})
        
        tickets = self.env['sorteo.ticket'].search([('customer_id', '=', self.partner_id.id)],)
        self.n_tickets_acum = len(tickets)
        _logger.warning(tickets)   
        
    
class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    x_user_id = fields.Many2one('res.users',  string='Responsable')
    obj_padre = fields.Many2one(related="move_id.invoice_user_id", string="ResponsableTem")
    x_series = fields.Text("Series")
    tax_editable = fields.Boolean('tax e.')
    
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
    
    """@api.depends('move_id.invoice_payments_widget')
    def _compute_ref_pago(self):
        
        for line in self:
            payments_ref = self.env['account.payment'].search([('ref', '=', line.move_id.name)], limit=1)
            line.referencia_pago_report = payments_ref.name
            line.fecha_pago_report = payments_ref.date"""
            
    @api.depends('move_id.invoice_payments_widget')
    def _compute_ref_pago(self):
        # Obtener todas las referencias y fechas de pago únicas en una sola búsqueda
        payments_refs = self.env['account.payment'].search([
            ('ref', 'in', self.mapped('move_id.name'))
        ])

        # Crear un diccionario de referencias de pago y fechas de pago para facilitar el acceso
        payments_data = {payment.ref: (payment.name, payment.date) for payment in payments_refs}

        for line in self:
            # Obtener la referencia de pago y la fecha de pago desde el diccionario
            payment_info = payments_data.get(line.move_id.name)
            
            # Asignar valores a los campos calculados
            line.referencia_pago_report = payment_info[0] if payment_info else False
            line.fecha_pago_report = payment_info[1] if payment_info else False

            
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

   
