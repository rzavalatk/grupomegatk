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
- Saldos contables de bancos, tarjetas y préstamos solo de lectura, con saldo real editable.
- Solo efectivo y bancos forman el disponible; tarjetas y préstamos se muestran como obligaciones y no alteran la liquidez.
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
