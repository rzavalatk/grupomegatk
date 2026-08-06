from odoo import _, api, fields, models
from odoo.exceptions import AccessError


class ProductTemplate(models.Model): # clase product.template
    _inherit = "product.template" # hereda de la clase product.template

    owner_company_id = fields.Many2one(
        "res.company",
        string="Compania propietaria",
        default=lambda self: self.env.company,
        readonly=True,
        copy=False,
        help="Solo esta compania puede modificar o eliminar el producto.",
    )

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
        if not self.env.is_superuser():
            for vals in vals_list:
                owner_company_id = vals.get("owner_company_id")
                if owner_company_id and owner_company_id != self.env.company.id:
                    raise AccessError(
                        _(
                            "No puedes crear un producto con una compania propietaria distinta a la compania activa."
                        )
                    )

        for vals in vals_list:
            vals.setdefault("owner_company_id", self.env.company.id)

        products = super().create(vals_list) # crea los registros
        products._sync_single_website_field() # sincroniza el campo website_id para compatibilidad con integraciones que todavia leen ese campo
        return products

    def write(self, vals): # vals es un diccionario
        self._check_company_ownership_access()
        if (
            not self.env.is_superuser()
            and "owner_company_id" in vals
            and any(product.owner_company_id.id != vals["owner_company_id"] for product in self)
        ):
            raise AccessError(
                _("No esta permitido cambiar la compania propietaria del producto.")
            )

        res = super().write(vals) # actualiza los registros
        # Mantiene compatibilidad con integraciones que todavia leen website_id.
        if "website_ids_multi" in vals: # si se actualiza el campo website_ids_multi, sincroniza el campo website_id
            self._sync_single_website_field() # sincroniza el campo website_id para compatibilidad con integraciones que todavia leen ese campo
        return res # devuelve los registros actualizados

    def unlink(self):
        self._check_company_ownership_access()
        return super().unlink()

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

    def _check_company_ownership_access(self):
        """Permite editar/eliminar solo desde la compania propietaria."""
        self._ensure_owner_company()

        if self.env.is_superuser():
            return

        forbidden = self.filtered(
            lambda product: product.owner_company_id and product.owner_company_id != self.env.company
        )
        if forbidden:
            owners = ", ".join(sorted(set(forbidden.mapped("owner_company_id.name"))))
            raise AccessError(
                _(
                    "No puedes modificar productos de otra compania. Cambia a la compania propietaria para editar estos registros: %s"
                )
                % owners
            )

    def _ensure_owner_company(self):
        """Rellena compania propietaria para registros legacy sin propietario."""
        missing_owner = self.filtered(lambda product: not product.owner_company_id)
        for product in missing_owner:
            owner_company = (
                product.company_id
                or product.website_id.company_id
                or product.website_ids_multi[:1].company_id
                or product.create_uid.company_id
                or self.env.company
            )
            product.sudo().owner_company_id = owner_company.id
