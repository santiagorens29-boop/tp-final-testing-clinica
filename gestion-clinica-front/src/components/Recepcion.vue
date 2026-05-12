<template>
  <div class="recepcion-container">
    <!-- VISTA 1: LISTA DE TURNOS (Solo se muestra si NO estamos en modo consultorio) -->
    <div v-if="!modoConsultorio">
      <h2>Turnos de Hoy (Gestión)</h2>
      
      <table class="tabla-turnos">
        <thead>
          <tr>
            <th>Hora</th>
            <th>Paciente</th>
            <th>Estado</th>
            <th>Acción</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="turno in turnos" :key="turno.id">
            <td>{{ turno.hora }} hs</td>
            <td>{{ turno.paciente_nombre }} {{ turno.paciente_apellido }}</td>
            <td>
              <span :class="'status-' + (turno.estado ? turno.estado.toLowerCase() : 'programado')">
                {{ turno.estado || 'PROGRAMADO' }}
              </span>
            </td>
            <td>
              <!-- Acción para Secretaria -->
              <button 
                v-if="usuario.rol === 'secretaria' && turno.estado === 'PROGRAMADO'"
                class="btn-llegada"
                @click="marcarLlegada(turno.id)"
              >
                Marcar Llegada
              </button>
              
              <!-- Acción para Médico: Abre el Consultorio -->
              <!-- Acción para Médico -->
              <button 
                v-if="usuario.rol === 'medico' && (turno.estado.toLowerCase() === 'espera' || turno.estado.toLowerCase() === 'esperando')"
                class="btn-atender"
                @click="abrirConsultorio(turno)"
              >
                Atender
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- VISTA 2: COMPONENTE CONSULTORIO (Se muestra al presionar Atender) -->
    <Consultorio 
      v-else
      :turnoId="turnoSeleccionado.id"
      :pacienteId="turnoSeleccionado.paciente" 
      :medicoId="medicoIdActual"
      @finalizado="cerrarConsultorio"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
// Importamos el componente que creamos antes
import Consultorio from './Consultorio.vue'

// Props que recibe de App.vue o Staff.vue
const props = defineProps(['usuario'])

const turnos = ref([])
const modoConsultorio = ref(false)
const turnoSeleccionado = ref(null)

// Obtenemos el ID del médico desde el usuario logueado
const medicoIdActual = computed(() => props.usuario?.id)

const obtenerTurnos = async () => {
  try {
    const response = await axios.get('http://127.0.0.1:8000/gestion/turnos-hoy/')
    turnos.value = response.data
  } catch (error) {
    console.error("Error al obtener turnos:", error)
  }
}

onMounted(() => {
  obtenerTurnos()
})

// LÓGICA DE TRANSICIÓN
const abrirConsultorio = (turno) => {
  turnoSeleccionado.value = turno
  modoConsultorio.value = true
}

const cerrarConsultorio = () => {
  modoConsultorio.value = false
  turnoSeleccionado.value = null
  obtenerTurnos() // Refrescamos la lista para ver el turno como FINALIZADO
}

const marcarLlegada = async (id) => {
  try {
    await axios.patch(`http://127.0.0.1:8000/gestion/turnos/${id}/`, { estado: 'ESPERANDO' })
    obtenerTurnos()
  } catch (error) {
    console.error("Error al marcar llegada:", error)
  }
}
</script>

<style scoped>
/* Mantenemos tus estilos originales */
.recepcion-container { padding: 20px; }
.tabla-turnos { width: 100%; border-collapse: collapse; margin-top: 20px; }
.tabla-turnos th, .tabla-turnos td { padding: 12px; border-bottom: 1px solid #eee; text-align: left; }
.status-esperando { color: #f39c12; font-weight: bold; }
.status-finalizado { color: #27ae60; font-weight: bold; }
.btn-llegada { background-color: #3498db; color: white; border: none; padding: 8px 12px; border-radius: 4px; cursor: pointer; }
.btn-atender { background-color: #2ecc71; color: white; border: none; padding: 8px 12px; border-radius: 4px; cursor: pointer; }
</style>