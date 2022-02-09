# -*- coding: utf-8 -*-
from odoo import models, fields, api

class CrmVisits(models.Model):
    _name = "crm.visits"

    @api.one
    def _api_key(self):
        params_system = self.env['ir.config_parameter'].sudo().search([])
        for param in params_system:
            if param.key == "google_maps_api_key":
                self.api_key = param.value

    @api.one
    def _total_time_compute(self):
        if self.timestamp_end_visit and self.timestamp_init_visit:
            self.total_time_compute = self.timestamp_end_visit - self.timestamp_init_visit
            self.write({
                'total_time': self.timestamp_end_visit - self.timestamp_init_visit
            })

    @api.one
    def _view(self):
        if self.timestamp_init_visit:
            self.button_init = True
        else:
            self.button_init = False

        if self.timestamp_end_visit:
            self.button_end = True
        else:
            self.button_end = False

    @api.one
    def _name_doc(self):
        if self.tipo_id.name:
            self.name = self.tipo_id.name


    name = fields.Char("Título de oportunidad",compute=_name_doc)
    tipo_soporte = fields.Selection([
		('follow_up', 'Seguimiento'),
		('repair', 'Reparación'),
		('study', 'Estudio'),
		('delivery', 'Entrega de producto'),
		('demonstration', 'Demostración de producto'),
		('delivery_invoice', 'Entrega de facturas o cotización'),
		],string="Tipo de visita",required=True)
    user_id = fields.Many2one("res.users", "Comercial",
                              default=lambda self: self.env.user)
    pertner_id = fields.Many2one("res.partner", "Cliente")
    new_partner = fields.Boolean("Nuevo cliente")
    partner_name = fields.Char("Nombre del cliente",default="")
    partner_phone = fields.Char("Teléfono del cliente",default="")
    partner_email = fields.Char("Email del cliente",default="")
    tipo_id = fields.Many2one(
        'crm.lead.tipo', string='Tipo de oportunidad', required=True)
    currency_id = fields.Many2one(
        "res.currency", default=lambda self: self.env.user.currency_id)
    opportunity_id = fields.Many2one("crm.lead")
    planned_revenue = fields.Monetary(string='Ingreso estimado', store=True)
    api_key = fields.Char(compute=_api_key)
    total_time_compute = fields.Char("Tiempo", compute=_total_time_compute)
    total_time = fields.Char()
    lat_init_visit = fields.Float(
        "Latitud inicial", digits=(4, 15), readonly=True)
    lng_init_visit = fields.Float(
        "Longitud inicial", digits=(4, 15), readonly=True)
    lat_end_visit = fields.Float(
        "Latitud final", digits=(4, 15), readonly=True)
    lng_end_visit = fields.Float(
        "Longitud final", digits=(4, 15), readonly=True)
    timestamp_init_visit = fields.Datetime(
        "Fecha y hora inicial", readonly=True)
    timestamp_end_visit = fields.Datetime("Fecha y hora final", readonly=True)
    button_init = fields.Boolean(compute=_view, default=False)
    button_end = fields.Boolean(compute=_view, default=False)
    saved = fields.Boolean(default=False)
    create_opportunity = fields.Boolean(default=False)
    state_visit = fields.Selection([
		('in_visit', 'En visita'),
		('in_opportunity', 'En oportunidad')
		],string="Estado de la visita",default='in_visit')
    description = fields.Text("Notas internas")


    @api.model
    def create(self, vals):
        vals['saved'] = True
        if not vals['tipo_soporte']:
            vals['tipo_soporte'] = 'visita'
        res = super(CrmVisits, self).create(vals)
        return res

    def go_to_opportunity(self):
        return {
            'name': self.tipo_id.name,
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'crm.lead',
            'res_id': self.opportunity_id.id, 
        }


    @api.multi
    def open_wizard(self):
        current_website = self.env['website'].get_current_website()
        return current_website.id


    @api.multi
    @api.one
    def create_chance(self):
        vals = {
            "user_id": self.user_id.id,
            "tipo_id": self.tipo_id.id,
            "planned_revenue": self.planned_revenue,
            "description": self.description,
            "name": self.tipo_id.name,
            "type": 'opportunity',
        }
        if self.new_partner:
            price = self.env['product.pricelist'].sudo().search([('name','=','Precio A 10%')])
            partner = {
                'name': self.partner_name,
                'phone': self.partner_phone,
                'email': self.partner_email,
                "user_id": self.user_id.id,
                'company_type': 'company',
                'property_product_pricelist': price[0].id
            }
            partner_id = self.env['res.partner'].create(partner)
            vals['partner_id'] = partner_id.id
        else:
            vals['partner_id'] = self.pertner_id.id
        opportunity_id = self.env['crm.lead'].create(vals)
        write = {
            "opportunity_id": opportunity_id.id,
            "create_opportunity": True,
            "state_visit": 'in_opportunity'
        }
        if self.new_partner:
            write['pertner_id'] = vals['partner_id']
            write['new_partner'] = False
        self.write(write)
        return self.go_to_opportunity()
        
        