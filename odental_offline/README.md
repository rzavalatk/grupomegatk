# O Dental Contingencia Offline

Este módulo ofrece una pantalla independiente y adaptable a teléfonos para continuar una atención
cuando falla internet.

## Alcance seguro

- Descarga únicamente las citas autorizadas del intervalo operativo cercano.
- Cifra agenda y anotaciones localmente con AES-GCM.
- Deriva la clave local mediante PBKDF2-SHA-256 con 300,000 iteraciones.
- La clave nunca se envía al servidor ni se conserva en almacenamiento persistente.
- Captura notas clínicas, indicaciones y hallazgos odontológicos.
- Reintenta sin duplicar entradas mediante UUID de lote y de anotación.
- Guarda solo la huella SHA-256 del dispositivo en Odoo.
- Exige revisión profesional antes de crear un borrador clínico.
- Nunca firma evoluciones, recetas ni odontogramas automáticamente.
- Conserva lotes, entradas, revisores, destinos y huellas como evidencia de auditoría.

El `service worker` conserva únicamente la interfaz genérica. Los nombres de pacientes, la agenda y
las anotaciones se almacenan dentro de la bóveda cifrada de IndexedDB.

