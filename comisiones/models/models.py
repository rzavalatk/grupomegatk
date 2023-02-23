# -*- coding: utf-8 -*-

from odoo import models, api, fields
from datetime import datetime as dt
import datetime
import pytz


class Usuarios(models.Model):
    _inherit = "res.users"

    comision_id = fields.Many2one("account.comisiones")
    
class Facturas(models.Model):
    _inherit = "account.invoice"

    comision_id = fields.Many2one("account.comisiones")


class ComisionesLine(models.Model):
    _name = "account.comisiones.line"
    _order = "user_id asc"
    vencimiento = [{
        'from': 0,
        'to': 14,
        'pay': 100
    }, {
        'from': 15,
        'to': 44,
        'pay': 50
    },
        {
        'from': 45,
        'to': 74,
        'pay': 10
    },
        {
        'from': 75,
        'to': 100,
        'pay': 0
    }]
    
    @api.one
    def _pocentaje_pago(self):
        for item in self.vencimiento:
            if self.antiguedad_pago >= item['from'] and self.antiguedad_pago <= item['to']:
                self.pocentaje_pago = item['pay']

             
    @api.one
    def _comision_pagar(self):
        self.comision_pagar = self.forma_comision * (self.pocentaje_pago/100)
        

    comision_id = fields.Many2one("account.comisiones")
    user_id = fields.Many2one("res.users", "Comercial")
    invoice_line_id = fields.Many2one(
        "account.invoice.line", string="Linea de Factura")
    currency_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.user.company_id.currency_id.id)
    posible_comision = fields.Monetary("Comision Posible")
    forma_comision = fields.Monetary("Com Forma Pago")
    comision_pagar = fields.Monetary("Comision a Pagar",compute=_comision_pagar)
    antiguedad_pago = fields.Integer("Antigüedad del pago")
    pocentaje_pago = fields.Float("Pago %",compute=_pocentaje_pago)
    pocentaje_comision = fields.Float("%")


