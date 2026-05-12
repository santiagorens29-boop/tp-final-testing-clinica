<template>
  <div class="consultorio-container" v-if="paciente">
    <aside class="sidebar-clinica">
      <h3>Perfil Clínico</h3>
      <div v-if="perfil" class="perfil-card">
        <p><strong>Grupo Sanguíneo:</strong> {{ perfil.grupo_sanguineo || 'No cargado' }}</p>
        <p class="alerta"><strong>Alergias:</strong> {{ perfil.alergias || 'Ninguna' }}</p>
        <p><strong>Enf. Crónicas:</strong> {{ perfil.enfermedades_cronicas || 'Ninguna' }}</p>
        <p><strong>Medicación:</strong> {{ perfil.medicacion_habitual || 'Ninguna' }}</p>
      </div>
      <hr />
      <h4>Historial Reciente</h4>
      <div v-for="evo in evolucionesAnteriores" :key="evo.id" class="evo-mini-card">
        <small>{{ evo.fecha_creacion }} - {{ evo.especialidad_nombre }}</small>
        <p>{{ evo.motivo }}</p>
      </div>
    </aside>

    <main class="area-atencion">
      <header class="paciente-header">
        <div class="header-info">
          <h2>Atendiendo a: {{ paciente.nombre }} {{ paciente.apellido }}</h2>
          <span>DNI: {{ paciente.dni }} | Edad: {{ calcularEdad(paciente.fecha_nacimiento) }} años</span>
        </div>
        <button class="btn-editar-ficha" @click="editandoFicha = !editandoFicha">
          {{ editandoFicha ? 'Ver Evolución' : 'Editar Datos Personales' }}
        </button>
      </header>

      <section v-if="editandoFicha" class="ficha-administrativa card">
        <h3>Datos Administrativos y de Cobertura</h3>
        <div class="grid-ficha">
          <div class="grupo-input">
            <label>
              <input type="checkbox" v-model="paciente.es_particular"> Paciente Particular (Sin Obra Social)
            </label>
            <div v-if="!paciente.es_particular" class="buscador-container">
              <label>Obra Social / Prepaga:</label>
              <input 
                v-model="busquedaOS" 
                @input="buscarOS" 
                type="text" 
                placeholder="Escriba para buscar (ej: OSDE, Swiss...)"
              >
              <ul v-if="sugerenciasOS.length" class="sugerencias">
                <li v-for="os in sugerenciasOS" :key="os.id" @click="seleccionarOS(os)">
                  {{ os.text }}
                </li>
              </ul>
              <div v-if="paciente.obra_social_nombre" class="tag-seleccionado">
                Seleccionado: <strong>{{ paciente.obra_social_nombre }}</strong>
              </div>
            </div>
          </div>

          <div class="grupo-input" v-if="!paciente.es_particular">
            <label>Nro Afiliado:</label>
            <input v-model="paciente.nro_afiliado" type="text">
          </div>

          <div class="grupo-input">
            <label>Médico de Cabecera:</label>
            <input 
              v-model="busquedaMedico" 
              @input="buscarMed" 
              type="text" 
              placeholder="Buscar médico del staff..."
            >
            <ul v-if="sugerenciasMed.length" class="sugerencias">
              <li v-for="m in sugerenciasMed" :key="m.id" @click="seleccionarMedico(m)">
                {{ m.text }}
              </li>
            </ul>
            <div v-if="paciente.medico_cabecera_nombre" class="tag-seleccionado">
              Asignado: <strong>{{ paciente.medico_cabecera_nombre }}</strong>
            </div>
          </div>

          <div class="grupo-input">
            <label>Fecha de Nacimiento:</label>
            <input v-model="paciente.fecha_nacimiento" type="date">
          </div>
        </div>
        <button class="btn-guardar-ficha" @click="actualizarDatosPaciente">Guardar Cambios Administrativos</button>
      </section>

      <div v-else class="formulario-evolucion">
        <div class="grupo-input">
          <label>Motivo de Consulta:</label>
          <input v-model="nuevaEvolucion.motivo" type="text" placeholder="Ej: Control de rutina">
        </div>

        <div class="grupo-input">
          <label>Descripción / Evolución Médica:</label>
          <textarea 
            v-model="nuevaEvolucion.descripcion" 
            rows="10" 
            placeholder="Escriba aquí los hallazgos del examen físico, diagnóstico y plan..."
          ></textarea>
        </div>

        <div class="actions">
          <button class="btn-cancelar" @click="cancelar">Cancelar</button>
          <button class="btn-guardar" @click="guardarEvolucion" :disabled="guardando">
            {{ guardando ? 'Firmando y Guardando...' : 'Finalizar y Firmar Consulta' }}
          </button>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import axios from 'axios'

