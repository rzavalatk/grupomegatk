# -*- coding: utf-8 -*-
import logging
import math
import base64
import re
import unicodedata
from lxml import etree

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from odoo.tools import parse_date

_logger = logging.getLogger(__name__)


try:
    from num2words import num2words
except ImportError:
    _logger.warning("The num2words python library is not installed, amount-to-text features won't be fully available.")
    num2words = None


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    #@api.model_create_multi
    def print_report(self):
        context = self.env.context
        id = context['active_id']
        ids = context['active_ids']
        self = self.browse(id)
        try:
            pdf_pos = self.env.ref(
                'reportes_custom.stock_picking_custom_pos').render_qweb_pdf(ids)
            pdf = self.env.ref(
                'reportes_custom.stock_picking_custom').render_qweb_pdf(ids)
            self.env['ir.attachment'].create({
                'name': f"Orden de entraga pos - {self.name}",
                'type': 'binary',
                'datas': base64.encodestring(pdf_pos[0]),
                'datas_fname': f'Orden de entraga pos -  {self.name}.pdf',
                'res_model': 'stock.picking',
                'res_id': id,
                'mimetype': 'application/x-pdf'
            })
            self.env['ir.attachment'].create({
                'name': f"Orden de entrega -  {self.name}",
                'type': 'binary',
                'datas': base64.encodestring(pdf[0]),
                'datas_fname': f'Orden de entrega -  {self.name}.pdf',
                'res_model': 'stock.picking',
                'res_id': id,
                'mimetype': 'application/x-pdf'
            })
        except:
            self.env.user.notify_danger(
                title="Se ha producido un error interno:",
                message="""La Firma no fue adjuntada correctamente, profavor intente nuevamente""")
            self.write({'passed': "No"})
            print("///////////Error al adjuntar el reporte//////////////")
        return True

    sign = fields.Binary()
    passed = fields.Char(string="Aprobado", default="No")

class ResCurrencyInherit(models.Model):
    _inherit = 'res.currency'

    def amount_to_text(self, amount):
        self.ensure_one()
        
        def _num2words(number, lang):
            try:
                return num2words(number, lang=lang).title()
            except NotImplementedError:
                return num2words(number, lang='en').title()

        if num2words is None:
            logging.getLogger(__name__).warning("The library 'num2words' is missing, cannot render textual amounts.")
            return ""

        formatted = "%.{0}f".format(self.decimal_places) % amount
        parts = formatted.partition('.')
        integer_value = int(parts[0])
        fractional_value = int(parts[2] or 0)

        lang = tools.get_lang(self.env)
        amount_words = tools.ustr('{amt_value} {amt_word}').format(
                        amt_value=_num2words(integer_value, lang=lang.iso_code),
                        amt_word=self.currency_unit_label,
                        )
        if not self.is_zero(amount - integer_value):
            amount_words += ' ' + _('con') + tools.ustr(' {amt_value} {amt_word}').format(
                        amt_value=_num2words(fractional_value, lang=lang.iso_code),
                        amt_word=self.currency_subunit_label,
                        )
        return amount_words

    
class InvoiceOrder(models.Model):
    _inherit = 'account.move'

    # @api.multi
    def _compute_amount_in_word(self):
        for rec in self:
            rec.num_word = str(rec.currency_id.amount_to_text(rec.amount_total))

    num_word = fields.Char(string="Amount In Words:", compute='_compute_amount_in_word')    

class HelpdeskTagCompatibility(models.Model):
    _inherit = 'helpdesk.tag'
    # Keep name as varchar-compatible field to avoid JSON translation SQL on legacy DBs.
    name = fields.Char(string='Tag', translate=False)


