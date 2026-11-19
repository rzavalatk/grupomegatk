# Correccion de fechas de captura

Version 18.0.1.0.19. La actualizacion no cambia registros existentes automaticamente.

En una operacion de tipo prestamo, en estado Contratada y antes de registrar cobros,
el usuario configurado como Luis Moran, con sus permisos existentes de gerente y
autorizacion exclusiva, puede abrir **Corregir fechas del contrato**.

El asistente permite revisar fecha de operacion, fecha del contrato y primera cuota.
Muestra la ultima cuota resultante y el inicio de cuota nivelada. Exige motivo y
confirmacion expresa. Conserva los IDs de las cuotas y sus importes: solo desplaza
las fechas de un plan mensual regular. No recalcula capital, intereses, tasa o plazo.

No modifica autorizaciones, firmas, documentos, fondeo, desembolsos, asientos,
conciliaciones, cuentas, vencimientos contables ni correlativos. Los PDF firmados
originales se conservan y no se regeneran; su respaldo documental debe revisarse
separadamente. La fecha de firma original y la fecha contractual son datos distintos.

Bloquea planes personalizados o incompletos, operaciones activas o reestructuradas,
cobros (incluidos borradores), aplicaciones, mora registrada, capital conciliado,
partidas revertidas, fechas posteriores al desembolso y revisiones que quedaron
desactualizadas. Un error revierte toda la correccion. No permite editar otros datos
usando un indicador de contexto enviado desde el navegador.

El boton **Definir vencimiento CxC** permanece como una revision contable separada.
El desplazamiento del plan no cambia automaticamente el vencimiento del capital.

Las pruebas utilizan exclusivamente operaciones y documentos ficticios en CI.
