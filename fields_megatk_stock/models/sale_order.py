# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def _prepare_invoice(self):
        invoiceline = self.env['account.invoice.line']
        invoice = invoiceline.search(
            [('sale_line_ids.order_id.id', '=', self.id)], limit=1)
        if invoice:
            invoice_vals = super(SaleOrder, self)._prepare_invoice()
            invoice_vals['internal_number'] = invoice.invoice_id.internal_number
            return invoice_vals

        else:
            return super(SaleOrder, self)._prepare_invoice()
        # invoice_vals = super(SaleOrder, self)._prepare_invoice()
        #invoice_vals['precio_id'] = self.precio_id.id
        # return invoice_vals
        
    def get_users_auth(self):
        params = self.env['res.config.settings'].sudo().get_values()
        users = self.env['res.users'].sudo().browse(params['users_ids'][0][2])
        emails = []
        for user in users:
             emails.append(user.sudo().email)
        return emails

    @api.multi
    def action_confirm(self):
        if self.env.user.company_id.id != 10:
            emails = self.get_users_auth()
            if self.env.user.email not in emails:
                message = ''
                for line in self.order_line:
                    if line.product_id.type == 'product':
                        stock_quant = self.env['stock.quant'].search(
                            [('product_id.id', '=', line.product_id.id), ('location_id.id', '=', self.warehouse_id.lot_stock_id.id)])
                        if stock_quant:
                            if stock_quant.quantity < line.product_uom_qty:
                                if stock_quant.quantity > 0:
                                    message += _('\nPlanea vender %s Unidad(es) de %s pero solo tiene %s Unidad(es) disponible(s) en el almacén %s.') % \
                                        (line.product_uom_qty, line.product_id.name,
                                         stock_quant.quantity, self.warehouse_id.name)
                                if stock_quant.quantity <= 0:
                                    message += ('\nPlanea vender %s Unidad(es) de %s pero no tiene cantidades disponible(s) en el almacén %s.') % \
                                        (line.product_uom_qty, line.product_id.name,
                                         self.warehouse_id.name)
                        else:
                            message += ('\nPlanea vender %s Unidad(es) de %s pero no tiene cantidades disponible(s) en el almacén %s.') % \
                                (line.product_uom_qty, line.product_id.name,
                                 self.warehouse_id.name)
                    elif line.product_id.type == 'consu':
                        message += ('\nEl producto %s no esta disponible para la venta') % \
                            (line.product_id.name)
                if message != '':
                    raise UserError(_(message))

        return super(SaleOrder, self).action_confirm()


class Invoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    def unlink(self):
        for invoice in self:
            if invoice.move_name:
                company = self.env.user.company_id.id
                invoice_searh = self.env['account.invoice']
                resul_invoice = invoice_searh.search(
                    [('internal_number', '=', invoice.internal_number), ('company_id', '=', company)])
                if len(resul_invoice) > 1:
                    invoice.write({'move_name': ''})
                else:
                    raise UserError(
                        _('No se puede eliminar una factura que ya fue validada.'))

        return super(Invoice, self).unlink()
