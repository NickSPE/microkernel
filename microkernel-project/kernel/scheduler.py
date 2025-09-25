"""
SCHEDULER - Planificador de Procesos del Microkernel
=====================================================
Implementa algoritmos de planificación para gestionar
la ejecución de procesos de manera eficiente.
"""

import time
import threading
from typing import List, Optional
from kernel.microkernel import ProcessState, get_kernel

class Scheduler:
    """
    Planificador de procesos para el microkernel
    Implementa Round Robin con prioridades
    """
    
    def __init__(self, time_slice: float = 0.1):
        self.time_slice = time_slice  # Quantum de tiempo en segundos
        self.scheduler_thread: Optional[threading.Thread] = None
        self.running = False
        self.current_process = None
        self.scheduler_lock = threading.RLock()
        
        print(f"⏰ SCHEDULER: Inicializado (quantum: {time_slice*1000}ms)")
    
    def start(self):
        """Inicia el planificador"""
        with self.scheduler_lock:
            if self.running:
                return
            
            self.running = True
            self.scheduler_thread = threading.Thread(target=self._scheduling_loop)
            self.scheduler_thread.daemon = True
            self.scheduler_thread.start()
            
            print("🔄 SCHEDULER: Planificador iniciado")
    
    def stop(self):
        """Detiene el planificador"""
        with self.scheduler_lock:
            self.running = False
            if self.scheduler_thread and self.scheduler_thread.is_alive():
                self.scheduler_thread.join(timeout=1.0)
            
            print("⏹️  SCHEDULER: Planificador detenido")
    
    def _scheduling_loop(self):
        """Bucle principal del planificador"""
        kernel = get_kernel()
        
        while self.running:
            try:
                # Obtener procesos listos para ejecutar
                ready_processes = self._get_ready_processes()
                
                if ready_processes:
                    # Seleccionar el siguiente proceso usando Round Robin con prioridades
                    next_process = self._select_next_process(ready_processes)
                    
                    if next_process:
                        self._execute_process_slice(next_process)
                
                # Pequeña pausa para no saturar la CPU
                time.sleep(0.01)
                
            except Exception as e:
                print(f"❌ SCHEDULER ERROR: {e}")
    
    def _get_ready_processes(self) -> List:
        """Obtiene todos los procesos en estado READY"""
        kernel = get_kernel()
        return [p for p in kernel.list_processes() if p.state == ProcessState.READY]
    
    def _select_next_process(self, ready_processes: List) -> Optional:
        """Selecciona el siguiente proceso a ejecutar"""
        if not ready_processes:
            return None
        
        # Ordenar por prioridad (mayor prioridad primero) y luego por tiempo de creación
        ready_processes.sort(key=lambda p: (-p.priority, p.created_at))
        
        # Round Robin: si hay un proceso actual, buscar el siguiente
        if self.current_process and self.current_process in ready_processes:
            current_index = ready_processes.index(self.current_process)
            # Seleccionar el siguiente proceso de la misma prioridad
            same_priority = [p for p in ready_processes if p.priority == self.current_process.priority]
            if len(same_priority) > 1:
                next_index = (same_priority.index(self.current_process) + 1) % len(same_priority)
                return same_priority[next_index]
        
        # Si no hay proceso actual o solo hay uno, seleccionar el primero
        return ready_processes[0]
    
    def _execute_process_slice(self, process):
        """Ejecuta un proceso por un quantum de tiempo"""
        with self.scheduler_lock:
            if not self.running:
                return
            
            self.current_process = process
            
            # Cambiar estado a RUNNING
            old_state = process.state
            process.state = ProcessState.RUNNING
            
            print(f"🏃 SCHEDULER: Ejecutando {process.name} (PID: {process.pid})")
            
            # Simular ejecución por el quantum de tiempo
            start_time = time.time()
            
            # En un sistema real, aquí se haría el cambio de contexto
            # Por simplicidad, solo esperamos el tiempo del quantum
            time.sleep(self.time_slice)
            
            execution_time = time.time() - start_time
            
            # Volver el proceso al estado READY (Round Robin)
            if process.state == ProcessState.RUNNING:
                process.state = ProcessState.READY
                print(f"⏸️  SCHEDULER: {process.name} devuelto a READY ({execution_time*1000:.1f}ms)")
    
    def set_time_slice(self, new_slice: float):
        """Cambia el quantum de tiempo del planificador"""
        with self.scheduler_lock:
            old_slice = self.time_slice
            self.time_slice = new_slice
            print(f"⏰ SCHEDULER: Quantum cambiado de {old_slice*1000:.1f}ms a {new_slice*1000:.1f}ms")
    
    def get_scheduling_info(self) -> dict:
        """Obtiene información sobre el estado del planificador"""
        kernel = get_kernel()
        processes = kernel.list_processes()
        
        return {
            'running': self.running,
            'time_slice_ms': self.time_slice * 1000,
            'current_process': self.current_process.name if self.current_process else None,
            'ready_processes': len([p for p in processes if p.state == ProcessState.READY]),
            'running_processes': len([p for p in processes if p.state == ProcessState.RUNNING]),
            'blocked_processes': len([p for p in processes if p.state == ProcessState.BLOCKED]),
            'total_processes': len(processes)
        }
    
    def print_scheduling_status(self):
        """Imprime el estado del planificador"""
        info = self.get_scheduling_info()
        
        print("\n" + "-"*40)
        print("⏰ ESTADO DEL PLANIFICADOR")
        print("-"*40)
        print(f"🔄 Estado: {'Activo' if info['running'] else 'Inactivo'}")
        print(f"⚡ Quantum: {info['time_slice_ms']:.1f}ms")
        print(f"🎯 Proceso actual: {info['current_process'] or 'Ninguno'}")
        print(f"📊 Procesos por estado:")
        print(f"   • Listos: {info['ready_processes']}")
        print(f"   • Ejecutándose: {info['running_processes']}")
        print(f"   • Bloqueados: {info['blocked_processes']}")
        print(f"   • Total: {info['total_processes']}")
        print("-"*40)

