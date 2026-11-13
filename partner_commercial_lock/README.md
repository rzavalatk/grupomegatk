# Bloqueo de reasignación del comercial del contacto

Propuesta para Odoo 18. No está instalada ni activada en producción.

El campo es `res.partner.user_id` (Contactos → Venta y compra → Comercial).
Los vendedores y técnicos miembros de **No reasignar comercial de contactos** pueden leer ese campo
y conservar sus demás permisos, pero no cambiarlo, quitarlo ni apropiarse de
un contacto existente que no tenga comercial. La comprobación se ejecuta en
`write` antes de guardar, incluidas importaciones, API y cambios en lote.
Enviar el mismo comercial no bloquea la edición de otros campos.

El grupo es restrictivo y no concede ACL, reglas de registro, empresas ni
privilegios de administración. No se asigna automáticamente a ningún usuario.
No se usan como excepción los grupos generales de Ventas/Administrador,
Limites/Vendedor o Editar Comercial en Cotizaciones: el permiso de reasignar
contactos debe definirse por separado del permiso de modificar cotizaciones.

El módulo no cambia asignaciones existentes ni redefine la creación de
contactos: conserva el valor predeterminado y las reglas de los módulos
instalados. En el formulario el campo queda de solo lectura para el grupo
restringido; se conservan por OR otras condiciones de solo lectura. La
comprobación del servidor sigue siendo obligatoria si otra vista altera la UI.

## Activación controlada

1. Confirmar el repositorio y la rama que realmente despliegan el Odoo actual.
2. Usar un respaldo y una copia de pruebas de la base actual. Instalar solo
   `partner_commercial_lock`; no es necesario actualizar `grupos_accesos` ni
   reinstalar componentes existentes.
3. Asignar **No reasignar comercial de contactos** a los vendedores y técnicos definidos
   por Administración en las empresas donde se aplique la política.
   Mantener fuera del grupo a Gerencia de Ventas, la cuenta de Facturación y
   las cuentas autorizadas de Administración: conservarán sus permisos actuales
   para reasignar, sin recibir ACL ni privilegios nuevos por este módulo.
   Incluir esta asignación en el alta de futuros vendedores y técnicos.
4. Ejecutar las pruebas en una base de pruebas, nunca con registros comerciales
   reales: `odoo-bin -d <base_pruebas> -i partner_commercial_lock --test-enable
   --test-tags /partner_commercial_lock --stop-after-init --without-demo=all`.
   Si el módulo ya está instalado en pruebas, usar `-u` en vez de `-i`.
5. Verificar la vista final con Studio y los demás módulos activos. Comprobar
   con un vendedor y un técnico la lectura del comercial, el rechazo de cambio
   y borrado, la edición de otro dato, y con cada cuenta autorizada de Gerencia
   de Ventas, Facturación y Administración la reasignación permitida.
   Revisar también importación/API, lote y contactos compartidos entre empresas.
6. Publicar e instalar en producción únicamente tras esas comprobaciones.

## Validación disponible

Se incluyen 15 pruebas de integración de Odoo para lectura, bloqueo, borrado,
contactos sin comercial, edición de otros campos, mismo valor, lote sin cambios
parciales, contextos, sudo, aislamiento por usuario, cambio de membresía y
técnicos con o sin permisos de Ajustes. No existe una excepción implícita por
pertenecer a un grupo administrativo general.

Validación del commit `13cc0f8698194be358155af5259002bcd78e3b6d`: instalación
correcta y 15 pruebas aprobadas, 0 fallos y 0 errores, en Odoo 18/PostgreSQL
con datos ficticios y sin credenciales de producción. Evidencia:
https://github.com/ajz04megatk/grupomegatk/actions/runs/43431861214

El workflow `Pruebas del bloqueo de comercial` permite repetir esa validación.
La prueba aislada no sustituye la comprobación de compatibilidad con la copia
de la base actual ni acredita que el módulo esté instalado en producción.

## Reversión

Retirar el grupo restrictivo de los usuarios afectados desactiva esta
restricción sin tocar clientes ni credenciales. Antes de retirar el módulo,
revisar las vistas heredadas y el procedimiento de respaldo del entorno.
