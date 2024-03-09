# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import Warning
from datetime import datetime, date
import logging
#from itertools import ifilter
# mapping invoice type to journal type

_logger = logging.getLogger(__name__)

TYPE2JOURNAL = {
    'out_invoice': 'sale',
    'in_invoice': 'purchase',
    'out_refund': 'sale',
    'in_refund': 'purchase',
}


class AccountMove(models.Model):
    _inherit = "account.move"

    # @api.model_create_multi
    @api.depends("company_id")
    def _default_fiscal_validated(self, company_id):
        if company_id:
            fiscal_sequence_ids = self.env["sar.authorization.code"].search(
                [('company_id', '=', company_id), ('active', '=', True)])
            if fiscal_sequence_ids:
                return True
            else:
                return False

    @api.depends('line_ids.price_subtotal', 'line_ids.price_total',
                 'currency_id', 'company_id', 'invoice_date', 'move_type', 'date')
    def _compute_price_total_vt(self):
        descuento = 0
        exento = 0
        gravado = 0
        subtotal = 0
        isv = 0
        for line in self.line_ids:
            descuento = descuento + \
                ((line.price_unit * line.quantity) * (line.discount / 100))
            subtotal = subtotal + line.price_subtotal
            for tax in line.tax_ids:  # Iterar sobre los impuestos aplicados en la línea
                isv = isv + tax.amount

                if tax.amount == 0:
                    exento = exento + line.price_subtotal
                else:
                    gravado = gravado + line.price_subtotal

        #self.descuento = descuento
        self.exento = exento
        #self.gravado = gravado

    @api.model_create_multi
    @api.depends("journal_id")
    def _default_sequence(self, journal_id):
        flag = 0
        domain = [
            ('is_fiscal_sequence', '=', True),
            ('active', '=', True),
            ('journal_id', '=', journal_id),
            '|',
            ('code', '=', self.move_type),
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

    """@api.model_create_multi
    @api.depends("sequence_ids")
    def _internal_number_sequence(self):
        for inv in self:
            if inv.move_id and inv.move_type == 'out_invoice' or inv.move_type == 'out_refund':
                if not inv.internal_number:
                    if self.fiscal_control and self.sequence_ids:
                        new_name = self.sequence_ids.with_context(
                            ir_sequence_date=inv.move_id.date).next_by_id()
                        #inv.move_id.write({'name': self.invoice_date})
                        inv.write({'internal_number': new_name})
                        self.internal_number = new_name"""

    """def button_confirm(self):
        for invoice in self:
            if invoice.type in ('out_invoice', 'out_refund'):
                sequence = self.env['ir.sequence'].next_by_id(
                    invoice.sequence_ids.id)
                invoice.internal_number = sequence
        return super(AccountMove, self).button_confirm()"""

    @api.onchange('sequence_ids')
    def _compute_internal_number(self):
        for inv in self:
            if inv.move_type == 'out_invoice' or inv.move_type == 'out_refund':
                if not inv.internal_number and inv.sequence_ids:
                    new_name = inv.sequence_ids.next_by_id()
                    inv.write({'internal_number': new_name})
                    

    fiscal_control = fields.Boolean(
        'Fiscal Control', help='If is a Fiscal Document')
    price_total_total_text = fields.Char(
        "price_total", compute='get_totalt', default='Cero')
    # Unique number of the invoice, computed automatically when the invoice is created
    internal_number = fields.Char(string='Número interno', default=False,states={'draft': [('readonly', False)]},
                                  help="Unique number of the invoice, computed automatically when the invoice is created.", copy=False)
    sequence_ids = fields.Many2one("ir.sequence", "Número Fiscal", states={'draft': [('readonly', False)]},
                                   domain="[('is_fiscal_sequence', '=',True),('active', '=', True), '|',('code','=', move_type),('code','=', 'in_refund'),('journal_id', '=', journal_id), '|', ('user_ids','=',False),('user_ids','in', user_id)]")
    x_compra_exenta = fields.Char("Orden de compra exenta", default="N/A")
    x_registro_exonerado = fields.Char("Registro exonerado", default="N/A")
    x_registro_sag = fields.Char("Registro del SAG", default="N/A")
    x_registro_diplomatico = fields.Char("N° Diplomático", default="N/A")
    x_comision = fields.Selection(
        [('1', 'SI'), ('2', 'NO')], string='Comisión Pagada', required=True, default='2')
    descuento = fields.Monetary(
        string='Descuento', store=True, readonly=True, compute='_compute_price_total_vt')
    exento = fields.Monetary(string='Exento', store=True,
                             readonly=True, compute='_compute_price_total_vt')
    gravado = fields.Monetary(
        string='Gravado', store=True, readonly=True, compute='_compute_price_total_vt')

    @api.depends('journal_id')
    def get_totalt(self):
        self.price_total_total_text = ''

        if self.currency_id:
            self.price_total_total_text = self.to_word(
                self.amount_total, self.currency_id.name)
        else:
            self.price_total_total_text = self.to_word(
                self.amount_totall, self.user_id.company_id.currency_id.name)
        return True
    
    
    def to_word(self, number, mi_moneda):
        valor = number
        number = int(number)
        centavos = int((round(valor-number, 2)) * 100)
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
            {'country': u'Colombia', 'currency': 'COP', 'singular': u'PESO COLOMBIANO',
                'plural': u'PESOS COLOMBIANOS', 'symbol': u'$'},
            {'country': u'Honduras', 'currency': 'HNL',
                'singular': u'Lempira', 'plural': u'Lempiras', 'symbol': u'L'},
            {'country': u'Estados Unidos', 'currency': 'USD',
                'singular': u'DÓLAR', 'plural': u'DÓLARES', 'symbol': u'US$'},
            {'country': u'Europa', 'currency': 'EUR',
                'singular': u'EURO', 'plural': u'EUROS', 'symbol': u'€'},
            {'country': u'México', 'currency': 'MXN', 'singular': u'PESO MEXICANO',
                'plural': u'PESOS MEXICANOS', 'symbol': u'$'},
            {'country': u'Perú', 'currency': 'PEN', 'singular': u'NUEVO SOL',
                'plural': u'NUEVOS SOLES', 'symbol': u'S/.'},
            {'country': u'Reino Unido', 'currency': 'GBP',
                'singular': u'LIBRA', 'plural': u'LIBRAS', 'symbol': u'£'}
        )
        if mi_moneda != None:
            try:
                moneda = list(
                    filter(lambda x: x['currency'] == mi_moneda, MONEDAS))
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
        if(centavos) > 0:
            converted += "con %2i/100 Centavos" % centavos
        return converted.title()

    def convert_group(self, n):
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
            {'country': u'Colombia', 'currency': 'COP', 'singular': u'PESO COLOMBIANO',
                'plural': u'PESOS COLOMBIANOS', 'symbol': u'$'},
            {'country': u'Honduras', 'currency': 'HNL',
                'singular': u'Lempira', 'plural': u'Lempiras', 'symbol': u'L'},
            {'country': u'Estados Unidos', 'currency': 'USD',
                'singular': u'DÓLAR', 'plural': u'DÓLARES', 'symbol': u'US$'},
            {'country': u'Europa', 'currency': 'EUR',
                'singular': u'EURO', 'plural': u'EUROS', 'symbol': u'€'},
            {'country': u'México', 'currency': 'MXN', 'singular': u'PESO MEXICANO',
                'plural': u'PESOS MEXICANOS', 'symbol': u'$'},
            {'country': u'Perú', 'currency': 'PEN', 'singular': u'NUEVO SOL',
                'plural': u'NUEVOS SOLES', 'symbol': u'S/.'},
            {'country': u'Reino Unido', 'currency': 'GBP',
                'singular': u'LIBRA', 'plural': u'LIBRAS', 'symbol': u'£'}
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
                output += '%sY %s' % (DECENAS[int(n[1]) - 2],
                                      UNIDADES[int(n[2])])
            else:
                output += '%s%s' % (DECENAS[int(n[1]) - 2],
                                    UNIDADES[int(n[2])])

        return output

    def addComa(self, snum):
        s = snum
        i = s.index('.')  # Se busca la posición del punto decimal
        while i > 3:
            i = i - 3
            s = s[:i] + ',' + s[i:]
        return s

    """def create(self, vals):
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
                    ('code', '=', vals.get("move_type"))]
                sequence = self.env["ir.sequence"].search(domain)
                for count in sequence:
                    flag += 1
                if flag == 1:
                    vals["sequence_ids"] = self.env['ir.sequence'].search(domain).id
        invoice = super(AccountMove, self).create(vals)
        return invoice"""

    @api.onchange('journal_id')
    def _onchange_journal_inh(self):
        self.fiscal_control = self._default_fiscal_validated(
            self.company_id.id)
        self.sequence_ids = self._default_sequence(self.journal_id.id)

    #@api.model_create_multi
    def action_date_assign(self):
        res = super(AccountMove, self).action_date_assign()
        if self.state:
            if not self.invoice_date:
                self.invoice_date = date.today()
            if self.sequence_ids:
                if not self.invoice_date:
                    raise Warning(
                        _('No existe fecha establecida para esta factura'))
                if self.invoice_date > self.sequence_ids.expiration_date:
                    raise Warning(_('The Expiration Date for this fiscal sequence is %s ') % (
                        self.sequence_ids.expiration_date))
                if self.sequence_ids.vitt_number_next_actual > self.sequence_ids.max_value:
                    raise Warning(
                        _('The range of sequence numbers is finished'))
        return res

    @api.onchange("company_id")
    def onchange_company_id(self):
        flag = 0
        fiscal_sequence_ids = self.env["sar.authorization.code"].search(
            [('company_id', '=', self.company_id.id), ('active', '=', True)])
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

    #@api.model
    def action_move_create(self):
        res = super(AccountMove, self).action_move_create()
        for inv in self:
            if inv.move_id and inv.move_type == 'out_invoice' or inv.move_type == 'out_refund':
                if not inv.internal_number:
                    if self.fiscal_control and self.sequence_ids:
                        new_name = self.sequence_ids.next_by_id()
                        inv.write({'internal_number': new_name})
                        print("Este es un mensaje de depuración")
                else:
                    inv.move_id.write({'name': inv.move_id.date})
        return res

    @api.onchange('cash_rounding_id', 'invoice_line_ids', 'tax_line_ids', 'price_total_total')
    def _onchange_cash_rounding_vt(self):
        descuento = 0
        exento = 0
        gravado = 0
        for line in self.invoice_line_ids:
            descuento = descuento + \
                ((line.price_unit * line.quantity) * (line.discount / 100))
            if line.tax_ids.amount == 0:
                exento = exento + line.price_subtotal
            else:
                gravado = gravado + line.price_subtotal

        self.descuento = descuento
        self.exento = exento
        self.gravado = gravado
