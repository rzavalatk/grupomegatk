from odoo import http
from odoo.http import request
from odoo.addons.http_routing.models.ir_http import slug


class Ks_Footer(http.Controller):

    @http.route([
        '/theme_footer/vals',
    ], type='json', auth="public", website=True)
    def Ks_FooterValues(self):
        vals = request.env['theme.footer'].sudo().search([], limit=1)

        categories = request.env['product.public.category'].sudo().browse(vals.mapped("ks_shopping_links").ids)
        links = request.env['theme.links'].sudo().browse(vals.mapped("ks_links").ids).read()
        policy_links = request.env['theme.policy_links'].sudo().browse(vals.mapped("ks_policy").ids).read()
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for category in categories:
            category_url = ("/shop/category/%s" % slug(category))
            category.update({"category_url": category_url})

        for link in links:
            link_img = base_url + "/web/image/theme.links/" + str(link['id']) + "/ks_links_images"
            link.update({
                "link_img": link_img,
            })

        values = {
            "catogries": categories.read(),
            "office_address": vals.ks_office_address.split(","),
            "ks_usefull_links": links,
            "policy_links": policy_links,
        }
        return values
