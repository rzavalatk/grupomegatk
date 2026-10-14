# Dictado e inteligencia clínica de O Dental

## Objetivo

El profesional dicta hallazgos en español durante la consulta. O Dental propone
campos estructurados del paciente correcto, muestra lo interpretado y permite
corregirlo antes de guardar. Cada alta o modificación queda atribuida al usuario
que la confirmó. La voz no firma consentimientos, evoluciones ni odontogramas.

## Primera entrega: hallazgo del odontograma (en desarrollo)

1. En un odontograma guardado como borrador, abrir **Dictar hallazgo**.
2. Dictar localmente en un navegador compatible o escribir el texto. No se
   inicia reconocimiento remoto de voz. Si falta reconocimiento local en español,
   se informa y se conserva la entrada manual.
3. Interpretar un hallazgo por vez. Se admiten código FDI o nombre de la pieza,
   superficie, condición, estado y texto después de «detalle» o «nota».
4. Mostrar los campos propuestos. Ante datos ausentes o ambiguos, dejar el campo
   vacío para que el profesional lo corrija. No inventar diagnósticos.
5. **Guardar hallazgo revisado** aplica las validaciones del modelo y escribe
   auditoría de creación y de revisión del dictado. Se respeta el acceso por
   organización y se rechazan odontogramas firmados.

Ejemplo: «Tercer molar superior derecho, superficie oclusal, fractura,
existente, detalle: borde distal». Propone pieza 18, superficie oclusal,
condición fractura, estado existente y el detalle indicado.

Esta entrega usa reconocimiento local del dispositivo cuando está disponible
y reglas conservadoras para estructurar un solo hallazgo. No constituye aún
un asistente de IA que comprenda narraciones clínicas libres o varios hallazgos.

## Asistente clínico completo (pendiente)

- Dictado continuo por consulta, identificación inequívoca de paciente,
  expediente, profesional, sede y encuentro antes de proponer cambios.
- Propuestas separadas para antecedentes, evolución, diagnóstico, tratamiento,
  odontograma, procedimientos y metadatos de imágenes. La agenda y los cobros
  requieren sus propios flujos y permisos; no se mezclan con hallazgos clínicos.
- Extracción con modelo clínico configurable, salida tipada y validada contra
  catálogos O Dental; vocabulario dental de Honduras y numeración FDI.
- Pantalla de diferencias y confirmación por campo, incertidumbre visible,
  corrección manual y prevención de duplicados. Nunca publicar por inferencia
  un diagnóstico, consentimiento o firma.
- Registro de quién dictó, quién revisó, qué propuso el sistema, qué se aceptó
  y qué se corrigió. Retención de audio y transcripción configurable por clínica.
- Elección y evaluación de motor de voz y modelo de lenguaje, privacidad,
  residencia de datos, costos y autorización específica antes de enviar audio
  o datos de salud a un servicio externo. Odoo.sh no incluye por sí solo ese motor.
- Pruebas clínicas con casos sintéticos, varias piezas/superficies, negaciones,
  correcciones, acentos, ruido, paciente equivocado, acceso entre empresas y
  cancelación sin guardar.

## Estado

El primer flujo está preparado en código para revisión y pruebas Odoo.sh.
El asistente clínico completo, la integración de un modelo de lenguaje y la
compatibilidad universal de dictado aún no están implementados ni habilitados
en MegaSmile.