const props = defineProps(['turnoId', 'pacienteId', 'medicoId'])
const emit = defineEmits(['finalizado'])

// Estados
const paciente = ref(null)
const perfil = ref(null)
const evolucionesAnteriores = ref([])
const guardando = ref(false)
const editandoFicha = ref(false)

// Buscadores
const busquedaOS = ref('')
const sugerenciasOS = ref([])
const busquedaMedico = ref('')
const sugerenciasMed = ref([])

const nuevaEvolucion = ref({
  motivo: '',
  descripcion: '',
  paciente: props.pacienteId,
  medico: props.medicoId,
  turno: props.turnoId
})

onMounted(async () => {
  try {
    const [resPac, resPerfil, resEvos] = await Promise.all([
      axios.get(`http://127.0.0.1:8000/gestion/detalle-paciente/${props.pacienteId}/`),
      axios.get(`http://127.0.0.1:8000/gestion/perfil-clinico/${props.pacienteId}/`),
      axios.get(`http://127.0.0.1:8000/gestion/evoluciones-paciente/${props.pacienteId}/`)
    ])
    paciente.value = resPac.data
    perfil.value = resPerfil.data
    evolucionesAnteriores.value = resEvos.data
  } catch (e) {
    console.error("Error cargando datos del consultorio", e)
  }
})

// --- LÓGICA DE BUSCADORES ---
const buscarOS = async () => {
  if (busquedaOS.value.length < 2) { sugerenciasOS.value = []; return }
  const res = await axios.get(`http://127.0.0.1:8000/gestion/buscar-obras-sociales/?q=${busquedaOS.value}`)
  sugerenciasOS.value = res.data
}

const seleccionarOS = (os) => {
  paciente.value.obra_social = os.id
  paciente.value.obra_social_nombre = os.text
  sugerenciasOS.value = []
  busquedaOS.value = ''
}

const buscarMed = async () => {
  if (busquedaMedico.value.length < 2) { sugerenciasMed.value = []; return }
  const res = await axios.get(`http://127.0.0.1:8000/gestion/buscar-medicos/?q=${busquedaMedico.value}`)
  sugerenciasMed.value = res.data
}

const seleccionarMedico = (m) => {
  paciente.value.medico_cabecera = m.id
  paciente.value.medico_cabecera_nombre = m.text
  sugerenciasMed.value = []
  busquedaMedico.value = ''
}

// --- ACTUALIZAR DATOS PACIENTE ---
const actualizarDatosPaciente = async () => {
  try {
    // Usamos patch para actualizar solo los campos administrativos
    await axios.patch(`http://127.0.0.1:8000/gestion/detalle-paciente/${props.pacienteId}/`, paciente.value)
    alert("Ficha administrativa actualizada.")
    editandoFicha.value = false
  } catch (e) {
    alert("Error al actualizar datos personales.")
  }
}

// --- UTILIDADES ---
const calcularEdad = (fecha) => {
  if (!fecha) return 'S/D'
  const hoy = new Date()
  const cumple = new Date(fecha)
  return hoy.getFullYear() - cumple.getFullYear()
}

const guardarEvolucion = async () => {
  if (!nuevaEvolucion.value.motivo || !nuevaEvolucion.value.descripcion) {
    alert("Por favor, complete el motivo y la descripción.")
    return
  }
  guardando.value = true
  try {
    await axios.post('http://127.0.0.1:8000/gestion/evoluciones/', nuevaEvolucion.value)
    alert("Consulta guardada exitosamente.")
    emit('finalizado')
  } catch (e) {
    alert("Error al guardar la consulta.")
  } finally {
    guardando.value = false
  }
}

const cancelar = () => {
  if (confirm("¿Está seguro? Los datos se perderán.")) emit('finalizado')
}
</script>

<style scoped>
/* (Se mantienen tus estilos y se agregan los nuevos) */
.paciente-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #eee; padding-bottom: 10px; }
.btn-editar-ficha { background: #3498db; color: white; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer; }
.ficha-administrativa { background: #fdfdfd; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px; }
.grid-ficha { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 15px; }
.buscador-container { position: relative; }
.sugerencias { position: absolute; background: white; border: 1px solid #ccc; width: 100%; z-index: 10; list-style: none; padding: 0; margin: 0; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
.sugerencias li { padding: 10px; cursor: pointer; border-bottom: 1px solid #eee; }
.sugerencias li:hover { background: #f1f1f1; }
.tag-seleccionado { margin-top: 5px; font-size: 0.85em; color: #27ae60; }
.btn-guardar-ficha { margin-top: 20px; background: #2ecc71; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; width: 100%; }
/* ... (resto de tus estilos originales) ... */
</style>