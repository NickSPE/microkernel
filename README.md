# 🏛️ Sistema Operativo Microkernel - Proyecto Educativo

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://python.org)
[![Licencia](https://img.shields.io/badge/Licencia-MIT-green.svg)](LICENSE)
[![Estado](https://img.shields.io/badge/Estado-Demo-orange.svg)](README.md)

## 📋 Descripción

Este proyecto es una **implementación educativa** de un sistema operativo con **arquitectura microkernel** desarrollado en Python. El objetivo es demostrar los principios fundamentales de los microkernels, donde el núcleo del sistema mantiene solo las funcionalidades más esenciales, mientras que los servicios se ejecutan en espacio de usuario.

### 🎯 Propósito Educativo

- **Demostrar** los principios de la arquitectura microkernel
- **Ilustrar** la separación entre núcleo y servicios
- **Mostrar** la comunicación entre procesos (IPC)
- **Ejemplificar** aplicaciones en espacio de usuario
- **Comparar** con arquitecturas monolíticas

## 🏗️ Arquitectura del Sistema

### Componentes Principales

```
microkernel-project/
├── kernel/           # Núcleo del sistema (funciones esenciales)
├── services/         # Servicios en espacio de usuario
├── apps/            # Aplicaciones de demostración
├── utils/           # Utilidades del sistema
└── main.py          # Punto de entrada del sistema
```

### 🔥 Microkernel (kernel/)
El núcleo mínimo que proporciona:
- **Gestión básica de procesos** - Creación, scheduling, terminación
- **Gestión de memoria** - Asignación y liberación básica
- **Comunicación entre procesos (IPC)** - Mensajes, semáforos, memoria compartida
- **Carga de servicios** - Registro y comunicación con servicios

### 🔧 Servicios (services/)
Servicios modulares que se ejecutan fuera del kernel:
- **FileSystemService** - Sistema de archivos virtual
- **NetworkService** - Simulación de conectividad de red
- **DriverService** - Controladores de dispositivos virtuales
- **SecurityService** - Autenticación y autorización

### 📱 Aplicaciones (apps/)
Aplicaciones de demostración en espacio de usuario:
- **Calculator** - Calculadora con operaciones matemáticas
- **TextEditor** - Editor de texto con gestión de archivos
- **Browser** - Navegador web simulado

### 🛠️ Utilidades (utils/)
- **Logger** - Sistema de logging centralizado
- **Config** - Gestor de configuración del sistema

## 🚀 Instalación y Ejecución

### Requisitos
- Python 3.7 o superior
- Sistema operativo: Windows, Linux, macOS

### Instalación
```bash
# Clonar o descargar el proyecto
git clone <url-del-repositorio>
cd microkernel-project

# No se requieren dependencias externas, solo Python estándar
```

### Ejecución
```bash
# Ejecutar el sistema completo
python main.py

# O ejecutar componentes individuales para pruebas
python kernel/microkernel.py
python services/fs_service.py
python apps/calculator.py
```

## 🎪 Demostraciones Incluidas

Al ejecutar `main.py`, el sistema iniciará automáticamente demostraciones de:

### 1. 🧮 Calculadora
- Operaciones matemáticas básicas
- Funciones avanzadas (trigonométricas, logarítmicas)
- Historial de operaciones
- Memoria de calculadora

### 2. 📝 Editor de Texto
- Creación y edición de archivos
- Operaciones de texto (insertar, eliminar, buscar, reemplazar)
- Integración con sistema de archivos
- Funcionalidad de deshacer

### 3. 🌐 Navegador Web
- Navegación por sitios simulados
- Marcadores e historial
- Búsqueda en páginas
- Integración con servicios de red

## 📚 Conceptos Demostrados

### Arquitectura Microkernel vs Monolítica

| Aspecto | Microkernel | Monolítico |
|---------|-------------|------------|
| **Tamaño del núcleo** | Mínimo | Grande |
| **Servicios** | Espacio de usuario | Espacio del kernel |
| **Comunicación** | IPC | Llamadas directas |
| **Fallos** | Aislados | Pueden afectar todo |
| **Mantenimiento** | Modular | Complejo |
| **Rendimiento** | Menor overhead de IPC | Más rápido |

### Principios Implementados

#### 🔒 **Separación de Privilegios**
```python
# El kernel ejecuta con privilegios mínimos
kernel.create_process(name="calculator", target_func=calc_loop)

# Los servicios se ejecutan sin privilegios del kernel
fs_service = FileSystemService()  # Espacio de usuario
```

#### 📡 **Comunicación IPC**
```python
# Mensajes entre procesos
ipc.send_message(dest_pid, {"action": "save_file", "data": content})

# Memoria compartida
shared_mem = ipc.create_shared_memory("file_buffer", 1024)
```

#### 🧩 **Modularidad**
```python
# Servicios intercambiables
kernel.register_service("filesystem", FileSystemService())
kernel.register_service("network", NetworkService())
```

## 📁 Estructura Detallada de Archivos

```
microkernel-project/
│
├── kernel/
│   ├── microkernel.py     # Núcleo principal del sistema
│   ├── scheduler.py       # Planificador de procesos
│   └── ipc.py            # Comunicación entre procesos
│
├── services/
│   ├── fs_service.py      # Servicio de sistema de archivos
│   ├── net_service.py     # Servicio de red
│   ├── driver_service.py  # Servicio de controladores
│   └── security_service.py # Servicio de seguridad
│
├── apps/
│   ├── calculator.py      # Aplicación calculadora
│   ├── text_editor.py     # Editor de texto
│   └── browser.py         # Navegador web simulado
│
├── utils/
│   ├── logger.py          # Sistema de logging
│   └── config.py          # Gestor de configuración
│
├── config/
│   └── microkernel.json   # Archivo de configuración
│
├── logs/
│   └── microkernel.log    # Archivo de logs
│
├── main.py               # Punto de entrada principal
└── README.md            # Este archivo
```

## 🔍 Componentes Técnicos

### Kernel Core (microkernel.py)
- **Clase Process**: Representa procesos del sistema
- **Clase Microkernel**: Núcleo principal con gestión mínima
- **Gestión de Memoria**: Asignación y tracking básico
- **Registro de Servicios**: Interfaz para servicios externos

### Planificador (scheduler.py)
- **Round Robin**: Planificación circular con quantum
- **Priority**: Planificación por prioridades
- **FIFO**: Primero en llegar, primero en ser servido

### IPC (ipc.py)
- **Mensajes**: Comunicación asíncrona entre procesos
- **Semáforos**: Sincronización de recursos compartidos
- **Memoria Compartida**: Intercambio eficiente de datos
- **Pipes**: Comunicación secuencial entre procesos

## 🎓 Uso Educativo

### Para Estudiantes
1. **Estudiar** cada componente individualmente
2. **Ejecutar** demostraciones para ver funcionamiento
3. **Modificar** parámetros para experimentar
4. **Comparar** con sistemas monolíticos

### Para Profesores
1. **Demostrar** conceptos de SO en tiempo real
2. **Explicar** ventajas y desventajas de microkernels
3. **Mostrar** IPC y separación de servicios
4. **Asignar** ejercicios de modificación

## 🔧 Personalización y Extensión

### Agregar Nuevos Servicios
```python
class MyCustomService:
    def __init__(self):
        self.name = "MyService"
        self.version = "1.0"
        self.running = False
    
    def start(self):
        self.running = True
        return True
    
    def stop(self):
        self.running = False

# Registrar en el kernel
kernel.register_service("myservice", MyCustomService())
```

### Crear Nuevas Aplicaciones
```python
class MyApp:
    def __init__(self):
        self.name = "MyApp"
        self.process_id = None
    
    def start(self, session_token=None):
        kernel = get_kernel()
        self.process_id = kernel.create_process(
            name=self.name,
            target_func=self._app_loop
        )
        return kernel.start_process(self.process_id)
    
    def _app_loop(self):
        # Lógica de la aplicación
        pass
```

## 📊 Configuración del Sistema

El sistema usa archivos JSON para configuración:

```json
{
  "kernel": {
    "max_processes": 1000,
    "memory_limit": 536870912,
    "debug_mode": false
  },
  "scheduler": {
    "algorithm": "round_robin",
    "time_quantum": 50
  },
  "security": {
    "session_timeout": 3600,
    "enable_audit": true
  }
}
```

## 🐛 Debugging y Logs

### Sistema de Logging
El sistema incluye logging completo:
- **Niveles**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Salida**: Consola y archivo
- **Filtrado**: Por nivel y componente
- **Estadísticas**: Análisis de logs

### Configuración de Debug
```python
# Habilitar modo debug en configuración
config.set_value("kernel", "debug_mode", True)
config.set_value("logging", "level", "DEBUG")
```

## ⚠️ Limitaciones Conocidas

Este es un proyecto **educativo**, no un SO real:

- **No hay protección de memoria real** - Simulada en Python
- **No maneja hardware real** - Dispositivos virtuales
- **IPC simplificado** - No implementa todos los mecanismos
- **Scheduling cooperativo** - No hay interrupciones reales
- **Sin persistencia real** - Archivos en memoria

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas! Especialmente:

- **Nuevos servicios** educativos
- **Aplicaciones de demostración** adicionales
- **Mejoras en documentación**
- **Ejemplos de uso** para el aula
- **Traducciones**

### Cómo Contribuir
1. Fork del repositorio
2. Crear rama para nueva funcionalidad
3. Implementar cambios
4. Añadir tests/demos si es necesario
5. Submit pull request

## 📖 Referencias y Recursos

### Libros Recomendados
- "Operating System Concepts" - Silberschatz, Galvin, Gagne
- "Modern Operating Systems" - Andrew S. Tanenbaum
- "Operating Systems: Three Easy Pieces" - Remzi H. Arpaci-Dusseau

### Papers Académicos
- "Microkernel-based operating systems" - Tanenbaum et al.
- "Exokernel: An Operating System Architecture for Application-Level Resource Management"
- "The performance of μ-kernel-based systems"

### Microkernels Reales
- **QNX** - Sistema en tiempo real
- **L4** - Familia de microkernels
- **MINIX** - Sistema educativo
- **GNU Hurd** - Proyecto GNU

## 📝 Licencia

Este proyecto está bajo la **Licencia MIT** - ver archivo [LICENSE](LICENSE) para detalles.

## 👥 Autores

- **Proyecto Educativo** - Implementación para VI Ciclo Universidad
- **Propósito**: Demostración de arquitectura microkernel

## 🎉 Agradecimientos

- Inspirado en los trabajos de Andrew S. Tanenbaum sobre microkernels
- Referencias de implementación de QNX y L4
- Comunidad educativa de sistemas operativos

---

## 🚀 ¡Empezar Ahora!

```bash
python main.py
```

¡Disfruta explorando la arquitectura microkernel! 🎓

---

*Proyecto desarrollado con fines educativos para demostrar conceptos de sistemas operativos y arquitectura microkernel.*