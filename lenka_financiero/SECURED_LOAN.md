# Préstamo con aval o garantía

Referencia revisada: `Contrato de Prestamo Condepah.doc`. Su estructura de préstamo y aval solidario se adapta a personas naturales y a entidades. Los datos del caso de referencia no se incluyen en el código ni en las pruebas.

## Operación

1. Seleccionar **Préstamo** y **Con aval o garantía**.
2. En **Cliente**, registrar a la entidad deudora con su RTN; para una persona natural, seleccionar su contacto.
3. En **Datos del contrato**, seleccionar al representante legal / firmante y completar su identidad y facultades. El documento de identidad de la persona es independiente del RTN fiscal. Se toma del nuevo campo **Documento de identidad (Lenka)** del contacto; la identidad del firmante puede completarse en la operación.
4. Si el representante también será aval, pulsar **Agregar representante como aval personal**. Otros avales se seleccionan en **Avales**. Cada aval debe tener registrado su documento de identidad.
5. En **Garantías**, registrar tipo, propietario, descripción, serie/VIN/matrícula y valores. El contrato describe el respaldo ofrecido; los documentos de formalización o inscripción permanecen en el expediente.
6. Calcular el plan y pulsar **Generar documentos**. Se selecciona una sola plantilla de contrato según la modalidad de respaldo. Cada aval tiene su comparecencia y firma personal, además de la firma del representante por la entidad.

La nueva plantilla mantiene las tasas, la mora y el plan mixto de la operación. No modifica aprobaciones, préstamos existentes ni documentos firmados.

## Instalación y comprobación

Actualizar `lenka_financiero` a `18.0.1.0.8`. Ejecutar primero en desarrollo:

```bash
odoo-bin -u lenka_financiero --test-enable --test-tags /lenka_financiero:TestSecuredLoanContract --stop-after-init --no-http
```

Hay trece pruebas para funciones separadas, aval distinto, múltiples avales, garantía sin aval, RTN distinto de identidad, errores de datos, escape de HTML, selección de plantilla, aislamiento de empresa y protección de contratos firmados.

La plantilla se crea por empresa al generar un préstamo respaldado. Para dejarla visible de antemano, el administrador puede ejecutar `_approved_secured_loan_template(company)` en `lenka.contract.template`. Conserva el logo existente del contrato sin aval de esa misma empresa. Los datos del prestamista y pagos se reutilizan de ese formato aprobado o se completan en la operación.

El informe reutiliza las fuentes incrustadas de la vista **Lenka fiduciario - Times New Roman 14** de la instalación actual. Compensa la escala de impresión de su formato de papel para obtener cuerpo de 14 puntos y título de 20 puntos; verificar en el PDF del entorno de destino. Las firmas no utilizan tablas ni bordes.

Validación del 16 de octubre de 2026: las trece pruebas de `TestSecuredLoanContract` se ejecutaron en Odoo 18, desarrollo `lenka-pilot`, instancia `40008750`, con cero fallos y cero errores. La ejecución detectó y permitió corregir el escape de porcentajes CSS en los espacios de firma. Se utilizó una copia aislada del módulo en `/tmp/lenka-secured-addons`, antepuesta mediante `ADDONS_PATH` al lanzador Odoo.sh, sin reemplazar el código del repositorio del piloto. Sintaxis Python y XML comprobada. La revisión visual del PDF en destino y la publicación en producción siguen pendientes: el conector GitHub devuelve 403 al crear la solicitud en `rzavalatk/grupomegatk`.
