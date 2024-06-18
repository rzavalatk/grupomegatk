from odoo import models, fields, api
from datetime import datetime

class CustomAccountMove(models.Model):
    _name = 'custom.account.move'
    _description = 'Custom Account Move'

    date_from = fields.Date('Date from')
    date_to = fields.Date('Date to')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)

    @api.model
    def create_account_moves(self, date):
        # Buscar todos los asientos contables de una fecha específica
        account_moves = self.env['account.move'].search(['&', '&', ('date', '>=', self.date_from), ('date', '<=', self.date_to), ('company_id', '=', self.company_id.id),])

        # Buscar todas las transferencias relacionadas con una orden de compra
        stock_moves = self.env['stock.picking'].search(['&',
            ('state', '=', 'done'),
            ('company_id', '=', self.company_id.id),  # Asumiendo que las órdenes de compra tienen 'PO' en el origen
        ])

        for stock_move in stock_moves:
            
            if stock_move.origin:
                # Buscar la orden de compra relacionada con la transferencia
                purchase_order = self.env['purchase.order'].search(['&', ('name', '=', stock_move.origin), ('company_id', '=', self.company_id.id)], limit=1)

                if purchase_order:
                    # Buscar la factura de proveedor relacionada con la orden de compra
                    vendor_bill = self.env['account.invoice'].search([('origin', '=', purchase_order.name)], limit=1)

                    
                    # Evaluar si hay un asiento contable para la transferencia
                    related_account_move = account_moves.filtered(lambda am: am.ref == stock_move.name)

                    if not related_account_move:
                        # Crear un asiento contable por cada línea de la transferencia
                        move_lines = []
                        for line in stock_move.move_ids_without_package:
                            # Buscar la línea de orden de compra correspondiente
                            order_line = purchase_order.order_line.filtered(lambda ol: ol.product_id.id == line.product_id.id)

                            if order_line:
                                price_subtotal = order_line.price_subtotal

                                # Crear líneas de apunte contable
                                move_lines.append((0, 0, {
                                    'account_id': self.env['account.account'].search([('code', '=', 'product_stock_account_code')], limit=1).id,
                                    'partner_id': stock_move.partner_id.id,
                                    'name': line.product_id.name,
                                    'debit': price_subtotal,
                                    'credit': 0,
                                    'date_maturity': date,
                                }))
                                move_lines.append((0, 0, {
                                    'account_id': self.env['account.account'].search([('code', '=', 'product_stock_account_code')], limit=1).id,
                                    'partner_id': stock_move.partner_id.id,
                                    'name': line.product_id.name,
                                    'debit': 0,
                                    'credit': price_subtotal,
                                    'date_maturity': date,
                                }))

                        # Crear el asiento contable
                        self.env['account.move'].create({
                            'date': stock_move.date,
                            'ref': stock_move.name,
                            'journal_id': self.env['account.journal'].search([('code', '=', 'STJ')], limit=1).id,
                            'company_id': self.env['res.company'].search([('name', '=', 'IMASA')], limit=1).id,
                            'line_ids': move_lines,
                        })

# Luego, este modelo debe ser registrado en el __init__.py del módulo correspondiente
