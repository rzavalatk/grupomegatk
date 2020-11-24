# -*- encoding: utf-8 -*-
from dateutil.relativedelta import relativedelta
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import Warning


class LiquidacionTarjetas(models.Model):
    _name = "gastos.tarjeta.megatk"
    _inherit = ['mail.thread','mail.activity.mixin']
    _order = 'create_date desc'
    

    @api.onchange("currency_id")
    def onchangecurrency(self):
        if self.currency_id:
            if self.currency_id != self.company_id.currency_id:
                tasa = self.currency_id.with_context(date=self.fecha_inicio)
                print("tasa");print("tasa");print("tasa");print(tasa.rate);print("tasa");
                self.currency_rate = 1 / tasa.rate 
                self.es_moneda_base = False
            else:
                self.currency_rate = 1
                self.es_moneda_base = True

    @api.one
    @api.depends('detalle_gastos_ids.monto')
    def get_totalgastos(self):
        for gs in self:
            for line in gs.detalle_gastos_ids:
                gs.total_gastos += line.monto

    company_id = fields.Many2one("res.company", "Empresa", required=True, default=lambda self: self.env.user.company_id)
    name = fields.Char("Motivo", required=True, track_visibility='onchange')
    fecha_inicio = fields.Date("Fecha de inicio", required=True, track_visibility='onchange')
    fecha_aprobacion = fields.Date("Fecha de Aprobación", readonly=True, track_visibility='onchange')
    empleado_solicitud = fields.Many2one("res.partner", "Solicitante", required=True, track_visibility='onchange')
    #line_ids = fields.One2many("stock.requisition.line", "obj_parent", "Lineas")
    state = fields.Selection( [('draft', 'Borrador'),  ('pendiente', 'Pendiente de aprobacíón'), 
        ('liquidado', 'Validado'), ('rechazado', 'Rechazado')], string="Estado", default='draft')

    #relacion de unos a muchos
    detalle_gastos_ids = fields.One2many("gastos.tarjeta.lineas.megatk", "obj_parent", "Detalle de gastos")
    comentarios = fields.Text("Comentarios")
    total_gastos = fields.Float("Total gastos", store=True, track_visibility='onchange', compute=get_totalgastos)
    journal_id = fields.Many2one("account.journal", "Tarjeta", required=True, domain=[('type','=','bank')])
    debito_id = fields.Many2one('banks.debit', 'Apunte Contable', readonly=True)
    
    currency_id = fields.Many2one("res.currency", "Moneda", default=lambda self: self.env.user.company_id.currency_id, domain=[('active', '=', True)])
    cuenta_gasto_id = fields.Many2one("account.account", "Cuenta de gastos")
    fecha_liquidacion = fields.Date("Fecha de liquidación")

    es_moneda_base = fields.Boolean("Es moneda base")
    currency_rate = fields.Float("Tasa de Cambio", digits=(12, 6))
    cotizaciones_ids = fields.Many2many(comodel_name="sale.order",relation="gastos_tarjetas_sale_order",column1="tarjetas_ids",column2="sale_order_ids",string="Cotización")

    @api.multi
    def solicitar_aprobacion(self):
        if not self.detalle_gastos_ids:
            raise Warning(_('No existe detalle de gastos'))
        self.write({'state': 'pendiente'})

    @api.multi
    def rechazar_gastos(self):
        self.write({'state': 'rechazado'})

    @api.multi
    def liquidar_gastos(self):
        #if self.total_gastos <= 0:
            #raise Warning(_('Debe de ingresar los gastos reales, no puede ser cero la suma de los gastos para esta solicitud.'))

        if not self.fecha_liquidacion:
            self.fecha_liquidacion = datetime.now().date()
        if not self.journal_id:
            raise Warning(_('No ha seleccionado una tarjeta para generar la liquidación.'))

        obj_debit = self.env["banks.debit"]
        lineas = []
        for detalle_tarjeta in self.detalle_gastos_ids:
            val_lineas = {
                'account_id': detalle_tarjeta.account_id.id,
                'analytic_id': detalle_tarjeta.analytic_id.id,
                'move_type': 'debit',
                'name': detalle_tarjeta.name,
                'amount': detalle_tarjeta.monto,
                'partner_id': detalle_tarjeta.partner_id.id,
            }
            lineas.append((0, 0, val_lineas))
        val_encabezado = {
            'company_id': self.company_id.id,
            'journal_id': self.journal_id.id,
            'date' : self.fecha_inicio,
            'total': self.total_gastos,
            'name': self.name,
            'es_moneda_base': self.es_moneda_base,
            'currency_rate': self.currency_rate,
            'currency_id': self.currency_id.id,
            'doc_type': 'debit',
            'debit_line': lineas,
            'number_calc': '001',
        }
        
        id_move = obj_debit.create(val_encabezado)
        id_move.action_validate()
        self.debito_id = id_move.id
        self.write({'state': 'liquidado'})


    @api.multi
    def back_draft(self):
        self.write({'state': 'draft'})


    @api.multi
    def unlink(self):
        if self.state == 'pendiente' or self.state == 'aprobado'  or self.state =='liquidado':
            raise Warning(_('No puede eliminar gastos en proceso o liquidados.'))
        return super(LiquidacionTarjetas, self).unlink()

class LineaGastos(models.Model):
    _name = "gastos.tarjeta.lineas.megatk"

    obj_parent = fields.Many2one("gastos.tarjeta.megatk", "Gasto")
    name = fields.Char("Descripción")
    comprobante = fields.Char("Factura/Comprobante")
    account_id = fields.Many2one('account.account', 'Cuenta', domain="[('company_id', '=', parent.company_id)]")
    analytic_id = fields.Many2one("account.analytic.account", string="Cuenta Analitica", domain="[('company_id', '=', parent.company_id)]")
    partner_id = fields.Many2one('res.partner', 'Empresa', domain="[('company_id', '=', parent.company_id)]")
    monto = fields.Float("Monto a liquidar")