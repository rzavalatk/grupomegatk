# O Dental Asistente IA

Este módulo incorpora una capa segura para instrucciones escritas o dictadas:

- Dictado en español desde navegadores compatibles, con entrada manual alternativa.
- Analizador determinista inicial para evoluciones, odontograma y agenda.
- Propuestas estructuradas que el profesional debe revisar y confirmar.
- Ejecución mediante los modelos y validaciones normales de O Dental.
- Evoluciones, odontogramas y citas nuevas siempre se crean en borrador.
- Ninguna firma clínica ni publicación se realiza automáticamente.
- Deshacer únicamente para borradores creados por la sesión que no hayan cambiado.
- Huellas digitales y auditoría inmutable de captura, propuesta, confirmación y ejecución.

La arquitectura admite incorporar posteriormente un proveedor de transcripción o un modelo de
lenguaje. Dicho proveedor solo podrá entregar propuestas dentro del mismo esquema permitido;
nunca recibirá permiso para ejecutar modelos o métodos arbitrarios de Odoo.
