# Entregas de Lenka y Tesorería

Instalar `lenka_financiero` versión 18.0.1.0.13 y el puente `lenka_banks` versión 18.0.1.0.1 sobre el módulo existente `banks`. El puente no se instala automáticamente y no modifica préstamos, asientos, chequeras ni usuarios existentes al instalarse.

## Actualización aislada de los históricos de otras empresas

Las protecciones de líneas se registran al construir el registro de Odoo, mediante el mecanismo de hooks que también utiliza Audit Log. No se amplía el esquema de `account.move.line` al actualizar Lenka. Los métodos originales y sus permisos siguen ejecutándose; las validaciones adicionales se limitan a asientos efectivamente vinculados a refinanciamientos o cheques Lenka. Se conservan las protecciones de creación, edición y borrado, incluyendo el intento de trasladar una línea hacia un asiento protegido.

La instalación no elimina, modifica ni agrega excepciones a restricciones contables globales. No corrige datos históricos, ni cambia saldos, monedas, estados o correlativos de otras empresas. Esto conserva el despliegue multiempresa existente; no crea una base de datos separada. En producción se configura y utiliza únicamente INVERSIONES LENKA.

CI incluye la actualización desde el código anterior de producción en una base aislada con dos asientos ficticios, uno publicado y otro cancelado, de otra empresa. El escenario reproduce una restricción previamente ausente, instala la actualización y el puente, reinicia Odoo y compara todos los registros históricos y restricciones con su estado original. Ningún dato real se copia a CI.

## Nuevas entregas

Cada desembolso representa una entrega. Para dos cheques por L150,000 crear dos desembolsos, cada uno con su banco y fuente de fondeo. La suma aplicada sigue limitada al monto del préstamo.

Seleccionar **Banco / diario de salida**. Transferencias usan la referencia bancaria y el banco seleccionado. Efectivo requiere un diario de caja. Una entrega directa mediante tarjeta usa un diario general cuya cuenta predeterminada sea la obligación de tarjeta de pasivo corriente; no se registra como salida de Banpaís. El origen del fondeo sigue siendo un dato separado, en la fuente de fondeo del préstamo.

Para **Cheque**, Aplicar desembolso mantiene la reserva financiera; **Crear borrador contable** utiliza `banks.check`, su secuencia del banco y su generador nativo para crear un solo cheque y un solo asiento borrador. Revisar el cheque y publicar su asiento con Contabilidad. **Ver cheques de Tesorería** permite consultar sus números. No se usa otra numeración de Lenka ni se publica automáticamente el asiento.

Se requieren los permisos existentes Gerente de Lenka, Cheques Usuario Avanzado y los permisos contables correspondientes. No se amplían roles ni permisos de usuarios. La chequera debe tener una sola secuencia de tipo cheque sin rangos por fecha. Su configuración debe coincidir con los cheques físicos disponibles antes de emitirlos.

## Cheques ya contabilizados

En un desembolso aplicado por cheque, con asiento publicado y sin cheques vinculados, **Identificar cheques ya contabilizados** abre el desglose. Registrar únicamente los números físicos y valores efectivamente entregados.

Ejemplo ilustrativo, nunca aplicado por la instalación: LENKA-OP-000003, asiento IL-Dep-Ban-L.0306, total L300,000; cheque667 L150,000 y cheque668 L150,000. Los números se formatean con la chequera existente. Deben ser anteriores al siguiente número disponible y no existir en Tesorería ni como otro asiento del mismo banco.

El asistente crea los registros de identificación en `banks.check` vinculados al asiento original; NO crea asientos, cambia líneas, modifica la CxC, publica pagos ni retrocede el correlativo. Los importes deben coincidir exactamente con el asiento y el desembolso. Por ahora esta regularización histórica admite la moneda base de la empresa y asientos simples de cartera contra banco.

Los registros históricos muestran que son identificación de cheques ya contabilizados y permiten comprobante, no una nueva impresión del cheque físico. Se bloquea su regeneración, borrado o anulación directa porque dos cheques pueden compartir el mismo asiento original. Una corrección posterior requiere revisión contable controlada; no se ofrece anulación automática de un cheque de préstamo en esta primera entrega.

## Límites

El puente protege los asientos vinculados y valida la cartera y banco antes de publicarlos. No cambia el circuito general de otros cheques ajenos a Lenka. No hace correcciones retroactivas por sí solo ni mueve fondos.

La referencia de transferencia y los números de cheques son datos diferentes. Los nuevos cheques toman el siguiente número de la chequera de Tesorería; los cheques físicos antiguos se registran mediante el asistente histórico.

El módulo móvil pendiente no está incluido. La rama conserva el refinanciamiento ya contabilizado de la entrega anterior.

CI instala el núcleo con su suite completa y después el puente con el módulo `banks` real en otra base aislada. Verificar ambos resultados antes de instalar.
