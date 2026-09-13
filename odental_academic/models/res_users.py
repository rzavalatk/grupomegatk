from odoo import api, models
from odoo.exceptions import ValidationError


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.constrains("groups_id")
    def _check_academic_student_isolation(self):
        student_group = self.env.ref(
            "odental_academic.group_odental_academic_student", raise_if_not_found=False
        )
        clinical_group = self.env.ref(
            "odental_core.group_odental_user", raise_if_not_found=False
        )
        if not student_group or not clinical_group:
            return
        for user in self:
            if student_group in user.groups_id and clinical_group in user.groups_id:
                raise ValidationError(
                    "Un estudiante académico no puede tener simultáneamente acceso clínico "
                    "general. Retire uno de los dos perfiles."
                )

