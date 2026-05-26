# Informe del Proyecto: Sistema de Gestión Clínica

## 1.1. Descriptivo del Software
**Objetivo del Software:** Desarrollar una herramienta integral para la gestión de pacientes, turnos y registros médicos en una clínica familiar.

## 1.2. Requerimientos Implementados
### Requerimientos Funcionales:
* **RF1:** Registro y gestión de perfiles de pacientes.
* **RF2:** Sistema de asignación y visualización de turnos médicos.
* **RF3:** Gestión de historias clínicas digitales.

### Requerimientos No Funcionales:
* **RNF1 (Seguridad):** Autenticación de usuarios para proteger datos sensibles.
* **RNF2 (Rendimiento):** El tiempo de carga de las consultas no debe superar los 2 segundos.


## 2. Diseñar un conjunto de Pruebas

### 2.1. Prueba de componentes (Diseño)
* **Objetivo:** Verificar de forma aislada la función de validación de formato de correo electrónico en el módulo de registro de pacientes.
* **Caso de Prueba CP-01:** * *Entrada:* "santiago@ejemplo.com"
  * *Resultado Esperado:* True (Formato válido).
* **Caso de Prueba CP-02:** * *Entrada:* "santiago.com" (Sin el @)
  * *Resultado Esperado:* False o ValueError (Formato inválido).

### 2.6. Prueba de camino (Diseño)
* **Objetivo:** Garantizar la cobertura de todas las ramas lógicas (if/else) en la función de cálculo de copagos según la cobertura del paciente (Particular, Obra Social o Prepaga).
* **Camino 1 (Particular):** * *Entrada:* Paciente marca casilla "Particular" -> Anula ingreso de prestadora.
  * *Resultado Esperado:* Costo base total de la consulta sin descuentos.
* **Camino 2 (Con descuento por Obra Social/Prepaga):** * *Entrada:* Paciente ingresa "Swiss Medical" u "OSDE" -> Aplica filtro de tabla.
  * *Resultado Esperado:* Cálculo del porcentaje de descuento correspondiente y generación del saldo de copago.


  ### 2.2. Prueba de Integración (Diseño)
* [cite_start]**Objetivo:** Verificar la correcta transferencia de datos y consistencia en el flujo de información entre el módulo de "Inicio de Sesión" y el módulo de "Perfil de Usuario/Médico"[cite: 176, 178].
* **Caso de Prueba CP-03:**
  * [cite_start]*Entrada:* Autenticación exitosa del médico (DNI y Contraseña correctos)[cite: 188].
  * [cite_start]*Resultado Esperado:* El sistema transfiere el ID de sesión de forma segura y carga correctamente en el perfil los datos asociados (Nombre, Apellido, Especialidad y Matrícula)[cite: 179, 205].

### 2.5. Prueba de Interfaz (Diseño)
* [cite_start]**Objetivo:** Validar el comportamiento de los componentes de la interfaz de usuario (UI) en el formulario de filtrado de obras sociales y prepagas para evitar errores de tipeo[cite: 137].
* **Caso de Prueba CP-04:**
  * *Entrada:* El usuario escribe "swis" en el campo dinámico de prestadora.
  * *Resultado Esperado:* La interfaz despliega un menú interactivo, filtra las opciones coincidentes y resalta "Swiss Medical" para permitir su selección con un clic.


### 2.3. Prueba de Caja negra (Diseño)
* **Objetivo:** Evaluar la respuesta del sistema ante el ingreso de datos inválidos en el formulario de registro de pacientes, basándose puramente en las especificaciones de negocio.
* **Caso de Prueba CP-05:**
  * *Entrada:* Se intenta guardar un paciente marcando la opción "Particular" pero con datos residuales de una obra social cargados en el formulario.
  * *Resultado Esperado:* El sistema debe anular automáticamente el ingreso de datos de la prestadora, limpiar esos campos y procesar el alta como paciente particular de forma limpia.

### 2.4. Prueba de Rendimiento (Diseño)
* **Objetivo:** Medir el comportamiento, la latencia y la estabilidad del servidor al procesar la carga y filtrado de historias clínicas concurrentes.
* **Caso de Prueba CP-06:**
  * *Entrada:* Simular un escenario de carga donde se realizan peticiones simultáneas de consulta al endpoint de perfiles clínicos.
  * *Resultado Esperado:* El tiempo de respuesta y procesamiento de las consultas debe mantenerse por debajo del límite establecido de 2 segundos, sin generar picos críticos de consumo de recursos ni caída de sesiones.


## 3. Planificar la ejecución de las Pruebas y Documentación

### 3.1. Planificación del Cronograma de Ejecución
Para garantizar un proceso de testing ordenado, se estableció el siguiente cronograma de ejecución interna previo a la fecha límite del Sprint 3 (27/05/2026):

| Fecha de Ejecución | Código de Prueba | Tipo de Prueba | Componente / Módulo Enfocado |
| :--- | :--- | :--- | :--- |
| 21/05/2026 | CP-01 y CP-02 | Componentes y Camino | Validación de Email y Cálculo de Copagos (`models.py`) |
| 22/05/2026 | CP-03 | Integración | Flujo de Login y pasaje de datos al Perfil del Médico |
| 23/05/2026 | CP-04 | Interfaz (UI) | Formulario Predictivo de Obras Sociales (Vue.js) |
| 24/05/2026 | CP-05 | Caja Negra | Validación de Registro de Pacientes con datos redundantes |
| 25/05/2026 | CP-06 | Rendimiento | Simulación de carga concurrente en endpoint de perfiles clínicos |

### 3.2. Documentación de la Ejecución: Lógica Interna (Backend)

#### Caso de Prueba CP-01: Validación de formato de correo electrónico
* **Entorno de prueba:** Entorno de desarrollo local, Django Test Framework (Unittest).
* **Procedimiento:** Se ejecutó un test unitario sobre el validador del campo `email` del modelo `Paciente` enviando un string con formato válido.
* **Resultado Obtenido:** Exitoso (Passed). El sistema procesó la entrada "santiago@ejemplo.com" devolviendo True y permitiendo el flujo de registro sin lanzar excepciones.

#### Caso de Prueba CP-02: Validación de formato de correo inválido
* **Entorno de prueba:** Entorno de desarrollo local, Django Test Framework (Unittest).
* **Procedimiento:** Se forzó la inserción del string "santiago.com" (sin el carácter @) en el campo `email` del serializer `TurnoReservaSerializer`.
* **Resultado Obtenido:** Exitoso (Passed). El validador del componente capturó el error de sintaxis correctamente y arrojó un `ValidationError`, impidiendo el guardado en la base de datos.

#### Caso de Prueba CP-06 (Camino): Cobertura de ramas (if/else) en cálculo de copagos
* **Entorno de prueba:** Consola interactiva de Django (`manage.py shell`).
* **Procedimiento:** Se testearon los caminos lógicos de asignación según la cobertura del paciente. Al ingresar un paciente con `es_particular=True`, el sistema ejecutó el *Camino 1* anulando datos de obras sociales. Al ingresar "Swiss Medical", ejecutó el *Camino 2* aplicando las relaciones de llaves foráneas definidas en el modelo `ObraSocial`.
* **Resultado Obtenido:** Exitoso (Passed). La cobertura de ramas se completó al 100%, garantizando que el estado financiero de la consulta sea consistente con la condición del paciente.