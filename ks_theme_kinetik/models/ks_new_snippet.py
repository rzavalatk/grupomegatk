# # -*- coding: utf-8 -*-
from odoo import models, fields, api


class Ks_NewSnippet(models.Model):
    _name = 'theme.ks_new_snippet'
    _description = 'Save the custom snippets'

    name = fields.Char("Name",required='true')
    ks_snippet_body = fields.Html('Snippet Html', sanitize=False)
    ks_snippet_css = fields.Text('Snippet Css')
    ks_snippet_thumbnail = fields.Binary("Thumbnail", attachment=True)

    @api.model
    def create(self, values):
        rec = super(Ks_NewSnippet, self).create(values)
        return rec
