# O Dental Caja y Facturación

Bloque financiero inicial para Odoo 18:

- factura clínica en borrador desde un plan aprobado;
- facturación centralizada o independiente según la compañía del plan;
- autorización SAR por empresa, sede, diario y tipo de documento;
- CAI, vigencia y rango capturados exactamente desde la autorización oficial;
- correlativo fiscal asignado de forma transaccional al publicar;
- sesiones de caja, arqueo y diferencias;
- cobros vinculados al asistente estándar de pagos de Odoo.

O Dental no genera CAI ni publica documentos automáticamente. El administrador registra la
autorización emitida por SAR y el contador conserva el control final sobre la publicación y el pago.

## Control de abonos y caja

- Un abono menor que el saldo exige motivo y autorización del propietario de la
  organización, distinta persona del cajero. Conserva usuario, fecha, importe y saldo.
- Cambiar los datos del cobro invalida su autorización. El asistente de pago vuelve
  a validarla y no permite modificar importe, diario, moneda o factura ni dar de
  baja el saldo restante como diferencia.
- Las facturas clínicas se cobran desde Cobros clínicos. El pago contable queda
  enlazado antes de publicarse, y un pago registrado no puede alterarse o borrarse.
- Las cajas, cobros, presupuestos aprobados y correlativos emitidos no se desbloquean
  mediante parámetros enviados por el cliente.
- Los pagos dentales no generan tickets de sorteos de la personalización comercial.
- Caja depende de tratamientos y contabilidad; no requiere instalar comunicaciones
  ni alquileres para recibir pacientes y cobrar.

## Alcance y pendientes antes de producción

Este bloque debe revisarse antes de instalarlo para cobros reales. No configura
empresas, usuarios, permisos de contabilidad, impuestos, diarios ni rangos fiscales.

La base utilizada en pruebas contiene personalizaciones que exigen la ubicación
regional del cajero y un permiso de lectura SAR al crear asientos. Los usuarios
sintéticos de prueba incluyen esos requisitos; no se han asignado a usuarios reales.
El permiso SAR existente requiere revisar sus reglas por compañía antes de
concederlo a una nueva clínica. No se agregan permisos de sorteos al cajero.

Si existe otro módulo fiscal SAR instalado, el contador debe definir un solo flujo
fiscal antes de activar el control fiscal dental. No habilitar dos generadores de
correlativos sobre una misma factura ni inventar CAI, impuestos o autorizaciones.

Las pruebas verifican operaciones secuenciales y aislamiento de lectura clínica;
no certifican concurrencia de dos cobros simultáneos ni todas las vías de conciliación
manual de contabilidad. Las devoluciones y anulaciones de cobros registrados requieren
un flujo supervisado de rectificación pendiente de implementar.

Una autorización informática no prueba cuánto efectivo entregó físicamente un
paciente: siguen siendo necesarios recibos verificables y supervisión del arqueo.
