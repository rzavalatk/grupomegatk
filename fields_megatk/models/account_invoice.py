# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from collections import defaultdict
import logging
import math
import time

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
    @api.onchange('invoice_user_id')
    def _onchange_vendedor(self):
        if self.invoice_user_id.id == 59:
            self.team_id = self.env['crm.team'].search([('id', '=', 47)], limit=1)
        else:
            pass
        
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
        
    @api.depends('amount_residual', 'move_type', 'state', 'company_id')
    def _compute_payment_state(self):
        stored_ids = tuple(self.ids)
        if stored_ids:
            self.env['account.partial.reconcile'].flush_model()
            self.env['account.payment'].flush_model(['is_matched'])

            queries = []
            for source_field, counterpart_field in (('debit', 'credit'), ('credit', 'debit')):
                queries.append(f'''
                    SELECT
                        source_line.id AS source_line_id,
                        source_line.move_id AS source_move_id,
                        account.account_type AS source_line_account_type,
                        ARRAY_AGG(counterpart_move.move_type) AS counterpart_move_types,
                        COALESCE(BOOL_AND(COALESCE(pay.is_matched, FALSE))
                            FILTER (WHERE counterpart_move.payment_id IS NOT NULL), TRUE) AS all_payments_matched,
                        BOOL_OR(COALESCE(BOOL(pay.id), FALSE)) as has_payment,
                        BOOL_OR(COALESCE(BOOL(counterpart_move.statement_line_id), FALSE)) as has_st_line
                    FROM account_partial_reconcile part
                    JOIN account_move_line source_line ON source_line.id = part.{source_field}_move_id
                    JOIN account_account account ON account.id = source_line.account_id
                    JOIN account_move_line counterpart_line ON counterpart_line.id = part.{counterpart_field}_move_id
                    JOIN account_move counterpart_move ON counterpart_move.id = counterpart_line.move_id
                    LEFT JOIN account_payment pay ON pay.id = counterpart_move.payment_id
                    WHERE source_line.move_id IN %s AND counterpart_line.move_id != source_line.move_id
                    GROUP BY source_line.id, source_line.move_id, account.account_type
                ''')

            self._cr.execute(' UNION ALL '.join(queries), [stored_ids, stored_ids])

            payment_data = defaultdict(lambda: [])
            for row in self._cr.dictfetchall():
                payment_data[row['source_move_id']].append(row)
        else:
            payment_data = {}

        for invoice in self:
            if invoice.payment_state == 'invoicing_legacy':
                continue

            currencies = invoice._get_lines_onchange_currency().currency_id
            currency = currencies if len(currencies) == 1 else invoice.company_id.currency_id
            reconciliation_vals = payment_data.get(invoice.id, [])
            payment_state_matters = invoice.is_invoice(True)

            if payment_state_matters:
                reconciliation_vals = [x for x in reconciliation_vals if x['source_line_account_type'] in ('asset_receivable', 'liability_payable')]

            new_pmt_state = 'not_paid'
            if invoice.state == 'posted':

                if payment_state_matters:
                    if currency.is_zero(invoice.amount_residual):
                        if any(x['has_payment'] or x['has_st_line'] for x in reconciliation_vals):
                            if all(x['all_payments_matched'] for x in reconciliation_vals):
                                new_pmt_state = 'paid'
                            else:
                                new_pmt_state = invoice._get_invoice_in_payment_state()
                        else:
                            new_pmt_state = 'paid'

                            reverse_move_types = set()
                            for x in reconciliation_vals:
                                for move_type in x['counterpart_move_types']:
                                    reverse_move_types.add(move_type)

                            in_reverse = (invoice.move_type in ('in_invoice', 'in_receipt')
                                          and (reverse_move_types == {'in_refund'} or reverse_move_types == {'in_refund', 'entry'}))
                            out_reverse = (invoice.move_type in ('out_invoice', 'out_receipt')
                                           and (reverse_move_types == {'out_refund'} or reverse_move_types == {'out_refund', 'entry'}))
                            misc_reverse = (invoice.move_type in ('entry', 'out_refund', 'in_refund')
                                            and reverse_move_types == {'entry'})
                            if in_reverse or out_reverse or misc_reverse:
                                new_pmt_state = 'reversed'

                    elif reconciliation_vals:
                        new_pmt_state = 'partial'

            invoice.payment_state = new_pmt_state

            # --- Agregar lógica adicional cuando el estado sea 'paid' ---
            if new_pmt_state == 'paid':
                for move in self:
                    if move.payment_reference:  # Si el campo payment_reference tiene un valor
                        _logger.warning("Entra al if de payment_reference " + move.payment_reference)
                        # Buscar el pago relacionado por su referencia
                        time.sleep(1)
                        payment = self.env['account.payment'].search([('ref', '=', move.payment_reference)], limit=1)
                        _logger.warning(payment)
                        if payment and payment.journal_id.id == 1030:  # Verifica si el diario del pago es el ID 1030
                            _logger.warning("Entra al if del diario")
                            for line in move.invoice_line_ids:
                                _logger.warning(f"Precio ID: {line.precio_id.id}")
                                if line.precio_id.name.id == 1:  # Verifica si el precio_id es igual a 1
                                    _logger.warning("Condición cumplida, cambiando el comercial.")
                                    # Cambia el comercial al ID 78 usando write
                                    move.write({'invoice_user_id': 60})
                                    break  # Sal del bucle después de aplicar el cambi
                                
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
        credit_term =self.env['account.payment.term'].search([('id', '=', self.invoice_payment_term_id.id)])
        if credit_term.credit:
            _logger.warning("Entra al action post " + str(self.move_type))
            if self.move_type in ['out_invoice', 'in_invoice']:
                if not self.env.user.has_group('fields_megatk.factura_credito_manager'):
                    raise UserError("No tienes permisos para validar esta factura.")
    
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
        
    def copy(self, default=None):
        self.ensure_one()
        allowed_company_name = "INVERSIONES LENKA"  # Cambia esto por el nombre de tu compañía
        if self.move_type != 'in_invoice':
            if self.company_id.name != allowed_company_name:
                raise UserError(_("No se permite duplicar facturas para esta compañía."))

        return super(Account_Move, self).copy(default)
        
    
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
    
    def create(self, vals_list):
        for vals in vals_list:
            # ✅ Ignorar cuentas que no sean 8672 o 8670
            if vals.get('account_id') not in [8672, 8670]:
                _logger.warning(f"Ignorado account_id: {vals.get('account_id')}")
                continue
            move = self.env['account.move'].browse(vals['move_id'])
            if move.move_type == 'entry':
                if move.journal_id.id == 1088:  # Caso de Meditek
                    if vals.get('account_id') == 8672:
                        vals['account_id'] = 2680
                elif move.journal_id.id == 1087:
                    if vals.get('account_id') == 8670:
                        vals['account_id'] = 2676
        return super(AccountMoveLine, self).create(vals_list)
    
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

   
