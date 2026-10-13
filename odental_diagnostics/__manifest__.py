{
    "name": "O Dental Odontograma e Imágenes",
    "summary": "Odontograma versionado y repositorio de imágenes clínicas y DICOM",
    "version": "18.0.1.1.0",
    "category": "Services/Healthcare",
    "author": "MEGATK / MEDITEKSA",
    "license": "LGPL-3",
    "depends": ["odental_clinical"],
    "data": [
        "security/odental_diagnostics_security.xml",
        "security/ir.model.access.csv",
        "data/odental.tooth.csv",
        "data/odental_diagnostics_sequence.xml",
        "views/odontogram_views.xml",
        "views/clinical_image_views.xml",
        "views/clinical_record_views.xml",
        "views/odental_diagnostics_menus.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "odental_diagnostics/static/src/js/odontogram_chart.js",
            "odental_diagnostics/static/src/xml/odontogram_chart.xml",
            "odental_diagnostics/static/src/scss/odontogram_chart.scss",
        ],
    },
    "application": False,
    "installable": True,
}
