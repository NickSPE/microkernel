"""
IPC - Inter-Process Communication
=================================
Módulo especializado en comunicación entre procesos
Proporciona diferentes mecanismos de IPC como mensajes,
semáforos, memoria compartida, etc.
"""

import threading
import time
import queue
from typing import Dict, Any, Optional, List
from enum import Enum
from kernel.microkernel import get_kernel

class IPCType(Enum):
    MESSAGE = "message"
    SHARED_MEMORY = "shared_memory"  
    SEMAPHORE = "semaphore"
    PIPE = "pipe"

class Message:
    """Representa un mensaje IPC"""
    def __init__(self, sender: str, receiver: str, data: Any, msg_type: str = "data"):
        self.sender = sender
        self.receiver = receiver
        self.data = data
        self.msg_type = msg_type
        self.timestamp = time.time()
        self.id = f"{sender}-{receiver}-{int(self.timestamp * 1000000)}"
    
    def __str__(self):
        return f"Message[{self.sender}→{self.receiver}: {self.msg_type}]"

class Semaphore:
    """Semáforo para sincronización entre procesos"""
    def __init__(self, name: str, initial_value: int = 1):
        self.name = name
        self.value = initial_value
        self.initial_value = initial_value
        self.waiting_processes: List[str] = []
        self.lock = threading.RLock()
        self.condition = threading.Condition(self.lock)
        
    def acquire(self, process_id: str, timeout: Optional[float] = None) -> bool:
        """Adquiere el semáforo"""
        with self.condition:
            start_time = time.time()
            
            while self.value <= 0:
                if process_id not in self.waiting_processes:
                    self.waiting_processes.append(process_id)
                
                print(f"🔒 SEMAPHORE: {process_id} esperando {self.name}")
                
                # Esperar con timeout opcional
                if timeout:
                    remaining = timeout - (time.time() - start_time)
                    if remaining <= 0:
                        if process_id in self.waiting_processes:
                            self.waiting_processes.remove(process_id)
                        return False
                    self.condition.wait(timeout=remaining)
                else:
                    self.condition.wait()
            
            # Adquirir el semáforo
            self.value -= 1
            if process_id in self.waiting_processes:
                self.waiting_processes.remove(process_id)
            
            print(f"✅ SEMAPHORE: {process_id} adquirió {self.name} (valor: {self.value})")
            return True
    
    def release(self, process_id: str):
        """Libera el semáforo"""
        with self.condition:
            self.value += 1
            print(f"🔓 SEMAPHORE: {process_id} liberó {self.name} (valor: {self.value})")
            self.condition.notify()

class SharedMemory:
    """Memoria compartida entre procesos"""
    def __init__(self, name: str, size: int = 1024):
        self.name = name
        self.size = size
        self.data: Dict[str, Any] = {}
        self.lock = threading.RLock()
        self.access_count = 0
        self.authorized_processes: List[str] = []
    
    def authorize_process(self, process_id: str):
        """Autoriza a un proceso para acceder a la memoria compartida"""
        with self.lock:
            if process_id not in self.authorized_processes:
                self.authorized_processes.append(process_id)
                print(f"🔑 SHARED_MEM: {process_id} autorizado para {self.name}")
    
    def read(self, process_id: str, key: str) -> Optional[Any]:
        """Lee datos de la memoria compartida"""
        with self.lock:
            if process_id not in self.authorized_processes:
                print(f"❌ SHARED_MEM: {process_id} no autorizado para leer {self.name}")
                return None
            
            self.access_count += 1
            value = self.data.get(key)
            print(f"📖 SHARED_MEM: {process_id} leyó '{key}' de {self.name}")
            return value
    
    def write(self, process_id: str, key: str, value: Any) -> bool:
        """Escribe datos en la memoria compartida"""
        with self.lock:
            if process_id not in self.authorized_processes:
                print(f"❌ SHARED_MEM: {process_id} no autorizado para escribir en {self.name}")
                return False
            
            self.data[key] = value
            self.access_count += 1
            print(f"✏️  SHARED_MEM: {process_id} escribió '{key}' en {self.name}")
            return True

