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

## Catálogo de especialidades y áreas de práctica

En **Configuración clínica > Especialidades**, el administrador clínico puede
crear, renombrar y archivar especialidades propias de su compañía. Las entradas
estándar compartidas se muestran para selección, pero solo el administrador
global de O Dental puede cambiarlas. En la ficha del profesional, el selector
permite «Crear y editar» una entrada local mediante su formulario completo;
la creación rápida de texto libre permanece desactivada. Se pueden asignar
varias áreas a un mismo profesional y consultar el reporte por especialidad.

Ejemplos como terapia láser pueden registrarse como áreas de práctica; un
procedimiento concreto, como una sesión de terapia láser o una aplicación de
toxina botulínica, se define por separado en **Configuración clínica > Servicios**.
Registrar un área no equivale a validar credenciales o habilitación profesional.

## Validación local

```bash
python3 tools/validate_odental.py
```

Las pruebas funcionales de Odoo están en `odental_core/tests/` y deben ejecutarse en la rama de desarrollo de Odoo.sh con el módulo instalado.
