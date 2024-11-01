import requests
from odoo import models, fields, api

class BlogPostFacebookPublisher(models.Model):
    _inherit = 'blog.post'

    is_published_facebook = fields.Boolean(default=False, string="Publicado en Facebook")

    @api.model
    def publish_to_facebook(self):
        facebook_page_id = 'YOUR_PAGE_ID'  # ID de tu página de Facebook
        access_token = 'YOUR_ACCESS_TOKEN'  # Token de acceso
        
        # Formatea el contenido que deseas publicar en Facebook
        for post in self.search([('is_published_facebook', '=', False)]):
            message = f"Nuevo blog publicado: {post.name}\n{post.website_url}"
            url = f"https://graph.facebook.com/{facebook_page_id}/feed"
            data = {
                "message": message,
                "access_token": access_token
            }

            # Realiza la solicitud para publicar en Facebook
            response = requests.post(url, data=data)
            if response.status_code == 200:
                post.is_published_facebook = True  # Marcar como publicado en Facebook
            else:
                # Manejo de errores si la publicación falla
                _logger.error("Error al publicar en Facebook: %s", response.json())
