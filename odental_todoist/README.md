# Disponibilidad de O Dental desde Todoist

Piloto para intercambiar disponibilidad entre O Dental y la agenda personal del
profesional. Las reuniones de Todoist bloquean O Dental: recepción solo ve
**No disponible**, el profesional y el intervalo; sus títulos y descripciones
no se copian. Las citas clínicas se publican en el Inbox privado de Todoist
con nombre del paciente, servicio general y horario, sin expediente ni notas.

## Preparación

1. Actualizar `odental_core` e instalar `odental_todoist` en una base de prueba.
2. Verificar que el usuario de Odoo del odontólogo tenga el grupo **Profesional**,
   esté enlazado a su ficha de profesional y que esa ficha pertenezca a la
   organización y compañía clínicas correctas. Esto es necesario para que
   aparezca **O Dental → Clínica → Conectar mi Todoist**. No añadir otras
   compañías ni permisos de administración generales.
3. El profesional obtiene su token personal en su propia cuenta de Todoist y
   lo pega directamente en el formulario de Odoo. No enviarlo por chat ni a la
   recepcionista. Elegir etiqueta `reunión` y zona `America/Tegucigalpa`.
4. Crear en Todoist una tarea con la etiqueta `@reunión` y fecha **con hora**.
   Si Todoist permite duración explícita, se respeta; en una cuenta sin esa
   función se usa la duración predeterminada (60 minutos, configurable).
   Se importa como bloqueo privado al conectar y luego mediante una tarea
   programada. En Odoo.sh no se puede prometer una ejecución más frecuente que
   cada cinco minutos; staging puede tardar más si nadie usa la base.
   También se puede pulsar **Actualizar ahora**.

Al completar, eliminar o quitar la etiqueta, el siguiente sondeo cancela el
bloqueo en O Dental y libera el horario. Al cambiar hora o duración, mueve el
mismo bloqueo. Una cita clínica preexistente no se borra si entra un bloqueo
externo con conflicto: el formulario del bloqueo señala la coincidencia para
revisión humana. Una cita clínica creada por recepción aparece como tarea con
etiquetas `reunión` y `odental` en Todoist; mover la hora de esa tarea actualiza
la cita clínica, y mover o cancelar la cita en O Dental actualiza o elimina la
tarea. Si dos personas mueven la cita entre sondeos, prevalece la hora de
Todoist. Un choque clínico impide aplicar el cambio y muestra una advertencia
en la cita; se debe resolver antes de confirmarlo al paciente. Completar o
eliminar la tarea espejo no cancela una cita clínica de paciente: el sistema
la vuelve a publicar para evitar una cancelación accidental.

Las tareas sin hora no bloquean. Las fallas de API o
respuestas incompletas mantienen los bloqueos anteriores y dejan un estado de
error en **Mi disponibilidad Todoist**; el horario requiere revisión hasta que
se restablezca la sincronización. **Desconectar** borra el token almacenado y
libera los bloqueos de esa conexión, con confirmación visible.

Por defecto solo se exportan las citas del paciente sintético seleccionado.
El campo administrativo `export_all_patients` permite una activación posterior
para todas las citas de ese profesional y organización. Antes de activarlo hay
que validar conflictos y cancelaciones, obtener confirmación específica para
enviar nombres y servicios generales de pacientes reales al Todoist del
profesional y confirmar la identidad y acceso de la cuenta. No se activa al
actualizar el módulo.

El receptor `/odental/todoist/webhook` está inactivo mientras no se configure
`odental_todoist.webhook_client_secret` con el secreto de una aplicación Todoist
registrada. Comprueba HMAC y el ID del titular, consulta de nuevo Todoist y
conserva el sondeo como respaldo. Jennifer debe autorizar esa aplicación por
OAuth para que Todoist envíe eventos; su token personal no activa avisos. No
registrar ni autorizar una aplicación desde una cuenta ajena a la titular.

## Prueba de aceptación

- Crear tarea de prueba 10:00–11:00 con etiqueta `@reunión`; actualizar y
  comprobar **No disponible** en Agenda y rechazo de una nueva cita solapada.
- Moverla a 12:00; actualizar y comprobar disponible 10:00–11:00 y ocupado
  12:00–13:00.
- Completarla; actualizar y comprobar liberado 12:00–13:00, con el bloqueo
  cancelado fuera de la Agenda habitual.
- Repetir desde un usuario de otra clínica: no debe ver ni administrar la
  conexión, la tarea o la cita clínica de la primera organización.
- Crear cita clínica de prueba: debe aparecer en el Inbox Todoist con nombre y
  servicio general. Moverla en Todoist y comprobar la nueva hora en O Dental;
  moverla desde O Dental y comprobar el cambio en Todoist. Cancelarla en O
  Dental y comprobar que la tarea correspondiente desaparece.

Este módulo no integra Google Calendar, Outlook, Apple Calendar ni relojes;
esas fuentes requieren sus propios conectores y una política contra bloqueos
duplicados antes de activarse conjuntamente.
