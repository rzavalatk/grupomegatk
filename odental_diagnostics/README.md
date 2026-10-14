# O Dental Odontograma e Imágenes

Tercer bloque funcional de O Dental para Odoo 18.

Incluye catálogo FDI de 52 piezas permanentes y temporales, hallazgos por superficie,
odontogramas firmados con rectificaciones versionadas, archivos clínicos en el filestore
de Odoo, metadatos DICOM, huella SHA-256, privacidad selectiva y auditoría.

## Gráfico dental

En el formulario del odontograma se muestran las arcadas permanente, temporal o ambas
para la dentición mixta. El selector **Numeración visible** cambia entre FDI y
ADA/Universal en el dibujo y en la selección de piezas. Los registros conservan el
identificador FDI; cambiar la vista no cambia el hallazgo ni la firma. El dibujo de
raíces usa la forma habitual: incisivos y caninos una, premolares inferiores una,
molares inferiores dos y molares superiores tres. Hay variantes anatómicas reales.
Las zonas coloreadas resumen condiciones presentes, tratamientos planificados o
realizados y signos en seguimiento; la lista conserva detalles y notas clínicas.

En **Hallazgo o signo**, movilidad es un signo clínico. **Situación clínica** distingue
lo presente al examinar (incluida una restauración antigua), un tratamiento propuesto,
uno efectuado y una condición que se vigila. No es el estado de firma del odontograma.

Guarde primero un odontograma en borrador. Después seleccione una pieza o superficie
del gráfico para registrar un hallazgo mediante el formulario clínico. Si ya existe
un solo hallazgo en esa zona, el formulario lo abre para su revisión. Una zona con
varios hallazgos se consulta en la lista inferior. La firma bloquea modificaciones;
las correcciones se hacen mediante una rectificación versionada.

El dibujo es un esquema clínico, no una radiografía ni un diagnóstico automático.
Las imágenes clínicas y DICOM se gestionan en el repositorio de imágenes del expediente.
