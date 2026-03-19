# -*- coding: utf-8 -*-

from odoo.addons.website.controllers.form import WebsiteForm
from odoo.http import request


class WebsiteFormInherit(WebsiteForm):

    def _is_contact_page_submission(self):
        referrer = (request.httprequest.referrer or '').lower()
        return any(path in referrer for path in ('/contactus', '/contactenos', '/contacto', '/contact-us'))

    def _assign_website_tag_to_lead(self, lead_id):
        if not lead_id or not self._is_contact_page_submission():
            return
        lead = request.env['crm.lead'].sudo().browse(lead_id)
        if not lead.exists():
            return
        website_tag = request.env['crm.tag'].sudo().search([
            ('name', '=', 'Sitio Web')
        ], limit=1)
        if not website_tag or website_tag in lead.tag_ids:
            return
        lead.write({'tag_ids': [(4, website_tag.id)]})

    def _handle_website_form(self, model_name, **kwargs):
        response = super()._handle_website_form(model_name, **kwargs)
        if model_name != 'crm.lead':
            return response
        form_builder_id = request.session.get('form_builder_id')
        self._assign_website_tag_to_lead(form_builder_id)
        return response