class PriorityScheduler(Scheduler):
    """
    Planificador basado en prioridades
    Los procesos con mayor prioridad siempre se ejecutan primero
    """
    
    def __init__(self):
        super().__init__(time_slice=0.05)  # Quantum más pequeño para mayor responsividad
        print("🔝 PRIORITY SCHEDULER: Inicializado")
    
    def _select_next_process(self, ready_processes: List) -> Optional:
        """Selecciona siempre el proceso con mayor prioridad"""
        if not ready_processes:
            return None
        
        # Ordenar por prioridad (mayor primero) y por tiempo de creación como desempate
        ready_processes.sort(key=lambda p: (-p.priority, p.created_at))
        
        return ready_processes[0]

class FIFOScheduler(Scheduler):
    """
    Planificador First In, First Out (FIFO)
    Los procesos se ejecutan en el orden que llegaron
    """
    
    def __init__(self):
        super().__init__(time_slice=0.2)  # Quantum más largo
        print("📥 FIFO SCHEDULER: Inicializado")
    
    def _select_next_process(self, ready_processes: List) -> Optional:
        """Selecciona el proceso más antiguo"""
        if not ready_processes:
            return None
        
        # Ordenar solo por tiempo de creación (FIFO)
        ready_processes.sort(key=lambda p: p.created_at)
        
        return ready_processes[0]

# Instancia global del planificador
scheduler = Scheduler()

def get_scheduler():
    """Obtiene la instancia global del planificador"""
    return scheduler

def set_scheduler(new_scheduler: Scheduler):
    """Cambia el planificador del sistema"""
    global scheduler
    if scheduler.running:
        scheduler.stop()
    
    scheduler = new_scheduler
    print(f"🔄 SCHEDULER: Cambiado a {type(new_scheduler).__name__}")
    
    return scheduler