# -*- coding: utf-8 -*-
from odoo import http
from odoo.addons.portal.controllers import portal
from odoo.http import request


class TicketPortal(portal.CustomerPortal):
    """ Controlador para gestionar las acciones relacionadas con el portal del cliente relacionadas con tickets de ayuda.
    """

    def _prepare_home_portal_values(self, counters):
        """Prepara un diccionario de valores que se utilizarán en la vista del portal de inicio
        y obtiene su recuento."""
        values = super()._prepare_home_portal_values(counters)
        if 'ticket_count' in counters:
            ticket_count = request.env['help.ticket'].search_count(
                self._get_tickets_domain()) if request.env[
                'help.ticket'].check_access_rights(
                'read', raise_exception=False) else 0
            values['ticket_count'] = ticket_count
        return values

    def _get_tickets_domain(self):
        """Check al dominio de tickets de ayuda del usuario."""
        return [('customer_id', '=', request.env.user.partner_id.id)]

    @http.route(['/my/tickets'], type='http', auth="user", website=True)
    def portal_my_tickets(self):
        """Vista de tickets de ayuda."""
        domain = self._get_tickets_domain()
        tickets = request.env['help.ticket'].search(domain)
        values = {
            'default_url': "/my/tickets",
            'tickets': tickets,
            'page_name': 'ticket',
        }
        return request.render("odoo_website_helpdesk.portal_my_tickets",
                              values)

    @http.route(['/my/tickets/<int:id>'], type='http', auth="public",
                website=True)
    def portal_tickets_details(self, id):
        """Muestra una lista de tickets para el usuario actual en el portal de
        del usuario."""
        details = request.env['help.ticket'].sudo().search([('id', '=', id)])
        data = {
            'page_name': 'ticket',
            'ticket': True,
            'details': details,
        }
        return request.render("odoo_website_helpdesk.portal_ticket_details",
                              data)

    @http.route('/my/tickets/download/<id>', auth='public',
                type='http',
                website=True)
    def ticket_download_portal(self, id):
        """Descargue la información de la entrada en formato pdf del
         evento."""
        data = {
            'help': request.env['help.ticket'].sudo().browse(int(id))}
        report = request.env.ref(
            'odoo_website_helpdesk.action_report_helpdesk_ticket')
        pdf, _ = request.env.ref(
            'odoo_website_helpdesk.action_report_helpdesk_ticket').sudo()._render_qweb_pdf(
            report, data=data)
        pdf_http_headers = [('Content-Type', 'application/pdf'),
                            ('Content-Length', len(pdf)),
                            ('Content-Disposition',
                             'attachment; filename="Helpdesk Ticket.pdf"')]
        return request.make_response(pdf, headers=pdf_http_headers)


class WebsiteDesk(http.Controller):
    """Control para el manejo del formulario de tickets del helpdesk y su envío."""
    @http.route(['/helpdesk_ticket'], type='http', auth="public",
                website=True, sitemap=True)
    def helpdesk_ticket(self):
        """Renderizar el formulario de tickets."""
        types = request.env['helpdesk.types'].sudo().search([])
        categories = request.env['helpdesk.categories'].sudo().search([])
        product = request.env['product.template'].sudo().search([])
        values = {}
        values.update({
            'types': types,
            'categories': categories,
            'product_website': product
        })
        return request.render('odoo_website_helpdesk.ticket_form', values)

    @http.route(['/rating/<int:ticket_id>'], type='http', auth="public",
                website=True,
                sitemap=True)
    def rating(self, ticket_id):
        """Renderizar el formulario de calificación."""
        ticket = request.env['help.ticket'].browse(ticket_id)
        data = {
            'ticket': ticket.id,
        }
        return request.render('odoo_website_helpdesk.rating_form', data)

    @http.route(['/rating/<int:ticket_id>/submit'], type='http',
                auth="user",
                website=True, csrf=False,
                sitemap=True)
    def rating_backend(self, ticket_id, **post):
        """Renderizar el señal de calificación."""
        ticket = request.env['help.ticket'].browse(ticket_id)
        ticket.write({
            'customer_rating': post['rating'],
            'review': post['message'],
        })
        return request.render('odoo_website_helpdesk.rating_thanks')
