# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import Warning
from datetime import *
import time


class ConciliacionBancaria(models.Model):
    _name = 'conicliacion.bancaria'
    _inherit = ['mail.thread']
    _description = "Conciliación Bancaria"
    _order = 'date desc'


    @api.onchange("account_id")
    def onchangemoneda(self):
        if self.account_id:
            if self.account_id.currency_id:
                self.currency_id = self.account_id.currency_id.id
            else:
                if self.company_id:
                    self.currency_id = self.company_id.currency_id.id

    @api.onchange("date")
    def onchangefecha(self):         
        if self.date:
            self.mes_name = self.date.strftime("%B")


    company_id = fields.Many2one("res.company", "Compañia", required=True, track_visibility='onchange', default=lambda self: self.env.user.company_id)
    #('reconcile', '=', True),
    account_id = fields.Many2one("account.account", "Banco", track_visibility='onchange', required=True,)
    currency_id = fields.Many2one("res.currency", "Moneda", track_visibility='onchange')
    date = fields.Date(string="Fecha Final", help="Effective date for accounting entries", required=True, track_visibility='onchange')
    saldo_final = fields.Float(string='Saldo Final')
    name = fields.Text(string="Descripción", required=True, track_visibility='onchange')
    conciliacion_line = fields.One2many("conicliacion.bancaria.line", "conciliacion_id", "Detalle de conciliación")
    state = fields.Selection([('draft', 'Borrador'), ('validated', 'Validado'), ('anulated', "Anulado")], string="Estado", default='draft')
    difference = fields.Float(string='Diferencia', compute='_compute_rest_credit')
    mes_name = fields.Char("Mes del Año", track_visibility='onchange')
    saldo_inicial = fields.Float(string="Saldo Inicial")


    @api.depends('conciliacion_line.debe', 'conciliacion_line.haber', 'saldo_final', 'saldo_inicial')
    def _compute_rest_credit(self):
        for concil in self:
            debit_line = 0
            credit_line = 0
            for lines in self.conciliacion_line:
                if lines.es_conciliado:
                    if lines.debe > 0.0:
                        debit_line += lines.debe
                    if lines.haber > 0.0:
                        credit_line += lines.haber

            if concil.account_id.account_type == 'liability_credit_card':
                concil.difference = (concil.saldo_inicial + credit_line - debit_line) - concil.saldo_final

            if concil.account_id.account_type != 'liability_credit_card':
                concil.difference = concil.saldo_final - (concil.saldo_inicial + debit_line - credit_line) 

    def action_validate(self):
        if not self.conciliacion_line:
            raise Warning(_('No existen movimiento a conciliar') )

        if not round(self.difference, 2) == 0.0:
            raise Warning(_('Existe diferencia en la conicliación, debe de revisar todos los movimientos a conciliar') )

        if self.validar():
            raise Warning(_('hay movimientos cancelados, debe de revisar todos los movimientos a conciliar') )

        for mov_conciliar in self.conciliacion_line:            
            if mov_conciliar.es_conciliado:
                mov_conciliar.move_id.es_conciliado = True
                mov_conciliar.move_line_id.es_conciliado = True
                mov_conciliar.move_line_id.reconciled = True
                mov_conciliar.move_id.conciliacion_id = self.id

        self.write({'state': 'validated'})

    def validar(self):
        for mov_conciliar in self.conciliacion_line:
            if not mov_conciliar.move_id and mov_conciliar.es_conciliado or mov_conciliar.move_id.state=='draft':
                return True

        return False

    def quitar_null(self):
        for mov_conciliar in self.conciliacion_line:            
            if not mov_conciliar.move_id and not mov_conciliar.move_id.es_conciliado:
                mov_conciliar.unlink()

    def action_anulated(self):
        for mov_conciliar in self.conciliacion_line:
            if mov_conciliar.es_conciliado:
                mov_conciliar.move_id.es_conciliado = False
                mov_conciliar.move_line_id.es_conciliado = False
                mov_conciliar.move_line_id.reconciled = False
                mov_conciliar.move_id.conciliacion_id = False

        self.write({'state': 'anulated'})

    def back_draft(self):
        self.write({'state': 'draft'})


    def get_movimientos(self):
        obj_move_id = self.env["account.move.line"].search([('date', '<=', self.date), ('account_id', '=', self.account_id.id), 
            ('company_id', '=', self.company_id.id), ('es_conciliado', '=', False), ('move_id.state', '=', 'posted')])
        obj_concil_last = self.env["conicliacion.bancaria"].search([('state', '=', 'validated'), ('account_id','=',self.account_id.id)],limit=1)
        for cooncil in obj_concil_last:
            self.saldo_inicial = cooncil.saldo_final

        for movimiento in obj_move_id:
            obj_line = self.env["conicliacion.bancaria.line"]
            for obj_line_concil_delete in self.conciliacion_line:
                if obj_line_concil_delete.move_id.state == 'draft' or not obj_line_concil_delete.move_id:
                    obj_line_concil_delete.unlink()

            obj_line_concil_line = self.env["conicliacion.bancaria.line"].search([('conciliacion_id', '=', self.id), ('move_line_id', '=', movimiento.id)])

            if not obj_line_concil_line:
                vals = {
                    'conciliacion_id': self.id,
                    'move_id': movimiento.move_id.id,
                    'move_line_id': movimiento.id,
                    'partner_id': movimiento.partner_id.id,
                    'date': movimiento.date,
                    'currency_id': movimiento.currency_id.id,
                    'es_conciliado': False,
                    'name': movimiento.ref,
                    #'analytic_id': movimiento.analytic_id.id,
                    'importe_moneda': movimiento.amount_currency,
                }
                if movimiento.debit > 0:
                    vals["debe"] = movimiento.debit
                if movimiento.credit > 0:
                    vals["haber"] = movimiento.credit

                line_id =  obj_line.create(vals)


class Debitline(models.Model):
    _name = 'conicliacion.bancaria.line'
    _description = "description"

    conciliacion_id = fields.Many2one('conicliacion.bancaria', 'Conciliación')
    move_id = fields.Many2one("account.move", "Movimiento")
    move_line_id = fields.Many2one("account.move.line", "Linea de movimiento")
    partner_id = fields.Many2one('res.partner', 'Empresa')
    date = fields.Date(string="Fecha", help="Effective date for accounting entries", required=True)
    name = fields.Char('Descripción')
    debe = fields.Float('Debe')
    haber = fields.Float("Haber")
    currency_id = fields.Many2one('res.currency', string='Currency')
    analytic_id = fields.Many2one("account.analytic.account", string="Cuenta Analitica")
    es_conciliado = fields.Boolean("Conciliado")
    importe_moneda = fields.Float("Importe de moneda")