class Comisiones(models.Model):
    _name = "account.comisiones"
    _order = "create_date desc"
    

    def _existe_key(self, list, key):
        try:
            list[key]
            return True
        except:
            return False

    @api.one
    def _name_(self):
        try:
            if len(self.users_ids) > 1:
                    self.name = self.company_id.name + " - " + self.type + " // " + str(self.date)
            else:
                user_id = {}
                for item in self.users_ids:
                    user_id = item

                self.name = user_id.name + " // " + str(self.date)
        except :
            self.name = "Error: verifique 'Compañia', 'Tipo', 'Fecha' o 'Usuarios'"

    name = fields.Char("Comisión", compute=_name_)
    company_id = fields.Many2one(
        "res.company", "Compañia", default=lambda self: self.env.user.company_id.id)
    users_ids = fields.Many2many("res.users", "comision_id", string="Usuarios")
    comision_line = fields.One2many(
        "account.comisiones.line", "comision_id", string="Lineas de comision")
    facturas_ids = fields.One2many(
        "account.invoice", "comision_id", string="Facturas")
    date = fields.Date("Hasta la Fecha", default=lambda self: dt.now(
        pytz.timezone(self.env.context.get('tz') or self.env.user.tz)).date())
    type = fields.Selection([
        ("Soporte", "Soporte"),
        ("Vantas", "Vantas"),
    ], string="Tipo de comisiones",required=True)
    state = fields.Selection([
        ("draft", "Borrador"),
        ("init", "Iniciado"),
        ("proccess", "Proceso"),
        ("done", "Hecho"),
        ("cancel", "Cancelado")
    ], string="Estado", default="draft")

    def volver_borrador(self):
        self.write({
            'state': 'draft'
        })

    def cancel(self):
        # lines_ids = []
        # invoice_ids = []
        # for item in self.facturas_ids:
        #     invoice_ids.append((3, item.sudo().id))
        #     item.sudo().write({
        #          'x_comision': '2'
        #      })
        # for item in self.comision_line:
        #     lines_ids.append((2, item.sudo().id))

        self.write({
            'facturas_ids': [(5,0,[])],
            'comision_line': [(5,0,[])],
            'state': 'cancel'
        })

    def init_comisiones(self):
        invoices_ids = self.env['account.invoice'].search(['&', '&', '&', '&',
            ('date_invoice', '<=', self.date),
            ('user_id', 'in', self.users_ids.ids),
            ('type', '=', 'out_invoice'),
            ('x_comision', '=', '2'),
            ('state', '=', 'paid'),
        ])
        for item in invoices_ids:
            for line in item.invoice_line_ids:
                self.write({
                    'comision_line': [(0, 0, {
                        'user_id': item.user_id.id,
                        'invoice_line_id': line.id
                    })]
                })
        self.write({
            'state': 'init',
            'facturas_ids': [(6,0,invoices_ids.ids)]
        })

    def rangeDate(self, dateInit, dateEnd):
        dates = [
            dateInit + datetime.timedelta(n) for n in range(int((dateEnd - dateInit).days))
        ]
        if dateEnd > dateInit:
            return len(dates)
        else:
            return (-1) * len(dates)
            

    def proccess_comisiones(self):
        for line in self.comision_line:
            
            if not line.invoice_line_id.precio_id:
                precio = ""
            else:
                precio = "A" if line.invoice_line_id.precio_id.name.tipo_precio == "a" else "M"
            
            if precio == 'A':
                porcentaje = line.invoice_line_id.product_id.x_comisiones_a if line.invoice_line_id.x_user_id.tipo_vendedor == '1' else line.invoice_line_id.product_id.x_comisiones_a/2
            elif precio == 'M':
                porcentaje = line.invoice_line_id.product_id.x_comisiones_m if line.invoice_line_id.x_user_id.tipo_vendedor == '1' else line.invoice_line_id.product_id.x_comisiones_m/2
            else:
                porcentaje = 0
            porcentaje = 2 if porcentaje == 2.5 else porcentaje
            posible_comision = line.invoice_line_id.quantity * line.invoice_line_id.price_unit * (porcentaje/100)
            # Lo comentado es un proceso por si hay que hacer un proceso para los tipos de pagos
            # yo deje todo al 100 %
            # promedio = 0
            # for item in line.invoice_line_id.invoice_id.payment_ids:
            #     if line.invoice_line_id.precio_id.name.tipo_precio == "a":
            #         promedio = item.journal_id.comision_a
            #     else:
            #         promedio = item.journal_id.comision_m
            # denominador = len(line.invoice_line_id.invoice_id.payment_ids.ids)
            # promedio = promedio/denominador if denominador > 0 else 0
            # print("////////////",promedio,"/////////////")
            date_payment = ''
            for item in line.invoice_line_id.invoice_id.payment_ids:
                date_payment = item.payment_date
            if date_payment:
                length = self.rangeDate(line.invoice_line_id.invoice_id.date_due,date_payment)
            else: 
                length = -1
            line.write({
                'pocentaje_comision': porcentaje,
                'posible_comision': posible_comision,
                'forma_comision': posible_comision,
                'antiguedad_pago': length
            })
        self.write({
            'state': 'proccess'
        })
    
    def depurar_facturas(self):
        for factura in self.facturas_ids:
             factura.write({
                 'x_comision': '1'
             })
        self.write({
            'state': 'done'
        })
    
    def quit_depurar_facturas(self):
        for factura in self.facturas_ids:
             factura.write({
                 'x_comision': '2'
             })
        self.write({
            'state': 'proccess'
        })
        
        
    def generate_excel(self):
        vals = []
        for line in self.comision_line:
            payment_ref_name = ""
            payment_ref_date = ""
            payment_ref_tipo = ""
            for payment in line.invoice_line_id.invoice_id.payment_ids:
                payment_ref_name = payment.name
                payment_ref_date = payment.payment_date
                payment_ref_tipo = payment.journal_id.name
            
            if not line.invoice_line_id.precio_id:
                precio = ""
            else:
                precio = "A" if line.invoice_line_id.precio_id.name.tipo_precio == "a" else "M"
            
            vals.append({
                'Fecha creada': line.invoice_line_id.invoice_id.date_invoice,
                'Fecha vencimiento': line.invoice_line_id.invoice_id.date_due,
                'Número': line.invoice_line_id.invoice_id.number,
                'Cliente': line.invoice_line_id.invoice_id.partner_id.name,
                'Item': line.invoice_line_id.name,
                'Cantidad': line.invoice_line_id.quantity,
                'Precio unitario': line.invoice_line_id.price_unit,
                'Responsable': line.invoice_line_id.x_user_id.name,
                'Numero de Pagos': payment_ref_name,
                'Fecha el ultimo pago': payment_ref_date,
                'Tipo de pago': payment_ref_tipo,
                'Tipo de vendedor': "Tienda" if line.invoice_line_id.x_user_id.tipo_vendedor == '2' else "Calle",
                'Precio': precio,
                '%': line.pocentaje_comision,
                'Comision Posible': line.posible_comision,
                'Com Forma Pago': line.forma_comision,
                'Antigüedad del pago': line.antiguedad_pago,
                'Pago %': str(line.pocentaje_pago) + ' %',
                'Comision a Pagar': line.comision_pagar
            })
        return {
            'data': vals,
            'name': 'Comisiones ' + self.name
            }
