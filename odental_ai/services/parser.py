import re
import unicodedata
from datetime import datetime

import pytz

from odoo import fields
from odoo.exceptions import ValidationError


CONDITIONS = {
    "sana": "healthy",
    "caries": "caries",
    "restauracion": "restoration",
    "restauracion temporal": "temporary_restoration",
    "ausente": "missing",
    "no erupcionada": "unerupted",
    "corona": "crown",
    "implante": "implant",
    "endodoncia": "root_canal",
    "tratamiento endodontico": "root_canal",
    "extraccion indicada": "extraction_indicated",
    "fractura": "fracture",
    "movilidad": "mobility",
    "sellante": "sealant",
    "protesis": "prosthesis",
}

SURFACES = {
    "pieza completa": "whole",
    "completa": "whole",
    "oclusal": "occlusal",
    "incisal": "incisal",
    "mesial": "mesial",
    "distal": "distal",
    "vestibular": "buccal",
    "bucal": "buccal",
    "lingual": "lingual",
    "palatina": "palatal",
    "palatal": "palatal",
    "cervical": "cervical",
    "raiz": "root",
}

ENCOUNTER_PREFIXES = {
    "motivo": "chief_complaint",
    "motivo de consulta": "chief_complaint",
    "hallazgo": "clinical_findings",
    "hallazgos": "clinical_findings",
    "nota clinica": "clinical_findings",
    "evolucion": "clinical_findings",
    "diagnostico": "diagnosis_summary",
    "plan": "treatment_plan",
    "plan de tratamiento": "treatment_plan",
    "procedimiento": "procedures_performed",
    "procedimientos": "procedures_performed",
    "indicaciones": "prescriptions",
    "prescripcion": "prescriptions",
    "nota privada": "private_notes",
}


def _normalize(value):
    normalized = unicodedata.normalize("NFKD", value or "")
    return "".join(char for char in normalized if not unicodedata.combining(char)).lower()


def _first_alias(normalized, aliases):
    return next(
        (value for label, value in sorted(aliases.items(), key=lambda item: -len(item[0])) if label in normalized),
        False,
    )


def _local_datetime(session, line):
    match = re.search(
        r"\b(\d{1,2}/\d{1,2}/\d{4})\s+(?:a\s+las\s+)?(\d{1,2}:\d{2})\b",
        _normalize(line),
    )
    if not match:
        return False
    try:
        local_value = datetime.strptime(
            f"{match.group(1)} {match.group(2)}", "%d/%m/%Y %H:%M"
        )
        timezone = pytz.timezone(session.env.user.tz or "America/Tegucigalpa")
        localized = timezone.localize(local_value, is_dst=None)
    except (
        ValueError,
        pytz.UnknownTimeZoneError,
        pytz.AmbiguousTimeError,
        pytz.NonExistentTimeError,
    ) as error:
        raise ValidationError("La fecha u hora indicada no es válida.") from error
    return fields.Datetime.to_string(
        localized.astimezone(pytz.UTC).replace(tzinfo=None)
    )


def parse_command(session):
    """Return allowlisted action values and warnings; never execute user text directly."""
    lines = [line.strip() for line in (session.command_text or "").splitlines() if line.strip()]
    actions = []
    warnings = []
    encounter_payload = {}
    sequence = 10

    for line in lines:
        normalized = _normalize(line)
        prefix_match = re.match(r"^([^:]+):\s*(.+)$", line)
        if prefix_match:
            prefix = _normalize(prefix_match.group(1).strip())
            field_name = ENCOUNTER_PREFIXES.get(prefix)
            if field_name:
                value = prefix_match.group(2).strip()[:5000]
                if encounter_payload.get(field_name):
                    encounter_payload[field_name] += "\n" + value
                else:
                    encounter_payload[field_name] = value
                continue

        tooth_match = re.search(r"\bpieza\s+([1-8][1-8])\b", normalized)
        condition = _first_alias(normalized, CONDITIONS)
        if tooth_match and condition:
            surface = _first_alias(normalized, SURFACES) or "whole"
            status = "existing"
            if "planific" in normalized:
                status = "planned"
            elif "realizad" in normalized or "completad" in normalized:
                status = "completed"
            elif "observacion" in normalized or "monitoreo" in normalized:
                status = "monitor"
            actions.append(
                {
                    "sequence": sequence,
                    "action_type": "odontogram_finding",
                    "payload": {
                        "tooth_code": tooth_match.group(1),
                        "condition": condition,
                        "surface": surface,
                        "status": status,
                        "notes": line[:500],
                    },
                }
            )
            sequence += 10
            continue

        when = _local_datetime(session, line)
        if normalized.startswith("reprogramar") and when:
            actions.append(
                {
                    "sequence": sequence,
                    "action_type": "reschedule_appointment",
                    "payload": {"new_start": when},
                }
            )
            sequence += 10
            continue
        if normalized.startswith("agendar") and when:
            actions.append(
                {
                    "sequence": sequence,
                    "action_type": "create_appointment_draft",
                    "payload": {"start": when},
                }
            )
            sequence += 10
            continue
        if normalized in {"cancelar cita", "cancele la cita"}:
            actions.append(
                {
                    "sequence": sequence,
                    "action_type": "cancel_appointment",
                    "payload": {},
                }
            )
            sequence += 10
            continue
        warnings.append(f"No se interpretó: {line[:300]}")

    if encounter_payload:
        actions.insert(
            0,
            {
                "sequence": 5,
                "action_type": "create_encounter_draft",
                "payload": encounter_payload,
            },
        )
    return actions, warnings
