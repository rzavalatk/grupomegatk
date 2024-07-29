from odoo import models, fields, api, slug

class notificion_blog(models.Model):
    _inherit = ['blog.blog']

    #def get_blog_url(self):
    #    if self.website_id.name == 'megatk':
    #        return 'https://www.megatk.net/blog/' + slug(self)
    #    else:
    #        return 'https://www.meditekhn.net/blog/' + slug(self)

    def _check_for_publication(self, vals):
        if vals.get('is_published'):
            for post in self.filtered(lambda p: p.active):
                post.blog_id.message_post_with_view(
                    'website_blog.blog_post_template_new_post_blog',
                    subject=post.name,
                    values={'post': post},
                    subtype_id=self.env['ir.model.data']._xmlid_to_res_id('website_blog.mt_blog_blog_published'))
            return True
        return False