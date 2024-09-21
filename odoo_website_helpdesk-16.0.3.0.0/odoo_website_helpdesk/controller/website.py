# -*- coding: utf-8 -*-

import base64
import json
from odoo import _, http
from psycopg2 import IntegrityError
from odoo.http import request
from odoo.exceptions import ValidationError
from odoo.addons.website.controllers.form import WebsiteForm


class HelpdeskProduct(http.Controller):
    """Controla los productos del sitio web y devuelve el producto."""
    @http.route('/product', auth='public', type='json')
    def product(self):
        """Product control function"""
        products = request.env['product.template'].sudo().search_read([],
                                                                      ['name',
                                                                       'id'])
        return products


class WebsiteFormInherit(WebsiteForm):
    """Este módulo amplía la funcionalidad del controlador de formularios del sitio web
    para gestionar la creación de nuevos tickets de ayuda. Proporciona un nuevo
    controlador para mostrar una lista de tickets para el usuario actual en su
    usuario actual en su portal, y anula el método del controlador del formulario del sitio web
    para crear un nuevo ticket de help desk."""
    def _handle_website_form(self, model_name, **kwargs):
        
        customer = request.env.user.partner_id
        if model_name == 'help.ticket':
            tickets = request.env['ticket.stage'].search([])
            for rec in tickets:
                sequence = tickets.mapped('sequence')
                lowest_sequence = tickets.filtered(
                    lambda x: x.sequence == min(sequence))
                if rec == lowest_sequence:
                    lowest_stage_id = lowest_sequence
            products = kwargs.get('product')
            if products:
                splited_product = products.split(',')
                product_list = [int(i) for i in splited_product]
                rec_val = {
                    'customer_name': kwargs.get('customer_name'),
                    'subject': kwargs.get('subject'),
                    'description': kwargs.get('description'),
                    'email': kwargs.get('email_from'),
                    'phone': kwargs.get('phone'),
                    'priority': kwargs.get('priority'),
                    'product_ids': product_list,
                    'stage_id': lowest_stage_id.id,
                    'customer_id': customer.id,
                    'ticket_type': kwargs.get('ticket_type'),
                    'category_id': kwargs.get('category'),
                }
                ticket_id = request.env['help.ticket'].sudo().create(rec_val)
                request.session['ticket_number'] = ticket_id.name
                request.session['ticket_id'] = ticket_id.id
                model_record = request.env['ir.model'].sudo().search(
                    [('model', '=', model_name)])
                data = self.extract_data(model_record, request.params)
                if ('ticket_attachment' in request.params or
                        request.httprequest.files or data.get(
                        'attachments')):
                    attached_files = data.get('attachments')
                    for attachment in attached_files:
                        attached_file = attachment.read()
                        request.env['ir.attachment'].sudo().create({
                            'name': attachment.filename,
                            'res_model': 'help.ticket',
                            'res_id': ticket_id.id,
                            'type': 'binary',
                            'datas': base64.encodebytes(attached_file),
                        })
                request.session[
                    'form_builder_model_model'] = model_record.model
                request.session['form_builder_model'] = model_record.name
                request.session['form_builder_id'] = ticket_id.id
                return json.dumps({'id': ticket_id.id})
            else:
                rec_val = {
                    'customer_name': kwargs.get('customer_name'),
                    'subject': kwargs.get('subject'),
                    'description': kwargs.get('description'),
                    'email': kwargs.get('email_from'),
                    'phone': kwargs.get('phone'),
                    'priority': kwargs.get('priority'),
                    'stage_id': lowest_stage_id.id,
                    'customer_id': customer.id,
                    'ticket_type': kwargs.get('ticket_type'),
                    'category_id': kwargs.get('category'),
                }
                ticket_id = request.env['help.ticket'].sudo().create(rec_val)
                request.session['ticket_number'] = ticket_id.name
                request.session['ticket_id'] = ticket_id.id
                model_record = request.env['ir.model'].sudo().search(
                    [('model', '=', model_name)])
                data = self.extract_data(model_record, request.params)
                if ('ticket_attachment' in request.params or
                        request.httprequest.files or data.get(
                        'attachments')):
                    attached_files = data.get('attachments')
                    for attachment in attached_files:
                        attached_file = attachment.read()
                        request.env['ir.attachment'].sudo().create({
                            'name': attachment.filename,
                            'res_model': 'help.ticket',
                            'res_id': ticket_id.id,
                            'type': 'binary',
                            'datas': base64.encodebytes(attached_file),
                        })
                request.session['form_builder_model_model'] = model_record.model
                request.session['form_builder_model'] = model_record.name
                request.session['form_builder_id'] = ticket_id.id
                return json.dumps({'id': ticket_id.id})
        else:
            model_record = request.env['ir.model'].sudo().search(
                [('model', '=', model_name)])
            if not model_record:
                return json.dumps({
                    'error': _("The form's specified model does not exist")
                })
            try:
                data = self.extract_data(model_record, request.params)
            
            except ValidationError as e:
                return json.dumps({'error_fields': e.args[0]})
            try:
                id_record = self.insert_record(request, model_record,
                                               data['record'], data['custom'],
                                               data.get('meta'))
                if id_record:
                    self.insert_attachment(model_record, id_record,
                                           data['attachments'])
                    
                    if model_name == 'mail.mail':
                        request.env[model_name].sudo().browse(id_record).send()

            
            except IntegrityError:
                return json.dumps(False)
            request.session['form_builder_model_model'] = model_record.model
            request.session['form_builder_model'] = model_record.name
            request.session['form_builder_id'] = id_record
            return json.dumps({'id': id_record})
