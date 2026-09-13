# O Dental Core

Primer bloque funcional de O Dental para Odoo 18.

Incluye:

- organizaciones individuales, compartidas, clínicas e institucionales;
- profesionales y pacientes separados por organización;
- sedes y recursos reservables (consultorios, sillones, equipos y asistentes);
- servicios con duración, preparación y limpieza configurables;
- duración particular por profesional;
- agenda con calendario, flujo de estados y prevención de conflictos;
- perfiles de usuario clínico, profesional, administrador clínico y administrador global;
- reglas de acceso por organización.

## Validación local

```bash
python3 tools/validate_odental.py
```

Las pruebas funcionales de Odoo están en `odental_core/tests/` y deben ejecutarse en la rama de desarrollo de Odoo.sh con el módulo instalado.

