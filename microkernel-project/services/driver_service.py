"""
DRIVER SERVICE - Servicio de Controladores de Dispositivos
==========================================================
Simula la gestión de dispositivos de hardware
como discos, impresoras, tarjetas de red, etc.
"""

import time
import threading
import random
from typing import Dict, List, Optional, Any
from enum import Enum
from kernel.microkernel import get_kernel

class DeviceType(Enum):
    STORAGE = "storage"
    NETWORK = "network" 
    INPUT = "input"
    OUTPUT = "output"
    MEMORY = "memory"
    GRAPHICS = "graphics"

class DeviceState(Enum):
    OFFLINE = "offline"
    INITIALIZING = "initializing"
    ONLINE = "online"
    ERROR = "error"
    MAINTENANCE = "maintenance"

class VirtualDevice:
    """Representa un dispositivo virtual del sistema"""
    
    def __init__(self, device_id: str, name: str, device_type: DeviceType):
        self.device_id = device_id
        self.name = name
        self.device_type = device_type
        self.state = DeviceState.OFFLINE
        self.driver_version = "1.0"
        self.firmware_version = "1.0"
        self.created_at = time.time()
        self.last_accessed = time.time()
        self.operations_count = 0
        self.error_count = 0
        self.properties = {}
        self.capabilities = []
        
        # Estadísticas específicas del dispositivo
        self.stats = {
            'read_operations': 0,
            'write_operations': 0,
            'bytes_read': 0,
            'bytes_written': 0,
            'uptime': 0,
            'error_rate': 0.0
        }
    
    def initialize(self) -> bool:
        """Inicializa el dispositivo"""
        print(f"🔧 DEVICE: Inicializando {self.name} ({self.device_id})")
        self.state = DeviceState.INITIALIZING
        
        # Simular tiempo de inicialización
        time.sleep(random.uniform(0.1, 0.3))
        
        # Simular fallo ocasional de inicialización
        if random.random() < 0.05:  # 5% de fallo
            self.state = DeviceState.ERROR
            self.error_count += 1
            print(f"❌ DEVICE: Error inicializando {self.name}")
            return False
        
        self.state = DeviceState.ONLINE
        self.last_accessed = time.time()
        print(f"✅ DEVICE: {self.name} inicializado correctamente")
        return True
    
    def shutdown(self) -> bool:
        """Apaga el dispositivo"""
        print(f"⏹️  DEVICE: Apagando {self.name}")
        self.state = DeviceState.OFFLINE
        return True
    
    def read_data(self, size: int = 1024) -> Optional[bytes]:
        """Simula lectura de datos del dispositivo"""
        if self.state != DeviceState.ONLINE:
            return None
        
        # Simular tiempo de lectura
        time.sleep(random.uniform(0.001, 0.01))
        
        # Simular error ocasional
        if random.random() < 0.01:  # 1% error
            self.error_count += 1
            return None
        
        self.stats['read_operations'] += 1
        self.stats['bytes_read'] += size
        self.last_accessed = time.time()
        self.operations_count += 1
        
        # Generar datos simulados
        data = b'x' * size
        return data
    
    def write_data(self, data: bytes) -> bool:
        """Simula escritura de datos al dispositivo"""
        if self.state != DeviceState.ONLINE:
            return False
        
        # Simular tiempo de escritura
        time.sleep(random.uniform(0.001, 0.02))
        
        # Simular error ocasional
        if random.random() < 0.01:  # 1% error
            self.error_count += 1
            return False
        
        size = len(data)
        self.stats['write_operations'] += 1
        self.stats['bytes_written'] += size
        self.last_accessed = time.time()
        self.operations_count += 1
        
        return True
    
    def get_info(self) -> Dict[str, Any]:
        """Obtiene información completa del dispositivo"""
        uptime = time.time() - self.created_at if self.state == DeviceState.ONLINE else 0
        error_rate = self.error_count / max(self.operations_count, 1) * 100
        
        return {
            'device_id': self.device_id,
            'name': self.name,
            'type': self.device_type.value,
            'state': self.state.value,
            'driver_version': self.driver_version,
            'firmware_version': self.firmware_version,
            'uptime_seconds': uptime,
            'operations_count': self.operations_count,
            'error_count': self.error_count,
            'error_rate_percent': error_rate,
            'last_accessed': time.ctime(self.last_accessed),
            'properties': self.properties.copy(),
            'capabilities': self.capabilities.copy(),
            'statistics': self.stats.copy()
        }

