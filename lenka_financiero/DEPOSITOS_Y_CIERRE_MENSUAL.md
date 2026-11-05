# Depositos adicionales y cierre de intereses

Version del nucleo: **18.0.1.0.15**. El puente de cheques mantiene **18.0.1.0.2**.

## Operacion

En **Inversionistas / Depositantes**, abrir una cuenta activa y elegir **Registrar deposito adicional**. Indicar fecha efectiva de ingreso, importe, banco o caja de la misma empresa y referencia del comprobante. Cada ingreso conserva la moneda, tasa y vencimiento del contrato original. La regla comercial de abrir otra cuenta una vez transcurridos tres meses se gestiona fuera del software; no se agrega un bloqueo automatico.

**Confirmar y crear borrador contable** aumenta el capital una sola vez y prepara un asiento borrador: debito al banco / caja receptora y credito a la obligacion con el inversionista. Requiere los permisos existentes de Lenka y Contabilidad; no asigna roles a usuarios. Revisar y publicar la partida desde Contabilidad. Solo usar para ingresos nuevos, sin un asiento previo; esta entrega no vincula automaticamente depositos ya contabilizados.

El banco debe tener su cuenta de liquidez configurada y la empresa su cuenta de obligacion con inversionistas de pasivo. Se respetan empresa y moneda. No se crean cuentas, bancos ni configuraciones al instalar. Un ingreso con un cierre de intereses en su fecha o posterior se rechaza para evitar alterar historia silenciosamente. Una referencia ya confirmada en la misma cuenta y banco no puede confirmarse otra vez.

El capital original se conserva. Los saldos muestran depositos adicionales, capital vigente y saldo de la cuenta incluyendo intereses netos pendientes. Los estados de cuenta incluyen los ingresos adicionales en su fecha y en los saldos iniciales posteriores.

## Cierre calendario

**Generar intereses al cierre** calcula los meses cerrados hasta la fecha actual. No programa ni ejecuta una tarea automatica al instalar, ni publica asientos. Cada linea tiene inicio, fecha final, dias reconocidos y divisor del mes. Si hay ingresos dentro del mes, la base mostrada es el capital promedio ponderado por dias.

El dia de ingreso se incluye. Los retiros y el vencimiento contractual dejan de devengar desde el inicio de su fecha. El divisor es el numero real de dias del mes: 28, 29, 30 o 31. Un mes completo genera exactamente la tasa mensual; la tasa anual se divide entre doce. La capitalizacion mensual incorpora el interes neto despues de la retencion configurada al terminar el mes; los contratos con pago al vencimiento no lo capitalizan.

Ejemplo ficticio: apertura el 20 de septiembre con capital 100,000 y tasa mensual 1.5%. Del 20 al 30, inclusive, son 11 dias: 100,000 x 1.5% x 11/30 = 550. Sin retencion, octubre comienza con base 100,550; su cierre reconoce 1,508.25. No se registra este ejemplo automaticamente.

Los retiros mantienen la liquidacion y tasa anticipada contratadas. Los depositos y retiros se serializan con el calculo para impedir dobles confirmaciones o cierres concurrentes sobre saldos distintos.

## Historial anterior

La instalacion no recalcula ni borra intereses, prestamos, cheques, asientos ni correlativos existentes. Las cuentas existentes adoptan el cierre calendario para lo siguiente, conservando las filas anteriores y su fecha. Si la ultima fila historica termina el 20 de octubre, el siguiente tramo es del 21 al 31 de octubre; no se duplica ningun dia. Esto es continuidad prospectiva, no una correccion retroactiva de los meses anteriores. Revisar por separado cualquier necesidad de recalcular el historial real antes de ejecutar acciones financieras.

El motor anterior por aniversario se conserva para compatibilidad con contratos historicos identificados explicitamente y para su suite de regresion; no se ofrece como alternativa editable en la pantalla ni es el valor por defecto.

Un deposito confirmado no puede reescribirse o eliminarse. Puede anularse si su partida sigue en borrador y todavia no tiene intereses o retiros posteriores. La anulacion conserva el registro y cancela el borrador. Si la partida ya esta publicada, se requiere una regularizacion contable revisada; la funcion no revierte contabilidad publicada automaticamente.

## Despliegue y verificacion

Actualizar **lenka_financiero** a 18.0.1.0.15 con el mecanismo autorizado. No reinstalar `banks`; conservar `lenka_banks` 18.0.1.0.2 y su configuracion. Comprobar la version instalada y que la cuenta muestre el cierre calendario, boton de deposito, pestana de ingresos y saldos. Verificar las vistas sin confirmar movimientos reales como prueba.

La CI ejecuta la suite completa del nucleo, el puente con `banks` real y una actualizacion desde el codigo anterior con datos exclusivamente ficticios de otra empresa. La actualizacion compara todos los valores historicos originales de asientos y de una inversion con interes por aniversario; solo admite los nuevos campos de calendario con sus valores iniciales documentados. No se amplian permisos de modelos existentes ni se agregan restricciones globales a `account.move.line`.
