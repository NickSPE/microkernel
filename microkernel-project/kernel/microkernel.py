"""
MICROKERNEL CORE - Núcleo Mínimo del Sistema
============================================
Este es el corazón de nuestro sistema microkernel.
Solo contiene las funcionalidades más esenciales:
- Gestión básica de procesos
- Gestión de memoria mínima
- Comunicación entre procesos (IPC)
- Control de servicios externos
"""

import threading
import time
import uuid
from typing import Dict, List, Optional, Any
from enum import Enum

class ProcessState(Enum):
    READY = "ready"
    RUNNING = "running"
    BLOCKED = "blocked"
    TERMINATED = "terminated"

class Process:
    """Representa un proceso en el sistema"""
    def __init__(self, pid: str, name: str, priority: int = 1):
        self.pid = pid
        self.name = name
        self.priority = priority
        self.state = ProcessState.READY
        self.memory_allocated = 0
        self.created_at = time.time()
        self.thread: Optional[threading.Thread] = None
        self.context = {}  # Contexto del proceso

    def __str__(self):
        return f"Process[PID={self.pid}, Name={self.name}, State={self.state.value}]"

class Microkernel:
    """
    Núcleo mínimo del sistema operativo
    Responsabilidades:
    1. Gestión básica de procesos
    2. Gestión mínima de memoria
    3. IPC (Comunicación entre procesos)
    4. Registro y control de servicios
    """
    
    def __init__(self):
        self.processes: Dict[str, Process] = {}
        self.services: Dict[str, Any] = {}
        self.memory_pool = 1024 * 1024  # 1MB de memoria simulada
        self.memory_used = 0
        self.message_queue: Dict[str, List[Dict]] = {}
        self.running = False
        self.kernel_lock = threading.RLock()
        
        # Estadísticas del kernel
        self.stats = {
            'processes_created': 0,
            'processes_terminated': 0,
            'services_registered': 0,
            'messages_sent': 0
        }
        
        print("🔵 MICROKERNEL: Núcleo inicializado")
    
    def start(self):
        """Inicia el microkernel"""
        with self.kernel_lock:
            self.running = True
            print("🚀 MICROKERNEL: Sistema iniciado")
            print(f"📊 Memoria disponible: {self.memory_pool // 1024}KB")
    
    def stop(self):
        """Detiene el microkernel y todos los procesos"""
        with self.kernel_lock:
            print("⏹️  MICROKERNEL: Deteniendo sistema...")
            
            # Terminar todos los procesos
            for pid in list(self.processes.keys()):
                self.terminate_process(pid)
            
            self.running = False
            print("🔴 MICROKERNEL: Sistema detenido")
    
    # ==================== GESTIÓN DE PROCESOS ====================
    
    def create_process(self, name: str, target_func=None, args=(), priority: int = 1) -> str:
        """Crea un nuevo proceso en el sistema"""
        with self.kernel_lock:
            pid = str(uuid.uuid4())[:8]  # PID único
            process = Process(pid, name, priority)
            
            # Verificar memoria disponible
            memory_needed = 1024  # 1KB por proceso (simulado)
            if not self.allocate_memory(process, memory_needed):
                raise Exception(f"❌ No hay memoria suficiente para el proceso {name}")
            
            self.processes[pid] = process
            self.message_queue[pid] = []  # Cola de mensajes para el proceso
            self.stats['processes_created'] += 1
            
            print(f"✅ PROCESO CREADO: {process}")
            
            # Si se proporciona una función, crear y iniciar el hilo
            if target_func:
                process.thread = threading.Thread(
                    target=self._run_process, 
                    args=(pid, target_func, args)
                )
                process.thread.daemon = True
                process.state = ProcessState.READY
            
            return pid
    
    def _run_process(self, pid: str, target_func, args):
        """Ejecuta un proceso en su propio hilo"""
        try:
            process = self.processes[pid]
            process.state = ProcessState.RUNNING
            print(f"🏃 EJECUTANDO: {process.name} (PID: {pid})")
            
            # Ejecutar la función del proceso
            target_func(*args)
            
        except Exception as e:
            print(f"❌ ERROR en proceso {pid}: {e}")
        finally:
            if pid in self.processes:
                self.processes[pid].state = ProcessState.TERMINATED
    
    def start_process(self, pid: str) -> bool:
        """Inicia un proceso que está listo"""
        with self.kernel_lock:
            if pid not in self.processes:
                return False
            
            process = self.processes[pid]
            if process.state == ProcessState.READY and process.thread:
                process.thread.start()
                return True
            return False
    
    def terminate_process(self, pid: str) -> bool:
        """Termina un proceso y libera sus recursos"""
        with self.kernel_lock:
            if pid not in self.processes:
                return False
            
            process = self.processes[pid]
            process.state = ProcessState.TERMINATED
            
            # Liberar memoria
            self.deallocate_memory(process)
            
            # Limpiar cola de mensajes
            if pid in self.message_queue:
                del self.message_queue[pid]
            
            # Eliminar el proceso
            del self.processes[pid]
            self.stats['processes_terminated'] += 1
            
            print(f"🗑️  PROCESO TERMINADO: {process.name} (PID: {pid})")
            return True
    
    def list_processes(self) -> List[Process]:
        """Lista todos los procesos del sistema"""
        with self.kernel_lock:
            return list(self.processes.values())
    
    def get_process(self, pid: str) -> Optional[Process]:
        """Obtiene información de un proceso específico"""
        return self.processes.get(pid)
    
    # ==================== GESTIÓN DE MEMORIA ====================
    
    def allocate_memory(self, process: Process, size: int) -> bool:
        """Asigna memoria a un proceso"""
        if self.memory_used + size > self.memory_pool:
            return False
        
        self.memory_used += size
        process.memory_allocated = size
        print(f"🧠 MEMORIA: {size} bytes asignados a {process.name}")
        return True
    
    def deallocate_memory(self, process: Process) -> bool:
        """Libera la memoria de un proceso"""
        if process.memory_allocated > 0:
            self.memory_used -= process.memory_allocated
            print(f"🧠 MEMORIA: {process.memory_allocated} bytes liberados de {process.name}")
            process.memory_allocated = 0
            return True
        return False
    
    def get_memory_info(self) -> Dict[str, int]:
        """Obtiene información del uso de memoria"""
        return {
            'total': self.memory_pool,
            'used': self.memory_used,
            'free': self.memory_pool - self.memory_used,
            'percentage': (self.memory_used / self.memory_pool) * 100
        }
    
    # ==================== COMUNICACIÓN ENTRE PROCESOS (IPC) ====================
    
    def send_message(self, from_pid: str, to_pid: str, message: Any) -> bool:
        """Envía un mensaje de un proceso a otro (IPC)"""
        with self.kernel_lock:
            if to_pid not in self.message_queue:
                return False
            
            msg = {
                'from': from_pid,
                'to': to_pid,
                'message': message,
                'timestamp': time.time()
            }
            
            self.message_queue[to_pid].append(msg)
            self.stats['messages_sent'] += 1
            
            print(f"📨 MENSAJE: {from_pid} → {to_pid}")
            return True
    
    def receive_message(self, pid: str) -> Optional[Dict]:
        """Recibe un mensaje para un proceso"""
        with self.kernel_lock:
            if pid not in self.message_queue or not self.message_queue[pid]:
                return None
            
            return self.message_queue[pid].pop(0)
    
    def has_messages(self, pid: str) -> bool:
        """Verifica si un proceso tiene mensajes pendientes"""
        return pid in self.message_queue and len(self.message_queue[pid]) > 0
    
    # ==================== GESTIÓN DE SERVICIOS ====================
    
    def register_service(self, name: str, service_instance: Any) -> bool:
        """Registra un servicio en el kernel"""
        with self.kernel_lock:
            if name in self.services:
                print(f"⚠️  SERVICIO: {name} ya está registrado")
                return False
            
            self.services[name] = service_instance
            self.stats['services_registered'] += 1
            print(f"🔌 SERVICIO REGISTRADO: {name}")
            return True
    
    def get_service(self, name: str) -> Optional[Any]:
        """Obtiene una referencia a un servicio"""
        return self.services.get(name)
    
    def unregister_service(self, name: str) -> bool:
        """Desregistra un servicio"""
        with self.kernel_lock:
            if name not in self.services:
                return False
            
            del self.services[name]
            print(f"🔌 SERVICIO DESREGISTRADO: {name}")
            return True
    
    def list_services(self) -> List[str]:
        """Lista todos los servicios registrados"""
        return list(self.services.keys())
    
    # ==================== INFORMACIÓN DEL SISTEMA ====================
    
    def get_system_info(self) -> Dict[str, Any]:
        """Obtiene información completa del sistema"""
        memory_info = self.get_memory_info()
        
        return {
            'kernel_running': self.running,
            'processes': {
                'total': len(self.processes),
                'running': len([p for p in self.processes.values() if p.state == ProcessState.RUNNING]),
                'ready': len([p for p in self.processes.values() if p.state == ProcessState.READY]),
                'blocked': len([p for p in self.processes.values() if p.state == ProcessState.BLOCKED])
            },
            'memory': memory_info,
            'services': {
                'registered': len(self.services),
                'list': self.list_services()
            },
            'statistics': self.stats.copy(),
            'uptime': time.time() - (self.stats.get('start_time', time.time()))
        }
    
    def print_system_status(self):
        """Imprime el estado actual del sistema"""
        info = self.get_system_info()
        
        print("\n" + "="*50)
        print("📊 ESTADO DEL MICROKERNEL")
        print("="*50)
        print(f"🟢 Estado: {'Activo' if info['kernel_running'] else 'Inactivo'}")
        print(f"⚡ Procesos: {info['processes']['total']} total")
        print(f"   • En ejecución: {info['processes']['running']}")
        print(f"   • Listos: {info['processes']['ready']}")
        print(f"   • Bloqueados: {info['processes']['blocked']}")
        print(f"🧠 Memoria: {info['memory']['used']}/{info['memory']['total']} bytes ({info['memory']['percentage']:.1f}%)")
        print(f"🔌 Servicios: {info['services']['registered']} registrados")
        print(f"📈 Estadísticas:")
        print(f"   • Procesos creados: {info['statistics']['processes_created']}")
        print(f"   • Procesos terminados: {info['statistics']['processes_terminated']}")
        print(f"   • Servicios registrados: {info['statistics']['services_registered']}")
        print(f"   • Mensajes enviados: {info['statistics']['messages_sent']}")
        print("="*50)

# Instancia global del microkernel
kernel = Microkernel()

def get_kernel():
    """Obtiene la instancia global del microkernel"""
    return kernel