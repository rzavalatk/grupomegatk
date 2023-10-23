# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import Warning
from datetime import datetime, date
#from itertools import ifilter
# mapping invoice type to journal type
TYPE2JOURNAL = {
    'out_invoice': 'sale',
    'in_invoice': 'purchase',
    'out_refund': 'sale',
    'in_refund': 'purchase',
}


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    @api.depends("company_id")
    def _default_fiscal_validated(self, company_id):
        if company_id:
            fiscal_sequence_ids = self.env["sar.authorization.code"].search([('company_id', '=', company_id), ('active', '=', True)])
            if fiscal_sequence_ids:
                return True
            else:
                return False

    @api.one
    @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount', 'tax_line_ids.amount_rounding',
                 'currency_id', 'company_id', 'date_invoice', 'type', 'date')
    def _compute_amount_vt(self):
        descuento = 0
        exento = 0
        gravado = 0
        subtotal = 0
        isv = 0
        for line in self.invoice_line_ids:
            descuento = descuento + ((line.price_unit * line.quantity) * (line.discount / 100))
            subtotal = subtotal + line.price_subtotal
            isv = isv + line.price_tax
            if line.price_tax == 0:
                exento = exento + line.price_subtotal
            else:
                gravado = gravado + line.price_subtotal

        self.descuento = descuento
        self.exento = exento
        self.gravado = gravado

    @api.multi
    @api.depends("journal_id")
    def _default_sequence(self, journal_id):
        flag = 0
        domain = [
            ('is_fiscal_sequence', '=', True),
            ('active', '=', True),
            ('journal_id', '=', journal_id),
            '|',
            ('code', '=', self.type),
            ('code', '=', 'in_refund'),
            '|',
            ('user_ids', 'in', self.user_id.id),
            ('user_ids', 'in', False),
        ]
        sequence = self.env['ir.sequence'].search(domain)
        for count in sequence:
            flag += 1
        if flag == 1:
            return self.env['ir.sequence'].search(domain)

    fiscal_control = fields.Boolean('Fiscal Control', help='If is a Fiscal Document')
    amount_total_text = fields.Char("Amount Total", compute = 'get_totalt', default='Cero')
    # Unique number of the invoice, computed automatically when the invoice is created
    internal_number = fields.Char(string='Número interno', default=False, help="Unique number of the invoice, computed automatically when the invoice is created.", copy=False)
    sequence_ids = fields.Many2one("ir.sequence", "Número Fiscal", states={'draft': [('readonly', False)]},
                                   domain="[('is_fiscal_sequence', '=',True),('active', '=', True), '|',('code','=', type),('code','=', 'in_refund'),('journal_id', '=', journal_id), '|', ('user_ids','=',False),('user_ids','in', user_id)]")
    x_compra_exenta = fields.Char("Orden de compra exenta", default="N/A");
    x_registro_exonerado = fields.Char("Registro exonerado", default="N/A");
    x_registro_sag = fields.Char("Registro del SAG", default="N/A");
    x_comision = fields.Selection([('1','SI'),('2','NO')], string='Comisión Pagada', required=True, default='2')
    descuento = fields.Monetary(string='Descuento', store=True, readonly=True, compute='_compute_amount_vt')
    exento = fields.Monetary(string='Exento', store=True, readonly=True, compute='_compute_amount_vt')
    gravado = fields.Monetary(string='Gravado', store=True, readonly=True, compute='_compute_amount_vt')
    
    @api.one
    @api.depends('journal_id')
    def get_totalt(self):
        self.amount_total_text=''

        if self.currency_id:
            self.amount_total_text=self.to_word(self.amount_total,self.currency_id.name)
        else:
            self.amount_total_text =self.to_word(self.amount_total,self.user_id.company_id.currency_id.name)
        return True

    def to_word(self,number, mi_moneda):
        valor = number
        number = int(number)
        centavos = int((round(valor-number,2)) * 100)
        UNIDADES = (
            '',
            'UN ',
            'DOS ',
            'TRES ',
            'CUATRO ',
            'CINCO ',
            'SEIS ',
            'SIETE ',
            'OCHO ',
            'NUEVE ',
            'DIEZ ',
            'ONCE ',
            'DOCE ',
            'TRECE ',
            'CATORCE ',
            'QUINCE ',
            'DIECISEIS ',
            'DIECISIETE ',
            'DIECIOCHO ',
            'DIECINUEVE ',
            'VEINTE '
        )

        DECENAS = (
            'VENTI',
            'TREINTA ',
            'CUARENTA ',
            'CINCUENTA ',
            'SESENTA ',
            'SETENTA ',
            'OCHENTA ',
            'NOVENTA ',
            'CIEN ')

        CENTENAS = (
            'CIENTO ',
            'DOSCIENTOS ',
            'TRESCIENTOS ',
            'CUATROCIENTOS ',
            'QUINIENTOS ',
            'SEISCIENTOS ',
            'SETECIENTOS ',
            'OCHOCIENTOS ',
            'NOVECIENTOS '
        )
        MONEDAS = (
            {'country': u'Colombia', 'currency': 'COP', 'singular': u'PESO COLOMBIANO', 'plural': u'PESOS COLOMBIANOS', 'symbol': u'$'},
            {'country': u'Honduras', 'currency': 'HNL', 'singular': u'Lempira', 'plural': u'Lempiras', 'symbol': u'L'},
            {'country': u'Estados Unidos', 'currency': 'USD', 'singular': u'DÓLAR', 'plural': u'DÓLARES', 'symbol': u'US$'},
            {'country': u'Europa', 'currency': 'EUR', 'singular': u'EURO', 'plural': u'EUROS', 'symbol': u'€'},
            {'country': u'México', 'currency': 'MXN', 'singular': u'PESO MEXICANO', 'plural': u'PESOS MEXICANOS', 'symbol': u'$'},
            {'country': u'Perú', 'currency': 'PEN', 'singular': u'NUEVO SOL', 'plural': u'NUEVOS SOLES', 'symbol': u'S/.'},
            {'country': u'Reino Unido', 'currency': 'GBP', 'singular': u'LIBRA', 'plural': u'LIBRAS', 'symbol': u'£'}
            )
        if mi_moneda != None:
        	try:
        		moneda = list(filter(lambda x: x['currency'] == mi_moneda, MONEDAS))
        		moneda = moneda[0]
        		if number < 2:
        			moneda = moneda['singular']
        		else:
        			moneda = moneda['plural']
        	except:
        		return "Tipo de moneda inválida"
        else:
        	moneda = ""
		        
        converted = ''
        if not (0 < number < 999999999):
            return 'No es posible convertir el numero a letras'

        number_str = str(number).zfill(9)
        millones = number_str[:3]
        miles = number_str[3:6]
        cientos = number_str[6:]

        if(millones):
            if(millones == '001'):
                converted += 'UN MILLON '
            elif(int(millones) > 0):
                converted += '%sMILLONES ' % self.convert_group(millones)

        if(miles):
            if(miles == '001'):
                converted += 'MIL '
            elif(int(miles) > 0):
                converted += '%sMIL ' % self.convert_group(miles)

        if(cientos):
            if(cientos == '001'):
                converted += 'UN '
            elif(int(cientos) > 0):
                converted += '%s ' % self.convert_group(cientos)
        converted += moneda + ' '
        if(centavos)>0:
            converted+= "con %2i/100 Centavos"%centavos
        return converted.title()

    def convert_group(self,n):
        UNIDADES = (
            '',
            'UN ',
            'DOS ',
            'TRES ',
            'CUATRO ',
            'CINCO ',
            'SEIS ',
            'SIETE ',
            'OCHO ',
            'NUEVE ',
            'DIEZ ',
            'ONCE ',
            'DOCE ',
            'TRECE ',
            'CATORCE ',
            'QUINCE ',
            'DIECISEIS ',
            'DIECISIETE ',
            'DIECIOCHO ',
            'DIECINUEVE ',
            'VEINTE '
        )
        DECENAS = (
            'VEINTI',
            'TREINTA ',
            'CUARENTA ',
            'CINCUENTA ',
            'SESENTA ',
            'SETENTA ',
            'OCHENTA ',
            'NOVENTA ',
            'CIEN '
        )

        CENTENAS = (
            'CIENTO ',
            'DOSCIENTOS ',
            'TRESCIENTOS ',
            'CUATROCIENTOS ',
            'QUINIENTOS ',
            'SEISCIENTOS ',
            'SETECIENTOS ',
            'OCHOCIENTOS ',
            'NOVECIENTOS '
        )
        MONEDAS = (
            {'country': u'Colombia', 'currency': 'COP', 'singular': u'PESO COLOMBIANO', 'plural': u'PESOS COLOMBIANOS', 'symbol': u'$'},
            {'country': u'Honduras', 'currency': 'HNL', 'singular': u'Lempira', 'plural': u'Lempiras', 'symbol': u'L'},
            {'country': u'Estados Unidos', 'currency': 'USD', 'singular': u'DÓLAR', 'plural': u'DÓLARES', 'symbol': u'US$'},
            {'country': u'Europa', 'currency': 'EUR', 'singular': u'EURO', 'plural': u'EUROS', 'symbol': u'€'},
            {'country': u'México', 'currency': 'MXN', 'singular': u'PESO MEXICANO', 'plural': u'PESOS MEXICANOS', 'symbol': u'$'},
            {'country': u'Perú', 'currency': 'PEN', 'singular': u'NUEVO SOL', 'plural': u'NUEVOS SOLES', 'symbol': u'S/.'},
            {'country': u'Reino Unido', 'currency': 'GBP', 'singular': u'LIBRA', 'plural': u'LIBRAS', 'symbol': u'£'}
        )
        output = ''

        if(n == '100'):
            output = "CIEN "
        elif(n[0] != '0'):
            output = CENTENAS[int(n[0]) - 1]

        k = int(n[1:])
        if(k <= 20):
            output += UNIDADES[k]
        else:
            if((k > 30) & (n[2] != '0')):
                output += '%sY %s' % (DECENAS[int(n[1]) - 2], UNIDADES[int(n[2])])
            else:
                output += '%s%s' % (DECENAS[int(n[1]) - 2], UNIDADES[int(n[2])])

        return output

    def addComa(self, snum ):
        s = snum;
        i = s.index('.') # Se busca la posición del punto decimal
        while i > 3:
            i = i - 3
            s = s[:i] +  ',' + s[i:]
        return s

    @api.model
    def create(self, vals):
        if not vals.get("sequence_ids"):
            vals["fiscal_control"] = 0
            vals["sequence_ids"] = 0
            if vals.get("company_id"):
                vals["fiscal_control"] = self._default_fiscal_validated(vals.get("company_id"))
            else:
                company_id = self.env["res.users"].browse(vals.get("user_id")).company_id.id
                vals["fiscal_control"] = self._default_fiscal_validated(company_id)

            if vals.get("journal_id") and not vals["fiscal_control"]:
                company_id = self.env["account.journal"].browse(vals.get("journal_id")).company_id.id
                vals["fiscal_control"] = self._default_fiscal_validated(company_id)

            if vals["fiscal_control"] and vals.get("journal_id"):
                flag = 0
                domain = [
                    ('is_fiscal_sequence', '=', True),
                    ('active', '=', True),
                    ('journal_id', '=', vals.get("journal_id")),
                    ('code', '=', vals.get("type"))]
                sequence = self.env["ir.sequence"].search(domain)
                for count in sequence:
                    flag += 1
                if flag == 1:
                    vals["sequence_ids"] = self.env['ir.sequence'].search(domain).id
        invoice = super(AccountInvoice, self).create(vals)
        return invoice
    @api.onchange('journal_id')
    def _onchange_journal_inh(self):
        self.fiscal_control = self._default_fiscal_validated(self.company_id.id)
        self.sequence_ids = self._default_sequence(self.journal_id.id)

    @api.multi
    def action_date_assign(self):
        res = super(AccountInvoice, self).action_date_assign()
        if self.state:
            if not self.date_invoice:
                self.date_invoice=date.today()
            if self.sequence_ids:
                if not self.date_invoice:
                    raise Warning(_('No existe fecha establecida para esta factura'))
                if self.date_invoice > self.sequence_ids.expiration_date:
                    raise Warning(_('The Expiration Date for this fiscal sequence is %s ') % (self.sequence_ids.expiration_date))
                if self.sequence_ids.vitt_number_next_actual > self.sequence_ids.max_value:
                    raise Warning(_('The range of sequence numbers is finished'))
        return res

    @api.onchange("company_id")
    def onchange_company_id(self):
        flag = 0
        fiscal_sequence_ids = self.env["sar.authorization.code"].search([('company_id', '=', self.company_id.id), ('active', '=', True)])
        company = self.env["res.company"].search([('id', '>', 0)])
        for count in company:
            flag += 1
        if fiscal_sequence_ids:
            self.fiscal_control = True
        else:
            self.fiscal_control = False
        # TODO: Revisar este tema de onchange por lo momentos se dejara por defecto como viene
        # if flag > 1:
        #    domain = [
        #        ('type', '=', self.type),
        #        ('company_id', '=', self.company_id.id),
        #    ]
        #    self.journal_id = self.env['account.journal'].search(domain).id

    @api.multi
    def action_move_create(self):
        res = super(AccountInvoice, self).action_move_create()
        for inv in self:
            if inv.move_id and inv.type == 'out_invoice' or inv.type == 'out_refund':
                if not inv.internal_number:
                    if self.fiscal_control and self.sequence_ids:
                        new_name = self.sequence_ids.with_context(ir_sequence_date=inv.move_id.date).next_by_id()
                        inv.move_id.write({'name': new_name})
                        inv.write({'internal_number': new_name})
                else:
                    inv.move_id.write({'name': inv.internal_number})
        return res

    @api.onchange('cash_rounding_id', 'invoice_line_ids', 'tax_line_ids', 'amount_total')
    def _onchange_cash_rounding_vt(self):
        descuento = 0
        exento = 0
        gravado = 0
        for line in self.invoice_line_ids:
            descuento = descuento + ((line.price_unit * line.quantity) * (line.discount / 100))
            if line.price_tax == 0:
                exento = exento + line.price_subtotal
            else:
                gravado = gravado + line.price_subtotal

        self.descuento = descuento
        self.exento = exento
        self.gravado = gravado

