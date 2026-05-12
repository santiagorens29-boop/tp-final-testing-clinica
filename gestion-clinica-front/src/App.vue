<template>
  <div class="app-container">
    <header>
      <h1 v-if="vistaActual === 'paciente'">Reserva de Turnos</h1>
      <h1 v-else-if="vistaActual === 'login'">Acceso al Staff</h1>
      <!-- Se agregó un botón pequeño de cerrar sesión para conveniencia -->
      <h1 v-else>
        Gestión de Clínica - Hola, {{ usuarioLogueado.user }}
        <button @click="cerrarSesion" style="font-size: 0.5em; margin-left: 10px; cursor: pointer;">Cerrar Sesión</button>
      </h1>
    </header>

    <!-- 1. Portal Público -->
    <PortalPaciente v-if="vistaActual === 'paciente'" />

    <!-- 2. Pantalla de Login (Entrada B) -->
    <div v-if="vistaActual === 'login'" class="card login-container">
      <div class="grupo-input">
        <label>Usuario:</label>
        <input v-model="credenciales.username" type="text" placeholder="Ej: secretaria_ana">
      </div>
      <div class="grupo-input" style="margin-top: 15px;">
        <label>Contraseña:</label>
        <input v-model="credenciales.password" type="password" placeholder="••••••••">
      </div>
      <button class="btn-login" @click="manejarLogin" style="margin-top: 20px;">Ingresar al Sistema</button>
      <p style="text-align:center; margin-top:15px; font-size:0.8em; color:#7f8c8d;">
        Área restringida para personal autorizado.
      </p>
    </div>

    <!-- 3. Sección Interna Protegida con paso de Props -->
    <div v-if="vistaActual === 'staff'">
      <Recepcion :usuario="usuarioLogueado" />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import axios from 'axios'
import PortalPaciente from './components/PortalPaciente.vue'
import Recepcion from './components/Recepcion.vue'

const vistaActual = ref('paciente')
const usuarioLogueado = ref(null)
const credenciales = reactive({ username: '', password: '' })

const verificarRuta = () => {
  const ruta = window.location.pathname
  
  // LÓGICA DE PERSISTENCIA:
  // Primero revisamos si hay una sesión guardada en el navegador
  const sesionGuardada = localStorage.getItem('usuarioClinica')
  
  if (sesionGuardada) {
    usuarioLogueado.value = JSON.parse(sesionGuardada)
    vistaActual.value = 'staff'
  } else if (ruta.includes('/staff')) {
    vistaActual.value = 'login'
  } else {
    vistaActual.value = 'paciente'
  }
}

onMounted(() => {
  verificarRuta()
})

const manejarLogin = async () => {
  try {
    const res = await axios.post('http://127.0.0.1:8000/gestion/login/', {
      username: credenciales.username,
      password: credenciales.password
    })
    
    if (res.data.status === 'success') {
      usuarioLogueado.value = res.data
      
      // GUARDAR SESIÓN: Guardamos los datos en localStorage para que sobrevivan al F5
      localStorage.setItem('usuarioClinica', JSON.stringify(res.data))
      
      vistaActual.value = 'staff'
      credenciales.username = ''
      credenciales.password = ''
    } else {
      alert("Usuario o contraseña incorrectos.")
    }
  } catch (e) {
    console.error("Error en login:", e)
    alert("Error de conexión con el servidor de gestión.")
  }
}

// Función para limpiar la sesión manualmente si es necesario
const cerrarSesion = () => {
  localStorage.removeItem('usuarioClinica')
  usuarioLogueado.value = null
  vistaActual.value = 'login'
}
</script>

<style>
.app-container { max-width: 800px; margin: 0 auto; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 20px; }
header h1 { text-align: center; color: #2c3e50; margin-bottom: 30px; }
.login-container { max-width: 400px; margin: 0 auto; padding: 30px; background: white; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); border: 1px solid #eee; }
.grupo-input label { display: block; margin-bottom: 5px; font-weight: bold; color: #34495e; }
.grupo-input input { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box; }
.btn-login { width: 100%; padding: 12px; background: #27ae60; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 16px; transition: 0.2s; }
.btn-login:hover { background: #219150; }
.card { background: white; padding: 20px; border-radius: 12px; }
</style>