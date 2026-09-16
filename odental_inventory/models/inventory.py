from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


class ODentalOrganization(models.Model):
    _inherit = "odental.organization"

    clinical_stock_location_id = fields.Many2one(
        "stock.location", string="Existencias clínicas",
        domain="[('usage', '=', 'internal'), ('company_id', 'in', [False, company_id])]",
        check_company=True,
    )
    clinical_consumption_location_id = fields.Many2one(
        "stock.location", string="Destino de consumo clínico",
        domain="[('usage', 'in', ('customer', 'production', 'inventory')), ('company_id', 'in', [False, company_id])]",
        check_company=True,
    )
    clinical_picking_type_id = fields.Many2one(
        "stock.picking.type", string="Operación de consumo clínico",
        domain="[('company_id', 'in', [False, company_id])]",
        check_company=True,
    )


class ODentalService(models.Model):
    _inherit = "odental.service"

    material_template_ids = fields.One2many(
        "odental.service.material", "service_id", string="Protocolo de materiales"
    )


class ODentalServiceMaterial(models.Model):
    _name = "odental.service.material"
    _description = "Material previsto por servicio O Dental"
    _order = "sequence, id"

    sequence = fields.Integer(string="Secuencia", default=10)
    service_id = fields.Many2one(
        "odental.service", string="Servicio", required=True, ondelete="cascade", index=True
    )
    organization_id = fields.Many2one(related="service_id.organization_id", store=True, index=True)
    company_id = fields.Many2one(related="organization_id.company_id", store=True, index=True)
    product_id = fields.Many2one(
        "product.product", string="Material", required=True, ondelete="restrict",
        domain="[('type', '!=', 'service')]", check_company=True
    )
    quantity = fields.Float(string="Cantidad", required=True, default=1.0)
    product_uom_id = fields.Many2one("uom.uom", string="Unidad", required=True)
    mandatory = fields.Boolean(string="Obligatorio", default=True)
    notes = fields.Char(string="Observaciones")

    _sql_constraints = [
        ("service_product_unique", "unique(service_id, product_id)", "El material ya está incluido en este servicio."),
        ("quantity_positive", "check(quantity > 0)", "La cantidad prevista debe ser mayor que cero."),
    ]

    @api.onchange("product_id")
    def _onchange_product(self):
        for line in self:
            if line.product_id:
                line.product_uom_id = line.product_id.uom_id

    @api.constrains("product_id", "product_uom_id", "company_id")
    def _check_product(self):
        for line in self:
            if line.product_id.type == "service":
                raise ValidationError("Un servicio no puede utilizarse como material clínico.")
            if line.product_id.company_id and line.product_id.company_id != line.company_id:
                raise ValidationError("El material pertenece a otra compañía.")
            if line.product_uom_id.category_id != line.product_id.uom_id.category_id:
                raise ValidationError("La unidad debe pertenecer a la categoría de medida del producto.")


