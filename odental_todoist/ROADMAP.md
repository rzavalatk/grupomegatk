# Próximos conectores y reserva en línea

## Sincronización rápida y despliegue permanente

La tarea programada de Odoo.sh funciona según disponibilidad y no garantiza
menos de cinco minutos, incluso en producción. Staging reduce la frecuencia
cuando la base está inactiva. Mantener el sondeo como conciliación de respaldo.

Para reducir la espera: publicar cambios de O Dental tras confirmar la
transacción y recibir eventos `item:added`, `item:updated`, `item:deleted`,
`item:completed` y `item:uncompleted` mediante el webhook de Todoist. El
webhook necesita aplicación registrada, URL HTTPS pública y autorización OAuth
de la profesional; su token personal actual no habilita esas notificaciones.
Verificar firma HMAC, identidad y organización de cada evento, evitar bucles y
duplicados, y volver a consultar Todoist en vez de confiar en datos de un
evento retrasado o fuera de orden. Conservar la prioridad de la hora elegida
por la doctora y la señal de conflicto, sin mover silenciosamente pacientes.

La activación para pacientes reales queda separada del despliegue de código:
`export_all_patients` empieza desactivado. Confirmar expresamente el envío a
Todoist de nombre, servicio general y horario para todas las citas futuras
de MegaSmile antes de activarlo. Una reconstrucción de staging copia otra vez
producción y puede perder la conexión y token de esta prueba; preparar una
nueva prueba y autorización OAuth sin interrumpir el piloto actual.

La cita clínica vive en `odental.appointment`. El profesional decide la hora
desde su agenda personal cuando la conexión está activa; recepción también
puede editarla en O Dental. Si ambos lados cambian la hora antes de conciliar,
se aplica la del profesional. Una colisión con otra cita queda marcada para
revisión y nunca desplaza a un segundo paciente de forma silenciosa.

## Google Calendar y otros calendarios

Agregar un adaptador por proveedor con identificador externo, fechas UTC,
organización, profesional y última versión conciliada. Solo importar intervalos
ocupados privados; los eventos clínicos salientes muestran los datos mínimos
que autorice la clínica. Identificar y excluir eventos generados por O Dental
para evitar bucles y bloques duplicados si Todoist ya se sincroniza con Google.
Outlook y Apple Calendar requieren evaluar autenticación y capacidades del
proveedor antes de conectarlos. No activar cuentas sin autorización del titular.

## Enlace para pacientes

Implementar por organización, sede, profesional y servicio. El enlace para
invitación debe tener token revocable y vencimiento; la clínica también podrá
habilitar una página pública separadamente. Mostrar solo horas disponibles,
nunca nombres de pacientes ni contenido de agendas personales.

Calcular huecos con horarios de atención, descansos, duración del servicio,
preparación/limpieza, consultorio y equipos; descontar citas clínicas, bloqueos
personales y solicitudes pendientes. Pedir únicamente datos de contacto y
consentimiento, validar de nuevo el hueco al enviar y evitar reservas
simultáneas. La primera versión crea una **solicitud pendiente** para recepción;
confirmarla genera la cita clínica y sincroniza la agenda del profesional.
La confirmación automática puede habilitarse después de probar recursos,
colisiones y aislamiento por empresa. Nunca exponer expedientes al público.

Odoo 18 tiene su propia aplicación Citas con enlaces compartibles, pero una
reserva allí no debe considerarse cita O Dental hasta construir y probar un
puente con `odental.appointment` y sus reglas de disponibilidad.
