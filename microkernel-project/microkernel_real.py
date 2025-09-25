"""
MICROKERNEL COMPLETO CON ARCHIVOS REALES
========================================
Sistema completo que crea archivos REALES en disco duro
+ todos los comandos de simulación de fallos
"""

import sys
import os
import time
import threading

# Agregar el directorio actual al path
sys.path.insert(0, os.path.abspath('.'))

# Importar todo
from kernel.microkernel import Microkernel
from services.real_fs_service import RealFileSystemService  # ← NUEVO servicio REAL
from services.net_service import NetworkService
from services.driver_service import DriverService
from services.security_service import SecurityService

class MicrokernelReal:
    def __init__(self):
        """Inicializar el microkernel con archivos REALES"""
        print("🚀 INICIANDO MICROKERNEL CON ARCHIVOS REALES...")
        print("="*50)
        
        # Crear kernel y servicios
        self.kernel = Microkernel()
        
        # Usar el servicio de archivos REAL
        self.fs_service = RealFileSystemService("./microkernel_files")  # ← ARCHIVOS REALES
        self.net_service = NetworkService()
        self.driver_service = DriverService()
        self.security_service = SecurityService()
        
        # Registrar en el kernel
        self.kernel.register_service("fs", self.fs_service)
        self.kernel.register_service("net", self.net_service)
        self.kernel.register_service("driver", self.driver_service)
        self.kernel.register_service("security", self.security_service)
        
        # Iniciar el kernel
        self.kernel.start()
        
        # Iniciar cada servicio manualmente
        self.fs_service.start()
        self.net_service.start()
        self.driver_service.start()
        self.security_service.start()
        time.sleep(1)  # Dar tiempo a los hilos
        
        print("✅ MICROKERNEL CON ARCHIVOS REALES INICIADO")
        print("="*50)

    def _print_help(self):
        """Mostrar ayuda completa"""
        print("\n" + "="*60)
        print("🎮 COMANDOS DISPONIBLES - ARCHIVOS REALES")
        print("="*60)
        print("📊 ESTADO:")
        print("  status                    - Estado de todos los servicios")
        print("  status <servicio>         - Estado de un servicio específico")
        print("")
        print("💥 SIMULACIÓN DE FALLOS:")
        print("  fail <servicio>          - Hacer fallar un servicio")
        print("  recover <servicio>       - Recuperar un servicio")
        print("")
        print("🧪 VERIFICACIÓN:")
        print("  test                     - Probar todos los servicios")
        print("  test <servicio>          - Probar un servicio específico")
        print("")
        print("🎯 USO DIRECTO (CREA ARCHIVOS REALES):")
        print("  use fs create <archivo> <contenido>    - Crear archivo EN DISCO")
        print("  use fs read <archivo>                  - Leer archivo")
        print("  use fs write <archivo> <contenido>     - Escribir archivo")
        print("  use fs delete <archivo>                - Eliminar archivo")
        print("  use fs list                            - Listar archivos")
        print("  use fs info <archivo>                  - Info detallada del archivo")
        print("  use net resolve <dominio>              - Resolver DNS")
        print("  use net interfaces                     - Ver interfaces")
        print("  use driver list                        - Listar dispositivos")
        print("  use driver read <device> <bytes>       - Leer dispositivo")
        print("  use security login <user> <pass>       - Login")
        print("  use security users                     - Ver usuarios")
        print("")
        print("📍 INSPECCIÓN INTERNA:")
        print("  inspect fs                - Ver archivos en memoria Y disco")
        print("  inspect net               - Ver caché DNS y config")
        print("  inspect driver            - Ver dispositivos en memoria")
        print("  inspect security          - Ver usuarios y sesiones")
        print("")
        print("🗂️ COMANDOS ESPECIALES:")
        print("  real ls                   - Listar archivos reales en disco")
        print("  real path                 - Ver ruta real de archivos")
        print("  real stats                - Estadísticas del sistema real")
        print("")
        print("❓ OTROS:")
        print("  help                     - Esta ayuda")
        print("  demo                     - Demostración automática")
        print("  exit                     - Salir")
        print("="*60)

    def _handle_status(self, args):
        """Manejar comando status"""
        if not args:
            # Estado de todos
            print("\n📊 ESTADO DE TODOS LOS SERVICIOS:")
            print("-" * 40)
            services = ["fs", "net", "driver", "security"]
            for service_name in services:
                service = getattr(self, f"{service_name}_service")
                status = "🔴 FALLADO" if service.failed else "🟢 FUNCIONANDO"
                health = "❌ NO SALUDABLE" if service.failed else "✅ SALUDABLE"
                if service_name == "fs":
                    print(f"  {service_name:12} → {status} ({health}) [ARCHIVOS REALES]")
                else:
                    print(f"  {service_name:12} → {status} ({health})")
        else:
            # Estado específico
            service_name = args[0]
            if hasattr(self, f"{service_name}_service"):
                service = getattr(self, f"{service_name}_service")
                print(f"\n📋 ESTADO DETALLADO DE {service_name.upper()}:")
                print("-" * 30)
                print(f"Estado: {'🔴 FALLADO' if service.failed else '🟢 FUNCIONANDO'}")
                print(f"Salud: {'❌ NO SALUDABLE' if service.failed else '✅ SALUDABLE'}")
                
                # Información específica del servicio
                if service_name == "fs":
                    stats = service.get_stats()
                    print(f"Tipo: SISTEMA DE ARCHIVOS REAL")
                    print(f"Archivos virtuales: {stats['total_files']}")
                    print(f"Archivos reales: {stats['real_files']}")
                    print(f"Ruta base: {stats['real_base_path']}")
                elif service_name == "net":
                    dns_entries = len(service.dns_cache)
                    interfaces_up = sum(1 for iface in service.network_interfaces.values() if iface['status'] == 'up')
                    print(f"DNS Cache: {dns_entries} entradas")
                    print(f"Interfaces activas: {interfaces_up}")
                elif service_name == "driver":
                    devices_online = len([d for d in service.devices.values() if d.state.value == 'online'])
                    total_devices = len(service.devices)
                    print(f"Dispositivos: {devices_online}/{total_devices} online")
                elif service_name == "security":
                    active_sessions = len(service.active_sessions)
                    total_users = len(service.users)
                    print(f"Sesiones activas: {active_sessions}")
                    print(f"Usuarios totales: {total_users}")
            else:
                print(f"❌ Servicio '{service_name}' no encontrado")

    def _handle_fail(self, args):
        """Manejar comando fail"""
        if not args:
            print("❌ Uso: fail <servicio>")
            print("   Servicios: fs, net, driver, security")
            return
        
        service_name = args[0]
        if hasattr(self, f"{service_name}_service"):
            service = getattr(self, f"{service_name}_service")
            service.failed = True
            print(f"💥 {service_name.upper()}: Servicio marcado como FALLADO")
            if service_name == "fs":
                print(f"🔴 Los archivos REALES ya creados seguirán en disco")
                print(f"🔴 Pero NO se podrán crear/leer/escribir nuevos archivos")
            else:
                print(f"🔴 Todas las operaciones de {service_name} ahora fallarán")
        else:
            print(f"❌ Servicio '{service_name}' no encontrado")

    def _handle_recover(self, args):
        """Manejar comando recover"""
        if not args:
            print("❌ Uso: recover <servicio>")
            return
        
        service_name = args[0]
        if hasattr(self, f"{service_name}_service"):
            service = getattr(self, f"{service_name}_service")
            service.failed = False
            print(f"🔄 {service_name.upper()}: Servicio RECUPERADO")
            if service_name == "fs":
                print(f"🟢 Ahora se pueden crear/leer archivos REALES nuevamente")
            else:
                print(f"🟢 Todas las operaciones de {service_name} ahora funcionarán")
        else:
            print(f"❌ Servicio '{service_name}' no encontrado")

    def _handle_test(self, args):
        """Manejar comando test"""
        if not args:
            # Probar todos
            print("\n🧪 PROBANDO TODOS LOS SERVICIOS:")
            print("=" * 40)
            services = ["fs", "net", "driver", "security"]
            for service_name in services:
                self._test_service(service_name)
                print()
        else:
            # Probar específico
            service_name = args[0]
            if hasattr(self, f"{service_name}_service"):
                print(f"\n🧪 PROBANDO {service_name.upper()}:")
                print("-" * 30)
                self._test_service(service_name)
            else:
                print(f"❌ Servicio '{service_name}' no encontrado")

    def _test_service(self, service_name):
        """Probar un servicio específico"""
        try:
            if service_name == "fs":
                # Probar crear, leer archivo REAL
                test_file = f"test_file_{int(time.time())}.txt"
                success = self.fs_service.create_file(test_file, "contenido de prueba REAL", "admin")
                print(f"📁 Crear archivo REAL: {'✅ OK' if success else '❌ FALLO'}")
                
                if success:
                    content = self.fs_service.read_file(test_file, "admin")
                    print(f"📖 Leer archivo REAL: {'✅ OK' if content else '❌ FALLO'}")
                    
                    # Mostrar ruta real
                    info = self.fs_service.get_file_info(test_file)
                    if info:
                        print(f"🗂️ Archivo real en: {info['real_path']}")
                        print(f"💾 Existe en disco: {'✅ SÍ' if info['exists_on_disk'] else '❌ NO'}")
                
            elif service_name == "net":
                # Probar DNS
                ip = self.net_service.resolve_dns("test-domain.com")
                print(f"🌐 Resolver DNS: {'✅ OK' if ip else '❌ FALLO'}")
                
            elif service_name == "driver":
                # Probar leer dispositivo
                data = self.driver_service.device_read("hdd0", 128, "admin")
                print(f"💾 Leer dispositivo: {'✅ OK' if data else '❌ FALLO'}")
                
            elif service_name == "security":
                # Probar login
                token = self.security_service.login("admin", "admin123")
                print(f"🔒 Login: {'✅ OK' if token else '❌ FALLO'}")
                if token:
                    valid = self.security_service.validate_session(token)
                    print(f"✅ Validar sesión: {'✅ OK' if valid else '❌ FALLO'}")
                    self.security_service.logout(token)
                
        except Exception as e:
            print(f"💥 Error en test: {e}")

    def _handle_use(self, args):
        """Manejar comandos de uso directo"""
        if len(args) < 2:
            print("❌ Uso: use <servicio> <acción> [parámetros...]")
            print("   Ejemplo: use fs create mi_archivo.txt 'contenido'")
            return
        
        service_name = args[0]
        action = args[1]
        
        try:
            if service_name == "fs":
                self._use_filesystem(action, args[2:])
            elif service_name == "net":
                self._use_network(action, args[2:])
            elif service_name == "driver":
                self._use_driver(action, args[2:])
            elif service_name == "security":
                self._use_security(action, args[2:])
            else:
                print(f"❌ Servicio '{service_name}' no soportado para 'use'")
        except Exception as e:
            print(f"💥 Error: {e}")

    def _use_filesystem(self, action, args):
        """Usar sistema de archivos REAL directamente"""
        if action == "create":
            if len(args) < 2:
                print("❌ Uso: use fs create <archivo> <contenido>")
                return
            filename = args[0]
            content = " ".join(args[1:])  # Unir todo el contenido
            success = self.fs_service.create_file(filename, content, "admin")
            if success:
                print(f"✅ Archivo '{filename}' creado exitosamente")
                info = self.fs_service.get_file_info(filename)
                if info:
                    print(f"🗂️ Virtual: fs_service.root_dir.files['{filename}']")
                    print(f"💾 REAL: {info['real_path']}")
                    print(f"📁 En disco: {'✅ SÍ' if info['exists_on_disk'] else '❌ NO'}")
            else:
                print(f"❌ Error al crear archivo '{filename}'")
                
        elif action == "read":
            if not args:
                print("❌ Uso: use fs read <archivo>")
                return
            filename = args[0]
            content = self.fs_service.read_file(filename, "admin")
            if content:
                print(f"📄 Contenido de '{filename}' (sincronizado desde disco):")
                print(f"📝 {content}")
                info = self.fs_service.get_file_info(filename)
                if info:
                    print(f"💾 Archivo real: {info['real_path']}")
            else:
                print(f"❌ No se pudo leer '{filename}' (no existe o servicio fallado)")
        
        elif action == "write":
            if len(args) < 2:
                print("❌ Uso: use fs write <archivo> <contenido>")
                return
            filename = args[0]
            content = " ".join(args[1:])
            success = self.fs_service.write_file(filename, content, "admin")
            if success:
                print(f"✅ Contenido escrito a '{filename}' (virtual + disco)")
            else:
                print(f"❌ Error escribiendo a '{filename}'")
        
        elif action == "delete":
            if not args:
                print("❌ Uso: use fs delete <archivo>")
                return
            filename = args[0]
            success = self.fs_service.delete_file(filename, "admin")
            if success:
                print(f"✅ Archivo '{filename}' eliminado (virtual + disco)")
            else:
                print(f"❌ Error eliminando '{filename}'")
                
        elif action == "list":
            files = self.fs_service.list_directory("/")
            print("📂 Archivos disponibles:")
            for file_info in files:
                print(f"   📄 {file_info}")
        
        elif action == "info":
            if not args:
                print("❌ Uso: use fs info <archivo>")
                return
            filename = args[0]
            info = self.fs_service.get_file_info(filename)
            if info:
                print(f"ℹ️ Información de '{filename}':")
                print(f"   📏 Tamaño: {info['size']} bytes")
                print(f"   👤 Owner: {info['owner']}")
                print(f"   📅 Creado: {info['created_at']}")
                print(f"   📝 Modificado: {info['modified_at']}")
                print(f"   💾 Ruta real: {info['real_path']}")
                print(f"   📁 En disco: {'✅ SÍ' if info['exists_on_disk'] else '❌ NO'}")
            else:
                print(f"❌ No se encontró información de '{filename}'")
        else:
            print(f"❌ Acción '{action}' no soportada para fs")

    def _use_network(self, action, args):
        """Usar servicio de red directamente"""
        if action == "resolve":
            if not args:
                print("❌ Uso: use net resolve <dominio>")
                return
            domain = args[0]
            ip = self.net_service.resolve_dns(domain)
            if ip:
                print(f"📍 {domain} → {ip}")
                print(f"🗄️ Guardado en: net_service.dns_cache['{domain}']")
            else:
                print(f"❌ No se pudo resolver '{domain}'")
                
        elif action == "interfaces":
            print("🔌 Interfaces de red:")
            for name, info in self.net_service.network_interfaces.items():
                status = "🟢" if info['status'] == 'up' else "🔴"
                print(f"   {status} {name}: {info['address']} (MTU: {info['mtu']})")
        else:
            print(f"❌ Acción '{action}' no soportada para net")

    def _use_driver(self, action, args):
        """Usar controladores directamente"""
        if action == "list":
            print("🔧 Dispositivos disponibles:")
            devices = self.driver_service.list_devices()
            for device in devices:
                status = "🟢" if device.state.value == 'online' else "🔴"
                print(f"   {status} {device.device_id}: {device.name} ({device.device_type.value})")
                
        elif action == "read":
            if len(args) < 2:
                print("❌ Uso: use driver read <device_id> <bytes>")
                return
            device_id = args[0]
            try:
                bytes_to_read = int(args[1])
                data = self.driver_service.device_read(device_id, bytes_to_read, "admin")
                if data:
                    print(f"📖 Leídos {len(data)} bytes de {device_id}")
                    print(f"🔢 Primeros 20 bytes: {data[:20]}")
                else:
                    print(f"❌ No se pudo leer de '{device_id}'")
            except ValueError:
                print("❌ El número de bytes debe ser un entero")
        else:
            print(f"❌ Acción '{action}' no soportada para driver")

    def _use_security(self, action, args):
        """Usar seguridad directamente"""
        if action == "login":
            if len(args) < 2:
                print("❌ Uso: use security login <usuario> <password>")
                return
            username = args[0]
            password = args[1]
            token = self.security_service.login(username, password)
            if token:
                print(f"✅ Login exitoso para '{username}'")
                print(f"🔑 Token: {token[:20]}...")
                print(f"🗂️ Guardado en: security_service.active_sessions")
            else:
                print(f"❌ Login fallido para '{username}'")
                
        elif action == "users":
            print("👥 Usuarios del sistema:")
            for username, user in self.security_service.users.items():
                status = "🔒" if user.is_locked else "🔓"
                last = "Nunca" if not user.last_login else "Recientemente"
                print(f"   {status} {username} - Último login: {last}")
        else:
            print(f"❌ Acción '{action}' no soportada para security")

    def _handle_inspect(self, args):
        """Inspeccionar dónde se guardan los datos internamente"""
        if not args:
            print("❌ Uso: inspect <servicio>")
            print("   Servicios: fs, net, driver, security")
            return
            
        service_name = args[0]
        
        if service_name == "fs":
            print("🔍 INSPECCIÓN INTERNA - SISTEMA DE ARCHIVOS REAL:")
            print("-" * 50)
            stats = self.fs_service.get_stats()
            print(f"📍 Ubicación virtual: fs_service.root_dir.files")
            print(f"📍 Ubicación REAL: {stats['real_base_path']}")
            print(f"📊 Total archivos virtuales: {stats['total_files']}")
            print(f"📊 Total archivos reales: {stats['real_files']}")
            print("📄 Archivos híbridos:")
            for filename, file_obj in self.fs_service.root_dir.files.items():
                exists_real = os.path.exists(file_obj.real_path) if file_obj.real_path else False
                print(f"   • {filename}:")
                print(f"     └─ Virtual: VirtualFile ({file_obj.size} bytes)")
                print(f"     └─ Real: {file_obj.real_path}")
                print(f"     └─ En disco: {'✅ SÍ' if exists_real else '❌ NO'}")
                print(f"     └─ Content preview: '{file_obj.content[:30]}{'...' if len(file_obj.content) > 30 else ''}'")
        
        elif service_name == "net":
            print("🔍 INSPECCIÓN INTERNA - SERVICIO DE RED:")
            print("-" * 40)
            print(f"📍 DNS Cache: net_service.dns_cache")
            print(f"📊 Entradas DNS: {len(self.net_service.dns_cache)}")
            for domain, ip in self.net_service.dns_cache.items():
                print(f"   🌐 {domain} → {ip}")
                
        elif service_name == "driver":
            print("🔍 INSPECCIÓN INTERNA - CONTROLADORES:")
            print("-" * 38)
            print(f"📍 Ubicación: driver_service.devices")
            print(f"📊 Total dispositivos: {len(self.driver_service.devices)}")
            for device_id, device in self.driver_service.devices.items():
                print(f"   💾 {device_id}:")
                print(f"     └─ Objeto: VirtualDevice")
                print(f"     └─ Nombre: {device.name}")
                print(f"     └─ Estado: {device.state.value}")
                print(f"     └─ Operaciones: {device.operations_count}")
                
        elif service_name == "security":
            print("🔍 INSPECCIÓN INTERNA - SEGURIDAD:")
            print("-" * 35)
            print(f"📍 Usuarios: security_service.users")
            print(f"📊 Total usuarios: {len(self.security_service.users)}")
            for username, user in self.security_service.users.items():
                print(f"   👤 {username}:")
                print(f"     └─ Locked: {user.is_locked}")
            print(f"📍 Sesiones: security_service.active_sessions")
            print(f"📊 Sesiones activas: {len(self.security_service.active_sessions)}")
        else:
            print(f"❌ Servicio '{service_name}' no encontrado")

    def _handle_real(self, args):
        """Manejar comandos especiales para archivos reales"""
        if not args:
            print("❌ Uso: real <comando>")
            print("   Comandos: ls, path, stats")
            return
        
        command = args[0]
        
        if command == "ls":
            print("📁 ARCHIVOS REALES EN DISCO:")
            print("-" * 30)
            base_path = self.fs_service.real_base_path
            try:
                if os.path.exists(base_path):
                    for root, dirs, files in os.walk(base_path):
                        level = root.replace(base_path, '').count(os.sep)
                        indent = ' ' * 2 * level
                        print(f"{indent}📁 {os.path.basename(root)}/")
                        subindent = ' ' * 2 * (level + 1)
                        for file in files:
                            file_path = os.path.join(root, file)
                            size = os.path.getsize(file_path)
                            print(f"{subindent}📄 {file} ({size} bytes)")
                else:
                    print(f"❌ Directorio base no existe: {base_path}")
            except Exception as e:
                print(f"❌ Error listando archivos reales: {e}")
        
        elif command == "path":
            print(f"🗂️ RUTA BASE REAL: {self.fs_service.real_base_path}")
            print(f"📍 Ruta absoluta: {os.path.abspath(self.fs_service.real_base_path)}")
            
        elif command == "stats":
            stats = self.fs_service.get_stats()
            print("📊 ESTADÍSTICAS DEL SISTEMA REAL:")
            print("-" * 35)
            for key, value in stats.items():
                print(f"   {key}: {value}")
        else:
            print(f"❌ Comando real '{command}' no reconocido")

    def _handle_demo(self):
        """Demostración automática completa con archivos REALES"""
        print("\n🎭 DEMOSTRACIÓN AUTOMÁTICA - ARCHIVOS REALES")
        print("=" * 55)
        
        print("\n1️⃣ Creando archivo REAL de prueba...")
        success = self.fs_service.create_file("demo_real.txt", "Este archivo existe en DISCO DURO", "admin")
        if success:
            info = self.fs_service.get_file_info("demo_real.txt")
            print("✅ Archivo creado")
            print(f"💾 Ruta real: {info['real_path']}")
        
        print("\n2️⃣ Escribiendo contenido adicional...")
        self.fs_service.write_file("demo_real.txt", "\nLínea añadida desde el microkernel", "admin", append=True)
        
        print("\n3️⃣ Leyendo archivo (sincronizando desde disco)...")
        content = self.fs_service.read_file("demo_real.txt", "admin")
        if content:
            print(f"📄 Contenido leído:\n{content}")
        
        print("\n4️⃣ Resolviendo DNS...")
        ip = self.net_service.resolve_dns("demo.microkernel.local")
        print(f"🌐 demo.microkernel.local → {ip}")
        
        print("\n5️⃣ Simulando fallo del sistema de archivos...")
        self.fs_service.failed = True
        success = self.fs_service.create_file("fallo.txt", "No debería funcionar", "admin")
        print(f"💥 Crear archivo con servicio fallado: {'❌ FALLÓ' if not success else '✅ FUNCIONÓ'}")
        print("📁 NOTA: Los archivos ya creados siguen en disco")
        
        print("\n6️⃣ Verificando que archivos reales persisten...")
        print("🔍 Listando archivos reales en disco:")
        try:
            for file in os.listdir(self.fs_service.real_base_path):
                if file.endswith('.txt'):
                    print(f"   💾 {file} (existe realmente)")
        except:
            print("   ❌ Error listando archivos")
        
        print("\n7️⃣ Recuperando servicio...")
        self.fs_service.failed = False
        success = self.fs_service.create_file("recuperado.txt", "Ahora funciona y se guarda en disco", "admin")
        if success:
            print("🔄 Servicio recuperado - Nuevo archivo creado")
        
        print("\n✅ DEMOSTRACIÓN COMPLETADA")
        print("💡 ¡Los archivos creados están realmente en tu disco!")
        print(f"📁 Ubicación: {self.fs_service.real_base_path}")

    def run(self):
        """Ejecutar el microkernel interactivo"""
        print("\n🎮 MICROKERNEL INTERACTIVO - ARCHIVOS REALES")
        print("Escribe 'help' para ver todos los comandos disponibles")
        print("Escribe 'exit' para salir")
        print("🗂️ Los archivos se guardan en:", self.fs_service.real_base_path)
        
        while True:
            try:
                command_input = input("\n🎮 real-microkernel> ").strip()
                
                if not command_input:
                    continue
                    
                parts = command_input.split()
                command = parts[0].lower()
                args = parts[1:]
                
                if command == "help":
                    self._print_help()
                elif command == "status":
                    self._handle_status(args)
                elif command == "fail":
                    self._handle_fail(args)
                elif command == "recover":
                    self._handle_recover(args)
                elif command == "test":
                    self._handle_test(args)
                elif command == "use":
                    self._handle_use(args)
                elif command == "inspect":
                    self._handle_inspect(args)
                elif command == "real":
                    self._handle_real(args)
                elif command == "demo":
                    self._handle_demo()
                elif command == "exit":
                    print("👋 ¡Hasta luego!")
                    print(f"💾 Tus archivos quedan guardados en: {self.fs_service.real_base_path}")
                    break
                else:
                    print(f"❌ Comando '{command}' no reconocido. Escribe 'help' para ver los comandos disponibles.")
                    
            except KeyboardInterrupt:
                print("\n👋 ¡Hasta luego!")
                print(f"💾 Tus archivos quedan guardados en: {self.fs_service.real_base_path}")
                break
            except Exception as e:
                print(f"💥 Error: {e}")

def main():
    """Función principal"""
    try:
        microkernel = MicrokernelReal()
        microkernel.run()
    except KeyboardInterrupt:
        print("\n👋 Programa interrumpido")
    except Exception as e:
        print(f"💥 Error fatal: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()