class ODentalMaterialConsumption(models.Model):
    _name = "odental.material.consumption"
    _description = "Consumo de materiales O Dental"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "consumption_date desc, id desc"

    name = fields.Char(default="Nuevo", readonly=True, copy=False, index=True)
    appointment_id = fields.Many2one("odental.appointment", required=True, ondelete="restrict", index=True)
    organization_id = fields.Many2one(related="appointment_id.organization_id", store=True, index=True)
    company_id = fields.Many2one(related="organization_id.company_id", store=True, index=True)
    patient_id = fields.Many2one(related="appointment_id.patient_id", store=True, index=True)
    professional_id = fields.Many2one(related="appointment_id.professional_id", store=True, index=True)
    service_id = fields.Many2one(related="appointment_id.service_id", store=True, index=True)
    consumption_date = fields.Datetime(required=True, default=fields.Datetime.now, tracking=True)
    line_ids = fields.One2many("odental.material.consumption.line", "consumption_id", string="Materiales")
    picking_id = fields.Many2one("stock.picking", string="Transferencia de inventario", readonly=True, copy=False)
    state = fields.Selection(
        [("draft", "Pendiente de revisión"), ("ready", "Listo para inventario"),
         ("allocated", "Transferencia creada"), ("posted", "Descontado"), ("cancelled", "Cancelado")],
        required=True, default="draft", tracking=True, index=True
    )
    notes = fields.Text()

    _sql_constraints = [
        ("appointment_unique", "unique(appointment_id)", "Solo puede existir un consumo por cita."),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "Nuevo") == "Nuevo":
                vals["name"] = self.env["ir.sequence"].next_by_code("odental.material.consumption") or "Nuevo"
        records = super().create(vals_list)
        records.action_prepare_materials()
        return records

    def write(self, vals):
        protected = {"state", "picking_id"}
        if protected.intersection(vals) and not self.env.context.get("odental_inventory_transition"):
            raise UserError("Utilice las acciones del consumo para cambiar su estado o transferencia.")
        if {"appointment_id", "line_ids"}.intersection(vals) and any(
            record.state in {"allocated", "posted", "cancelled"} for record in self
        ):
            raise UserError("Un consumo procesado ya no puede cambiarse.")
        return super().write(vals)

    def action_prepare_materials(self):
        for consumption in self:
            if consumption.state != "draft":
                raise UserError("Solo puede preparar materiales en estado pendiente.")
            existing = consumption.line_ids.mapped("template_id")
            commands = []
            for template in consumption.service_id.material_template_ids - existing:
                commands.append((0, 0, {
                    "template_id": template.id,
                    "product_id": template.product_id.id,
                    "quantity_planned": template.quantity,
                    "quantity_used": template.quantity,
                    "product_uom_id": template.product_uom_id.id,
                    "mandatory": template.mandatory,
                }))
            if commands:
                consumption.write({"line_ids": commands})
        return True

    def action_ready(self):
        for consumption in self:
            if consumption.state != "draft":
                raise UserError("Solo un consumo pendiente puede confirmarse.")
            if not consumption.line_ids:
                raise ValidationError("Agregue al menos un material utilizado.")
            required_missing = consumption.line_ids.filtered(lambda line: line.mandatory and line.quantity_used <= 0)
            if required_missing:
                raise ValidationError("Registre la cantidad utilizada de todos los materiales obligatorios.")
            consumption.line_ids._validate_lot_and_quantity()
            consumption.with_context(odental_inventory_transition=True).write({"state": "ready"})

    def _check_configuration(self):
        self.ensure_one()
        organization = self.organization_id
        if not organization.clinical_stock_location_id:
            raise ValidationError("Configure la ubicación de existencias clínicas en la organización.")
        if not organization.clinical_consumption_location_id:
            raise ValidationError("Configure el destino de consumo clínico en la organización.")
        if not organization.clinical_picking_type_id:
            raise ValidationError("Configure el tipo de operación de inventario clínico.")

    def action_create_picking(self):
        self.ensure_one()
        if not self.env.user.has_group("odental_core.group_odental_manager"):
            raise AccessError("Solo un administrador clínico puede crear la transferencia de inventario.")
        if self.state != "ready":
            raise UserError("Confirme primero el consumo de materiales.")
        if self.picking_id:
            return self.action_view_picking()
        self._check_configuration()
        organization = self.organization_id
        move_commands = []
        for line in self.line_ids.filtered(lambda item: item.quantity_used > 0):
            move_commands.append((0, 0, {
                "name": f"{self.name} — {line.product_id.display_name}",
                "product_id": line.product_id.id,
                "product_uom_qty": line.quantity_used,
                "product_uom": line.product_uom_id.id,
                "location_id": organization.clinical_stock_location_id.id,
                "location_dest_id": organization.clinical_consumption_location_id.id,
                "odental_consumption_line_id": line.id,
            }))
        picking = self.env["stock.picking"].with_company(self.company_id).create({
            "picking_type_id": organization.clinical_picking_type_id.id,
            "location_id": organization.clinical_stock_location_id.id,
            "location_dest_id": organization.clinical_consumption_location_id.id,
            "origin": self.name,
            "odental_consumption_id": self.id,
            "move_ids": move_commands,
        })
        picking.action_confirm()
        picking.action_assign()
        self.with_context(odental_inventory_transition=True).write({
            "picking_id": picking.id, "state": "allocated"
        })
        return self.action_view_picking()

    def action_mark_posted(self):
        for consumption in self:
            if not consumption.picking_id or consumption.picking_id.state != "done":
                raise ValidationError("Valide primero la transferencia desde Inventario de Odoo.")
            for line in consumption.line_ids.filtered(lambda item: item.lot_id and item.quantity_used > 0):
                moves = consumption.picking_id.move_ids.filtered(
                    lambda move: move.odental_consumption_line_id == line
                )
                if line.lot_id not in moves.move_line_ids.mapped("lot_id"):
                    raise ValidationError(
                        f"El lote validado en Inventario no coincide con el registrado para "
                        f"{line.product_id.display_name}."
                    )
            consumption.with_context(odental_inventory_transition=True).write({"state": "posted"})
            record = self.env["odental.clinical.record"].search([
                ("patient_id", "=", consumption.patient_id.id)
            ], limit=1)
            if record:
                record._log_event(
                    "material_consumption", f"Consumo de materiales registrado: {consumption.name}",
                    source_record=consumption
                )

    def action_cancel(self):
        for consumption in self:
            if consumption.picking_id and consumption.picking_id.state == "done":
                raise UserError("No se puede cancelar un consumo cuya transferencia ya fue validada.")
            if consumption.picking_id and consumption.picking_id.state not in {"done", "cancel"}:
                consumption.picking_id.action_cancel()
            consumption.with_context(odental_inventory_transition=True).write({"state": "cancelled"})

    def action_view_picking(self):
        self.ensure_one()
        if not self.picking_id:
            raise UserError("Todavía no existe una transferencia de inventario.")
        return {
            "type": "ir.actions.act_window", "res_model": "stock.picking",
            "res_id": self.picking_id.id, "view_mode": "form", "target": "current",
        }


