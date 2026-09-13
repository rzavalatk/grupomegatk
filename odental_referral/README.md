# O Dental Referencias y Acceso Temporal

Implementa referencias clínicas selectivas para profesionales externos sin entregar el
expediente completo.

## Controles incluidos

- Alcance explícito por antecedente, evolución, odontograma, imagen y plan clínico.
- Huella criptográfica del contenido: cualquier cambio posterior invalida la cápsula.
- Exclusión obligatoria de elementos marcados como no compartibles.
- Justificación para información clasificada como restringida.
- Consentimiento vigente del paciente y autorización del administrador clínico.
- Firma digital del paciente o representante mediante su propio enlace y segundo factor.
- Enlace aleatorio de alta entropía y código temporal de seis dígitos.
- Las credenciales se muestran una vez en un asistente temporal; los registros permanentes
  conservan solo huellas SHA-256 y el código se invalida después del primer uso.
- Bloqueo temporal después de cinco intentos incorrectos.
- Vencimiento por tiempo, revocación, retiro del consentimiento o máximo de accesos.
- Cierre automático del acceso cuando el especialista entrega su informe.
- Portal externo limitado a la cápsula clínica seleccionada.
- Informe externo inmutable y separado, pendiente de revisión profesional.
- Bitácora de verificaciones, consultas y archivos accedidos.

La opción de impedir descargas elimina el botón correspondiente y entrega los archivos
compatibles únicamente para visualización en línea. Como en cualquier aplicación web,
no puede impedir capturas de pantalla realizadas por el receptor.
