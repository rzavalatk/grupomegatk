# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import Warning

class AccountInvoice(models.Model):
	_inherit = "account.invoice"

	numero_factura = fields.Char('Número de factura', help='Número de factura')
	cai_proveedor = fields.Char("Cai Proveedor")

#     @api.model
#     def invoice_line_move_line_get(self):
#         res = []
#         for line in self.invoice_line_ids:
#             if line.quantity==0:
#                 continue
#             tax_ids = []
#             for tax in line.invoice_line_tax_ids:
#                 tax_ids.append((4, tax.id, None))
#                 for child in tax.children_tax_ids:
#                     if child.type_tax_use != 'none':
#                         tax_ids.append((4, child.id, None))
#             analytic_tag_ids = [(4, analytic_tag.id, None) for analytic_tag in line.analytic_tag_ids]

#             if line.partner_line_id:
#               move_line_dict = {
#                   'invl_id': line.id,
#                   'type': 'src',
#                   'name': line.name.split('\n')[0][:64],
#                   'price_unit': line.price_unit,
#                   'quantity': line.quantity,
#                   'price': line.price_subtotal,
#                   'account_id': line.account_id.id,
#                   'product_id': line.product_id.id,
#                   'uom_id': line.uom_id.id,
#                   'account_analytic_id': line.account_analytic_id.id,
#                   'tax_ids': tax_ids,
#                   'invoice_id': self.id,
#                   'analytic_tag_ids': analytic_tag_ids
#               }
#             else:
#               move_line_dict = {
#                   'invl_id': line.id,
#                   'type': 'src',
#                   'name': line.name.split('\n')[0][:64],
#                   'price_unit': line.price_unit,
#                   'quantity': line.quantity,
#                   'price': line.price_subtotal,
#                   'account_id': line.account_id.id,
#                   'product_id': line.product_id.id,
#                   'uom_id': line.uom_id.id,
#                   'account_analytic_id': line.account_analytic_id.id,
#                   'tax_ids': tax_ids,
#                   'invoice_id': self.id,
#                   'analytic_tag_ids': analytic_tag_ids
#               }
				
		

#             res.append(move_line_dict)
#         return res

#     @api.multi
#     def action_move_create(self):
#         """ Creates invoice related analytics and financial move lines """
#         account_move = self.env['account.move']

#         for inv in self:
#             if not inv.journal_id.sequence_id:
#                 raise UserError(_('Please define sequence on the journal related to this invoice.'))
#             if not inv.invoice_line_ids:
#                 raise UserError(_('Please create some invoice lines.'))
#             if inv.move_id:
#                 continue

#             ctx = dict(self._context, lang=inv.partner_id.lang)

#             if not inv.date_invoice:
#                 inv.with_context(ctx).write({'date_invoice': fields.Date.context_today(self)})
#             if not inv.date_due:
#                 inv.with_context(ctx).write({'date_due': inv.date_invoice})
#             company_currency = inv.company_id.currency_id

#             # create move lines (one per invoice line + eventual taxes and analytic lines)
#             iml = inv.invoice_line_move_line_get()
#             iml += inv.tax_line_move_line_get()

#             diff_currency = inv.currency_id != company_currency
#             # create one move line for the total and possibly adjust the other lines amount
#             total, total_currency, iml = inv.with_context(ctx).compute_invoice_totals(company_currency, iml)

#             name = inv.name or '/'
#             if inv.payment_term_id:
#                 totlines = inv.with_context(ctx).payment_term_id.with_context(currency_id=company_currency.id).compute(total, inv.date_invoice)[0]
#                 res_amount_currency = total_currency
#                 ctx['date'] = inv._get_currency_rate_date()
#                 for i, t in enumerate(totlines):
#                     if inv.currency_id != company_currency:
#                         amount_currency = company_currency.with_context(ctx).compute(t[1], inv.currency_id)
#                     else:
#                         amount_currency = False

#                     # last line: add the diff
#                     res_amount_currency -= amount_currency or 0
#                     if i + 1 == len(totlines):
#                         amount_currency += res_amount_currency

#                     iml.append({
#                         'type': 'dest',
#                         'name': name,
#                         'price': t[1],
#                         'account_id': inv.account_id.id,
#                         'date_maturity': t[0],
#                         'amount_currency': diff_currency and amount_currency,
#                         'currency_id': diff_currency and inv.currency_id.id,
#                         'invoice_id': inv.id
#                     })
#             else:
#                 iml.append({
#                     'type': 'dest',
#                     'name': name,
#                     'price': total,
#                     'account_id': inv.account_id.id,
#                     'date_maturity': inv.date_due,
#                     'amount_currency': diff_currency and total_currency,
#                     'currency_id': diff_currency and inv.currency_id.id,
#                     'invoice_id': inv.id
#                 })
			
#             line = []
#             for l in iml:
#                 if 'invl_id' in l:
#                     invoice_line = self.env['account.invoice.line'].search([('id','=',l['invl_id'])])
#                     line.append((0, 0, self.line_get_convert(l, invoice_line.partner_line_id.id)))
#                     #print(line)
#                     #print('/////////////////////////////////////////////////')

#                 else:
#                     part = self.env['res.partner']._find_accounting_partner(inv.partner_id)
#                     line.append((0, 0, self.line_get_convert(l, part.id)))
#                     #print(line)
#                     #print('/////////////////////////////////////////////////')

#             line = inv.group_lines(iml, line)
#             print(line)
#             print('/////////////////////////////////////////////////')

#             journal = inv.journal_id.with_context(ctx)
#             line = inv.finalize_invoice_move_lines(line)
#             print(line)
#             print('/////////////////////////////////////////////////')
#             date = inv.date or inv.date_invoice
#             move_vals = {
#                 'ref': inv.reference,
#                 'line_ids': line,
#                 'journal_id': journal.id,
#                 'date': date,
#                 'narration': inv.comment,
#             }
#             ctx['company_id'] = inv.company_id.id
#             ctx['invoice'] = inv
#             ctx_nolang = ctx.copy()
#             ctx_nolang.pop('lang', None)
#             move = account_move.with_context(ctx_nolang).create(move_vals)
#             # Pass invoice in context in method post: used if you want to get the same
#             # account move reference when creating the same invoice after a cancelled one:
#             move.post()
#             # make the invoice point to that move
#             vals = {
#                 'move_id': move.id,
#                 'date': date,
#                 'move_name': move.name,
#             }
#             inv.with_context(ctx).write(vals)
#         return True

# class AccountInvoiceLine(models.Model):
#     _inherit = "account.invoice.line"

#     partner_line_id = fields.Many2one('res.partner', 'Empresa', domain="[('company_id', '=', parent.company_id)]")
	

#            