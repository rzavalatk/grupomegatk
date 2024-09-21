# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request


class TicketSearch(http.Controller):
    """Control para manejar la búsqueda en el portal del cliente
    filtrado por las entradas."""
    @http.route(['/ticketsearch'], type='json', auth="public", website=True)
    def ticket_search(self, **kwargs):
        """ Mostrar la lista de entradas que cumplen la condición de búsqueda.
        Búsqueda de entradas por nombre o asunto"""
        search_value = kwargs.get("search_value")
        tickets = request.env["help.ticket"].search(
            ['|', ('name', 'ilike', search_value),
             ('subject', 'ilike', search_value)])
        values = {
            'tickets': tickets,
        }
        response = http.Response(template='odoo_website_helpdesk.ticket_table',
                                 qcontext=values)
        return response.render()
