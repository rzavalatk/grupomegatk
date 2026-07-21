from odoo import api, fields, models


class ProductTemplate(models.Model): 
    _inherit = "product.template" # hereda de la clase product.template

    website_ids_multi = fields.Many2many(
        "website", # modelo de destino de la relacion
        "product_template_website_multi_rel", # tabla intermedia que relaciona productos y sitios web
        "product_tmpl_id", #columna que apunta al id del producto
        "website_id", #columna que apunta al id del sitio web
        string="Sitios web", # nombre de la relacion
        help="Si se deja vacio, el producto queda disponible para todos los sitios.", # ayuda
    )

    @api.model_create_multi # permite crear multiples registros
    def create(self, vals_list): # vals_list es una lista de diccionarios
        products = super().create(vals_list) # crea los registros
        products._sync_single_website_field() # sincroniza el campo website_id para compatibilidad con integraciones que todavia leen ese campo
        return products

    def write(self, vals): # vals es un diccionario
        res = super().write(vals) # actualiza los registros
        # Mantiene compatibilidad con integraciones que todavia leen website_id.
        if "website_ids_multi" in vals: # si se actualiza el campo website_ids_multi, sincroniza el campo website_id
            self._sync_single_website_field() # sincroniza el campo website_id para compatibilidad con integraciones que todavia leen ese campo
        return res # devuelve los registros actualizados

    def _sync_single_website_field(self): # sincroniza el campo website_id
        """Sincroniza website_id desde website_ids_multi para compatibilidad.

        - 1 sitio seleccionado: se escribe ese mismo valor en website_id.
        - 0 o mas de 1: website_id queda vacio para evitar inconsistencias.
        """
        for product in self: # recorre los registros de productos
            if len(product.website_ids_multi) == 1: # si hay 1 sitio seleccionado
                product.website_id = product.website_ids_multi.id # se escribe ese mismo valor en website_id
            else: # si hay 0 o mas de 1
                product.website_id = False # website_id queda vacio para evitar inconsistencias
