<template>
  <div class="portal-paciente">
    <!-- 1. SELECCIÓN DE MÉDICO -->
    <div class="card">
      <label>1. Seleccione el Profesional:</label>
      <select v-model="medicoId" class="input-grande" @change="limpiarSeleccion">
        <option value="1">Dr. Juan Pérez (Cardiología)</option>
      </select>
    </div>

    <!-- 2. SELECCIÓN DE DÍA -->
    <div class="card">
      <label>2. ¿Qué día prefiere asistir?</label>
      <div class="dias-grid">
        <button 
          v-for="(nombre, index) in diasNombres" 
          :key="index"
          @click="seleccionarDia(index)"
          :class="{ 'activo': diaSemana === index }"
        >
          {{ nombre }}
        </button>
      </div>
    </div>

    <!-- 3. RESULTADOS DE HORARIOS -->
    <div v-if="diaSemana !== null" class="resultados">
      <div v-if="loading" class="aviso">Buscando disponibilidades...</div>
      
      <div v-else-if="proximasFechas.length === 0" class="aviso">
        No hay horarios para este día.
      </div>

      <div v-else>
        <div v-for="fechaObj in proximasFechas" :key="fechaObj.dia" class="bloque-fecha">
          <h4 class="fecha-titulo">{{ formatearFecha(fechaObj.dia) }}</h4>
          
          <div class="horarios-grid">
            <button 
              v-for="turno in fechaObj.turnos" 
              :key="turno.hora"
              :disabled="!turno.libre"
              :class="['btn-hora', turno.libre ? 'hora-libre' : 'hora-ocupada', { 'seleccionado': turnoSeleccionado?.hora === turno.hora && turnoSeleccionado?.fecha === fechaObj.dia }]"
              @click="seleccionarTurno(fechaObj.dia, turno.hora)"
            >
              {{ turno.hora }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 4. MODAL DE CONFIRMACIÓN Y REGISTRO -->
    <div v-if="turnoSeleccionado" class="modal-overlay">
      <div class="card formulario-reserva">
        <h3>Confirmar Turno</h3>
        <p>Reserva para el <strong>{{ formatearFecha(turnoSeleccionado.fecha) }}</strong> a las <strong>{{ turnoSeleccionado.hora }} hs</strong></p>
        
        <hr style="margin: 15px 0; border: 0; border-top: 1px solid #eee;">

        <div v-if="paso === 1">
          <label>Ingresá tu DNI para continuar:</label>
          <input v-model="formulario.dni" class="input-grande" placeholder="DNI (sin puntos)">
          <button class="btn-confirmar" style="margin-top:15px" @click="verificarDniYSolicitar">Continuar</button>
        </div>

        <div v-if="paso === 2">
          <p class="aviso" style="text-align:left; color:#3498db; margin-bottom: 15px;">Parece que es tu primera vez. Completá tus datos:</p>
          <div class="grupo-input">
            <input v-model="formulario.nombre" placeholder="Nombre">
            <input v-model="formulario.apellido" placeholder="Apellido">
          </div>
          <div class="grupo-input">
            <input v-model="formulario.email" placeholder="Email">
            <input v-model="formulario.telefono" placeholder="Teléfono">
          </div>
          <button class="btn-confirmar" @click="solicitarCodigoNuevo">Enviar Código al Email</button>
        </div>

        <div v-if="paso === 3">
          <p>Enviamos un código a <strong>{{ emailPista }}</strong></p>
          <input v-model="formulario.codigo" class="input-grande" placeholder="000000" style="text-align:center; font-size:24px; letter-spacing:8px">
          <button class="btn-confirmar" style="margin-top:15px" @click="confirmarReserva">Finalizar Reserva</button>
        </div>

        <button class="btn-cancelar" style="margin-top:10px" @click="cerrarModal">Cancelar</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import axios from 'axios'

const API_BASE = "http://127.0.0.1:8000/portal"

const medicoId = ref("1")
const diaSemana = ref(null)
const proximasFechas = ref([])
const loading = ref(false)
const diasNombres = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

const turnoSeleccionado = ref(null)
const paso = ref(1) 
const emailPista = ref('')
const formulario = reactive({
  nombre: '', apellido: '', dni: '', telefono: '', email: '', codigo: ''
})

const seleccionarDia = (index) => {
  diaSemana.value = index
  buscarDisponibilidad()
}

const buscarDisponibilidad = async () => {
  if (diaSemana.value === null) return
  loading.value = true
  proximasFechas.value = []
  try {
    const url = `${API_BASE}/disponibilidad/${medicoId.value}/${diaSemana.value}/`
    const res = await axios.get(url)
    proximasFechas.value = res.data.proximos_dias
  } catch (e) {
    proximasFechas.value = []
  } finally {
    loading.value = false
  }
}

const seleccionarTurno = (fecha, hora) => {
  turnoSeleccionado.value = { fecha, hora }
  paso.value = 1
}

const cerrarModal = () => {
  turnoSeleccionado.value = null
  paso.value = 1
}

const verificarDniYSolicitar = async () => {
  try {
    const res = await axios.post(`${API_BASE}/solicitar-codigo/`, { dni: formulario.dni })
    emailPista.value = res.data.email_pista
    paso.value = res.data.status === 'paciente_existente' ? 3 : 2
  } catch (e) { alert("Error al verificar DNI") }
}

const solicitarCodigoNuevo = async () => {
  try {
    await axios.post(`${API_BASE}/solicitar-codigo/`, { 
      dni: formulario.dni, email: formulario.email, nombre: formulario.nombre, apellido: formulario.apellido 
    })
    paso.value = 3
  } catch (e) { alert("Error al enviar código") }
}

const confirmarReserva = async () => {
  try {
    const paquete = {
      ...formulario, medico: medicoId.value, fecha: turnoSeleccionado.value.fecha,
      hora: turnoSeleccionado.value.hora, paciente_dni: formulario.dni
    }
    await axios.post(`${API_BASE}/confirmar-reserva/`, paquete)
    alert("¡Turno reservado!")
    cerrarModal()
    buscarDisponibilidad()
  } catch (e) { alert("Error al confirmar reserva") }
}

const formatearFecha = (fechaStr) => {
  if (!fechaStr) return ''
  return new Date(fechaStr + 'T00:00:00').toLocaleDateString('es-AR', { weekday: 'long', day: 'numeric', month: 'long' })
}

const limpiarSeleccion = () => {
  diaSemana.value = null
  proximasFechas.value = []
}
</script>

<style scoped>
/* Estilos específicos para el Portal del Paciente */
.card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; }
.input-grande { width: 100%; padding: 12px; border-radius: 8px; border: 1px solid #ccc; margin-top: 10px; }
.dias-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(100px, 1fr)); gap: 10px; }
.dias-grid button { padding: 10px; border: 1px solid #3498db; background: white; border-radius: 8px; cursor: pointer; }
.dias-grid button.activo { background: #3498db; color: white; }
.horarios-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(80px, 1fr)); gap: 10px; }
.btn-hora { padding: 10px; border-radius: 6px; cursor: pointer; border: 1px solid #ddd; }
.hora-libre { background: #eafaf1; color: #27ae60; }
.hora-ocupada { opacity: 0.5; cursor: not-allowed; }
.modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); display: flex; justify-content: center; align-items: center; z-index: 1000; }
.btn-confirmar { background: #27ae60; color: white; width: 100%; padding: 12px; border-radius: 6px; border: none; cursor: pointer; }
.btn-cancelar { background: #95a5a6; color: white; width: 100%; padding: 8px; border-radius: 6px; border: none; cursor: pointer; }
.aviso { text-align: center; color: #7f8c8d; }
.bloque-fecha { background: #f9f9f9; padding: 15px; border-radius: 10px; margin-bottom: 15px; }
.formulario-reserva { max-width: 500px; width: 90%; }
.grupo-input { display: flex; gap: 10px; margin-bottom: 10px; }
.grupo-input input { width: 100%; padding: 10px; border-radius: 6px; border: 1px solid #ccc; }
</style>