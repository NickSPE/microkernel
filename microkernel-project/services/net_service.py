"""
NETWORK SERVICE - Servicio de Red
=================================
Simula operaciones de red como conexiones, 
transferencia de datos, etc.
"""

import time
import threading
import random
import json
from typing import Dict, List, Optional, Any
from enum import Enum
from kernel.microkernel import get_kernel

class ConnectionState(Enum):
    CLOSED = "closed"
    CONNECTING = "connecting"
    ESTABLISHED = "established"
    CLOSING = "closing"
    ERROR = "error"

class NetworkPacket:
    """Representa un paquete de red"""
    def __init__(self, source: str, destination: str, data: Any, packet_type: str = "data"):
        self.source = source
        self.destination = destination
        self.data = data
        self.packet_type = packet_type
        self.timestamp = time.time()
        self.size = len(str(data).encode('utf-8'))
        self.id = f"{source}-{destination}-{int(self.timestamp * 1000000)}"
    
    def __str__(self):
        return f"Packet[{self.source}→{self.destination}: {self.packet_type} ({self.size}B)]"

class NetworkConnection:
    """Representa una conexión de red"""
    def __init__(self, connection_id: str, local_address: str, remote_address: str):
        self.id = connection_id
        self.local_address = local_address
        self.remote_address = remote_address
        self.state = ConnectionState.CLOSED
        self.created_at = time.time()
        self.last_activity = time.time()
        self.bytes_sent = 0
        self.bytes_received = 0
        self.packets_sent = 0
        self.packets_received = 0
    
    def send_data(self, data: Any) -> bool:
        """Simula el envío de datos"""
        if self.state != ConnectionState.ESTABLISHED:
            return False
        
        packet_size = len(str(data).encode('utf-8'))
        self.bytes_sent += packet_size
        self.packets_sent += 1
        self.last_activity = time.time()
        
        return True
    
    def receive_data(self, packet: NetworkPacket) -> bool:
        """Simula la recepción de datos"""
        if self.state != ConnectionState.ESTABLISHED:
            return False
        
        self.bytes_received += packet.size
        self.packets_received += 1
        self.last_activity = time.time()
        
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de la conexión"""
        uptime = time.time() - self.created_at
        
        return {
            'id': self.id,
            'local_address': self.local_address,
            'remote_address': self.remote_address,
            'state': self.state.value,
            'uptime_seconds': uptime,
            'bytes_sent': self.bytes_sent,
            'bytes_received': self.bytes_received,
            'packets_sent': self.packets_sent,
            'packets_received': self.packets_received,
            'last_activity': time.ctime(self.last_activity)
        }

class NetworkService:
    """
    Servicio de Red del Sistema
    Maneja conexiones, transferencia de datos, etc.
    """
    
    def __init__(self):
        self.name = "NetworkService"
        self.version = "1.0"
        self.running = False
        self.failed = False  # Para simulación de fallos
        self.connections: Dict[str, NetworkConnection] = {}
        self.packet_queue: List[NetworkPacket] = []
        self.network_interfaces = {
            "lo": {"address": "127.0.0.1", "status": "up", "mtu": 65536},
            "eth0": {"address": "192.168.1.100", "status": "up", "mtu": 1500},
            "wlan0": {"address": "192.168.0.50", "status": "down", "mtu": 1500}
        }
        self.routing_table = []
        self.dns_cache = {
            "localhost": "127.0.0.1",
            "gateway": "192.168.1.1",
            "dns-server": "8.8.8.8"
        }
        self.network_stats = {
            'packets_sent': 0,
            'packets_received': 0,
            'bytes_sent': 0,
            'bytes_received': 0,
            'connections_created': 0,
            'connections_closed': 0
        }
        self.net_lock = threading.RLock()
        self.network_thread: Optional[threading.Thread] = None
        
        print("🌐 NET_SERVICE: Servicio de red inicializado")
    
    def start(self):
        """Inicia el servicio de red"""
        with self.net_lock:
            if self.running:
                return True
            
            self.running = True
            
            # Iniciar hilo de procesamiento de red
            self.network_thread = threading.Thread(target=self._network_loop)
            self.network_thread.daemon = True
            self.network_thread.start()
            
            print("🟢 NET_SERVICE: Servicio de red iniciado")
            return True
    
    def stop(self):
        """Detiene el servicio de red"""
        with self.net_lock:
            self.running = False
            
            # Cerrar todas las conexiones
            for conn_id in list(self.connections.keys()):
                self.close_connection(conn_id)
            
            print("🔴 NET_SERVICE: Servicio de red detenido")
    
    def _check_service_health(self) -> bool:
        """Verifica si el servicio está en estado funcional"""
        if self.failed:
            print("❌ NET_SERVICE: Servicio ha fallado - Operación rechazada")
            return False
        
        if not self.running:
            print("⚠️  NET_SERVICE: Servicio no está iniciado")
            return False
            
        return True
    
    def _network_loop(self):
        """Bucle principal de procesamiento de red"""
        while self.running:
            try:
                # Procesar paquetes en cola
                if self.packet_queue:
                    self._process_packet_queue()
                
                # Verificar conexiones inactivas
                self._check_inactive_connections()
                
                # Pequeña pausa
                time.sleep(0.1)
                
            except Exception as e:
                print(f"❌ NET_SERVICE ERROR: {e}")
    
    def _process_packet_queue(self):
        """Procesa los paquetes en la cola"""
        with self.net_lock:
            packets_to_process = self.packet_queue[:]
            self.packet_queue.clear()
            
            for packet in packets_to_process:
                self._route_packet(packet)
    
    def _route_packet(self, packet: NetworkPacket):
        """Enruta un paquete a su destino"""
        # Simular enrutamiento básico
        print(f"📡 NET: Enrutando {packet}")
        
        # Buscar conexión de destino
        for conn in self.connections.values():
            if conn.remote_address == packet.destination or conn.local_address == packet.destination:
                if conn.receive_data(packet):
                    self.network_stats['packets_received'] += 1
                    self.network_stats['bytes_received'] += packet.size
                break
        
        # Simular latencia de red
        time.sleep(random.uniform(0.001, 0.01))
    
    def _check_inactive_connections(self):
        """Verifica conexiones inactivas y las cierra si es necesario"""
        current_time = time.time()
        inactive_timeout = 300  # 5 minutos
        
        inactive_connections = []
        for conn_id, conn in self.connections.items():
            if current_time - conn.last_activity > inactive_timeout:
                inactive_connections.append(conn_id)
        
        for conn_id in inactive_connections:
            print(f"⏱️  NET: Cerrando conexión inactiva {conn_id}")
            self.close_connection(conn_id)
    
    # ==================== GESTIÓN DE CONEXIONES ====================
    
    def create_connection(self, local_address: str, remote_address: str, process_id: str = "system") -> Optional[str]:
        """Crea una nueva conexión de red"""
        with self.net_lock:
            conn_id = f"conn_{len(self.connections)}_{int(time.time())}"
            
            # Verificar que las direcciones sean válidas
            if not self._validate_address(local_address) or not self._validate_address(remote_address):
                print(f"❌ NET: Direcciones inválidas: {local_address} → {remote_address}")
                return None
            
            connection = NetworkConnection(conn_id, local_address, remote_address)
            connection.state = ConnectionState.CONNECTING
            
            # Simular proceso de conexión
            time.sleep(random.uniform(0.01, 0.1))
            
            # Simular fallo ocasional de conexión
            if random.random() < 0.05:  # 5% de fallo
                connection.state = ConnectionState.ERROR
                print(f"❌ NET: Error al conectar {local_address} → {remote_address}")
                return None
            
            connection.state = ConnectionState.ESTABLISHED
            self.connections[conn_id] = connection
            self.network_stats['connections_created'] += 1
            
            print(f"✅ NET: Conexión establecida {conn_id} ({local_address} → {remote_address})")
            return conn_id
    
    def close_connection(self, connection_id: str) -> bool:
        """Cierra una conexión"""
        with self.net_lock:
            if connection_id not in self.connections:
                return False
            
            connection = self.connections[connection_id]
            connection.state = ConnectionState.CLOSING
            
            # Simular tiempo de cierre
            time.sleep(0.01)
            
            connection.state = ConnectionState.CLOSED
            del self.connections[connection_id]
            self.network_stats['connections_closed'] += 1
            
            print(f"🔚 NET: Conexión cerrada {connection_id}")
            return True
    
    def send_data(self, connection_id: str, data: Any, process_id: str = "system") -> bool:
        """Envía datos a través de una conexión"""
        with self.net_lock:
            if connection_id not in self.connections:
                print(f"❌ NET: Conexión {connection_id} no encontrada")
                return False
            
            connection = self.connections[connection_id]
            
            if not connection.send_data(data):
                print(f"❌ NET: Error enviando datos por {connection_id}")
                return False
            
            # Crear y enqueue el paquete
            packet = NetworkPacket(
                connection.local_address,
                connection.remote_address,
                data,
                "data"
            )
            
            self.packet_queue.append(packet)
            self.network_stats['packets_sent'] += 1
            self.network_stats['bytes_sent'] += packet.size
            
            print(f"📤 NET: Datos enviados por {connection_id} ({packet.size}B)")
            return True
    
    def get_connection_info(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene información de una conexión"""
        with self.net_lock:
            if connection_id not in self.connections:
                return None
            
            return self.connections[connection_id].get_stats()
    
    def list_connections(self) -> List[Dict[str, Any]]:
        """Lista todas las conexiones activas"""
        with self.net_lock:
            return [conn.get_stats() for conn in self.connections.values()]
    
    # ==================== UTILIDADES DE RED ====================
    
    def ping(self, target_address: str, timeout: float = 1.0) -> Dict[str, Any]:
        """Simula un ping a una dirección"""
        print(f"🏓 NET: Ping a {target_address}")
        
        start_time = time.time()
        
        # Simular latencia de red
        latency = random.uniform(0.001, 0.1)
        time.sleep(latency)
        
        # Simular pérdida ocasional de paquetes
        if random.random() < 0.05:  # 5% packet loss
            return {
                'target': target_address,
                'success': False,
                'error': 'Request timed out',
                'time_ms': timeout * 1000
            }
        
        elapsed = time.time() - start_time
        
        return {
            'target': target_address,
            'success': True,
            'time_ms': elapsed * 1000,
            'ttl': 64
        }
    
    def resolve_dns(self, hostname: str) -> Optional[str]:
        """Resuelve un nombre de host a dirección IP"""
        if not self._check_service_health():
            return None
            
        print(f"🔍 NET: Resolviendo DNS para {hostname}")
        
        # Simular tiempo de resolución DNS
        time.sleep(random.uniform(0.01, 0.1))
        
        # Buscar en caché local
        if hostname in self.dns_cache:
            ip = self.dns_cache[hostname]
            print(f"✅ NET: {hostname} → {ip} (caché)")
            return ip
        
        # Simular resolución DNS externa
        if random.random() < 0.9:  # 90% éxito
            # Generar IP ficticia
            ip = f"192.168.{random.randint(1, 254)}.{random.randint(1, 254)}"
            self.dns_cache[hostname] = ip
            print(f"✅ NET: {hostname} → {ip} (resuelto)")
            return ip
        
        print(f"❌ NET: Error resolviendo {hostname}")
        return None
    
    def _validate_address(self, address: str) -> bool:
        """Valida una dirección IP básica"""
        try:
            parts = address.split('.')
            if len(parts) != 4:
                return False
            
            for part in parts:
                if not (0 <= int(part) <= 255):
                    return False
            
            return True
        except:
            return False
    
    # ==================== CONFIGURACIÓN DE RED ====================
    
    def configure_interface(self, interface: str, address: str, status: str = "up") -> bool:
        """Configura una interfaz de red"""
        with self.net_lock:
            if interface not in self.network_interfaces:
                print(f"❌ NET: Interfaz {interface} no encontrada")
                return False
            
            if not self._validate_address(address):
                print(f"❌ NET: Dirección IP inválida: {address}")
                return False
            
            old_config = self.network_interfaces[interface].copy()
            self.network_interfaces[interface]['address'] = address
            self.network_interfaces[interface]['status'] = status
            
            print(f"🔧 NET: Interfaz {interface} configurada: {old_config['address']} → {address}")
            return True
    
    def get_interface_info(self, interface: str = None) -> Dict[str, Any]:
        """Obtiene información de interfaces de red"""
        if interface:
            return self.network_interfaces.get(interface, {})
        return self.network_interfaces.copy()
    
    def add_route(self, destination: str, gateway: str, interface: str) -> bool:
        """Añade una ruta a la tabla de enrutamiento"""
        with self.net_lock:
            route = {
                'destination': destination,
                'gateway': gateway,
                'interface': interface,
                'metric': 1,
                'timestamp': time.time()
            }
            
            self.routing_table.append(route)
            print(f"🛣️  NET: Ruta añadida: {destination} via {gateway}")
            return True
    
    # ==================== INFORMACIÓN Y ESTADÍSTICAS ====================
    
    def get_network_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de red"""
        return {
            'service_running': self.running,
            'active_connections': len(self.connections),
            'packets_in_queue': len(self.packet_queue),
            'network_interfaces': len(self.network_interfaces),
            'dns_cache_entries': len(self.dns_cache),
            'routing_table_entries': len(self.routing_table),
            'statistics': self.network_stats.copy()
        }
    
    def print_network_status(self):
        """Imprime el estado de la red"""
        stats = self.get_network_stats()
        
        print("\n" + "-"*40)
        print("🌐 ESTADO DEL SERVICIO DE RED")
        print("-"*40)
        print(f"🟢 Estado: {'Activo' if stats['service_running'] else 'Inactivo'}")
        print(f"🔗 Conexiones activas: {stats['active_connections']}")
        print(f"📦 Paquetes en cola: {stats['packets_in_queue']}")
        print(f"🌐 Interfaces: {stats['network_interfaces']}")
        print(f"🔍 Caché DNS: {stats['dns_cache_entries']} entradas")
        print(f"🛣️  Rutas: {stats['routing_table_entries']}")
        print(f"📊 Estadísticas:")
        print(f"   • Paquetes enviados: {stats['statistics']['packets_sent']}")
        print(f"   • Paquetes recibidos: {stats['statistics']['packets_received']}")
        print(f"   • Bytes enviados: {stats['statistics']['bytes_sent']}")
        print(f"   • Bytes recibidos: {stats['statistics']['bytes_received']}")
        print(f"   • Conexiones creadas: {stats['statistics']['connections_created']}")
        print(f"   • Conexiones cerradas: {stats['statistics']['connections_closed']}")
        print("-"*40)
    
    def print_interfaces(self):
        """Imprime información de interfaces"""
        print("\n🌐 INTERFACES DE RED:")
        for name, config in self.network_interfaces.items():
            status_icon = "🟢" if config['status'] == 'up' else "🔴"
            print(f"  {status_icon} {name}: {config['address']} (MTU: {config['mtu']})")

# Instancia global del servicio de red
net_service = NetworkService()

def get_net_service():
    """Obtiene la instancia global del servicio de red"""
    return net_service