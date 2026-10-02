# Flujo de caja proyectado

Módulo multiempresa para la proyección operativa, sin generar asientos ni modificar la contabilidad.

Incluye:

- Semanas 1, 2, 3 y Pendiente.
- Cobros esperados y pagos programados con historial en el chatter de Odoo.
- Registro de la nueva gestión y consulta del historial completo directamente desde cada cliente en CxC.
- Programación directa del cobro o pago desde cada fila de cartera, con empresa, contacto y tipo prellenados.
- Actualización inmediata de las insignias de semana al crear, mover o retirar una proyección.
- La última gestión es de solo lectura: toda observación nueva conserva fecha, autor e historial.
- Clasificación por empresa de clientes, CxC empleados, Grupo Mega, proveedores, acreedores, anticipos, legal, por depurar y por asignar.
- Saldos contables exclusivamente por la cuenta específica seleccionada, aunque varias cuentas compartan el diario bancario "Cheques"; cambiar el diario nunca sustituye esa cuenta.
- Disponible inicial visible y acumulativo para cada semana, incluidos los saldos negativos.
- Listas separadas para cobros, pagos a proveedores, pagos únicos y pagos recurrentes.
- Reporte ejecutivo y detallado en pantalla, PDF y archivo compatible con Excel.
- Menús y pestañas con verde para ingresos y rojo para salidas.
- Saldos en la moneda original de cada cuenta, con tipo de cambio, equivalente en lempiras y diferencia visible.
- Saldos de tarjetas y préstamos en su moneda original, con deuda proyectada después de consumos, desembolsos y pagos.
- Solo efectivo y bancos forman el disponible; tarjetas y préstamos se muestran como obligaciones y no alteran la liquidez.
- Un pago directo a proveedor con tarjeta aumenta la deuda de la tarjeta, pero no reduce el efectivo hasta que se pague la tarjeta.
- Separación operativa entre cobros de clientes, otros ingresos, pagos a proveedores y otros egresos.
- Otros ingresos permiten registrar préstamos o aportes de personas que no existen como contactos de Odoo.
- Egresos manuales recurrentes, por ejemplo planilla y alquiler, con moneda, fecha de tipo de cambio y equivalente en la moneda de la empresa.
- Tres roles configurables desde Ajustes > Usuarios: Gestor de cobros, Usuario y Administrador.
- Actualización inmediata del detalle de cartera desde Odoo, además de la actualización automática diaria.
- Aplicación independiente con icono propio en el selector de aplicaciones de Odoo.

## Roles

- **Gestor de cobros:** consulta solamente CxC, genera el detalle y registra nuevas gestiones con fecha y responsable.
- **Usuario:** administra la proyección, bancos, cobros, pagos y gastos manuales de sus empresas permitidas.
- **Administrador:** configura clasificaciones y conserva control total del módulo.

## Reglas operativas

- El módulo nunca crea asientos, facturas, pagos ni conciliaciones.
- El detalle de cartera se reconstruye con partidas abiertas de Odoo; no replica la contabilidad.
- Un saldo negativo en CxC se presenta como crédito; uno positivo en CxP como anticipo. Los demás saldos se clasifican por vencimiento.
- Cada usuario solo consulta y registra información de las compañías que tenga activas en Odoo.
- Bancos, cuentas, partidas y clasificaciones respetan la empresa activa y no pueden cruzarse entre compañías.
- Una cuenta contable solo puede aparecer una vez en el flujo; un mismo diario sí puede agrupar varias cuentas diferentes.
