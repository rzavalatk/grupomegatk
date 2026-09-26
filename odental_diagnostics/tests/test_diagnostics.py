import base64

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestODentalDiagnostics(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        values = {
            'name': 'Synthetic diagnostic clinician', 'login': 'odental-diagnostic-test',
            'company_id': cls.env.company.id, 'company_ids': [(6, 0, cls.env.company.ids)],
            'groups_id': [(6, 0, [cls.env.ref('base.group_user').id,
                cls.env.ref('odental_core.group_odental_professional').id])],
        }
        if 'autopost_bills' in cls.env['res.users']._fields:
            values['autopost_bills'] = 'never'
        cls.operator = cls.env['res.users'].with_context(no_reset_password=True).create(values)
        cls.organization = cls.env["odental.organization"].create(
            {"name": "Clínica diagnóstico", "code": "DIAG", 'owner_user_id': cls.operator.id,
             "user_ids": [(4, cls.env.user.id), (4, cls.operator.id)]}
        )
        cls.professional = cls.env["odental.professional"].create(
            {"name": "Dr. Diagnóstico", "organization_ids": [(4, cls.organization.id)]}
        )
        cls.patient = cls.env["odental.patient"].create(
            {"name": "Paciente diagnóstico", "organization_id": cls.organization.id}
        )
        cls.record = cls.env["odental.clinical.record"].create(
            {"patient_id": cls.patient.id}
        )
        cls.tooth_11 = cls.env.ref("odental_diagnostics.tooth_11")

    def test_signed_odontogram_is_immutable(self):
        chart = self.env["odental.odontogram"].create(
            {
                "clinical_record_id": self.record.id,
                "professional_id": self.professional.id,
                "dentition": "permanent",
                "finding_ids": [
                    (
                        0,
                        0,
                        {
                            "tooth_id": self.tooth_11.id,
                            "surface": "mesial",
                            "condition": "caries",
                            "status": "existing",
                        },
                    )
                ],
            }
        )
        chart.action_sign()
        self.assertEqual(chart.state, "signed")
        self.assertTrue(chart.content_hash)
        with self.assertRaises(UserError):
            chart.finding_ids.write({"notes": "Alteración"})

    def test_odontogram_amendment_copies_findings(self):
        chart = self.env["odental.odontogram"].create(
            {
                "clinical_record_id": self.record.id,
                "professional_id": self.professional.id,
                "finding_ids": [
                    (
                        0,
                        0,
                        {
                            "tooth_id": self.tooth_11.id,
                            "surface": "whole",
                            "condition": "healthy",
                            "status": "existing",
                        },
                    )
                ],
            }
        )
        chart.action_sign()
        action = chart.action_create_amendment()
        amendment = self.env["odental.odontogram"].browse(action["res_id"])
        self.assertEqual(amendment.version, 2)
        self.assertEqual(len(amendment.finding_ids), 1)
        amendment.amendment_reason = "Cambio clínico comprobado"
        amendment.action_sign()
        self.assertEqual(amendment.state, "signed")

    def test_primary_tooth_rejected_in_permanent_chart(self):
        tooth_51 = self.env.ref("odental_diagnostics.tooth_51")
        chart = self.env["odental.odontogram"].create(
            {
                "clinical_record_id": self.record.id,
                "professional_id": self.professional.id,
                "dentition": "permanent",
            }
        )
        with self.env.cr.savepoint(), self.assertRaises(ValidationError):
            self.env["odental.odontogram.finding"].create(
                {
                    "odontogram_id": chart.id,
                    "tooth_id": tooth_51.id,
                    "surface": "whole",
                    "condition": "healthy",
                }
            )

    def test_finalized_image_hash_and_immutability(self):
        content = b"O Dental clinical image test"
        image = self.env["odental.clinical.image"].create(
            {
                "clinical_record_id": self.record.id,
                "professional_id": self.professional.id,
                "category": "intraoral_photo",
                "modality": "PHOTO",
                "filename": "test.jpg",
                "file_data": base64.b64encode(content),
            }
        )
        self.assertEqual(image.file_size, len(content))
        self.assertTrue(image.file_hash)
        image.action_finalize()
        self.assertEqual(image.state, "final")
        with self.assertRaises(UserError):
            image.write({"notes": "Alteración posterior"})

    def _chart(self):
        return self.env['odental.odontogram'].with_user(self.operator).create({
            'clinical_record_id': self.record.id, 'professional_id': self.professional.id,
            'finding_ids': [(0, 0, {'tooth_id': self.tooth_11.id, 'condition': 'healthy'})],
        })

    def _image(self):
        return self.env['odental.clinical.image'].with_user(self.operator).create({
            'clinical_record_id': self.record.id, 'professional_id': self.professional.id,
            'category': 'document', 'filename': 'synthetic.txt',
            'file_data': base64.b64encode(b'Synthetic test document'),
        })

    def test_context_cannot_change_signed_chart(self):
        chart = self._chart()
        chart.action_sign()
        for values in ({'summary': 'Altered'}, {'state': 'draft'}, {'content_hash': 'fake'}):
            with self.assertRaises(UserError):
                chart.with_context(allow_odontogram_transition=True).write(values)
        self.assertEqual(chart.content_hash, chart._hash_payload())

    def test_chart_creation_cannot_bypass_signing(self):
        chart = self._chart()
        values = {'clinical_record_id': self.record.id, 'professional_id': self.professional.id}
        with self.assertRaises(UserError):
            chart.create(dict(values, state='signed'))
        with self.assertRaises(UserError):
            chart.with_context(default_state='signed').create(values)
        with self.assertRaises(UserError):
            chart.with_context(default_content_hash='fake').create(values)
        with self.assertRaises(UserError):
            chart.write({'signed_by_user_id': self.operator.id})

    def test_finding_defaults_cannot_modify_signed_chart(self):
        chart = self._chart()
        chart.action_sign()
        findings = self.env['odental.odontogram.finding'].with_user(self.operator)
        with self.assertRaises(UserError):
            findings.with_context(default_odontogram_id=chart.id).create({
                'tooth_id': self.tooth_11.id, 'condition': 'caries'})

    def test_image_context_and_metadata_are_protected(self):
        image = self._image()
        with self.assertRaises(UserError):
            image.write({'file_hash': 'fake'})
        with self.assertRaises(UserError):
            image.write({'finalized_by_user_id': self.operator.id})
        image.action_finalize()
        original_hash = image.file_hash
        for values in ({'file_data': base64.b64encode(b'Altered')}, {'state': 'draft'},
                       {'file_hash': 'fake'}, {'active': False}):
            with self.assertRaises(UserError):
                image.with_context(allow_image_transition=True).write(values)
        image.action_archive_clinical()
        self.assertEqual(image.state, 'archived')
        self.assertFalse(image.active)
        self.assertEqual(image.file_hash, original_hash)
        with self.assertRaises(UserError):
            image.unlink()
        events = self.env['odental.clinical.audit'].search([
            ('record_res_id', '=', image.id), ('model_name', '=', image._name)])
        self.assertTrue({'image_finalized', 'image_archived'}.issubset(set(events.mapped('event_type'))))

    def test_image_creation_requires_finalization_action(self):
        values = {'clinical_record_id': self.record.id, 'professional_id': self.professional.id,
                  'category': 'document', 'filename': 'synthetic.txt',
                  'file_data': base64.b64encode(b'Synthetic test document')}
        images = self.env['odental.clinical.image'].with_user(self.operator)
        with self.assertRaises(UserError):
            images.create(dict(values, state='final'))
        with self.assertRaises(UserError):
            images.with_context(default_state='final').create(values)
        with self.assertRaises(UserError):
            images.with_context(default_finalized_by_user_id=self.operator.id).create(values)

    def test_diagnostics_hidden_from_unrelated_clinician(self):
        outsider = self.operator.with_context(no_reset_password=True).copy({
            'login': 'odental-diagnostic-outsider', 'name': 'Synthetic outsider'})
        chart, image = self._chart(), self._image()
        for record, field in ((chart, 'summary'), (chart.finding_ids, 'notes'), (image, 'file_data')):
            with self.assertRaises(AccessError):
                record.with_user(outsider).read([field])
