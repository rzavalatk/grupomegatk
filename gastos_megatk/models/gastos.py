# -*- encoding: utf-8 -*-
from dateutil.relativedelta import relativedelta
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import Warning


class LiquidacionGastos(models.Model):
    _name = "gastos.megatk"
    _inherit = ['mail.thread','mail.activity.mixin']


    @api.multi
    def action_close_dialog(self):
        super(LiquidacionGastos, self).action_close_dialog()
        

    @api.onchange("empleado_solicitud")
    def onchangeempleado(self):
        if self.empleado_solicitud:
            self.cuenta_anticipo_id = self.empleado_solicitud.account_id.id

    @api.one
    @api.depends('detalle_gastos_ids.monto')
    def get_totalgastos(self):
        for gs in self:
            for line in gs.detalle_gastos_ids:
                gs.total_solicitado += line.monto
                gs.total_gastos += line.monto_comprobante
            gs.total_diferencia = gs.total_gastos - gs.monto_anticipo
            if gs.total_diferencia == 0:
                gs.activar_cuenta_cxc = False
                gs.activar_caja = False
                gs.activar_cuenta_gasto = True
            if gs.total_diferencia < 0:
                gs.activar_cuenta_cxc = True
                gs.activar_caja = False
                gs.activar_cuenta_gasto = True
            if gs.total_diferencia > 0 :
                gs.activar_cuenta_cxc = False
                gs.activar_caja = True
                gs.activar_cuenta_gasto = True

    @api.multi
    def unlink(self):
        for gastos in self:
            if gastos.state == 'pendiente' or gastos.state == 'aprobado' or gastos.state == 'desembolso' or gastos.state =='liquidado':
                raise Warning(_('No puede eliminar gastos en proceso o liquidados.'))
        return super(LiquidacionGastos, self).unlink()

    company_id = fields.Many2one("res.company", "Empresa", required=True, default=lambda self: self.env.user.company_id,)
    name = fields.Char("Motivo", required=True, track_visibility='onchange')
    fecha_inicio = fields.Date("Fecha de inicio", required=True, track_visibility='onchange')
    fecha_final = fields.Date("Fecha final", required=True, track_visibility='onchange')
    fecha_aprobacion = fields.Date("Fecha de Aprobación", readonly=True, track_visibility='onchange')
    empleado_solicitud = fields.Many2one("res.partner", "Solicitante", required=True, track_visibility='onchange')
    #line_ids = fields.One2many("stock.requisition.line", "obj_parent", "Lineas")
    state = fields.Selection( [('draft', 'Borrador'),  ('pendiente', 'Pendiente de aprobacíón'), ('aprobado', 'Aprobado'), ('desembolso', 'Desembolsado'),
        ('liquidado', 'Liquidado'), ('rechazado', 'Rechazado')], string="Estado", default='draft')
    tipo_gasto = fields.Selection([('viatico', 'Viatico'), ('otro', 'Otros')], string="Tipo de gasto", required=True)

    #relacion de unos a muchos
    detalle_gastos_ids = fields.One2many("gastos.lineas.megatk", "obj_parent", "Detalle de gastos")
    comentarios = fields.Text("Comentarios")
    total_solicitado = fields.Float("Monto solicitado", compute=get_totalgastos, track_visibility='onchange')
    total_gastos = fields.Float("Total gastos", compute=get_totalgastos, track_visibility='onchange')
    total_diferencia = fields.Float("Diferencia", compute=get_totalgastos, track_visibility='onchange')
    monto_anticipo = fields.Float("Monto de anticipo", track_visibility='onchange')
    banco_id = fields.Many2one("banks.check", "Cheque/Transferencia", track_visibility='onchange')
    journal_id = fields.Many2one("account.journal", "Diario", domain=[('type','=','general')])
    move_id = fields.Many2one('account.move', 'Apunte Contable', readonly=True)

    activar_cuenta_gasto = fields.Boolean("Activar", compute=get_totalgastos)
    activar_cuenta_cxc = fields.Boolean("Activar", compute=get_totalgastos)
    activar_caja = fields.Boolean("Activar", compute=get_totalgastos)
    analytic_id = fields.Many2one("account.analytic.account", string="Cuenta Analitica", domain="[('company_id', '=', company_id)]")

    cuenta_anticipo_id = fields.Many2one("account.account", "Cuenta de anticipos", required=True)
    cuenta_gasto_id = fields.Many2one("account.account", "Cuenta de gastos")
    cuenta_cxc_id = fields.Many2one("account.account", "Cuenta por cobrar")
    cuenta_caja_id = fields.Many2one("account.account", "Cuenta de caja/bancos")
    fecha_liquidacion = fields.Date("Fecha de liquidación")
    cotizaciones_ids = fields.Many2many(comodel_name="sale.order",relation="gastos_sale_order",column1="gastos_ids",column2="sale_order_ids",string="Cotización")

    @api.onchange("fecha_final")
    def onchangefechafinal(self):
        if self.fecha_inicio:
            if self.fecha_final < self.fecha_inicio:
                raise Warning(_('La fecha final debe de ser mayor que la fecha inicial') )

    @api.onchange("banco_id")
    def onchangebanco(self):
        if self.banco_id:
            self.monto_anticipo = self.banco_id.total

    @api.multi
    def solicitar_aprobacion(self):
        if not self.detalle_gastos_ids:
            raise Warning(_('No existe detalle de gastos'))
        self.write({'state': 'pendiente'})

    @api.multi
    def rechazar_gastos(self):
        self.write({'state': 'rechazado'})

    @api.multi
    def aprobar_gastos(self):
        self.write({'state': 'aprobado'})
        self.fecha_aprobacion = datetime.now()


    @api.multi
    def cancelar_liquidados(self):
        for move in self.move_id:
            move.write({'state': 'draft'})
            move.unlink()
        for line in self.detalle_gastos_ids:
            line.estado_parent = True
        self.write({'state': 'desembolso'})

    @api.multi
    def liquidar_gastos(self):
        #if self.total_gastos <= 0:
            #raise Warning(_('Debe de ingresar los gastos reales, no puede ser cero la suma de los gastos para esta solicitud.'))

        if not self.fecha_liquidacion:
            raise Warning(_('No existe una fecha de liquidación.'))
        if not self.journal_id:
            raise Warning(_('No existe un diario establecido para generar la liquidación.'))
        for line in self.detalle_gastos_ids:
            line.estado_parent = False
        account_move = self.env['account.move']
        lineas = []
        vals_credit_anticipo = {
            'debit': 0.0,
            'credit': self.monto_anticipo,
            'name': self.name,
            'account_id': self.cuenta_anticipo_id.id,
            'date': self.fecha_liquidacion,
            'partner_id': self.empleado_solicitud.id,
            #'company_id': self.company_id.id,
        }
        lineas.append((0, 0, vals_credit_anticipo))
        if self.total_diferencia == 0:
            if not self.cuenta_gasto_id:
                raise Warning(_('No existe una cuenta de gastos establecida para generar la liquidación.'))
            vals_cuenta_gasto = {
            'debit': self.total_gastos,
            'credit': 0.0,
            'name': self.name,
            'account_id': self.cuenta_gasto_id.id,
            'analytic_account_id': self.analytic_id.id,
            'date': self.fecha_liquidacion,
            'partner_id': self.empleado_solicitud.id,
            #'company_id': self.company_id.id,
            }
            lineas.append((0, 0, vals_cuenta_gasto))
        if self.total_diferencia < 0:
            if not self.cuenta_gasto_id:
                raise Warning(_('No existe una cuenta de gastos establecida para generar la liquidación.'))
            vals_cuenta_gasto = {
            'debit': self.total_gastos,
            'credit': 0.0,
            'name': self.name,
            'account_id': self.cuenta_gasto_id.id,
            'analytic_account_id': self.analytic_id.id,
            'date': self.fecha_liquidacion,
            'partner_id': self.empleado_solicitud.id,
            #'company_id': self.company_id.id,
            }
            lineas.append((0, 0, vals_cuenta_gasto))
            valor_cxc = self.total_diferencia * -1
            if not self.cuenta_cxc_id:
                raise Warning(_('No existe una cuenta por cobrar establecida para generar la liquidación.'))
            vals_cuenta_cxc = {
            'debit': valor_cxc,
            'credit': 0.0,
            'name': self.name,
            'account_id': self.cuenta_cxc_id.id,
            'date': self.fecha_liquidacion,
            'partner_id': self.empleado_solicitud.id,
            #'company_id': self.company_id.id,
            }
            lineas.append((0, 0, vals_cuenta_cxc))
        if self.total_diferencia > 0:
            if not self.cuenta_gasto_id:
                raise Warning(_('No existe una cuenta de gastos establecida para generar la liquidación.'))
            vals_cuenta_gasto = {
            'debit': self.total_gastos,
            'credit': 0.0,
            'name': self.name,
            'account_id': self.cuenta_gasto_id.id,
            'analytic_account_id': self.analytic_id.id,
            'date': self.fecha_liquidacion,
            'partner_id': self.empleado_solicitud.id,
            #'company_id': self.company_id.id,
            }
            lineas.append((0, 0, vals_cuenta_gasto))
            valor_cxc = self.total_diferencia
            if not self.cuenta_caja_id:
                raise Warning(_('No existe una cuenta de caja o bancos establecida para generar la liquidación.'))
            vals_cuenta_caja = {
            'debit': 0.0,
            'credit': valor_cxc,
            'name': self.name,
            'account_id': self.cuenta_caja_id.id,
            'date': self.fecha_liquidacion,
            'partner_id': self.empleado_solicitud.id,
            #'company_id': self.company_id.id,
            }
            lineas.append((0, 0, vals_cuenta_caja))
        values = {
            'journal_id': self.journal_id.id,
            'date': self.fecha_liquidacion,
            'ref': self.name,
            'line_ids': lineas,
            'state': 'posted',
        }
        id_move = account_move.create(values)
        id_move.post()
        self.move_id = id_move.id
        self.write({'state': 'liquidado'})

    @api.multi
    def back_draft(self):
        self.write({'state': 'draft'})

    @api.multi
    def desembolsar_gasto(self):
        if not self.banco_id:
            raise Warning(_('No se ha asignado cheque o transferencia a esta solicitud de gastos'))
        for line in self.detalle_gastos_ids:
            line.estado_parent = True
        self.write({'state': 'desembolso'})

    @api.multi
    def unlink(self):
        if self.state == 'pendiente' or self.state == 'aprobado' or self.state == 'desembolso' or self.state =='liquidado':
            raise Warning(_('No puede eliminar gastos en proceso o liquidados.'))
        return super(LiquidacionGastos, self).unlink()


class LineaGastos(models.Model):
    _name = "gastos.lineas.megatk"

    obj_parent = fields.Many2one("gastos.megatk", "Gasto")
    gasto_id = fields.Many2one("gastos.megatk.conceptos", "Tipo de gasto")
    name = fields.Char("Descripción")
    monto = fields.Float("Monto solicitado", required=True)
    comprobante = fields.Char("Factura/Comprobante")
    monto_comprobante = fields.Float("Monto a liquidar")
    estado_parent = fields.Boolean("Flag")

    @api.multi
    def unlink(self):
        if self.obj_parent.state == 'pendiente' or self.obj_parent.state == 'aprobado' or self.obj_parent.state == 'desembolso' or self.obj_parent.state =='liquidado':
            raise Warning(_('No puede eliminar gastos en proceso o liquidados.'))
        return super(LineaGastos, self).unlink()