class Pipe:
    """Tubería para comunicación unidireccional entre procesos"""
    def __init__(self, name: str, max_size: int = 100):
        self.name = name
        self.queue = queue.Queue(maxsize=max_size)
        self.readers: List[str] = []
        self.writers: List[str] = []
        self.created_at = time.time()
    
    def add_reader(self, process_id: str):
        """Añade un proceso lector"""
        if process_id not in self.readers:
            self.readers.append(process_id)
            print(f"📖 PIPE: {process_id} añadido como lector de {self.name}")
    
    def add_writer(self, process_id: str):
        """Añade un proceso escritor"""
        if process_id not in self.writers:
            self.writers.append(process_id)
            print(f"✏️  PIPE: {process_id} añadido como escritor de {self.name}")
    
    def write(self, process_id: str, data: Any, timeout: Optional[float] = None) -> bool:
        """Escribe datos en la tubería"""
        if process_id not in self.writers:
            print(f"❌ PIPE: {process_id} no está autorizado para escribir en {self.name}")
            return False
        
        try:
            self.queue.put(data, timeout=timeout)
            print(f"📝 PIPE: {process_id} escribió en {self.name}")
            return True
        except queue.Full:
            print(f"⚠️  PIPE: {self.name} está llena, {process_id} no pudo escribir")
            return False
    
    def read(self, process_id: str, timeout: Optional[float] = None) -> Optional[Any]:
        """Lee datos de la tubería"""
        if process_id not in self.readers:
            print(f"❌ PIPE: {process_id} no está autorizado para leer de {self.name}")
            return None
        
        try:
            data = self.queue.get(timeout=timeout)
            print(f"📖 PIPE: {process_id} leyó de {self.name}")
            return data
        except queue.Empty:
            return None

