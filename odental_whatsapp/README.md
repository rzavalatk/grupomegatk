# O Dental WhatsApp Cloud

Conecta la bandeja de `odental_communications` con WhatsApp Cloud API sin
guardar credenciales en el repositorio.

Incluye cuentas multinúmero por organización, plantillas aprobadas por Meta,
cola con reintentos, webhook con firma HMAC, estados enviado/entregado/leído,
respuestas interactivas e ingreso auditable de solicitudes de confirmación,
cancelación, reprogramación y aceptación de espacios liberados.

Los secretos se cargan mediante el asistente de credenciales y se almacenan
como parámetros protegidos de Odoo. El token de verificación se conserva solo
como resumen SHA-256. Las cancelaciones y reprogramaciones requieren revisión
por defecto; la confirmación puede aplicarse automáticamente.

