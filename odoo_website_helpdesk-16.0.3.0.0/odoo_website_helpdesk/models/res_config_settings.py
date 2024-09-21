# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """Esta clase amplía la funcionalidad del modelo 'res.config.settings'
     para proporcionar opciones de configuración para varias configuraciones relacionadas con el
     módulo de soporte tecnico.
   """
    _inherit = 'res.config.settings'

    show_create_task = fields.Boolean(
        string="Crear Tares",
        config_parameter='odoo_website_helpdesk.show_create_task',
        help='Al habilitar este campo puedes crear una tarea debajo del ticket')
    show_category = fields.Boolean(
        string="Categoria",
        config_parameter='odoo_website_helpdesk.show_category',
        help='Al habilitar esto se muestra la categoría del boleto.',
        implied_group='odoo_website_helpdesk.group_show_category')
    product_website = fields.Boolean(
        string="Producto en sitio web",
        config_parameter='odoo_website_helpdesk.product_website',
        help='Al habilitar esta función, puede mencionar el producto en el sitio web'
             ' en el momento de crear el ticketProduct en el sitio web')
    auto_close_ticket = fields.Boolean(
        string="Ticket de cierre automático",
        config_parameter='odoo_website_helpdesk.auto_close_ticket',
        help='Cerrar ticket automáticamente si se cumple la condición')
    no_of_days = fields.Integer(
        string="Número de días",
        config_parameter='odoo_website_helpdesk.no_of_days',
        help='Después de esta fecha el ticket se cerrará automáticamente.')
    closed_stage = fields.Many2one(
        'ticket.stage', string='Etapa de cierre',
        help='Etapa de cierre',
        config_parameter='odoo_website_helpdesk.closed_stage')

    reply_template_id = fields.Many2one(
        'mail.template',
        string='ID retransmitida',
        domain="[('model', '=', 'help.ticket')]",
        config_parameter='odoo_website_helpdesk.reply_template_id',
        help='Plantilla de respuesta')
    helpdesk_menu_show = fields.Boolean(
        string='Soporte tecnico Menu',
        config_parameter='odoo_website_helpdesk.helpdesk_menu_show',
        help='Al habilitar esta opción para hacer visible el menú de soporte técnico en el sitio web')

    @api.onchange('closed_stage')
    def closed_stage_a(self):
        """Este método se activa cuando se cambia el campo 'closed_stage'.
         Actualiza el atributo 'closing_stage' de la etapa seleccionada y
         lo borra para otras etapas.
       """
        stage = self.closed_stage.id
        in_stage = self.env['ticket.stage'].search([('id', '=', stage)])
        not_in_stage = self.env['ticket.stage'].search([('id', '!=', stage)])
        in_stage.closing_stage = True
        for each in not_in_stage:
            each.closing_stage = False

    @api.constrains('show_category')
    def show_category_subcategory(self):
        """ Este método de restricción se activa cuando el campo 'show_category'
        está cambiado. Actualiza los usuarios en 'group_show_category' según
        el valor 'show_category'.
       """
        if self.show_category:
            group_cat = self.env.ref(
                'odoo_website_helpdesk.group_show_category')
            group_cat.write({
                'users': [(4, self.env.user.id)]
            })
        else:
            group_cat = self.env.ref(
                'odoo_website_helpdesk.group_show_category')
            group_cat.write({
                'users': [(5, False)]
            })
