# Preparación de instalación — Financiero Lenka

Fecha: 9 de octubre de 2026.

## Destino y autorización

Destino previsto: proyecto Odoo.sh `grupomegatk`, rama `master`, https://grupomegatk.odoo.com/odoo, compartido con O Dental. Aplicar únicamente el módulo `lenka_financiero`; no actualizar ni reinstalar módulos ajenos.

PR de preparación: https://github.com/rzavalatk/grupomegatk/pull/58. Mantener en borrador, sin auto-merge. Luis debe dar una orden expresa para instalar. Su autorización de pruebas no autoriza producción.

Sentinel es exclusivamente el entorno autorizado de pruebas. Sus datos y permisos no se trasladan automáticamente a producción. Android e iPhone siguen fuera de esta entrega.

## Estado de preparación

Paquete técnico preparado para instalar cuando Luis lo ordene. Los contratos, diarios y cuentas pueden cargarse después de instalar; no son requisitos previos de instalación. Se puede comenzar con clientes, cotizaciones y cálculo de planes. Completar cada configuración antes de usar la función que la requiere.

## Resultado técnico verificado

### Cambio contractual aprobado el 9 de octubre

- Versión preparada: 18.0.1.0.3. Contrato de financiamiento de equipo aprobado por Luis, parametrizado sin datos personales ni bancarios del ejemplo Conzuma.
- La primera generación de financiamiento, si no existe contrato activo, crea una plantilla por empresa. También se puede seleccionar desde **Datos del contrato → Usar contrato aprobado de Lenka**. No sustituye plantillas personalizadas ni textos ya generados.
- Firmantes, serie, garantía, ISV incluido, instrucciones de pago y ciudad se completan en Datos del contrato. Información faltante se imprime con líneas en blanco; debe completarse antes de usar el documento para firma.
- Importes, tasa, mora, moneda y cronograma proceden de la operación. El ISV es desglose del precio, no un cargo adicional. El plan anexo refleja las cuotas calculadas, incluido el redondeo final.
- PDF tamaño carta con firmas y rúbricas al pie; descargar, obtener firma, subir el archivo y marcar firmado. Nunca se simula una firma.
- Se conservan las cláusulas comerciales aprobadas de inflación, cambio de moneda y recuperación. Este cambio no automatiza ajustes de tasas ni recuperación de bienes.
- Elisa configurará diarios y cuentas después de instalar. La generación contractual no depende de esa configuración.
- Validación local: sintaxis Python/XML y cobertura de variables. Pruebas de integración nuevas en `tests/test_approved_contract.py`; resultado Odoo.sh pendiente de ejecución para esta versión. No confundir con los resultados de la versión anterior siguientes.

### Versión anterior

- Versión: 18.0.1.0.2.
- Batería Odoo 18: **196 pruebas, 0 fallos, 0 errores**, build `grupomegatk-lenka-pilot-39344503`, commit `e451240d172d49fedd696ec5ca9c7757cded1ebd` (PR65).
- Ciclos explícitos de crédito y depósito en USD y HNL, incluyendo contrato con adjunto de prueba, desembolso, cobro, retiro y borradores contables. Los cuatro casos verifican empresa, moneda y equilibrio contable y no se omiten por falta de cuentas demo.
- Suite existente: amortización, abonos, acceso por empresa, permisos, reestructuración, estados de cuenta e intereses.
- Sentinel: acceso confirmado como Luis Moran, permiso Gerente de Lenka; empresa INVERSIONES LENKA. Cotización ficticia LENKA-OP-000001: HNL 10,000, prima 1,000, financiado 9,000, tasa mensual 3%, 12 cuotas de 904.16, saldo final cero. Observaciones conservadas después de guardar y recargar.
- Ícono definitivo: archivo PNG exacto enviado por Luis el 6 de octubre, 1024×1024, 1,010,678 bytes; blob Git `e5b3dd8119b7bd0f4872da2ab8450bc124c64510`. Sin edición ni regeneración.
- PR64 contiene esa misma versión y las pruebas ampliadas para Sentinel.

Estos resultados no sustituyen la configuración contable ni aprueban el contenido legal del contrato. No afirmar que toda la operación real está lista mientras existan los pendientes siguientes.

## Configuración posterior a la instalación

En la empresa INVERSIONES LENKA de Sentinel se observaron vacíos:

1. **Plantillas contractuales:** financiamiento de equipos aprobado e incorporado. Los contratos para préstamos y arrendamientos son formatos distintos y no se sustituyen por este contrato de equipo.
2. **Asignación contable (Elisa):** configurar los diarios de desembolsos, cobros e inversiones/depósitos y los códigos de cuentas de cartera, ingreso por intereses, ingreso por mora, anticipos no aplicados, comisión de tarjeta, costo de fondeo, obligación con inversionistas, gasto por intereses pasivos y retención por pagar. Confirmar también las tasas operativas de comisión y retención; no inferirlas de los valores predeterminados del módulo.

Estos datos pueden introducirse desde el sistema instalado. El contrato se requiere antes de completar la contratación de una operación; los diarios y cuentas, antes de generar los movimientos contables correspondientes. Su ausencia no bloquea instalar el módulo ni crear cotizaciones. No generar movimientos reales con parámetros de demostración.

## Procedimiento reservado para la orden de instalación

1. Confirmar la rama y el respaldo recuperable de producción; revisar cambios concurrentes.
2. Integrar el PR aprobado con la rama vigente, conservando O Dental y los demás módulos; no reemplazar el árbol de producción por una copia antigua de Sentinel.
3. Instalar solo `lenka_financiero`, sin ejecutar Preparar Demo Lenka ni importar datos ficticios.
4. Configurar el acceso de los usuarios expresamente autorizados en la empresa INVERSIONES LENKA. Los permisos otorgados únicamente en Sentinel no autorizan ampliaciones automáticas en producción. Cargar contratos y asignaciones contables cuando los responsables los definan.
5. Verificar carga del módulo, ícono, acceso, empresa y configuración. Esta comprobación posterior de instalación no crea créditos ni movimientos reales.

Si la instalación falla, revisar logs y recuperar mediante el respaldo y procedimiento de Odoo.sh; no desinstalar automáticamente ni borrar datos. Coordinar cualquier recuperación que afecte la base compartida.

