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