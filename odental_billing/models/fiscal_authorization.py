import re

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class ODentalFiscalAuthorization(models.Model):
    _name = "odental.fiscal.authorization"
    _description = "Autorización fiscal SAR O Dental"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_limit desc, id desc"

    name = fields.Char(default="Nueva autorización", required=True, tracking=True)
    organization_id = fields.Many2one(
        "odental.organization", required=True, ondelete="restrict", index=True, tracking=True
    )
    company_id = fields.Many2one(
        "res.company", string="Compañía emisora", required=True, ondelete="restrict", index=True
    )
    site_id = fields.Many2one(
        "odental.site", string="Sede / establecimiento", required=True, ondelete="restrict"
    )
    journal_id = fields.Many2one(
        "account.journal",
        string="Diario de ventas",
        required=True,
        ondelete="restrict",
        domain="[('type', '=', 'sale'), ('company_id', '=', company_id)]",
    )
    cai = fields.Char(
        string="CAI",
        required=True,
        copy=False,
        tracking=True,
        help="Clave otorgada por SAR. O Dental nunca genera ni inventa este valor.",
    )
    document_type = fields.Selection(
        [
            ("01", "Factura"),
            ("04", "Recibo por honorarios profesionales"),
            ("07", "Nota de crédito"),
        ],
        required=True,
        default="01",
        tracking=True,
    )
    establishment_code = fields.Char(
        string="Establecimiento", required=True, size=3, default="000"
    )
    emission_point_code = fields.Char(
        string="Punto de emisión", required=True, size=3, default="001"
    )
    range_start = fields.Integer(string="Inicio autorizado", required=True, default=1)
    range_end = fields.Integer(string="Fin autorizado", required=True)
    next_number = fields.Integer(
        string="Siguiente correlativo", required=True, default=1, copy=False, tracking=True
    )
    date_from = fields.Date(string="Vigente desde", required=True, default=fields.Date.context_today)
    date_limit = fields.Date(string="Fecha límite de emisión", required=True, tracking=True)
    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("active", "Activa"),
            ("exhausted", "Agotada"),
            ("expired", "Vencida"),
            ("revoked", "Revocada"),
        ],
        required=True,
        default="draft",
        tracking=True,
        index=True,
    )
    remaining_count = fields.Integer(compute="_compute_remaining_count")
    range_display = fields.Char(compute="_compute_range_display")
    notes = fields.Text()

    _sql_constraints = [
        (
            "company_cai_document_unique",
            "unique(company_id, cai, document_type)",
            "Esta autorización ya está registrada para la compañía y tipo de documento.",
        ),
    ]

    @api.depends("next_number", "range_end", "state")
    def _compute_remaining_count(self):
        for authorization in self:
            authorization.remaining_count = (
                max(authorization.range_end - authorization.next_number + 1, 0)
                if authorization.state in {"draft", "active"}
                else 0
            )

    @api.depends(
        "establishment_code", "emission_point_code", "document_type", "range_start", "range_end"
    )
    def _compute_range_display(self):
        for authorization in self:
            prefix = authorization._document_prefix()
            authorization.range_display = (
                f"{prefix}-{authorization.range_start:08d} a {prefix}-{authorization.range_end:08d}"
                if prefix and authorization.range_start and authorization.range_end
                else False
            )

    def _document_prefix(self):
        self.ensure_one()
        if not self.establishment_code or not self.emission_point_code or not self.document_type:
            return False
        return f"{self.establishment_code}-{self.emission_point_code}-{self.document_type}"

    @api.constrains("establishment_code", "emission_point_code")
    def _check_codes(self):
        for authorization in self:
            if not re.fullmatch(r"\d{3}", authorization.establishment_code or ""):
                raise ValidationError("El código de establecimiento debe contener tres dígitos.")
            if not re.fullmatch(r"\d{3}", authorization.emission_point_code or ""):
                raise ValidationError("El punto de emisión debe contener tres dígitos.")

    @api.constrains("range_start", "range_end", "next_number")
    def _check_range(self):
        for authorization in self:
            if authorization.range_start < 1 or authorization.range_end > 99999999:
                raise ValidationError("El rango debe estar entre 00000001 y 99999999.")
            if authorization.range_end < authorization.range_start:
                raise ValidationError("El fin del rango no puede ser menor que el inicio.")
            if not authorization.range_start <= authorization.next_number <= authorization.range_end + 1:
                raise ValidationError("El siguiente correlativo está fuera del rango autorizado.")

    @api.constrains("date_from", "date_limit")
    def _check_dates(self):
        for authorization in self:
            if authorization.date_limit < authorization.date_from:
                raise ValidationError("La fecha límite no puede ser anterior al inicio de vigencia.")

    @api.constrains("organization_id", "company_id", "site_id", "journal_id")
    def _check_scope(self):
        for authorization in self:
            organization = authorization.organization_id
            allowed_companies = organization.company_id | organization.mapped(
                "professional_ids.billing_company_id"
            )
            if authorization.company_id not in allowed_companies:
                raise ValidationError(
                    "La compañía emisora no pertenece a la organización ni a uno de sus profesionales."
                )
            if not authorization.site_id.is_available_to(organization):
                raise ValidationError("La sede no está disponible para esta organización.")
            if authorization.journal_id.company_id != authorization.company_id:
                raise ValidationError("El diario debe pertenecer a la compañía emisora.")
            if authorization.journal_id.type != "sale":
                raise ValidationError("La autorización fiscal requiere un diario de ventas.")

    def write(self, vals):
        protected = {
            "organization_id",
            "company_id",
            "site_id",
            "journal_id",
            "cai",
            "document_type",
            "establishment_code",
            "emission_point_code",
            "range_start",
            "range_end",
            "date_from",
            "date_limit",
            "next_number",
        }
        if not self.env.context.get("allow_fiscal_transition"):
            if "state" in vals:
                raise UserError("Utilice las acciones de la autorización para cambiar su estado.")
            if protected.intersection(vals) and any(record.state != "draft" for record in self):
                raise UserError("Una autorización activada no puede modificarse.")
        return super().write(vals)

    def unlink(self):
        if any(record.state != "draft" for record in self):
            raise UserError("Solo se pueden eliminar autorizaciones en borrador.")
        return super().unlink()

    def action_activate(self):
        today = fields.Date.context_today(self)
        for authorization in self:
            if authorization.state != "draft":
                raise UserError("Solo una autorización en borrador puede activarse.")
            if not authorization.cai.strip():
                raise ValidationError("Ingrese el CAI exactamente como fue emitido por SAR.")
            if not authorization.date_from <= today <= authorization.date_limit:
                raise ValidationError("La autorización no está vigente en la fecha actual.")
            if authorization.next_number > authorization.range_end:
                raise ValidationError("El rango autorizado ya está agotado.")
            overlapping = self.search_count(
                [
                    ("id", "!=", authorization.id),
                    ("company_id", "=", authorization.company_id.id),
                    ("journal_id", "=", authorization.journal_id.id),
                    ("document_type", "=", authorization.document_type),
                    ("state", "=", "active"),
                ]
            )
            if overlapping:
                raise ValidationError(
                    "Ya existe una autorización activa para este diario y tipo de documento."
                )
            authorization.with_context(allow_fiscal_transition=True).write({"state": "active"})

    def action_revoke(self):
        for authorization in self:
            if authorization.state not in {"active", "expired", "exhausted"}:
                raise UserError("Esta autorización no puede revocarse.")
            authorization.with_context(allow_fiscal_transition=True).write({"state": "revoked"})

    def action_refresh_status(self):
        today = fields.Date.context_today(self)
        for authorization in self.filtered(lambda item: item.state == "active"):
            new_state = False
            if authorization.date_limit < today:
                new_state = "expired"
            elif authorization.next_number > authorization.range_end:
                new_state = "exhausted"
            if new_state:
                authorization.with_context(allow_fiscal_transition=True).write(
                    {"state": new_state}
                )

    def _allocate_number(self, issue_date=None):
        self.ensure_one()
        issue_date = fields.Date.to_date(issue_date or fields.Date.context_today(self))
        self.env.cr.execute(
            "SELECT id FROM odental_fiscal_authorization WHERE id = %s FOR UPDATE",
            [self.id],
        )
        authorization = self.browse(self.id)
        authorization.invalidate_recordset(
            ["state", "next_number", "range_start", "range_end", "date_from", "date_limit"]
        )
        if authorization.state != "active":
            raise ValidationError("La autorización fiscal seleccionada no está activa.")
        if not authorization.date_from <= issue_date <= authorization.date_limit:
            raise ValidationError("La fecha de emisión está fuera de la vigencia autorizada.")
        if authorization.next_number > authorization.range_end:
            authorization.with_context(allow_fiscal_transition=True).write({"state": "exhausted"})
            raise ValidationError("El rango fiscal seleccionado está agotado.")
        sequential = authorization.next_number
        new_state = "exhausted" if sequential == authorization.range_end else "active"
        authorization.with_context(allow_fiscal_transition=True).write(
            {"next_number": sequential + 1, "state": new_state}
        )
        return f"{authorization._document_prefix()}-{sequential:08d}"
