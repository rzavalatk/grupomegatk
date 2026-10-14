# O Dental Expediente Clínico

Segundo bloque funcional de O Dental para Odoo 18.

Incluye expediente único por paciente, antecedentes con sensibilidad y reglas de
referencia, evoluciones clínicas firmadas e inmutables, rectificaciones versionadas,
consentimientos con instantánea del documento, huella SHA-256 y auditoría clínica.

## Anamnesis

En el expediente, la pestaña «Anamnesis» muestra las atenciones con fecha,
profesional, motivo de consulta e historia de la enfermedad actual. Al abrir una
atención se registran el relato del paciente, inicio y evolución de los síntomas,
hábitos orales, otros antecedentes, interconsultas y signos vitales de esa fecha.
La firma protege estos campos; una corrección de una atención firmada se hace
mediante una rectificación que conserva la versión anterior.

La ficha de paciente incorpora ocupación, estado civil y datos de identificación
del responsable cuando corresponda. El cuestionario de enfermedades con
respuestas Sí/No y las fichas de evolución y sintomatología de endodoncia quedan
pendientes de las plantillas clínicas que proporcionará MegaSmile. Esta versión
no crea respuestas por defecto ni sustituye el criterio del profesional.