class IPCManager:
    """
    Gestor principal de comunicación entre procesos
    Coordina todos los mecanismos de IPC
    """
    
    def __init__(self):
        self.messages: Dict[str, List[Message]] = {}
        self.semaphores: Dict[str, Semaphore] = {}
        self.shared_memories: Dict[str, SharedMemory] = {}
        self.pipes: Dict[str, Pipe] = {}
        self.ipc_lock = threading.RLock()
        
        print("📡 IPC_MANAGER: Sistema de comunicación inicializado")
    
    # ==================== GESTIÓN DE MENSAJES ====================
    
    def send_message(self, sender: str, receiver: str, data: Any, msg_type: str = "data") -> bool:
        """Envía un mensaje de un proceso a otro"""
        with self.ipc_lock:
            kernel = get_kernel()
            
            # Verificar que ambos procesos existen
            if not kernel.get_process(sender) or not kernel.get_process(receiver):
                print(f"❌ IPC: Proceso sender={sender} o receiver={receiver} no existe")
                return False
            
            message = Message(sender, receiver, data, msg_type)
            
            # Inicializar cola de mensajes si no existe
            if receiver not in self.messages:
                self.messages[receiver] = []
            
            self.messages[receiver].append(message)
            print(f"📨 IPC: {message}")
            return True
    
    def receive_message(self, process_id: str, timeout: Optional[float] = None) -> Optional[Message]:
        """Recibe un mensaje para un proceso"""
        with self.ipc_lock:
            if process_id not in self.messages or not self.messages[process_id]:
                return None
            
            message = self.messages[process_id].pop(0)
            print(f"📬 IPC: {process_id} recibió mensaje de {message.sender}")
            return message
    
    def has_messages(self, process_id: str) -> bool:
        """Verifica si un proceso tiene mensajes pendientes"""
        return process_id in self.messages and len(self.messages[process_id]) > 0
    
    def get_message_count(self, process_id: str) -> int:
        """Obtiene el número de mensajes pendientes"""
        return len(self.messages.get(process_id, []))
    
    # ==================== GESTIÓN DE SEMÁFOROS ====================
    
    def create_semaphore(self, name: str, initial_value: int = 1) -> bool:
        """Crea un nuevo semáforo"""
        with self.ipc_lock:
            if name in self.semaphores:
                print(f"⚠️  IPC: Semáforo '{name}' ya existe")
                return False
            
            self.semaphores[name] = Semaphore(name, initial_value)
            print(f"🔒 IPC: Semáforo '{name}' creado con valor {initial_value}")
            return True
    
    def acquire_semaphore(self, semaphore_name: str, process_id: str, timeout: Optional[float] = None) -> bool:
        """Adquiere un semáforo"""
        if semaphore_name not in self.semaphores:
            print(f"❌ IPC: Semáforo '{semaphore_name}' no existe")
            return False
        
        return self.semaphores[semaphore_name].acquire(process_id, timeout)
    
    def release_semaphore(self, semaphore_name: str, process_id: str) -> bool:
        """Libera un semáforo"""
        if semaphore_name not in self.semaphores:
            print(f"❌ IPC: Semáforo '{semaphore_name}' no existe")
            return False
        
        self.semaphores[semaphore_name].release(process_id)
        return True
    
    # ==================== GESTIÓN DE MEMORIA COMPARTIDA ====================
    
    def create_shared_memory(self, name: str, size: int = 1024) -> bool:
        """Crea un segmento de memoria compartida"""
        with self.ipc_lock:
            if name in self.shared_memories:
                print(f"⚠️  IPC: Memoria compartida '{name}' ya existe")
                return False
            
            self.shared_memories[name] = SharedMemory(name, size)
            print(f"🧠 IPC: Memoria compartida '{name}' creada ({size} bytes)")
            return True
    
    def authorize_shared_memory_access(self, memory_name: str, process_id: str) -> bool:
        """Autoriza el acceso a memoria compartida"""
        if memory_name not in self.shared_memories:
            print(f"❌ IPC: Memoria compartida '{memory_name}' no existe")
            return False
        
        self.shared_memories[memory_name].authorize_process(process_id)
        return True
    
    def read_shared_memory(self, memory_name: str, process_id: str, key: str) -> Optional[Any]:
        """Lee de memoria compartida"""
        if memory_name not in self.shared_memories:
            return None
        
        return self.shared_memories[memory_name].read(process_id, key)
    
    def write_shared_memory(self, memory_name: str, process_id: str, key: str, value: Any) -> bool:
        """Escribe en memoria compartida"""
        if memory_name not in self.shared_memories:
            return False
        
        return self.shared_memories[memory_name].write(process_id, key, value)
    
    # ==================== GESTIÓN DE TUBERÍAS ====================
    
    def create_pipe(self, name: str, max_size: int = 100) -> bool:
        """Crea una nueva tubería"""
        with self.ipc_lock:
            if name in self.pipes:
                print(f"⚠️  IPC: Tubería '{name}' ya existe")
                return False
            
            self.pipes[name] = Pipe(name, max_size)
            print(f"🚰 IPC: Tubería '{name}' creada (tamaño: {max_size})")
            return True
    
    def add_pipe_reader(self, pipe_name: str, process_id: str) -> bool:
        """Añade un proceso lector a una tubería"""
        if pipe_name not in self.pipes:
            return False
        
        self.pipes[pipe_name].add_reader(process_id)
        return True
    
    def add_pipe_writer(self, pipe_name: str, process_id: str) -> bool:
        """Añade un proceso escritor a una tubería"""
        if pipe_name not in self.pipes:
            return False
        
        self.pipes[pipe_name].add_writer(process_id)
        return True
    
    def write_pipe(self, pipe_name: str, process_id: str, data: Any, timeout: Optional[float] = None) -> bool:
        """Escribe en una tubería"""
        if pipe_name not in self.pipes:
            return False
        
        return self.pipes[pipe_name].write(process_id, data, timeout)
    
    def read_pipe(self, pipe_name: str, process_id: str, timeout: Optional[float] = None) -> Optional[Any]:
        """Lee de una tubería"""
        if pipe_name not in self.pipes:
            return None
        
        return self.pipes[pipe_name].read(process_id, timeout)
    
    # ==================== INFORMACIÓN Y ESTADÍSTICAS ====================
    
    def get_ipc_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del sistema IPC"""
        total_messages = sum(len(msgs) for msgs in self.messages.values())
        
        return {
            'messages': {
                'total_pending': total_messages,
                'processes_with_messages': len([pid for pid, msgs in self.messages.items() if msgs])
            },
            'semaphores': {
                'count': len(self.semaphores),
                'names': list(self.semaphores.keys())
            },
            'shared_memory': {
                'count': len(self.shared_memories),
                'total_size': sum(sm.size for sm in self.shared_memories.values()),
                'names': list(self.shared_memories.keys())
            },
            'pipes': {
                'count': len(self.pipes),
                'names': list(self.pipes.keys())
            }
        }
    
    def print_ipc_status(self):
        """Imprime el estado del sistema IPC"""
        stats = self.get_ipc_stats()
        
        print("\n" + "-"*40)
        print("📡 ESTADO DEL SISTEMA IPC")
        print("-"*40)
        print(f"📨 Mensajes: {stats['messages']['total_pending']} pendientes")
        print(f"🔒 Semáforos: {stats['semaphores']['count']} activos")
        print(f"🧠 Memoria compartida: {stats['shared_memory']['count']} segmentos")
        print(f"🚰 Tuberías: {stats['pipes']['count']} activas")
        print("-"*40)

# Instancia global del gestor IPC
ipc_manager = IPCManager()

def get_ipc_manager():
    """Obtiene la instancia global del gestor IPC"""
    return ipc_manager