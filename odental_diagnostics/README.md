# O Dental Odontograma e Imágenes

Tercer bloque funcional de O Dental para Odoo 18.

Incluye catálogo FDI de 52 piezas permanentes y temporales, hallazgos por superficie,
odontogramas firmados con rectificaciones versionadas, archivos clínicos en el filestore
de Odoo, metadatos DICOM, huella SHA-256, privacidad selectiva y auditoría.

## Gráfico dental

En el formulario del odontograma se muestran las arcadas permanente, temporal o ambas
para la dentición mixta. Las piezas siguen la numeración FDI. Las zonas coloreadas
resumen hallazgos existentes, planificados, realizados y en observación; la lista de
hallazgos bajo el gráfico conserva los detalles y las notas clínicas.

Guarde primero un odontograma en borrador. Después seleccione una pieza o superficie
del gráfico para registrar un hallazgo mediante el formulario clínico. Si ya existe
un solo hallazgo en esa zona, el formulario lo abre para su revisión. Una zona con
varios hallazgos se consulta en la lista inferior. La firma bloquea modificaciones;
las correcciones se hacen mediante una rectificación versionada.

El dibujo es un esquema clínico, no una radiografía ni un diagnóstico automático.
Las imágenes clínicas y DICOM se gestionan en el repositorio de imágenes del expediente.
