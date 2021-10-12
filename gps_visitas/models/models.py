# -*- coding: utf-8 -*-

from odoo import models, fields, api

class CrmStage(models.Model):
    _inherit = 'crm.stage'

    control_visit = fields.Boolean(string="Controlar visitas")


class CrmVisits(models.Model):
    _name = "crm.visits"

    @api.model
    def create(self, vals):
        res = super(CrmVisits, self).create(vals)
        res.write({
            "client_name": res.id_visit.partner_id.name,
            "user_name": res.id_visit.user_id.name,
            "company_id": res.id_visit.company_id.id,
        })
        id = self.env.context.get("rec", False)
        recod = self.env['crm.lead'].browse(id)
        recod.write({
            "last_link": res.id
        })
        return res

    @api.model
    def write(self, vals):
        res = super(CrmVisits, self).write(vals)
        if 'timestamp_end_visit' in vals:
            self.total_time = self.timestamp_end_visit - self.timestamp_init_visit
        return res
    

    @api.one
    def _api_key(self):
        params_system = self.env['ir.config_parameter'].sudo().search([])
        for param in params_system:
            if param.key == "google_maps_api_key":
                self.api_key = param.value


    id_visit = fields.Many2one("crm.lead", "Oportunidad")
    company_id = fields.Many2one("res.company", "Compañia")
    api_key = fields.Char(compute=_api_key)
    client_name = fields.Char("Cliente")
    user_name = fields.Char("Comercial")
    total_time = fields.Char("Tiempo")
    lat_init_visit = fields.Float("Lat inicial", digits=(4, 15))
    lng_init_visit = fields.Float("Lng inicial", digits=(4, 15))
    lat_end_visit = fields.Float("Lat final", digits=(4, 15))
    lng_end_visit = fields.Float("Lng final", digits=(4, 15))
    timestamp_init_visit = fields.Datetime("Fecha y hora inicial")
    timestamp_end_visit = fields.Datetime("Fecha y hora final")

    @api.multi
    def visits_filter_by_company(self):
        return {
            'name': "Visitas",
            'type': 'ir.actions.act_window',
            'res_model': 'crm.visits',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'domain': [('company_id', '=', self.env.user.company_id.id)],
            'target': 'current',
        }


class CrmStage(models.Model):
    _inherit = 'crm.lead'

    @api.one
    def _see_init_visit(self):
        if self.stage_id.control_visit:
            self.see_init_visit = True
        else:
            self.see_init_visit = False
        print(self.see_init_visit)

    @api.one
    def _num_visits(self):
        self.num_visits = len(self.visits)

    see_init_visit = fields.Boolean(compute=_see_init_visit)
    see_end_visit = fields.Boolean(default=False)
    num_visits = fields.Integer(compute=_num_visits)
    last_link = fields.Integer()
    visits = fields.One2many('crm.visits', 'id_visit', string="Visitas")

    @api.multi
    def write_init(self, vals):
        obj = self.with_context(rec=self.id).write({
            "visits": [(0, 0, vals)],
            "see_end_visit": True
        })
        return obj

    def write_end(self, vals):
        obj = {}
        if self.last_link:
            obj = self.sudo().write({
                "visits": [(1, self.last_link, vals)],
                "see_end_visit": False
            })
        else:
            obj = self.sudo().write({
                "see_end_visit": False
            })
        return obj

    @api.multi
    def go_to_visits_filter(self):
        return {
            'name': "Visitas "+self.user_id.name,
            'view_mode': 'tree,form',
            'res_model': 'crm.visits',
            'type': 'ir.actions.act_window',
            'domain': [('id_visit', '=', self.id)],
        }


    @api.multi
    def open_wizard(self):
        current_website = self.env['website'].get_current_website()
        return current_website.id


