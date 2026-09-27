# O Dental Tratamientos y Presupuestos

Extiende O Dental con planes clínicos versionados, aceptación verificable del paciente y
conversión controlada a cotizaciones de Ventas de Odoo 18.

## Alcance

- Procedimientos por servicio, pieza y superficie dental.
- Precios, descuentos, impuestos, totales y avance clínico.
- Facturación centralizada por la clínica o independiente por profesional.
- Presentación, aprobación, rechazo, inicio, finalización y cancelación.
- Huella SHA-256 del contenido aprobado y bloqueo de cambios comerciales.
- Revisiones que preservan la versión aprobada anterior.
- Cotización en borrador vinculada al plan, creada solo por administradores.
- Auditoría clínica de los eventos principales.

El módulo no confirma pedidos ni emite facturas automáticamente.

## Integridad y separación por empresa

Los planes se crean en borrador. Los datos de aprobación y enlaces a cotización se
registran mediante las acciones del sistema. Un parámetro de contexto no desbloquea
planes aprobados; tampoco se pueden añadir o mover procedimientos a una versión
aprobada mediante valores predeterminados.

Los impuestos sugeridos se filtran por compañía de facturación. Los contactos
nuevos creados por el plan se asignan a esa compañía. El origen automático de un
producto solo puede registrarlo el sistema. Las etiquetas principales están en español.

Elegir correo, WhatsApp o portal como método de aceptación registra la evidencia
capturada por el operador; por sí solo no envía ni valida códigos externos.
