# Vencimiento contable del capital

Entrega propuesta 18.0.1.0.18. Solo repositorio autorizado ajz04megatk/grupomegatk.
La preparacion y CI de esta rama no acreditan instalacion en produccion.

En Desembolsos, un gerente puede indicar **Vencimiento contable del capital**
antes de generar la partida. Solo esa fecha expresamente seleccionada se lleva
al apunte Por cobrar; dejarla vacia conserva el comportamiento anterior.
Tambien cubre los nuevos cheques generados por lenka_banks mediante su enlace
normal, sin consumir ni cambiar otra secuencia.

Para un desembolso aplicado con partida borrador o publicada, **Definir
vencimiento CxC** propone la ultima cuota del plan como referencia y exige
fecha, motivo y confirmacion de que corresponde al capital pactado. Conserva
empresa, cliente, partida, importes, fecha contable, referencias, bancos,
cheques y conciliaciones. Usa los permisos contables nativos, sin sudo.
Rechaza capital ya conciliado, partidas revertidas o inconsistentes, apuntes
compartidos por importes diferentes y cuentas que no sean de tipo Por cobrar.
Los refinanciamientos ya aplicados permiten revisar su propio apunte existente;
no se crea otra CxC. El cambio deja nota en el desembolso.

La instalacion no modifica ninguna fecha de partidas existentes. Tampoco
recalcula planes, contratos, cobros, intereses ni mora. No cambia saldos reales.

El vencimiento final no sustituye los vencimientos parciales del capital: si
el contrato amortiza en cuotas, un unico apunte al final no muestra ese
desglose en antiguedad de saldos. El usuario debe confirmar el criterio
contractual antes de aplicarlo. Para el caso consultado, el plan observado
termina el 14/09/2028; no asumir automaticamente 14/10/2028 o 16/11/2028.
No se ejecutan ejemplos reales durante las pruebas o la instalacion.
