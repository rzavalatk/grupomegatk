# Preparación de instalación — Financiero Lenka

Fecha: 6 de octubre de 2026.

## Destino y autorización

Destino previsto: proyecto Odoo.sh `grupomegatk`, rama `master`, https://grupomegatk.odoo.com/odoo, compartido con O Dental. Aplicar únicamente el módulo `lenka_financiero`; no actualizar ni reinstalar módulos ajenos.

PR de preparación: https://github.com/rzavalatk/grupomegatk/pull/58. Mantener en borrador, sin auto-merge. Luis debe dar una orden expresa para instalar. Su autorización de pruebas no autoriza producción.

Sentinel es exclusivamente el entorno autorizado de pruebas. Sus datos y permisos no se trasladan automáticamente a producción. Android e iPhone siguen fuera de esta entrega.

## Resultado técnico verificado

- Versión: 18.0.1.0.2.
- Batería Odoo 18: **196 pruebas, 0 fallos, 0 errores**, build `grupomegatk-lenka-pilot-39344503`, commit `e451240d172d49fedd696ec5ca9c7757cded1ebd` (PR65).
- Ciclos explícitos de crédito y depósito en USD y HNL, incluyendo contrato con adjunto de prueba, desembolso, cobro, retiro y borradores contables. Los cuatro casos verifican empresa, moneda y equilibrio contable y no se omiten por falta de cuentas demo.
- Suite existente: amortización, abonos, acceso por empresa, permisos, reestructuración, estados de cuenta e intereses.
- Sentinel: acceso confirmado como Luis Moran, permiso Gerente de Lenka; empresa INVERSIONES LENKA. Cotización ficticia LENKA-OP-000001: HNL 10,000, prima 1,000, financiado 9,000, tasa mensual 3%, 12 cuotas de 904.16, saldo final cero. Observaciones conservadas después de guardar y recargar.
- Ícono definitivo: archivo PNG exacto enviado por Luis el 6 de octubre, 1024×1024, 1,010,678 bytes; blob Git `e5b3dd8119b7bd0f4872da2ab8450bc124c64510`. Sin edición ni regeneración.
- PR64 contiene esa misma versión y las pruebas ampliadas para Sentinel.

Estos resultados no sustituyen la configuración contable ni aprueban el contenido legal del contrato. No afirmar que toda la operación real está lista mientras existan los pendientes siguientes.

## Información pendiente para uso real

En la empresa INVERSIONES LENKA de Sentinel se observaron vacíos:

1. **Plantillas contractuales:** aportar contrato vigente aprobado para cada tipo de operación que se usará. No reemplazarlo por el contrato demo ni firmarlo en nombre de nadie.
2. **Asignación contable:** confirmar los diarios de desembolsos, cobros e inversiones/depósitos y los códigos de cuentas de cartera, ingreso por intereses, ingreso por mora, anticipos no aplicados, comisión de tarjeta, costo de fondeo, obligación con inversionistas, gasto por intereses pasivos y retención por pagar. Confirmar también las tasas operativas de comisión y retención; no inferirlas de los valores predeterminados del módulo.

Una vez recibidos, preparar la configuración en Sentinel, probar generación del contrato aprobado y borradores contables con esas asignaciones, y registrar los resultados antes de marcar la preparación como completa.

## Procedimiento reservado para la orden de instalación

1. Confirmar la rama y el respaldo recuperable de producción; revisar cambios concurrentes.
2. Integrar el PR aprobado con la rama vigente, conservando O Dental y los demás módulos; no reemplazar el árbol de producción por una copia antigua de Sentinel.
3. Instalar solo `lenka_financiero`, sin ejecutar Preparar Demo Lenka ni importar datos ficticios.
4. Aplicar la configuración validada de INVERSIONES LENKA y los permisos aprobados para los usuarios que operarán Lenka.
5. Verificar carga del módulo, ícono, acceso, empresa y configuración. Esta comprobación posterior de instalación no crea créditos ni movimientos reales.

Si la instalación falla, revisar logs y recuperar mediante el respaldo y procedimiento de Odoo.sh; no desinstalar automáticamente ni borrar datos. Coordinar cualquier recuperación que afecte la base compartida.