class ODentalMaterialConsumptionLine(models.Model):
    _name = "odental.material.consumption.line"
    _description = "Material consumido O Dental"
    _order = "id"

    consumption_id = fields.Many2one("odental.material.consumption", required=True, ondelete="cascade", index=True)
    organization_id = fields.Many2one(related="consumption_id.organization_id", store=True, index=True)
    company_id = fields.Many2one(related="organization_id.company_id", store=True, index=True)
    template_id = fields.Many2one("odental.service.material", ondelete="set null")
    product_id = fields.Many2one(
        "product.product", string="Material", required=True, ondelete="restrict",
        domain="[('type', '!=', 'service')]", check_company=True
    )
    quantity_planned = fields.Float(string="Cantidad prevista", readonly=True)
    quantity_used = fields.Float(string="Cantidad utilizada", required=True, default=1.0)
    product_uom_id = fields.Many2one("uom.uom", string="Unidad", required=True)
    lot_id = fields.Many2one("stock.lot", string="Lote/serie", domain="[('product_id', '=', product_id)]", check_company=True)
    mandatory = fields.Boolean(string="Obligatorio", default=True)
    notes = fields.Char()

    @api.onchange("product_id")
    def _onchange_product(self):
        for line in self:
            if line.product_id:
                line.product_uom_id = line.product_id.uom_id

    @api.constrains("product_id", "product_uom_id", "quantity_used", "lot_id")
    def _check_line(self):
        for line in self:
            if line.product_id.type == "service":
                raise ValidationError("Un servicio no puede registrarse como material consumido.")
            if line.quantity_used < 0:
                raise ValidationError("La cantidad utilizada no puede ser negativa.")
            if line.product_uom_id.category_id != line.product_id.uom_id.category_id:
                raise ValidationError("La unidad no corresponde al producto.")
            if line.lot_id and line.lot_id.product_id != line.product_id:
                raise ValidationError("El lote seleccionado pertenece a otro producto.")

    def _validate_lot_and_quantity(self):
        today = fields.Date.context_today(self)
        for line in self.filtered(lambda item: item.quantity_used > 0):
            if line.product_id.tracking != "none" and not line.lot_id:
                raise ValidationError(f"Seleccione lote o serie para {line.product_id.display_name}.")
            if line.lot_id and line.lot_id.expiration_date:
                expiration = fields.Datetime.context_timestamp(line, line.lot_id.expiration_date).date()
                if expiration < today:
                    raise ValidationError(f"El lote de {line.product_id.display_name} está vencido.")

    def write(self, vals):
        if any(line.consumption_id.state in {"allocated", "posted", "cancelled"} for line in self):
            raise UserError("Los materiales de un consumo procesado son inmutables.")
        return super().write(vals)

    def unlink(self):
        if any(line.consumption_id.state in {"allocated", "posted", "cancelled"} for line in self):
            raise UserError("Los materiales de un consumo procesado son inmutables.")
        return super().unlink()


class ODentalAppointment(models.Model):
    _inherit = "odental.appointment"

    material_consumption_ids = fields.One2many(
        "odental.material.consumption", "appointment_id", string="Consumos de materiales"
    )
    material_consumption_count = fields.Integer(compute="_compute_material_consumption_count")

    @api.depends("material_consumption_ids")
    def _compute_material_consumption_count(self):
        for appointment in self:
            appointment.material_consumption_count = len(appointment.material_consumption_ids)

    def write(self, vals):
        result = super().write(vals)
        if vals.get("state") == "done":
            for appointment in self.filtered(lambda item: item.service_id.material_template_ids):
                if not appointment.material_consumption_ids:
                    self.env["odental.material.consumption"].create({"appointment_id": appointment.id})
        return result

    def action_view_material_consumption(self):
        self.ensure_one()
        consumption = self.material_consumption_ids[:1]
        if not consumption and self.service_id.material_template_ids:
            consumption = self.env["odental.material.consumption"].create({"appointment_id": self.id})
        if not consumption:
            raise UserError("El servicio no tiene un protocolo de materiales configurado.")
        return {
            "type": "ir.actions.act_window", "res_model": "odental.material.consumption",
            "res_id": consumption.id, "view_mode": "form", "target": "current",
        }


class StockPicking(models.Model):
    _inherit = "stock.picking"

    odental_consumption_id = fields.Many2one(
        "odental.material.consumption", string="Consumo clínico O Dental", readonly=True, copy=False, index=True
    )


class StockMove(models.Model):
    _inherit = "stock.move"

    odental_consumption_line_id = fields.Many2one(
        "odental.material.consumption.line", string="Línea clínica O Dental", readonly=True, copy=False, index=True
    )


class ODentalClinicalAudit(models.Model):
    _inherit = "odental.clinical.audit"

    event_type = fields.Selection(
        selection_add=[("material_consumption", "Consumo de materiales")],
        ondelete={"material_consumption": "cascade"},
    )
