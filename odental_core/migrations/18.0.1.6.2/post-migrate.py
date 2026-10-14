"""Map known legacy free-text labels; keep unknown text for clinical review."""

import logging
import unicodedata


_logger = logging.getLogger(__name__)


def _key(value):
    value = unicodedata.normalize("NFKD", (value or "").strip().casefold())
    return " ".join("".join(c for c in value if not unicodedata.combining(c)).split())


ALIASES = {
    "odontologia general": "specialty_general",
    "odontologo general": "specialty_general",
    "endodoncia": "specialty_endodontics",
    "endodoncista": "specialty_endodontics",
    "ortodoncia": "specialty_orthodontics",
    "ortodoncista": "specialty_orthodontics",
    "periodoncia": "specialty_periodontics",
    "periodoncista": "specialty_periodontics",
    "odontopediatria": "specialty_pediatric",
    "odontopediatra": "specialty_pediatric",
    "cirugia oral y maxilofacial": "specialty_oral_surgery",
    "cirujano maxilofacial": "specialty_oral_surgery",
    "prostodoncia": "specialty_prosthodontics",
    "rehabilitacion oral": "specialty_oral_rehabilitation",
    "implantologia oral": "specialty_implantology",
    "implantologia": "specialty_implantology",
    "patologia oral": "specialty_oral_pathology",
    "radiologia oral y maxilofacial": "specialty_oral_radiology",
}


def migrate(cr, version):
    cr.execute(
        """SELECT name, res_id FROM ir_model_data
             WHERE module = 'odental_core' AND model = 'odental.specialty'"""
    )
    catalog = dict(cr.fetchall())
    cr.execute(
        """SELECT id, specialty FROM odental_professional
             WHERE specialty IS NOT NULL AND BTRIM(specialty) != ''"""
    )
    unrecognized = 0
    for professional_id, legacy_label in cr.fetchall():
        specialty_id = catalog.get(ALIASES.get(_key(legacy_label)))
        if not specialty_id:
            unrecognized += 1
            continue
        cr.execute(
            """INSERT INTO odental_professional_specialty_rel (professional_id, specialty_id)
                 SELECT %s, %s
                  WHERE NOT EXISTS (
                      SELECT 1 FROM odental_professional_specialty_rel
                       WHERE professional_id = %s AND specialty_id = %s
                  )""",
            (professional_id, specialty_id, professional_id, specialty_id),
        )
    if unrecognized:
        _logger.warning(
            "O Dental: %s legacy professional specialties need manual catalog review; original text preserved.",
            unrecognized,
        )
