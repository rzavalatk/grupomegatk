# Tu módulo: models/blog_post.py
from odoo import models, fields
from odoo.addons.http_routing.models.ir_http import slug

class BlogPost(models.Model):
    _inherit = 'blog.post'

    def _compute_website_url(self):
        """
        Extiende el método para computar la URL del sitio web de la publicación de blog
        y asegurar que incluya el dominio del sitio web correcto.
        """
        super(BlogPost, self)._compute_website_url()
        for blog_post in self:
            # Obtiene el dominio del website asociado con el blog
            domain = blog_post.website_id.domain if blog_post.website_id else ''
            # Genera la URL absoluta del blog post
            blog_post.website_url = "%s/blog/%s/%s" % (domain, slug(blog_post.blog_id), slug(blog_post))
