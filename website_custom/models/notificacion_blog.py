from odoo import models, fields, api

class notificacion_blog(models.Model):
    _inherit = ['blog.blog']

    def _check_for_publication(self, vals):
        if vals.get('is_published'):
            for post in self.filtered(lambda p: p.active):
                # Obtenemos el dominio del sitio web asociado al post
                website_domain = post.website_id.domain

                # Construimos la URL completa del post
                url = f"https://{website_domain}/blog/#{slug(object)}/#{slug(post)}"

                # Enviamos un correo con el enlace correcto
                post.blog_id.message_post_with_view(
                    'website_blog.blog_post_template_new_post_blog',
                    subject=post.name,
                    values={'post': post, 'url': url},
                    subtype_id=self.env['ir.model.data']._xmlid_to_res_id('website_blog.mt_blog_blog_published'))
            return True
        return False