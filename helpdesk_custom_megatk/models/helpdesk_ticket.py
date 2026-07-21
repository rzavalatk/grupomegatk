# -*- coding: utf-8 -*-
import unicodedata

from odoo import fields, models


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    x_is_technical_area = fields.Boolean(
        related="team_id.x_is_technical_area",
        store=True,
        readonly=True,
    )
    x_tecnico_diagnostico = fields.Text(string="Diagnostico tecnico")
    x_tecnico_solucion = fields.Text(string="Solucion aplicada")

    def _normalize_report_label(self, value):
        value = value or ""
        value = unicodedata.normalize("NFKD", value)
        value = "".join(char for char in value if not unicodedata.combining(char))
        return value.strip().lower()

    def _report_get_task_record(self):
        self.ensure_one()
        if "project.task" not in self.env:
            return False
        task_model = self.env["project.task"]
        if "ticket_id" not in task_model._fields:
            return False
        return task_model.search([("ticket_id", "=", self.id)], limit=1)

    def _report_get_worksheet_record(self):
        self.ensure_one()
        model_name = "x_project_task_worksheet_template_4"
        if model_name not in self.env:
            return False

        task = self._report_get_task_record()
        if not task:
            return False

        worksheet_model = self.env[model_name]
        candidate_fields = []
        for field_name, field in worksheet_model._fields.items():
            if getattr(field, "type", None) == "many2one" and getattr(field, "comodel_name", None) == "project.task":
                candidate_fields.append(field_name)

        for field_name in candidate_fields:
            worksheet = worksheet_model.search([(field_name, "=", task.id)], limit=1)
            if worksheet:
                return worksheet
        return False

    def _report_read_field(self, record, field_name, selection=False):
        if not record or field_name not in record._fields:
            return False
        value = record[field_name]
        if value in (False, None, ""):
            return False

        field = record._fields[field_name]
        field_type = getattr(field, "type", "")
        if selection and field_type == "selection":
            return dict(field.selection).get(value) or False
        if field_type == "many2one":
            return value.display_name or False
        return value

    def _report_pick_from_worksheet(self, labels=None, field_names=None, selection=False):
        self.ensure_one()
        worksheet = self._report_get_worksheet_record()
        if not worksheet:
            return False

        for field_name in (field_names or []):
            value = self._report_read_field(worksheet, field_name, selection=selection)
            if value not in (False, None, ""):
                return value

        normalized_labels = [self._normalize_report_label(label) for label in (labels or []) if label]
        if not normalized_labels:
            return False

        for field_name, field in worksheet._fields.items():
            field_label = self._normalize_report_label(getattr(field, "string", ""))
            if not field_label:
                continue
            if field_label in normalized_labels or any(label in field_label for label in normalized_labels):
                value = self._report_read_field(worksheet, field_name, selection=selection)
                if value not in (False, None, ""):
                    return value
        return False

    def _report_pick_from_ticket_or_lead(self, field_names=None, selection=False):
        self.ensure_one()
        lead = self.lead_id if "lead_id" in self._fields else False

        for field_name in (field_names or []):
            value = self._report_read_field(self, field_name, selection=selection)
            if value not in (False, None, ""):
                return value
            if lead:
                value = self._report_read_field(lead, field_name, selection=selection)
                if value not in (False, None, ""):
                    return value
        return False

    def _report_pick(self, field_names=None, labels=None, default=""):
        self.ensure_one()
        value = self._report_pick_from_ticket_or_lead(field_names=field_names, selection=False)
        if value not in (False, None, ""):
            return value
        value = self._report_pick_from_worksheet(labels=labels, field_names=field_names, selection=False)
        if value not in (False, None, ""):
            return value
        return default

    def _report_pick_selection(self, field_names=None, labels=None, default=""):
        self.ensure_one()
        value = self._report_pick_from_ticket_or_lead(field_names=field_names, selection=True)
        if value not in (False, None, ""):
            return value
        value = self._report_pick_from_worksheet(labels=labels, field_names=field_names, selection=True)
        if value not in (False, None, ""):
            return value
        return default

    def _report_pick_binary(self, field_names=None, labels=None):
        self.ensure_one()
        value = self._report_pick_from_ticket_or_lead(field_names=field_names, selection=False)
        if value not in (False, None, ""):
            return value
        value = self._report_pick_from_worksheet(labels=labels, field_names=field_names, selection=False)
        if value not in (False, None, ""):
            return value
        return False

    def action_print_orden_ingreso(self):
        """Imprime la orden de ingreso del ticket"""
        return self.env.ref("helpdesk_custom_megatk.helpdesk_ticket_orden_ingreso").report_action(self)

    def action_print_visita_tecnica(self):
        """Imprime la visita técnica del ticket"""
        return self.env.ref("helpdesk_custom_megatk.helpdesk_ticket_visita_tecnica").report_action(self)

    def action_print_entrega_equipo(self):
        """Imprime la entrega de equipo del ticket"""
        return self.env.ref("helpdesk_custom_megatk.helpdesk_ticket_entrega_equipo").report_action(self)
