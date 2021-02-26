# # -*- coding: utf-8 -*-
from odoo import models, fields, api


class Ks_RecentlyViewedProducts(models.Model):
    _inherit = 'res.users'
    _description = 'Adding product template to res users'

    ks_viewed_products = fields.Many2many("product.template",'product_template_res_user',
                                          'res_user_id', 'product_template_id')


class Ks_Rating_avg(models.Model):
    _inherit = 'product.template'
    _description = 'Rating for recently view products'

    rating_count = fields.Integer('Rating count', compute="_compute_rating_stats")
    rating_avg = fields.Float("Rating Average", compute='_compute_rating_stats')

    @api.depends('rating_ids')
    def _compute_rating_stats(self):
        """ Compute avg and count in one query, as thoses fields will be used together most of the time. """
        domain = self._rating_domain()
        read_group_res = self.env['rating.rating'].read_group(domain + [('rating', '>=', 1)], ['rating:avg'], groupby=['res_id'],
                                                              lazy=False)
        read_group_res_count = self.env['rating.rating'].read_group(domain, ['rating:avg'], groupby=['res_id'],
                                                              lazy=False)
        # force average on rating column
        mapping = {item['res_id']: {'rating_avg': item['rating']} for item in read_group_res}
        mapping_count = {item['res_id']: {'rating_count': item['__count']} for item in read_group_res_count}

        for record in self:
            record.rating_count = mapping_count.get(record.id, {}).get('rating_count', 0)
            record.rating_avg = mapping.get(record.id, {}).get('rating_avg', 0)

    def _rating_domain(self):
        """ Returns a normalized domain on rating.rating to select the records to
            include in count, avg, ... computation of current model.
        """
        return ['&', '&', ('res_model', '=', self._name), ('res_id', 'in', self.ids), ('consumed', '=', True), ('website_published', '=', True)]

class Ks_ProductTemplate(models.Model):
    _inherit = 'product.template'
    _description = 'Adding users to products'

    ks_products_templates = fields.Many2many("res.users",'product_template_res_users')


class ks_RcentlyViewedRel(models.Model):
    _name = "product.template.res.users"
    _description = 'A rel table for user and their recently viewed products'

    product_template_id = fields.Many2one("product.template")
    res_user_id = fields.Many2one("res.users")
    recently_viewed_date = fields.Datetime(default=fields.Datetime.now())


class KSBRAND(models.Model):
    _inherit = 'ks_product_manager.ks_brand'
    _description = 'Adding website id to brands'

    website_id = fields.Many2one('website', string="website", store=True)

class KSPRODUCTVIDEO(models.Model):
    _inherit = 'product.image'
    _description = 'Adding website id to brands'

    product_video = fields.Binary("Video in Mp4", attachment=True)



class product_template(models.Model):
    _inherit = 'product.template'

    size_chart = fields.Binary(help="", string='Size Chart', attachment=True)
    size_chart_name = fields.Char()
