# # -*- coding: utf-8 -*-
from odoo import models, fields, api


class Ks_Footer(models.Model):
    _name = "theme.footer"
    _description = "This model let the user select the item for the footer layouts"

    name = fields.Char()
    ks_links = fields.Many2many("theme.links", string="Social Links")
    ks_office_address = fields.Char("Office Address")
    ks_shopping_links = fields.Many2many("product.public.category", string="Shop")
    ks_policy = fields.Many2many("theme.policy_links", string="Policy Links")


class ks_Links(models.Model):
    _name = "theme.links"
    _description = "Maintain the social media links of the website"

    name = fields.Char()
    ks_links_images = fields.Binary("Link Image")
    ks_link_address = fields.Char("Link Redirect Address", required=True)


class ks_Links(models.Model):
    _name = "theme.policy_links"
    _description = "Maintain the social media links of the website"

    name = fields.Char()
    ks_link_address = fields.Char("Link Redirect Address", required=True)
