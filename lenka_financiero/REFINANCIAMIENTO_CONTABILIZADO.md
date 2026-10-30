# Aplicación de refinanciamiento ya contabilizado

Cambio preparado para Odoo 18. Instalación en producción pendiente de la fecha indicada por Luis Morán. No migra ni aplica préstamos existentes automáticamente.

## Uso después de instalar

1. Revisar que el asiento de traslado esté publicado, con el cargo completo a la cuenta de cartera configurada en Lenka, a nombre del **registro nuevo** del cliente y un abono a la cuenta de intercambio. Ambos deben pertenecer a la empresa del préstamo. No seleccionar el pago del registro anterior.
2. En el préstamo contratado, abrir **Desembolsos → Agregar una línea**.
3. Seleccionar **Medio: Refinanciamiento ya contabilizado**. Un gerente de Lenka con acceso de lectura a la contabilidad selecciona **Apunte de capital ya contabilizado**. El formulario propone importe, fecha, beneficiario y referencia del asiento. No seleccionar fuente de salida bancaria.
4. Revisar y usar **Aplicar desembolso**. El registro conserva el apunte y permite **Ver asiento existente**. No existe una creación de borrador contable para este medio; el servidor también la impide por API.
5. Revisar el total aplicado, los desembolsos con entrega de fondos y el refinanciamiento. Cuando el total cubra el préstamo, usar **Activar operación**. Se mantienen los requisitos de autorización, contrato y fondeo existentes.

Ejemplo: préstamo L 75,000; cheque L 55,730.80 con su número registrado en **Número de cheque / transacción / referencia**; refinanciamiento L 19,269.20 vinculado al apunte de capital del asiento 1023. Total aplicado L 75,000, pendiente cero. El número 1023 es ilustrativo: no se busca ni aplica automáticamente ese asiento real.

## Controles y límites

- Reconoce el cargo completo de un apunte, no aplicaciones parciales ni asientos borrador. Empresa, moneda, cuenta de cartera y cliente deben coincidir exactamente. No identifica clientes por similitud del nombre.
- La contrapartida debe ser activo corriente (intercambio), no banco, ingreso o gasto. No admite asientos de cobros/desembolsos Lenka ni reversiones.
- No transforma ni fusiona contactos. No hace operaciones entre empresas; si el saldo anterior pertenece a otra empresa, debe resolverse la contabilidad intercompañía antes.
- El apunte solo puede utilizarse en una aplicación vigente. Se comprueba por servidor y por índice único parcial. Bloqueos del préstamo y asiento protegen solicitudes concurrentes.
- La aplicación no crea, publica, paga ni concilia asientos; tampoco añade intereses o mora al saldo trasladado. El contador debe verificar la composición del capital previamente.
- Anular antes de activar libera el vínculo operativo y conserva el asiento publicado y el historial. El asiento debe corregirse aparte si corresponde. No se puede anular con el préstamo activo/finalizado.
- Mientras una aplicación esté vigente, se impide modificar o revertir su asiento y modificar la identidad/monto del préstamo. Los cobros posteriores conservan su conciliación normal.
- La opción actual de Reestructuraciones para sustituir un préstamo Lenka se conserva con sus reglas, sin mezclar estos dos circuitos.
- El fondeo existente sigue cubriendo el monto financiado completo; estos registros describen el origen del financiamiento y no constituyen otra salida bancaria.
- Se conserva el campo de referencia de los desembolsos normales, con etiqueta explícita para cheque o transacción y seguimiento de sus cambios. No se vuelve obligatorio para datos históricos.

## Verificación

Se incluyen pruebas Odoo de integración en `tests/test_refinance_application.py` y un workflow exclusivo de la rama de AJZ para ejecutarlas con Odoo 18 y PostgreSQL 16 aislados. Nunca conecta al Odoo instalado ni usa sus credenciales o datos.

Antes de instalar: confirmar el resultado de CI y hacer una prueba en desarrollo con la configuración contable real, especialmente la cuenta de cartera utilizada por el asiento existente. No corregir cuentas reales automáticamente.

Esta rama parte del código de producción 21fdf283 y no incluye la aplicación móvil pendiente de integración. La versión 18.0.1.0.11 evita reutilizar la 18.0.1.0.10 reservada por esa rama; al integrar ambas se debe revisar el manifiesto.
