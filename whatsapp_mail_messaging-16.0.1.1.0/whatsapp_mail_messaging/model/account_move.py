# -*- coding: utf-8 -*-

from itertools import groupby

from odoo import models, _
from odoo.exceptions import UserError


class Account(models.Model):
    _inherit = 'account.move'

    def action_send_whatsapp(self):
        compose_form_id = self.env.ref(
            'whatsapp_mail_messaging.whatsapp_message_wizard_form').id
        ctx = dict(self.env.context)
        message_template = self.company_id.whatsapp_message
        default_message = "Hola" + " " + self.partner_id.name + ',' + '\n' + "Esta es su factura con numero" + ' ' + self.internal_number + ' ' + "con monto" + ' ' + str(
            self.amount_total) + self.currency_id.symbol + ' ' + "de " + self.company_id.name + ". Le rogamos remita el pago lo antes posible. " + '\n' + \
                  "Por favor, utilice la siguiente comunicación para su pago" + ' ' + self.name
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
        account_move_ids = self.env['account.move'].browse(
            self.env.context.get('active_ids'))
        partner_ids = []
        for account_move in account_move_ids:
            partner_ids.append(account_move.partner_id.id)
        partner_check = self.check_customers(partner_ids)
        if partner_check:
            account_move_numbers = account_move_ids.mapped('name')
            account_move_numbers = "\n".join(account_move_numbers)
            compose_form_id = self.env.ref(
                'whatsapp_mail_messaging.whatsapp_message_wizard_form').id
            ctx = dict(self.env.context)
            message = "Hola" + " " + self.partner_id.name + ',' + '\n' + "Sus pedidos son" + '\n' + account_move_numbers + \
                      ' ' + "No dude en ponerse en contacto con nosotros si tiene alguna pregunta."
            ctx.update({
                'default_message': message,
                'default_partner_id': account_move_ids[0].partner_id.id,
                'default_mobile': account_move_ids[0].partner_id.mobile,
                'default_image_1920': account_move_ids[0].partner_id.image_1920,
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
                'Parece que ha seleccionado Facturas de más de un cliente.'
                'Intente seleccionar las facturas de un único cliente'))
