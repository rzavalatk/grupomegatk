# -*- coding: utf-8 -*-
from odoo import models, api,fields


class CierreDiario(models.Model):
    _name = "account.cierre"
    
    regions_list = [
        ("Tegucigalpa","TGU"),
        ("San Pedro Sula","SPS"),
        ("Nicaragua","NIC")
    ]
    
    def _recorrec_lines(self,field):
        total = 0
        for item in self.cierre_line_ids:
            if field == 'total':
                total += item.total
            if field == 'cobrado':
                total += item.cobrado
            if field == 'facturado':
                total += item.facturado
        return round(total, 2)
        
    
    @api.one
    def _total(self):
        self.total = self._recorrec_lines("total")

    @api.one
    def _total_cobrado(self):
        self.total_cobrado = self._recorrec_lines("cobrado")

    
    @api.one
    def _total_facturado(self):
        self.total_facturado = self._recorrec_lines("facturado")
    
    
    @api.one
    def _team_id(self):
        if self.region == "San Pedro Sula":
            self.team_id = 43
        
       
    @api.one
    def _name_(self):
        self.name = self.company_id.name +" - "+ self.date.strftime("%d/%m/%Y")
                
    name = fields.Char(compute=_name_)
    cierre_line_ids = fields.One2many("account.cierre.line","cierre_id",string="Lineas de Cierre")
    company_id = fields.Many2one("res.company","Compañia", default=lambda self : self.env.user.company_id.id)
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True, default=lambda self : self.env.user.company_id.currency_id)
    total_facturado = fields.Monetary("Total Facturado",compute=_total_facturado)
    total_cobrado = fields.Monetary("Total Cobrado",compute=_total_cobrado)
    total = fields.Monetary("Total",compute=_total)
    region = fields.Selection(regions_list,string="Region/Zona")
    date = fields.Date("Fecha")
    state = fields.Selection([
        ("draft","Borrador"),
        ("init","Iniciado"),
        ("proccess","Proceso"),
        ("done","Hecho"),
        ("cancel","Cancelado")
    ],string="Estado",default="draft")
    date = fields.Date("Fecha")
    
    def volver_borrador(self):
        self.write({
            'state': 'draft'
        })
    
    def cancel(self):
        ids = []
        for item in self.cierre_line_ids:
            ids.append((2,item.id))
             
        self.write({
            'cierre_line_ids': ids,
            'state': 'cancel'
        })
    
    def iniciar_cierre(self):
        journal_ids = self.env['res.config.settings'].get_values_journal_ids()
        values = [(0, 0,  {
            'credito': True
        })]
        for item in journal_ids:
            values.append((0,0,{
                'journal_id': item
            }))
        self.write({
            'cierre_line_ids': values,
            'state': 'init'
        })
        
    
    def procesar_cierre(self):
        pagos=self.env['account.payment'].search([
            '&',
            '&',
            '&',
            ('payment_date','=',self.date),
            ('company_id','=',self.company_id.id),
            ('region','=',self.region),
            ('partner_type','=','customer'),
            ('state','=','posted'),
        ])
        teams_sps = self.env['res.config.settings'].get_values_teams_sps()
        if self.region == "San Pedro Sula":
            facturas=self.env['account.invoice'].search([
                '&',
                '&',
                '&',
                '&',
                '&',
                ('date_invoice','=',self.date),
                ('company_id','=',self.company_id.id),
                ('team_id','in', teams_sps),
                ('type','=','out_invoice'),
                ('state','!=','cancel'),
                ('state','!=','draft'),
            ])
        else:
            facturas=self.env['account.invoice'].search([
                '&',
                '&',
                '&',
                '&',
                '&',
                ('date_invoice','=',self.date),
                ('company_id','=',self.company_id.id),
                ('team_id','not in', teams_sps),
                ('type','=','out_invoice'),
                ('state','!=','cancel'),
                ('state','!=','draft'),
            ])
        ids_facturas = []
        journal_ids = self.env['res.config.settings'].get_values_journal_ids()
        for pago in pagos:
            if pago.journal_id.id in journal_ids:
                for item in self.cierre_line_ids:
                    if pago.journal_id.id == item.journal_id.id:
                        acumulado_factura = 0
                        for factura in pago.invoice_ids.ids:
                            if factura.id not in ids_facturas:
                                factura_id = self.env['account.invoice'].browse(factura)
                                if factura_id.date_invoice == self.date:
                                    acumulado_factura += factura_id.amount_total_signed
                        self.write({
                            'cierre_line_ids': [(1, item.id, {
                                'cobrado': pago.amount + item.cobrado,
                                'facturado': acumulado_factura + item.facturado
                            })]
                        })
            else:
                for item in self.cierre_line_ids:
                    if item.journal_id.name == "Efectivo":
                        acumulado_factura = 0
                        for factura in pago.invoice_ids.ids:
                            factura_id = self.env['account.invoice'].browse(factura)
                            if factura_id.date_invoice == self.date:
                                acumulado_factura += factura_id.amount_total_signed
                        self.write({
                            'cierre_line_ids': [(1, item.id, {
                                'cobrado': pago.amount + item.cobrado,
                                'facturado': acumulado_factura + item.facturado
                            })]
                        })
            ids_facturas = ids_facturas + pago.invoice_ids.ids
                        
                        
        for factura in facturas:
            if factura.id not in ids_facturas:
                if factura.payment_term_id.name != 'Contado':
                    for item in self.cierre_line_ids:
                        if item.credito: 
                            self.write({
                                'cierre_line_ids': [(1, item.id, {
                                    'facturado': factura.amount_total_signed + item.facturado
                                })]
                            })
                else:
                    for item in self.cierre_line_ids:
                        if item.journal_id.name == "Efectivo": 
                            self.write({
                                'cierre_line_ids': [(1, item.id, {
                                    'facturado': factura.amount_total_signed + item.facturado
                                })]
                            })
        self.write({
            'state': 'proccess'
        })
        
        
    def send_email(self,email):
        template = self.env.ref(
        'crons_mega.email_template_cierre_diario_1')
        email_values = {
            'email_from': 'azelaya@megatk.com',
            'email_to': email
        }
        template.send_mail(self.id, email_values=email_values, force_send=True)
        self.write({
            'state': 'done'
        })
        return True
    
    
    def go_to_view_tree(self):
        return {
            'name': 'Cierre Diario',
            'type': 'ir.actions.act_window',
            'res_model': 'account.cierre',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(False, 'tree'), (False, 'form')],
            'target': 'current',
            'domain': [('company_id', '=', self.env.user.company_id.id)],
        }
    
    
class CierreDiarioLine(models.Model):
    _name = "account.cierre.line"
    
    @api.one
    def _name_(self):
        if self.credito:
            self.name = "Creditos"
        else:
            self.name = self.journal_id.name
    
    
    @api.one
    def _total(self):
        total = self.cobrado - self.facturado
        self.total = round(total, 2)
    
        
    name = fields.Char("Nombre",compute=_name_)
    cierre_id = fields.Many2one("account.cierre")
    journal_id = fields.Many2one("account.journal")
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True, default=lambda self : self.env.user.company_id.currency_id)
    facturado = fields.Monetary("Facturado",default=0)
    cobrado = fields.Monetary("Cobrado",default=0)
    total = fields.Monetary("Total",compute=_total)
    credito = fields.Boolean("Es Crédito")
    
    def toggle_credito(self):
        self.credito = not self.credito
    
    