class ProjectTask(models.Model):
    _inherit = 'project.task'

    proposito_llamada = fields.Char(compute='_compute_hoja_trabajo_data', string='Proposito Llamada')
    proposito_visita = fields.Char(compute='_compute_hoja_trabajo_data', string='Proposito Visita')
    persona_reporto = fields.Char(compute='_compute_hoja_trabajo_data', string='Persona que reporto')
    telefono_visita = fields.Char(compute='_compute_hoja_trabajo_data', string='Telefono')
    correo_visita = fields.Char(compute='_compute_hoja_trabajo_data', string='Correo')
    direccion_visita = fields.Char(compute='_compute_hoja_trabajo_data', string='Direccion')
    tipo_soporte_label = fields.Char(compute='_compute_hoja_trabajo_data', string='Tipo de Soporte')
    tipo_visita_label = fields.Char(compute='_compute_hoja_trabajo_data', string='Tipo de Visita')
    estado_equipo_label = fields.Char(compute='_compute_hoja_trabajo_data', string='Estado del Equipo')

    def _normalize_worksheet_label(self, value):
        value = value or ''
        value = unicodedata.normalize('NFKD', value)
        value = ''.join(char for char in value if not unicodedata.combining(char))
        value = value.lower().strip()
        value = re.sub(r'[^a-z0-9\s]', ' ', value)
        value = re.sub(r'\s+', ' ', value).strip()
        return value

    def _get_task_worksheet_record(self):
        self.ensure_one()
        model_name = self.env.context.get('worksheet_model') or self.env.context.get('active_model') or 'x_project_task_worksheet_template_4'
        if not str(model_name).startswith('x_project_task_worksheet_template_'):
            model_name = 'x_project_task_worksheet_template_4'
        if model_name not in self.env:
            return False

        worksheet_id = self.env.context.get('worksheet_id')
        if worksheet_id:
            worksheet_ctx = self.env[model_name].browse(worksheet_id).exists()
            if worksheet_ctx:
                for field_name, field in worksheet_ctx._fields.items():
                    if getattr(field, 'type', None) == 'many2one' and getattr(field, 'comodel_name', None) == 'project.task':
                        if worksheet_ctx[field_name] and worksheet_ctx[field_name].id == self.id:
                            return worksheet_ctx

        worksheet_model = self.env[model_name]
        candidate_fields = []
        for field_name, field in worksheet_model._fields.items():
            if getattr(field, 'type', None) == 'many2one' and getattr(field, 'comodel_name', None) == 'project.task':
                candidate_fields.append(field_name)

        for field_name in candidate_fields:
            worksheet = worksheet_model.search([(field_name, '=', self.id)], limit=1)
            if worksheet:
                return worksheet
        return False

    def _get_worksheet_field_value(self, worksheet, labels, *, field_names=None, selection=False):
        if not worksheet:
            return ''

        def _format_value(field, value):
            field_type = getattr(field, 'type', None)
            if value in (False, None, ''):
                return ''
            if selection and field_type == 'selection':
                return dict(field.selection).get(value, '')
            if field_type == 'many2one':
                return value.display_name or ''
            if field_type in ('many2many', 'one2many'):
                return ', '.join(value.mapped('name')) if value else ''
            return value

        # Prefer exact technical field names from Studio when available.
        for field_name in (field_names or []):
            if field_name not in worksheet._fields:
                continue
            field = worksheet._fields[field_name]
            value = worksheet[field_name]
            formatted = _format_value(field, value)
            if formatted not in (False, None, ''):
                return formatted

        normalized_labels = [self._normalize_worksheet_label(label) for label in labels if label]
        for field_name, field in worksheet._fields.items():
            field_label = self._normalize_worksheet_label(getattr(field, 'string', ''))
            if not field_label:
                continue
            value = worksheet[field_name]
            if any(lbl == field_label or lbl in field_label or field_label in lbl for lbl in normalized_labels):
                formatted = _format_value(field, value)
                if formatted not in (False, None, ''):
                    return formatted
        return ''

    @api.depends('partner_id', 'name')
    def _compute_hoja_trabajo_data(self):
        for task in self:
            worksheet = task._get_task_worksheet_record()
            ticket = task.ticket_id if 'ticket_id' in task._fields else False
            lead = False
            if ticket and hasattr(ticket, 'lead_id'):
                lead = ticket.lead_id

            task.proposito_llamada = ''
            task.proposito_visita = task.name or ''
            task.persona_reporto = task.partner_id.name if task.partner_id else ''
            task.telefono_visita = task.partner_id.phone if task.partner_id else ''
            task.correo_visita = task.partner_id.email if task.partner_id else ''
            task.direccion_visita = task.partner_id.street if task.partner_id else ''
            task.tipo_soporte_label = ''
            task.tipo_visita_label = ''
            task.estado_equipo_label = ''

            if worksheet:
                task.tipo_soporte_label = task._get_worksheet_field_value(
                    worksheet,
                    ['Tipo de Soporte'],
                    field_names=['x_studio_tipo_de_soporte'],
                    selection=True,
                ) or task.tipo_soporte_label
                task.proposito_llamada = task._get_worksheet_field_value(
                    worksheet,
                    ['Proposito Llamada', 'Propósito Llamada'],
                    field_names=['x_studio_propsito_llamada'],
                ) or task.proposito_llamada
                task.estado_equipo_label = task._get_worksheet_field_value(
                    worksheet,
                    ['Estado del Equipo'],
                    # No se identifico el nombre tecnico exacto de Studio para este campo en capturas.
                    selection=True,
                ) or task.estado_equipo_label
                task.tipo_visita_label = task._get_worksheet_field_value(
                    worksheet,
                    ['Tipo de Visita'],
                    field_names=['x_studio_tipo_de_visita'],
                    selection=True,
                ) or task.tipo_visita_label
                task.proposito_visita = task._get_worksheet_field_value(
                    worksheet,
                    ['Proposito de la visita', 'Propósito de la visita'],
                    field_names=['x_studio_propsito_de_la_visita'],
                ) or task.proposito_visita
                task.persona_reporto = task._get_worksheet_field_value(
                    worksheet,
                    ['La persona que reporto', 'Persona que reporto'],
                    field_names=['x_studio_la_persona_que_reporto'],
                ) or task.persona_reporto
                task.telefono_visita = task._get_worksheet_field_value(
                    worksheet,
                    ['Telefono', 'Teléfono'],
                    field_names=['x_studio_telfono_1'],
                ) or task.telefono_visita
                task.correo_visita = task._get_worksheet_field_value(
                    worksheet,
                    ['Correo Electronico', 'Correo Electrónico'],
                    field_names=['x_studio_correo_electrnico'],
                ) or task.correo_visita
                task.direccion_visita = task._get_worksheet_field_value(
                    worksheet,
                    ['Direccion de visita', 'Dirección de visita'],
                    field_names=['x_studio_direccin_de_visita'],
                ) or task.direccion_visita

            if lead:
                task.proposito_llamada = getattr(lead, 'proposito_llamada', '') or task.proposito_llamada
                task.proposito_visita = getattr(lead, 'proposito', '') or task.proposito_visita
                task.persona_reporto = getattr(lead, 'reporto', '') or task.persona_reporto
                task.telefono_visita = getattr(lead, 'repor_tel', '') or task.telefono_visita
                task.correo_visita = getattr(lead, 'repor_email', '') or task.correo_visita
                task.direccion_visita = getattr(lead, 'repor_direction', '') or task.direccion_visita

                if 'tipo_soporte' in lead._fields and lead.tipo_soporte:
                    task.tipo_soporte_label = dict(lead._fields['tipo_soporte'].selection).get(lead.tipo_soporte, '') or task.tipo_soporte_label
                if 'tipo_visita' in lead._fields and lead.tipo_visita:
                    task.tipo_visita_label = dict(lead._fields['tipo_visita'].selection).get(lead.tipo_visita, '') or task.tipo_visita_label
                if 'estado_taller' in lead._fields and lead.estado_taller:
                    task.estado_equipo_label = dict(lead._fields['estado_taller'].selection).get(lead.estado_taller, '') or task.estado_equipo_label

    def _report_task_pick(self, field_names=None, labels=None, selection=False, default=''):
        self.ensure_one()
        field_names = field_names or []
        labels = labels or []

        worksheet_context_mode = bool(
            self.env.context.get('worksheet_id')
            or str(self.env.context.get('worksheet_model', '')).startswith('x_project_task_worksheet_template_')
            or str(self.env.context.get('active_model', '')).startswith('x_project_task_worksheet_template_')
        )

        worksheet = self._get_task_worksheet_record()
        if worksheet_context_mode and worksheet:
            value = self._get_worksheet_field_value(
                worksheet,
                labels,
                field_names=field_names,
                selection=selection,
            )
            if value not in (False, None, ''):
                return value

        lead = False
        if 'ticket_id' in self._fields and self.ticket_id and 'lead_id' in self.ticket_id._fields:
            lead = self.ticket_id.lead_id

        candidates = [self]
        if 'ticket_id' in self._fields and self.ticket_id:
            candidates.append(self.ticket_id)
        if lead:
            candidates.append(lead)

        for record in candidates:
            for field_name in field_names:
                if field_name not in record._fields:
                    continue
                value = record[field_name]
                if value in (False, None, ''):
                    continue
                field = record._fields[field_name]
                if selection and getattr(field, 'type', None) == 'selection':
                    return dict(field.selection).get(value, default) or default
                if getattr(field, 'type', None) == 'many2one':
                    return value.display_name or default
                if getattr(field, 'type', None) in ('many2many', 'one2many'):
                    return ', '.join(value.mapped('name')) if value else default
                return value

        if worksheet:
            value = self._get_worksheet_field_value(
                worksheet,
                labels,
                field_names=field_names,
                selection=selection,
            )
            if value not in (False, None, ''):
                return value

        return default

    def _report_task_title(self):
        self.ensure_one()
        title = (self.env.context.get('worksheet_title') or '').strip()
        if title:
            return title.upper()

        title = self._report_task_pick(
            field_names=['x_studio_nombre_de_plantilla', 'x_studio_titulo', 'x_name', 'name'],
            labels=['Plantilla de hoja de trabajo', 'Nombre de plantilla', 'Titulo', 'Título'],
            default='',
        )
        if not title:
            title = self.name or 'HOJA DE TRABAJO'
        return str(title).strip().upper()
