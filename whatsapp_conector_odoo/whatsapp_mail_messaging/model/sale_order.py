# -*- coding: utf-8 -*-

from itertools import groupby

from odoo import models, _
from odoo.exceptions import UserError


class Sale(models.Model):
    _inherit = 'sale.order'

    def action_send_whatsapp(self):
        compose_form_id = self.env.ref('whatsapp_mail_messaging.whatsapp_message_wizard_form').id
        ctx = dict(self.env.context)
        message_template = self.company_id.whatsapp_message
        default_message = "Hola" + " " + self.partner_id.name + ',' + '\n' + "Su cotización" + ' ' + self.name + ' ' + "con monto" + ' ' + str(
            self.amount_total) + self.currency_id.symbol + ' ' + "No dude en ponerse en contacto con nosotros si tiene alguna pregunta."
        message = message_template if message_template else default_message
        ctx.update({
            'default_message': message,
            'default_partner_id': self.partner_id.id,
            'default_mobile': self.partner_id.mobile,
            'default_image_1920': self.partner_id.image_1920,
        })
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'whatsapp.message.wizard',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    def check_customers(self, partner_ids):
        partners = groupby(partner_ids)
        return next(partners, True) and not next(partners, False)

    def action_whatsapp_multi(self):
        sale_order_ids = self.env['sale.order'].browse(self.env.context.get('active_ids'))
        partner_ids = []
        for sale in sale_order_ids:
            partner_ids.append(sale.partner_id.id)
        partner_check = self.check_customers(partner_ids)
        if partner_check:
            sale_numbers = sale_order_ids.mapped('name')
            sale_numbers = "\n".join(sale_numbers)
            compose_form_id = self.env.ref('whatsapp_mail_messaging.whatsapp_message_wizard_form').id
            ctx = dict(self.env.context)
            message = "Hola" + " " + self.partner_id.name + ',' + '\n' + "Sus ordenes son" + '\n' + sale_numbers + \
                      ' ' + '\n' + "No dude en ponerse en contacto con nosotros si tiene alguna pregunta."
            ctx.update({
                'default_message': message,
                'default_partner_id': sale_order_ids[0].partner_id.id,
                'default_mobile': sale_order_ids[0].partner_id.mobile,
                'default_image_1920': sale_order_ids[0].partner_id.image_1920,
            })
            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'whatsapp.message.wizard',
                'views': [(compose_form_id, 'form')],
                'view_id': compose_form_id,
                'target': 'new',
                'context': ctx,
            }
        else:
            raise UserError(_(
                'Parece que ha seleccionado pedidos de más de un cliente.'
                'Pruebe a seleccionar pedidos de un único cliente'))
