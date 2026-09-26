import base64
import binascii
import hashlib
import mimetypes

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class ODentalClinicalImage(models.Model):
    _name = "odental.clinical.image"
    _description = "Imagen clínica O Dental"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "capture_datetime desc, id desc"

    name = fields.Char(default="Nuevo", readonly=True, copy=False, index=True)
    active = fields.Boolean(default=True)
    clinical_record_id = fields.Many2one(
        "odental.clinical.record", required=True, ondelete="restrict", index=True
    )
    patient_id = fields.Many2one(
        related="clinical_record_id.patient_id", store=True, index=True
    )
    organization_id = fields.Many2one(
        related="clinical_record_id.organization_id", store=True, index=True
    )
    company_id = fields.Many2one(related="organization_id.company_id", store=True, index=True)
    encounter_id = fields.Many2one(
        "odental.clinical.encounter", string="Evolución relacionada", ondelete="set null"
    )
    professional_id = fields.Many2one(
        "odental.professional", required=True, ondelete="restrict", index=True, tracking=True
    )
    tooth_ids = fields.Many2many(
        "odental.tooth",
        "odental_clinical_image_tooth_rel",
        "image_id",
        "tooth_id",
        string="Piezas relacionadas",
    )
    category = fields.Selection(
        [
            ("intraoral_photo", "Fotografía intraoral"),
            ("extraoral_photo", "Fotografía extraoral"),
            ("periapical", "Radiografía periapical"),
            ("bitewing", "Radiografía bite-wing"),
            ("occlusal", "Radiografía oclusal"),
            ("panoramic", "Panorámica"),
            ("cephalometric", "Cefalométrica"),
            ("cbct", "CBCT"),
            ("intraoral_scan", "Escaneo intraoral"),
            ("document", "Documento clínico"),
            ("other", "Otro"),
        ],
        required=True,
        index=True,
        tracking=True,
    )
    modality = fields.Selection(
        [
            ("PHOTO", "Fotografía"),
            ("IO", "Radiografía intraoral"),
            ("DX", "Radiografía digital"),
            ("CR", "Radiografía computarizada"),
            ("CT", "Tomografía"),
            ("OT", "Otro"),
        ],
        string="Modalidad DICOM",
        default="OT",
    )
    capture_datetime = fields.Datetime(
        string="Fecha de captura", required=True, default=fields.Datetime.now, index=True
    )
    source_equipment = fields.Char(string="Equipo de origen")
    notes = fields.Text()
    sensitivity = fields.Selection(
        [("regular", "Clínica"), ("restricted", "Restringida")],
        required=True,
        default="regular",
        tracking=True,
    )
    referral_sharing = fields.Selection(
        [
            ("never", "Nunca compartir automáticamente"),
            ("review", "Revisión profesional obligatoria"),
            ("include", "Incluir cuando sea clínicamente necesario"),
        ],
        required=True,
        default="review",
        string="Uso en referencias",
        tracking=True,
    )
    file_data = fields.Binary(string="Archivo clínico", required=True, attachment=True)
    filename = fields.Char(required=True)
    mimetype = fields.Char(readonly=True)
    file_size = fields.Integer(string="Tamaño en bytes", readonly=True)
    file_hash = fields.Char(string="Huella SHA-256", readonly=True, copy=False, index=True)
    dicom_study_uid = fields.Char(string="DICOM Study UID", index=True)
    dicom_series_uid = fields.Char(string="DICOM Series UID", index=True)
    dicom_instance_uid = fields.Char(string="DICOM SOP Instance UID", index=True)
    state = fields.Selection(
        [("draft", "Borrador"), ("final", "Finalizada"), ("archived", "Archivada")],
        required=True,
        default="draft",
        tracking=True,
        index=True,
    )
    finalized_at = fields.Datetime(readonly=True)
    finalized_by_user_id = fields.Many2one("res.users", readonly=True)

    _sql_constraints = [
        (
            "dicom_instance_organization_unique",
            "unique(dicom_instance_uid, organization_id)",
            "Esta instancia DICOM ya está registrada en la organización.",
        )
    ]

    @api.model
    def _file_metadata(self, encoded_file, filename):
        try:
            raw_file = base64.b64decode(encoded_file, validate=True)
        except (binascii.Error, ValueError, TypeError) as error:
            raise ValidationError("El archivo clínico no contiene datos válidos.") from error
        mimetype = mimetypes.guess_type(filename or "")[0]
        if (filename or "").lower().endswith((".dcm", ".dicom")):
            mimetype = "application/dicom"
        return {
            "file_size": len(raw_file),
            "file_hash": hashlib.sha256(raw_file).hexdigest(),
            "mimetype": mimetype or "application/octet-stream",
        }

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "Nuevo") == "Nuevo":
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "odental.clinical.image"
                ) or "Nuevo"
            if vals.get("file_data"):
                vals.update(self._file_metadata(vals["file_data"], vals.get("filename")))
        images = super().create(vals_list)
        for image in images:
            image.clinical_record_id._log_event(
                "image_created",
                f"Imagen clínica creada: {image.name}",
                image.file_hash,
                source_record=image,
            )
        return images

    def write(self, vals):
        protected_fields = {
            "active",
            "clinical_record_id",
            "encounter_id",
            "professional_id",
            "tooth_ids",
            "category",
            "modality",
            "capture_datetime",
            "source_equipment",
            "notes",
            "sensitivity",
            "referral_sharing",
            "file_data",
            "filename",
            "mimetype",
            "file_size",
            "file_hash",
            "dicom_study_uid",
            "dicom_series_uid",
            "dicom_instance_uid",
            "finalized_at",
            "finalized_by_user_id",
        }
        if not self.env.context.get("allow_image_transition"):
            for image in self:
                if vals.get("state") in ("final", "archived"):
                    raise UserError("Utilice las acciones controladas de la imagen clínica.")
                if image.state in ("final", "archived") and protected_fields.intersection(vals):
                    raise UserError("Una imagen clínica finalizada no puede alterarse.")
                if (
                    image.state in ("final", "archived")
                    and vals.get("state")
                    and vals["state"] != image.state
                ):
                    raise UserError("El estado de una imagen finalizada no puede revertirse.")
        if vals.get("file_data"):
            filename = vals.get("filename") or (self[:1].filename if len(self) == 1 else False)
            vals.update(self._file_metadata(vals["file_data"], filename))
        return super().write(vals)

    def unlink(self):
        if any(image.state != "draft" for image in self):
            raise UserError("Una imagen finalizada debe conservarse como evidencia clínica.")
        return super().unlink()

    @api.constrains("clinical_record_id", "encounter_id", "professional_id")
    def _check_relations(self):
        for image in self:
            if image.organization_id not in image.professional_id.organization_ids:
                raise ValidationError("El profesional no pertenece a la organización del expediente.")
            if image.encounter_id and image.encounter_id.clinical_record_id != image.clinical_record_id:
                raise ValidationError("La evolución corresponde a otro expediente.")

    def action_finalize(self):
        for image in self:
            if image.state != "draft":
                raise UserError("Solo las imágenes en borrador pueden finalizarse.")
            if not image.file_data or not image.file_hash:
                raise ValidationError("Debe adjuntar un archivo clínico válido.")
            image.with_context(allow_image_transition=True).write(
                {
                    "state": "final",
                    "finalized_at": fields.Datetime.now(),
                    "finalized_by_user_id": self.env.user.id,
                }
            )
            image.clinical_record_id._log_event(
                "image_finalized",
                f"Imagen clínica finalizada: {image.name}",
                image.file_hash,
                source_record=image,
            )

    def action_archive_clinical(self):
        for image in self:
            if image.state != "final":
                raise UserError("Solo una imagen finalizada puede archivarse.")
            image.with_context(allow_image_transition=True).write(
                {"state": "archived", "active": False}
            )
            image.clinical_record_id._log_event(
                "image_archived",
                f"Imagen clínica archivada: {image.name}",
                image.file_hash,
                source_record=image,
            )
