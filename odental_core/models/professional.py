from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.osv import expression


class ODentalProfessional(models.Model):
    _name = "odental.professional"
    _description = "Profesional O Dental"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "first_surname, second_surname, first_name, middle_name, name"
    name = fields.Char(string="Nombre del profesional", required=True, tracking=True)
    first_name = fields.Char(string="Primer nombre", tracking=True)
    middle_name = fields.Char(string="Segundo nombre", tracking=True)
    first_surname = fields.Char(string="Primer apellido", tracking=True, index=True)
    second_surname = fields.Char(string="Segundo apellido", tracking=True, index=True)
    professional_code = fields.Char(
        string="Código interno",
        readonly=True,
        copy=False,
        index=True,
        help="Se genera automáticamente. No es necesario memorizarlo para crear citas.",
    )
    active = fields.Boolean(string="Activo", default=True)
    user_id = fields.Many2one(
        "res.users",
        string="Usuario de Odoo",
        tracking=True,
        help="Déjelo vacío si el profesional todavía no tendrá acceso al sistema.",
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Contacto",
        help="Ficha con teléfono, correo electrónico y dirección del profesional.",
    )
    license_number = fields.Char(string="Número de colegiación", tracking=True)
    specialty = fields.Char(string="Especialidad")
    organization_ids = fields.Many2many(
        "odental.organization", "odental_professional_organization_rel",
        "professional_id", "organization_id", required=True,
        string="Organizaciones a las que pertenece",
        help="Clínicas, universidades u otras organizaciones donde este profesional puede atender.",
    )
    company_id = fields.Many2one(
        "res.company", string="Compañía", required=True, default=lambda self: self.env.company, index=True
    )

    _sql_constraints = [
        (
            "professional_code_unique",
            "unique(professional_code)",
            "El código interno del profesional debe ser único.",
        ),
    ]

    @api.model
    def _split_legacy_name(self, value):
        """Conserva nombres anteriores al pasar al formulario estructurado."""
        parts = (value or "").strip().split()
        if not parts:
            return {}
        if len(parts) == 1:
            return {"first_name": parts[0]}
        if len(parts) == 2:
            return {"first_name": parts[0], "first_surname": parts[1]}
        if len(parts) == 3:
            return {
                "first_name": parts[0],
                "first_surname": parts[1],
                "second_surname": parts[2],
            }
        return {
            "first_name": parts[0],
            "middle_name": " ".join(parts[1:-2]),
            "first_surname": parts[-2],
            "second_surname": parts[-1],
        }

    @api.model
    def _compose_name(self, values):
        return " ".join(
            filter(
                None,
                (
                    (values.get("first_name") or "").strip(),
                    (values.get("middle_name") or "").strip(),
                    (values.get("first_surname") or "").strip(),
                    (values.get("second_surname") or "").strip(),
                ),
            )
        )

    def _display_base(self):
        self.ensure_one()
        surnames = " ".join(filter(None, (self.first_surname, self.second_surname)))
        given_names = " ".join(filter(None, (self.first_name, self.middle_name)))
        if surnames and given_names:
            return f"{surnames}, {given_names}"
        return surnames or given_names or self.name

    def _has_homonym(self):
        self.ensure_one()
        origin_id = self._origin.id
        if not origin_id or not self.name:
            return False
        return bool(
            self.search_count(
                [
                    ("id", "!=", origin_id),
                    ("company_id", "=", self.company_id.id),
                    ("name", "=ilike", self.name),
                ],
                limit=1,
            )
        )

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        if not name:
            return super().name_search(name=name, args=args, operator=operator, limit=limit)
        searchable_fields = (
            "name",
            "first_name",
            "middle_name",
            "first_surname",
            "second_surname",
            "specialty",
            "license_number",
            "professional_code",
        )
        search_domain = expression.OR(
            [[(field_name, operator, name)] for field_name in searchable_fields]
        )
        records = self.search(expression.AND([list(args or []), search_domain]), limit=limit)
        return [(record.id, record.display_name) for record in records]

    def _invalidate_homonym_labels(self, names):
        names = [name for name in names if name]
        if not names:
            return
        for company in self.mapped("company_id"):
            self.search(
                [("company_id", "=", company.id), ("name", "in", names)]
            ).invalidate_recordset(["display_name"])

    @api.depends(
        "name",
        "first_name",
        "middle_name",
        "first_surname",
        "second_surname",
        "specialty",
        "license_number",
        "professional_code",
        "company_id",
    )
    def _compute_display_name(self):
        for professional in self:
            label = professional._display_base()
            if professional.specialty:
                label = f"{label} — {professional.specialty}"
            if professional._has_homonym():
                differentiator = (
                    f"colegiación …{professional.license_number[-4:]}"
                    if professional.license_number
                    else professional.professional_code
                )
                if differentiator:
                    label = f"{label} · {differentiator}"
            professional.display_name = label

    @api.onchange("partner_id")
    def _onchange_partner_id_names(self):
        if self.partner_id and not any(
            (self.first_name, self.middle_name, self.first_surname, self.second_surname)
        ):
            parts = self._split_legacy_name(self.partner_id.name)
            for field_name, value in parts.items():
                setattr(self, field_name, value)

    @api.onchange(
        "first_name",
        "middle_name",
        "first_surname",
        "second_surname",
        "organization_ids",
        "company_id",
    )
    def _onchange_warn_homonym(self):
        candidate = self._compose_name(
            {
                "first_name": self.first_name,
                "middle_name": self.middle_name,
                "first_surname": self.first_surname,
                "second_surname": self.second_surname,
            }
        )
        if not candidate or not self.organization_ids:
            return
        domain = [
            ("id", "!=", self._origin.id or 0),
            ("company_id", "=", self.company_id.id),
            ("name", "=ilike", candidate),
            ("organization_ids", "in", self.organization_ids.ids),
        ]
        duplicates = self.search(domain, limit=3)
        if duplicates:
            return {
                "warning": {
                    "title": _("Posible profesional duplicado"),
                    "message": _(
                        "Ya existe un profesional con el mismo nombre en esta organización: %s. "
                        "Verifique el contacto y el número de colegiación antes de guardar."
                    )
                    % ", ".join(duplicates.mapped("display_name")),
                }
            }

    @api.model_create_multi
    def create(self, vals_list):
        prepared = []
        component_fields = {
            "first_name",
            "middle_name",
            "first_surname",
            "second_surname",
        }
        for incoming in vals_list:
            vals = dict(incoming)
            if vals.get("name") and not component_fields.intersection(vals):
                for field_name, value in self._split_legacy_name(vals["name"]).items():
                    vals.setdefault(field_name, value)
            composed_name = self._compose_name(vals)
            if composed_name:
                vals["name"] = composed_name
            prepared.append(vals)
        records = super().create(prepared)
        for record in records.filtered(lambda item: not item.professional_code):
            record.professional_code = f"PRO-{record.id:06d}"
        records._invalidate_homonym_labels(records.mapped("name"))
        return records

    def write(self, vals):
        component_fields = {
            "first_name",
            "middle_name",
            "first_surname",
            "second_surname",
        }
        previous_names = self.mapped("name")
        result = True
        for record in self:
            prepared = dict(vals)
            if prepared.get("name") and not component_fields.intersection(prepared):
                prepared.update(self._split_legacy_name(prepared["name"]))
            if component_fields.intersection(prepared):
                name_values = {
                    field_name: prepared.get(field_name, record[field_name])
                    for field_name in component_fields
                }
                prepared["name"] = self._compose_name(name_values)
            result = super(ODentalProfessional, record).write(prepared) and result
        self._invalidate_homonym_labels(previous_names + self.mapped("name"))
        return result

    @api.constrains("first_name", "first_surname")
    def _check_required_name_parts(self):
        for professional in self:
            if not professional.first_name or not professional.first_surname:
                raise ValidationError(
                    _("Indique al menos el primer nombre y el primer apellido del profesional.")
                )

    @api.constrains("user_id", "partner_id", "license_number", "company_id")
    def _check_unique_identity(self):
        for professional in self:
            base_domain = [
                ("id", "!=", professional.id),
                ("company_id", "=", professional.company_id.id),
            ]
            if professional.user_id and self.search_count(
                base_domain + [("user_id", "=", professional.user_id.id)], limit=1
            ):
                raise ValidationError(
                    _("Este usuario de Odoo ya está vinculado a otro profesional.")
                )
            if professional.partner_id and self.search_count(
                base_domain + [("partner_id", "=", professional.partner_id.id)], limit=1
            ):
                raise ValidationError(
                    _("Este contacto ya está vinculado a otro profesional.")
                )
            normalized_license = (professional.license_number or "").strip().casefold()
            if normalized_license:
                candidates = self.search(
                    base_domain + [("license_number", "!=", False)]
                )
                if any(
                    (candidate.license_number or "").strip().casefold()
                    == normalized_license
                    for candidate in candidates
                ):
                    raise ValidationError(
                        _("El número de colegiación ya pertenece a otro profesional.")
                    )

    def init(self):
        """Asigna un identificador estable a registros creados antes de esta mejora."""
        self.env.cr.execute(
            """
            UPDATE odental_professional
               SET professional_code = 'PRO-' || LPAD(id::text, 6, '0')
             WHERE professional_code IS NULL OR professional_code = ''
            """
        )
