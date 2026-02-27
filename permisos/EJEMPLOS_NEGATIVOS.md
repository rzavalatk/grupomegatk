# Ejemplos de Manejo de Saldos Negativos en Permisos

## Casos de Prueba para Validar la Lógica

### Caso 1: Empleado con 0 días solicita 1 día
**Entrada:**
- Saldo actual: 0 días, 0 horas, 0 minutos = 0 minutos
- Solicitud: 1 día = 480 minutos
- Operación: resta

**Proceso:**
- minutos_actuales = 0
- minutos_solicitados = 480
- minutos_resultante = 0 - 480 = -480

**Conversión a días/horas/minutos:**
- minutos_absolutos = 480
- dias = -1 (480 / 480 = 1, pero negativo)
- minutos_restantes = 0

**Resultado:** -1 días, 0 horas, 0 minutos

### Caso 2: Empleado con 0 días solicita 3 horas
**Entrada:**
- Saldo actual: 0 días, 0 horas, 0 minutos = 0 minutos
- Solicitud: 3 horas = 180 minutos
- Operación: resta

**Proceso:**
- minutos_resultante = 0 - 180 = -180

**Conversión:**
- minutos_absolutos = 180
- dias = 0 (180 < 480)
- horas = -3 (180 / 60 = 3, pero negativo)
- minutos_restantes = 0

**Resultado:** 0 días, -3 horas, 0 minutos

### Caso 3: Empleado con 2 horas solicita 1 día completo
**Entrada:**
- Saldo actual: 0 días, 2 horas, 0 minutos = 120 minutos
- Solicitud: 1 día = 480 minutos
- Operación: resta

**Proceso:**
- minutos_resultante = 120 - 480 = -360

**Conversión:**
- minutos_absolutos = 360
- dias = 0 (360 < 480)
- horas = -6 (360 / 60 = 6, pero negativo)
- minutos_restantes = 0

**Resultado:** 0 días, -6 horas, 0 minutos

### Caso 4: Empleado con 1.5 días solicita 2 días
**Entrada:**
- Saldo actual: 1 día, 4 horas, 0 minutos = 480 + 240 = 720 minutos
- Solicitud: 2 días = 960 minutos
- Operación: resta

**Proceso:**
- minutos_resultante = 720 - 960 = -240

**Conversión:**
- minutos_absolutos = 240
- dias = 0 (240 < 480)
- horas = -4 (240 / 60 = 4, pero negativo)
- minutos_restantes = 0

**Resultado:** 0 días, -4 horas, 0 minutos

### Caso 5: Empleado con deuda solicita más tiempo (acumula deuda)
**Entrada:**
- Saldo actual: -1 días, 0 horas, 0 minutos = -480 minutos
- Solicitud: 2 horas = 120 minutos
- Operación: resta

**Proceso:**
- minutos_resultante = -480 - 120 = -600

**Conversión:**
- minutos_absolutos = 600
- dias = -1 (600 / 480 = 1.25, tomar parte entera)
- minutos_restantes_abs = 600 - 480 = 120
- horas = -2 (120 / 60 = 2, pero negativo)

**Resultado:** -1 días, -2 horas, 0 minutos

## Validaciones Implementadas

✅ **No mezcla de signos**: Si hay días negativos, horas y minutos también deben ser negativos o cero
✅ **Rango de minutos**: Los minutos siempre están entre -59 y 59
✅ **Conversión correcta**: -480 minutos = -1 día, no se queda como -480 minutos
✅ **Logging detallado**: Registra todo el proceso para debugging