class DriverService:
    """
    Servicio de Controladores de Dispositivos
    Gestiona todos los dispositivos del sistema
    """
    
    def __init__(self):
        self.name = "DriverService"
        self.version = "1.0"
        self.running = False
        self.devices: Dict[str, VirtualDevice] = {}
        self.device_drivers: Dict[str, str] = {}  # device_id -> driver_name
        self.driver_lock = threading.RLock()
        self.monitoring_thread: Optional[threading.Thread] = None
        
        # Estadísticas del servicio
        self.service_stats = {
            'devices_registered': 0,
            'devices_online': 0,
            'devices_error': 0,
            'total_operations': 0,
            'driver_loads': 0,
            'driver_unloads': 0
        }
        
        # Crear algunos dispositivos de ejemplo
        self._create_default_devices()
        
        print("🔧 DRIVER_SERVICE: Servicio de controladores inicializado")
    
    def _create_default_devices(self):
        """Crea dispositivos de ejemplo"""
        # Disco duro primario
        hdd = VirtualDevice("hdd0", "Disco Duro Principal", DeviceType.STORAGE)
        hdd.properties = {
            'capacity_gb': 500,
            'rpm': 7200,
            'interface': 'SATA III',
            'model': 'Virtual HDD v1.0'
        }
        hdd.capabilities = ['read', 'write', 'format', 'defrag']
        self.devices['hdd0'] = hdd
        
        # SSD secundario
        ssd = VirtualDevice("ssd0", "Unidad SSD", DeviceType.STORAGE)
        ssd.properties = {
            'capacity_gb': 256,
            'interface': 'NVMe',
            'model': 'Virtual SSD v1.0',
            'write_cycles': 100000
        }
        ssd.capabilities = ['read', 'write', 'trim', 'secure_erase']
        self.devices['ssd0'] = ssd
        
        # Tarjeta de red
        nic = VirtualDevice("eth0", "Tarjeta de Red Ethernet", DeviceType.NETWORK)
        nic.properties = {
            'speed_mbps': 1000,
            'mac_address': '00:1B:44:11:3A:B7',
            'link_status': 'up',
            'duplex': 'full'
        }
        nic.capabilities = ['send', 'receive', 'promiscuous', 'wake_on_lan']
        self.devices['eth0'] = nic
        
        # Teclado USB
        keyboard = VirtualDevice("kbd0", "Teclado USB", DeviceType.INPUT)
        keyboard.properties = {
            'layout': 'QWERTY',
            'num_keys': 104,
            'interface': 'USB 2.0',
            'polling_rate': 125
        }
        keyboard.capabilities = ['key_press', 'key_release', 'led_control']
        self.devices['kbd0'] = keyboard
        
        # Monitor
        monitor = VirtualDevice("display0", "Monitor Principal", DeviceType.OUTPUT)
        monitor.properties = {
            'resolution': '1920x1080',
            'refresh_rate': 60,
            'color_depth': 24,
            'interface': 'HDMI'
        }
        monitor.capabilities = ['display', 'brightness_control', 'color_adjustment']
        self.devices['display0'] = monitor
        
        print(f"🔧 DRIVER_SERVICE: {len(self.devices)} dispositivos por defecto creados")
    
    def start(self):
        """Inicia el servicio de controladores"""
        with self.driver_lock:
            if self.running:
                return True
            
            self.running = True
            
            # Inicializar todos los dispositivos
            self._initialize_all_devices()
            
            # Iniciar hilo de monitoreo
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop)
            self.monitoring_thread.daemon = True
            self.monitoring_thread.start()
            
            print("🟢 DRIVER_SERVICE: Servicio de controladores iniciado")
            return True
    
    def stop(self):
        """Detiene el servicio de controladores"""
        with self.driver_lock:
            self.running = False
            
            # Apagar todos los dispositivos
            for device in self.devices.values():
                device.shutdown()
            
            print("🔴 DRIVER_SERVICE: Servicio de controladores detenido")
    
    def _initialize_all_devices(self):
        """Inicializa todos los dispositivos registrados"""
        print("🚀 DRIVER_SERVICE: Inicializando dispositivos...")
        
        for device in self.devices.values():
            if device.state == DeviceState.OFFLINE:
                device.initialize()
        
        self._update_service_stats()
    
    def _monitoring_loop(self):
        """Bucle de monitoreo de dispositivos"""
        while self.running:
            try:
                # Verificar estado de dispositivos
                self._check_device_health()
                
                # Actualizar estadísticas
                self._update_service_stats()
                
                # Pausa de monitoreo
                time.sleep(5.0)
                
            except Exception as e:
                print(f"❌ DRIVER_SERVICE MONITOR ERROR: {e}")
    
    def _check_device_health(self):
        """Verifica la salud de todos los dispositivos"""
        current_time = time.time()
        
        for device in self.devices.values():
            if device.state == DeviceState.ONLINE:
                # Verificar si el dispositivo ha estado inactivo demasiado tiempo
                if current_time - device.last_accessed > 300:  # 5 minutos
                    # Hacer un test básico
                    test_data = device.read_data(64)
                    if test_data is None:
                        print(f"⚠️  DRIVER: Dispositivo {device.name} no responde")
                        device.state = DeviceState.ERROR
                        device.error_count += 1
    
    def _update_service_stats(self):
        """Actualiza las estadísticas del servicio"""
        self.service_stats['devices_online'] = len([d for d in self.devices.values() 
                                                   if d.state == DeviceState.ONLINE])
        self.service_stats['devices_error'] = len([d for d in self.devices.values() 
                                                  if d.state == DeviceState.ERROR])
        self.service_stats['total_operations'] = sum(d.operations_count for d in self.devices.values())
    
    # ==================== GESTIÓN DE DISPOSITIVOS ====================
    
    def register_device(self, device: VirtualDevice, driver_name: str = "generic") -> bool:
        """Registra un nuevo dispositivo en el sistema"""
        with self.driver_lock:
            if device.device_id in self.devices:
                print(f"⚠️  DRIVER: Dispositivo {device.device_id} ya está registrado")
                return False
            
            self.devices[device.device_id] = device
            self.device_drivers[device.device_id] = driver_name
            self.service_stats['devices_registered'] += 1
            
            print(f"✅ DRIVER: Dispositivo {device.name} registrado con driver {driver_name}")
            
            # Inicializar si el servicio está corriendo
            if self.running:
                device.initialize()
            
            return True
    
    def unregister_device(self, device_id: str) -> bool:
        """Desregistra un dispositivo"""
        with self.driver_lock:
            if device_id not in self.devices:
                return False
            
            device = self.devices[device_id]
            device.shutdown()
            
            del self.devices[device_id]
            if device_id in self.device_drivers:
                del self.device_drivers[device_id]
            
            print(f"🗑️  DRIVER: Dispositivo {device.name} desregistrado")
            return True
    
    def get_device(self, device_id: str) -> Optional[VirtualDevice]:
        """Obtiene una referencia a un dispositivo"""
        return self.devices.get(device_id)
    
    def list_devices(self, device_type: Optional[DeviceType] = None) -> List[VirtualDevice]:
        """Lista dispositivos, opcionalmente filtrados por tipo"""
        devices = list(self.devices.values())
        
        if device_type:
            devices = [d for d in devices if d.device_type == device_type]
        
        return devices
    
    def get_device_info(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene información detallada de un dispositivo"""
        device = self.get_device(device_id)
        if not device:
            return None
        
        info = device.get_info()
        info['driver'] = self.device_drivers.get(device_id, 'unknown')
        return info
    
    # ==================== OPERACIONES DE DISPOSITIVOS ====================
    
    def device_read(self, device_id: str, size: int = 1024, process_id: str = "system") -> Optional[bytes]:
        """Lee datos de un dispositivo"""
        device = self.get_device(device_id)
        if not device:
            print(f"❌ DRIVER: Dispositivo {device_id} no encontrado")
            return None
        
        data = device.read_data(size)
        if data:
            print(f"📖 DRIVER: {process_id} leyó {len(data)} bytes de {device.name}")
        
        return data
    
    def device_write(self, device_id: str, data: bytes, process_id: str = "system") -> bool:
        """Escribe datos a un dispositivo"""
        device = self.get_device(device_id)
        if not device:
            print(f"❌ DRIVER: Dispositivo {device_id} no encontrado")
            return False
        
        success = device.write_data(data)
        if success:
            print(f"✏️  DRIVER: {process_id} escribió {len(data)} bytes a {device.name}")
        
        return success
    
    def device_control(self, device_id: str, command: str, parameters: Dict = None) -> bool:
        """Envía un comando de control a un dispositivo"""
        device = self.get_device(device_id)
        if not device:
            return False
        
        print(f"🎛️  DRIVER: Comando '{command}' enviado a {device.name}")
        
        # Simular procesamiento del comando
        time.sleep(random.uniform(0.01, 0.05))
        
        # Algunos comandos especiales
        if command == "reset":
            device.shutdown()
            time.sleep(0.1)
            return device.initialize()
        elif command == "test":
            return device.read_data(64) is not None
        elif command == "maintenance":
            device.state = DeviceState.MAINTENANCE
            return True
        
        return True
    
    # ==================== GESTIÓN DE CONTROLADORES ====================
    
    def load_driver(self, driver_name: str, driver_path: str = None) -> bool:
        """Simula la carga de un controlador"""
        print(f"📦 DRIVER: Cargando controlador {driver_name}")
        
        # Simular tiempo de carga
        time.sleep(random.uniform(0.1, 0.3))
        
        # Simular fallo ocasional
        if random.random() < 0.02:  # 2% fallo
            print(f"❌ DRIVER: Error cargando controlador {driver_name}")
            return False
        
        self.service_stats['driver_loads'] += 1
        print(f"✅ DRIVER: Controlador {driver_name} cargado exitosamente")
        return True
    
    def unload_driver(self, driver_name: str) -> bool:
        """Simula la descarga de un controlador"""
        print(f"📤 DRIVER: Descargando controlador {driver_name}")
        
        # Verificar si hay dispositivos usando este controlador
        devices_using = [device_id for device_id, driver in self.device_drivers.items() 
                        if driver == driver_name]
        
        if devices_using:
            print(f"⚠️  DRIVER: No se puede descargar {driver_name}, {len(devices_using)} dispositivos en uso")
            return False
        
        self.service_stats['driver_unloads'] += 1
        print(f"✅ DRIVER: Controlador {driver_name} descargado")
        return True
    
    # ==================== INFORMACIÓN Y ESTADÍSTICAS ====================
    
    def get_driver_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del servicio de controladores"""
        device_states = {}
        for state in DeviceState:
            device_states[state.value] = len([d for d in self.devices.values() if d.state == state])
        
        device_types = {}
        for dev_type in DeviceType:
            device_types[dev_type.value] = len([d for d in self.devices.values() 
                                              if d.device_type == dev_type])
        
        return {
            'service_running': self.running,
            'total_devices': len(self.devices),
            'device_states': device_states,
            'device_types': device_types,
            'loaded_drivers': len(set(self.device_drivers.values())),
            'service_statistics': self.service_stats.copy()
        }
    
    def print_driver_status(self):
        """Imprime el estado del servicio de controladores"""
        stats = self.get_driver_stats()
        
        print("\n" + "-"*50)
        print("🔧 ESTADO DEL SERVICIO DE CONTROLADORES")
        print("-"*50)
        print(f"🟢 Estado: {'Activo' if stats['service_running'] else 'Inactivo'}")
        print(f"📱 Dispositivos totales: {stats['total_devices']}")
        
        print("📊 Estados de dispositivos:")
        for state, count in stats['device_states'].items():
            icon = {"online": "🟢", "offline": "⚫", "error": "🔴", 
                   "initializing": "🟡", "maintenance": "🟠"}.get(state, "❓")
            print(f"   {icon} {state.capitalize()}: {count}")
        
        print("🏷️  Tipos de dispositivos:")
        for dev_type, count in stats['device_types'].items():
            icon = {"storage": "💾", "network": "🌐", "input": "⌨️", 
                   "output": "🖥️", "memory": "🧠", "graphics": "🎨"}.get(dev_type, "📱")
            print(f"   {icon} {dev_type.capitalize()}: {count}")
        
        print(f"📦 Controladores cargados: {stats['loaded_drivers']}")
        print(f"🔢 Operaciones totales: {stats['service_statistics']['total_operations']}")
        print("-"*50)
    
    def print_device_list(self):
        """Imprime lista detallada de dispositivos"""
        print("\n🔧 DISPOSITIVOS DEL SISTEMA:")
        
        for device in self.devices.values():
            state_icon = {"online": "🟢", "offline": "⚫", "error": "🔴", 
                         "initializing": "🟡", "maintenance": "🟠"}.get(device.state.value, "❓")
            type_icon = {"storage": "💾", "network": "🌐", "input": "⌨️", 
                        "output": "🖥️", "memory": "🧠", "graphics": "🎨"}.get(device.device_type.value, "📱")
            
            driver = self.device_drivers.get(device.device_id, 'unknown')
            
            print(f"  {state_icon} {type_icon} {device.name} ({device.device_id})")
            print(f"      Controlador: {driver} | Operaciones: {device.operations_count} | Errores: {device.error_count}")

# Instancia global del servicio de controladores
driver_service = DriverService()

def get_driver_service():
    """Obtiene la instancia global del servicio de controladores"""
    return driver_service