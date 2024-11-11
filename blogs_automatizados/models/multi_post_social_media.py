import requests
from odoo import models, fields, api

class BlogPostFacebookPublisher(models.Model):
    _inherit = 'blog.post'

    is_published_facebook = fields.Boolean(default=False, string="Publicado en Facebook")
    
    @api.model
    def publish_to_facebook(self):
        # Obtener el nombre del blog o página de origen
        blog_name = self.env['website_blog.blog'].search([('id', '=', self.id)]).name

        # Establecer la página de Facebook dependiendo del blog o página de origen
        if blog_name == 'Blog megatk':
            facebook_page_id = 'ID_DE_LA_PAGINA_MEGATK'
            access_token = 'TOKEN_DE_ACCESO_MEGATK'
        elif blog_name == 'Blog meditekhn':
            facebook_page_id = 'ID_DE_LA_PAGINA_MEDITEKHN'
            access_token = 'TOKEN_DE_ACCESO_MEDITEKHN'
        else:
            # Manejo de errores si no se encuentra la página de Facebook correspondiente
            self._logger.error("No se encontró la página de Facebook correspondiente para el blog %s", blog_name)
            return

        # Formatear el contenido que deseas publicar en Facebook
        for post in self.env['blog.post'].search([('is_published_facebook', '=', False)]):
            message = f"Nuevo blog publicado: {post.name}\n{post.website_url}"
            url = f"https://graph.facebook.com/{facebook_page_id}/feed"
            data = {
                "message": message,
                "access_token": access_token
            }

            # Realizar la solicitud para publicar en Facebook
            response = requests.post(url, data=data)
            if response.status_code == 200:
                post.is_published_facebook = True  # Marcar como publicado en Facebook
            else:
                # Manejo de errores si la publicación falla
                self._logger.error("Error al publicar en Facebook: %s", response.json())