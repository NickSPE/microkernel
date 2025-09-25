"""
MAIN - Punto de Entrada del Sistema Microkernel
===============================================
Archivo principal que inicializa y coordina todos los
componentes del sistema operativo microkernel.
"""

import time
import sys
import os
import signal
import threading
from pathlib import Path

# Añadir el directorio raíz al path para importaciones
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Importar componentes del microkernel
from kernel.microkernel import Microkernel, get_kernel
from kernel.scheduler import Scheduler
from kernel.ipc import IPCManager, get_ipc_manager

# Importar servicios
from services.fs_service import FileSystemService, get_fs_service
from services.net_service import NetworkService, get_net_service  
from services.driver_service import DriverService, get_driver_service
from services.security_service import SecurityService, get_security_service

# Importar aplicaciones
from apps.calculator import Calculator, create_calculator
from apps.text_editor import TextEditor, create_text_editor
from apps.browser import Browser, create_browser

# Importar utilidades
from utils.logger import Logger, get_logger, configure_logger, LogLevel
from utils.config import ConfigManager, get_config, load_config

class MicrokernelSystem:
    """
    Sistema Principal del Microkernel
    Coordina el inicio, ejecución y cierre del sistema completo
    """
    
    def __init__(self):
        self.name = "MicrokernelOS"
        self.version = "1.0.0"
        self.running = False
        self.startup_time = None
        self.shutdown_requested = False
        
        # Componentes del sistema
        self.kernel = None
        self.logger = None
        self.config = None
        self.services = {}
        self.applications = {}
        
        # Hilos de demostración
        self.demo_threads = []
        
        print(f"🔧 {self.name} v{self.version} - Sistema inicializando...")
    
    def initialize(self):
        """Inicializa todos los componentes del sistema"""
        try:
            print("\n" + "="*60)
            print("🚀 INICIALIZANDO MICROKERNEL SYSTEM")
            print("="*60)
            
            # 1. Inicializar logger
            self._initialize_logger()
            
            # 2. Cargar configuración
            self._initialize_config()
            
            # 3. Inicializar kernel
            self._initialize_kernel()
            
            # 4. Inicializar servicios
            self._initialize_services()
            
            # 5. Configurar aplicaciones
            self._initialize_applications()
            
            # 6. Configurar manejadores de señales
            self._setup_signal_handlers()
            
            self.startup_time = time.time()
            self.running = True
            
            self.logger.info("SYSTEM", f"{self.name} v{self.version} iniciado correctamente")
            print(f"✅ {self.name} iniciado correctamente!")
            
            return True
            
        except Exception as e:
            print(f"❌ Error inicializando el sistema: {e}")
            self._emergency_shutdown()
            return False
    
    def _initialize_logger(self):
        """Inicializa el sistema de logging"""
        print("📝 Inicializando sistema de logging...")
        
        # Configurar logger
        configure_logger(
            min_level=LogLevel.INFO,
            max_entries=10000,
            log_file="logs/microkernel.log",
            console_output=True
        )
        
        self.logger = get_logger()
        self.logger.info("SYSTEM", "Sistema de logging inicializado")
        print("✅ Logger configurado")
    
    def _initialize_config(self):
        """Inicializa el sistema de configuración"""
        print("⚙️  Cargando configuración del sistema...")
        
        self.config = get_config()
        
        # Intentar cargar desde archivo, si no existe usar configuración por defecto
        config_file = "config/microkernel.json"
        if os.path.exists(config_file):
            if load_config(config_file):
                self.logger.info("SYSTEM", f"Configuración cargada desde {config_file}")
            else:
                self.logger.warning("SYSTEM", "Error cargando configuración, usando valores por defecto")
        else:
            self.logger.info("SYSTEM", "Usando configuración por defecto")
            # Guardar configuración por defecto
            os.makedirs("config", exist_ok=True)
            self.config.save_to_file(config_file)
        
        # Validar configuración
        validation = self.config.validate_config()
        if not validation['is_valid']:
            self.logger.error("SYSTEM", f"Configuración inválida: {validation['errors']}")
            raise ValueError("Configuración del sistema inválida")
        
        if validation['warnings']:
            for warning in validation['warnings']:
                self.logger.warning("SYSTEM", f"Configuración: {warning}")
        
        print("✅ Configuración cargada y validada")
    
    def _initialize_kernel(self):
        """Inicializa el microkernel"""
        print("🔥 Inicializando microkernel...")
        
        # Obtener configuración del kernel
        kernel_config = self.config.get_kernel_config()
        
        # Crear e inicializar kernel
        self.kernel = get_kernel()
        
        # Configurar límites del kernel según configuración
        self.kernel.max_processes = kernel_config.get('max_processes', 1000)
        self.kernel.memory_limit = kernel_config.get('memory_limit', 512 * 1024 * 1024)
        
        # Inicializar IPC
        ipc_manager = get_ipc_manager()
        ipc_config = self.config.get_ipc_config()
        # Configurar IPC según configuración...
        
        self.logger.info("KERNEL", "Microkernel inicializado")
        print("✅ Kernel inicializado")
    
    def _initialize_services(self):
        """Inicializa todos los servicios del sistema"""
        print("🔧 Inicializando servicios del sistema...")
        
        # 1. Servicio de sistema de archivos
        fs_service = get_fs_service()
        if fs_service.start():
            self.kernel.register_service("filesystem", fs_service)
            self.services["filesystem"] = fs_service
            self.logger.info("SERVICE", "Servicio de archivos iniciado")
            print("  ✅ FileSystem Service")
        else:
            self.logger.error("SERVICE", "Error iniciando servicio de archivos")
        
        # 2. Servicio de red
        net_service = get_net_service()
        if net_service.start():
            self.kernel.register_service("network", net_service)
            self.services["network"] = net_service
            self.logger.info("SERVICE", "Servicio de red iniciado")
            print("  ✅ Network Service")
        else:
            self.logger.error("SERVICE", "Error iniciando servicio de red")
        
        # 3. Servicio de controladores
        driver_service = get_driver_service()
        if driver_service.start():
            self.kernel.register_service("drivers", driver_service)
            self.services["drivers"] = driver_service
            self.logger.info("SERVICE", "Servicio de controladores iniciado")
            print("  ✅ Driver Service")
        else:
            self.logger.error("SERVICE", "Error iniciando servicio de controladores")
        
        # 4. Servicio de seguridad
        security_service = get_security_service()
        if security_service.start():
            self.kernel.register_service("security", security_service)
            self.services["security"] = security_service
            self.logger.info("SERVICE", "Servicio de seguridad iniciado")
            print("  ✅ Security Service")
        else:
            self.logger.error("SERVICE", "Error iniciando servicio de seguridad")
        
        # Crear usuarios por defecto
        self._setup_default_users()
        
        print("✅ Servicios inicializados")
    
    def _setup_default_users(self):
        """Configura usuarios por defecto del sistema"""
        security_service = self.services.get("security")
        if not security_service:
            return
        
        # Crear usuario administrador
        admin_created = security_service.create_user("admin", "admin123", ["admin_access", "file_write", "system_control"])
        if admin_created:
            self.logger.info("SECURITY", "Usuario administrador creado")
        
        # Crear usuario normal
        user_created = security_service.create_user("user", "user123", ["file_read", "file_write"])
        if user_created:
            self.logger.info("SECURITY", "Usuario normal creado")
        
        # Crear usuario guest
        guest_created = security_service.create_user("guest", "guest", ["file_read"])
        if guest_created:
            self.logger.info("SECURITY", "Usuario invitado creado")
    
    def _initialize_applications(self):
        """Inicializa las aplicaciones del sistema"""
        print("📱 Configurando aplicaciones...")
        
        # Las aplicaciones se inicializarán bajo demanda
        self.applications = {
            "calculator": create_calculator,
            "text_editor": create_text_editor,
            "browser": create_browser
        }
        
        self.logger.info("SYSTEM", "Aplicaciones configuradas")
        print("✅ Aplicaciones configuradas")
    
    def _setup_signal_handlers(self):
        """Configura manejadores para señales del sistema"""
        def signal_handler(signum, frame):
            self.logger.info("SYSTEM", f"Señal recibida: {signum}")
            self.request_shutdown()
        
        # Configurar señales (solo en sistemas Unix-like)
        if hasattr(signal, 'SIGINT'):
            signal.signal(signal.SIGINT, signal_handler)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, signal_handler)
    
    def run_system(self):
        """Ejecuta el sistema principal"""
        if not self.running:
            print("❌ Sistema no inicializado")
            return
        
        print("\n" + "="*60)
        print("🎯 SISTEMA MICROKERNEL EN EJECUCIÓN")
        print("="*60)
        
        try:
            # Iniciar demostración del sistema
            self._run_system_demo()
            
            # Bucle principal del sistema
            while self.running and not self.shutdown_requested:
                self._system_heartbeat()
                time.sleep(1)
        
        except KeyboardInterrupt:
            self.logger.info("SYSTEM", "Interrupción de teclado recibida")
            self.request_shutdown()
        
        except Exception as e:
            self.logger.error("SYSTEM", f"Error en el bucle principal: {e}")
            self.request_shutdown()
        
        finally:
            self.shutdown()
    
    def _system_heartbeat(self):
        """Latido del corazón del sistema - monitoreo básico"""
        # Verificar estado de servicios
        failed_services = []
        for name, service in self.services.items():
            if hasattr(service, 'running') and not service.running:
                failed_services.append(name)
        
        if failed_services:
            self.logger.warning("SYSTEM", f"Servicios caídos: {failed_services}")
        
        # Log periódico de estadísticas (cada 60 segundos)
        if int(time.time()) % 60 == 0:
            uptime = time.time() - self.startup_time if self.startup_time else 0
            memory_info = self.kernel.get_memory_info()
            
            self.logger.info("SYSTEM", 
                f"Heartbeat - Uptime: {uptime:.0f}s, "
                f"Memoria: {memory_info['percentage']:.1f}%, "
                f"Procesos: {len(self.kernel.list_processes())}"
            )
    
    def _run_system_demo(self):
        """Ejecuta demostraciones de las aplicaciones"""
        print("\n🎪 INICIANDO DEMOSTRACIONES...")
        
        # Crear sesión de administrador para las demos
        security_service = self.services.get("security")
        admin_session = None
        if security_service:
            admin_session = security_service.login("admin", "admin123")
        
        # Demostración de la calculadora
        print("\n1️⃣  DEMO: Calculadora")
        calc_thread = threading.Thread(
            target=self._run_calculator_demo,
            args=(admin_session,),
            daemon=True
        )
        calc_thread.start()
        self.demo_threads.append(calc_thread)
        time.sleep(3)
        
        # Demostración del editor de texto
        print("\n2️⃣  DEMO: Editor de Texto")
        editor_thread = threading.Thread(
            target=self._run_text_editor_demo,
            args=(admin_session,),
            daemon=True
        )
        editor_thread.start()
        self.demo_threads.append(editor_thread)
        time.sleep(5)
        
        # Demostración del navegador
        print("\n3️⃣  DEMO: Navegador Web")
        browser_thread = threading.Thread(
            target=self._run_browser_demo,
            args=(admin_session,),
            daemon=True
        )
        browser_thread.start()
        self.demo_threads.append(browser_thread)
        time.sleep(5)
        
        print("\n✅ Todas las demostraciones iniciadas")
        print("💡 El sistema continuará ejecutándose...")
        print("💡 Presiona Ctrl+C para detener el sistema")
    
    def _run_calculator_demo(self, session_token):
        """Ejecuta demo de la calculadora"""
        try:
            calculator = create_calculator()
            if calculator.start(session_token):
                # La calculadora ejecutará su propia demo internamente
                while calculator.running:
                    time.sleep(1)
        except Exception as e:
            self.logger.error("DEMO", f"Error en demo calculadora: {e}")
    
    def _run_text_editor_demo(self, session_token):
        """Ejecuta demo del editor de texto"""
        try:
            text_editor = create_text_editor()
            if text_editor.start(session_token):
                # El editor ejecutará su propia demo internamente
                while text_editor.running:
                    time.sleep(1)
        except Exception as e:
            self.logger.error("DEMO", f"Error en demo editor: {e}")
    
    def _run_browser_demo(self, session_token):
        """Ejecuta demo del navegador"""
        try:
            browser = create_browser()
            if browser.start(session_token):
                # El navegador ejecutará su propia demo internamente
                while browser.running:
                    time.sleep(1)
        except Exception as e:
            self.logger.error("DEMO", f"Error en demo navegador: {e}")
    
    def get_system_status(self) -> dict:
        """Obtiene el estado completo del sistema"""
        uptime = time.time() - self.startup_time if self.startup_time else 0
        
        # Estado de servicios
        service_status = {}
        for name, service in self.services.items():
            service_status[name] = {
                'running': getattr(service, 'running', False),
                'version': getattr(service, 'version', 'N/A')
            }
        
        # Estado del kernel
        kernel_status = {
            'processes': len(self.kernel.list_processes()),
            'memory': self.kernel.get_memory_info(),
            'services_registered': len(self.kernel.list_services())
        }
        
        return {
            'system_name': self.name,
            'version': self.version,
            'running': self.running,
            'uptime_seconds': uptime,
            'uptime_formatted': f"{int(uptime // 3600):02d}:{int((uptime % 3600) // 60):02d}:{int(uptime % 60):02d}",
            'services': service_status,
            'kernel': kernel_status,
            'logger_stats': self.logger.get_stats() if self.logger else {},
            'config_stats': self.config.get_stats() if self.config else {}
        }
    
    def request_shutdown(self):
        """Solicita el cierre del sistema"""
        self.logger.info("SYSTEM", "Solicitud de cierre recibida")
        self.shutdown_requested = True
    
    def shutdown(self):
        """Cierra el sistema de forma ordenada"""
        print("\n" + "="*60)
        print("🛑 CERRANDO SISTEMA MICROKERNEL")
        print("="*60)
        
        self.running = False
        
        # Esperar a que terminen las demos
        print("⏸️  Esperando demos...")
        for thread in self.demo_threads:
            if thread.is_alive():
                thread.join(timeout=2)
        
        # Cerrar servicios
        print("🔧 Cerrando servicios...")
        for name, service in self.services.items():
            if hasattr(service, 'stop'):
                try:
                    service.stop()
                    self.logger.info("SERVICE", f"Servicio {name} detenido")
                    print(f"  ✅ {name}")
                except Exception as e:
                    self.logger.error("SERVICE", f"Error cerrando {name}: {e}")
        
        # Cerrar kernel
        print("🔥 Cerrando kernel...")
        if self.kernel:
            try:
                # Terminar todos los procesos
                for pid in self.kernel.list_processes():
                    self.kernel.terminate_process(pid)
                self.logger.info("KERNEL", "Kernel detenido")
                print("  ✅ Kernel")
            except Exception as e:
                self.logger.error("KERNEL", f"Error cerrando kernel: {e}")
        
        # Cerrar logger
        if self.logger:
            self.logger.info("SYSTEM", f"{self.name} cerrándose...")
            uptime = time.time() - self.startup_time if self.startup_time else 0
            self.logger.info("SYSTEM", f"Tiempo de actividad: {uptime:.1f} segundos")
            self.logger.shutdown()
            print("✅ Logger cerrado")
        
        # Guardar configuración final
        if self.config:
            self.config.save_to_file("config/microkernel.json")
            print("✅ Configuración guardada")
        
        print("\n👋 Sistema cerrado correctamente")
        print(f"Gracias por usar {self.name} v{self.version}!")
    
    def _emergency_shutdown(self):
        """Cierre de emergencia en caso de error crítico"""
        print("\n💥 CIERRE DE EMERGENCIA")
        self.running = False
        
        if self.logger:
            self.logger.critical("SYSTEM", "Cierre de emergencia activado")
            self.logger.shutdown()

def main():
    """Función principal del sistema"""
    # Banner de inicio
    print("\n" + "="*60)
    print("🏛️  SISTEMA OPERATIVO MICROKERNEL")
    print("   Demostración de Arquitectura Microkernel")
    print("   Universidad - VI Ciclo")
    print("="*60)
    print("📚 Propósito Educativo:")
    print("   • Demostrar principios de arquitectura microkernel")
    print("   • Mostrar separación de servicios del núcleo")
    print("   • Ilustrar comunicación entre procesos (IPC)")
    print("   • Ejemplo de aplicaciones en espacio de usuario")
    print("="*60)
    
    # Crear e inicializar sistema
    system = MicrokernelSystem()
    
    try:
        # Inicializar sistema
        if system.initialize():
            # Ejecutar sistema
            system.run_system()
        else:
            print("❌ Error inicializando el sistema")
            return 1
    
    except Exception as e:
        print(f"💥 Error crítico: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)