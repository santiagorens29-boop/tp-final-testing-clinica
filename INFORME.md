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