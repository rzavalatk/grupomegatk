# Cobros: banco, caja o intercambio por transaccion

Nucleo 18.0.1.0.17. Conservar lenka_banks 18.0.1.0.2 y banks existente.

La Forma de pago describe el medio; Destino del cobro y Banco / diario receptor determinan la cuenta debitada. Se muestra la Cuenta receptora antes de aplicar. Banco y Caja exigen diarios y cuentas de liquidez del tipo correspondiente y de la empresa del prestamo. Intercambio interno exige un diario general con cuenta puente de activo corriente, o el diario puente interno ya designado para esa empresa, sin cuenta bancaria real vinculada. Esta excepcion conserva su clasificacion historica; no convierte otros bancos en intercambio ni reclasifica cuentas. No se cambia ninguna configuracion al instalar.

Aplicar y crear borrador contable distribuye el pago y crea una sola partida borrador en una transaccion. Requiere los permisos existentes de Lenka y Contabilidad; no se conceden permisos nuevos ni se usa sudo para contabilizar. Si falla la configuracion o el permiso contable, tambien se revierte la aplicacion a cuotas. La partida debe revisarse y publicarse en Contabilidad para afectar saldos contables. Aplicado en Lenka y Publicado en Contabilidad son estados distintos y ambos quedan visibles.

Se conserva la distribucion existente entre mora, intereses, capital y anticipos. Un pago exclusivamente de intereses debita el destino seleccionado y acredita ingresos por intereses; no reduce capital. La serie LENKA-COB- se asigna una vez por partida nueva, sin consumir ni ajustar correlativos bancarios ni permitir que asientos ordinarios continuen esta serie. Las recepciones de inversionistas conservan su serie LENKA-REC-.

Los cobros antiguos conservan sus valores y partidas. No se escoge automaticamente banco o intercambio para ellos, ni se genera contabilidad al instalar. Para un cobro Aplicado sin partida, el gerente puede seleccionar destino y Crear borrador contable sin aplicar otra vez el pago. Antes debe comprobar si ya existe un asiento registrado en el banco: esta entrega no vincula automaticamente asientos de otros procesos y no debe duplicarse el ingreso. No crear un segundo cobro para completar la contabilidad del primero.

Los datos del destino se bloquean al crear la partida. Antes de publicarla se validan diario, empresa, fecha, cliente, moneda, importes y distribucion. Tras publicarla se protegen sus datos financieros y lineas, como los otros movimientos vinculados de Lenka; una correccion requiere regularizacion contable. No se cambian restricciones globales de SQL ni se escriben datos de otras empresas.

Validacion: suite del nucleo, integracion con banks real, dos solicitudes concurrentes del mismo cobro y actualizacion con historicos ficticios. Ningun prestamo, pago, cheque o asiento real se utiliza como prueba.
