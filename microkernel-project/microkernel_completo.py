"""
MICROKERNEL COMPLETO - TODO EN UNO
==================================
Sistema completo con:
- Simulación de fallos (fail/recover)
- Interacción directa con servicios (use)
- Verificación de funcionamiento (test)
- Estado de servicios (status)
- Comandos de ayuda (help)
"""

import sys
import os
import time
import threading

# Agregar el directorio actual al path
sys.path.insert(0, os.path.abspath('.'))

# Importar todo
from kernel.microkernel import Microkernel
from services.fs_service import FileSystemService
from services.net_service import NetworkService
from services.driver_service import DriverService
from services.security_service import SecurityService

class MicrokernelCompleto:
    def __init__(self):
        """Inicializar el microkernel completo"""
        print("🚀 INICIANDO MICROKERNEL COMPLETO...")
        print("="*50)
        
        # Crear kernel y servicios
        self.kernel = Microkernel()
        
        # Registrar servicios
        self.fs_service = FileSystemService()
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
        
        print("✅ MICROKERNEL COMPLETO INICIADO")
        print("="*50)

    def _print_help(self):
        """Mostrar ayuda completa"""
        print("\n" + "="*60)
        print("🎮 COMANDOS DISPONIBLES")
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
        print("🎯 USO DIRECTO:")
        print("  use fs create <archivo> <contenido>    - Crear archivo")
        print("  use fs read <archivo>                  - Leer archivo")
        print("  use fs list                            - Listar archivos")
        print("  use net resolve <dominio>              - Resolver DNS")
        print("  use net interfaces                     - Ver interfaces")
        print("  use driver list                        - Listar dispositivos")
        print("  use driver read <device> <bytes>       - Leer dispositivo")
        print("  use security login <user> <pass>       - Login")
        print("  use security users                     - Ver usuarios")
        print("")
        print("📍 INSPECCIÓN INTERNA:")
        print("  inspect fs                - Ver dónde se guardan archivos")
        print("  inspect net               - Ver caché DNS y config")
        print("  inspect driver            - Ver dispositivos en memoria")
        print("  inspect security          - Ver usuarios y sesiones")
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
                    files_count = len(service.root_dir.files)
                    print(f"Archivos: {files_count}")
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
                # Probar crear, leer archivo
                success = self.fs_service.create_file("test_file.txt", "contenido de prueba", "admin")
                print(f"📁 Crear archivo: {'✅ OK' if success else '❌ FALLO'}")
                
                if success:
                    content = self.fs_service.read_file("test_file.txt", "admin")
                    print(f"📖 Leer archivo: {'✅ OK' if content else '❌ FALLO'}")
                
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
        """Usar sistema de archivos directamente"""
        if action == "create":
            if len(args) < 2:
                print("❌ Uso: use fs create <archivo> <contenido>")
                return
            filename = args[0]
            content = " ".join(args[1:])  # Unir todo el contenido
            success = self.fs_service.create_file(filename, content, "admin")
            if success:
                print(f"✅ Archivo '{filename}' creado exitosamente")
                print(f"🗂️ Guardado en: fs_service.root_dir.files['{filename}']")
            else:
                print(f"❌ Error al crear archivo '{filename}'")
                
        elif action == "read":
            if not args:
                print("❌ Uso: use fs read <archivo>")
                return
            filename = args[0]
            content = self.fs_service.read_file(filename, "admin")
            if content:
                print(f"📄 Contenido de '{filename}':")
                print(f"📝 {content}")
            else:
                print(f"❌ No se pudo leer '{filename}' (no existe o servicio fallado)")
                
        elif action == "list":
            files = self.fs_service.list_directory("/")
            print("📂 Archivos disponibles:")
            for file_info in files:
                print(f"   📄 {file_info}")
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
            print("🔍 INSPECCIÓN INTERNA - SISTEMA DE ARCHIVOS:")
            print("-" * 45)
            print(f"📍 Ubicación: fs_service.root_dir.files")
            print(f"📊 Total archivos: {len(self.fs_service.root_dir.files)}")
            print("📄 Archivos en memoria:")
            for filename, file_obj in self.fs_service.root_dir.files.items():
                print(f"   • {filename}:")
                print(f"     └─ Objeto: VirtualFile")
                print(f"     └─ Tamaño: {file_obj.size} bytes")
                print(f"     └─ Owner: {file_obj.owner}")
                print(f"     └─ Content: '{file_obj.content[:30]}{'...' if len(file_obj.content) > 30 else ''}'")
                
        elif service_name == "net":
            print("🔍 INSPECCIÓN INTERNA - SERVICIO DE RED:")
            print("-" * 40)
            print(f"📍 DNS Cache: net_service.dns_cache")
            print(f"📊 Entradas DNS: {len(self.net_service.dns_cache)}")
            for domain, ip in self.net_service.dns_cache.items():
                print(f"   🌐 {domain} → {ip}")
            print(f"📍 Interfaces: net_service.network_interfaces")
            print(f"📊 Interfaces: {len(self.net_service.network_interfaces)}")
            for name, config in self.net_service.network_interfaces.items():
                print(f"   🔌 {name}: {config}")
                
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
                print(f"     └─ Stats: {device.stats}")
                
        elif service_name == "security":
            print("🔍 INSPECCIÓN INTERNA - SEGURIDAD:")
            print("-" * 35)
            print(f"📍 Usuarios: security_service.users")
            print(f"📊 Total usuarios: {len(self.security_service.users)}")
            for username, user in self.security_service.users.items():
                print(f"   👤 {username}:")
                print(f"     └─ Objeto: User")
                print(f"     └─ Locked: {user.is_locked}")
                print(f"     └─ Last login: {user.last_login}")
            print(f"📍 Sesiones: security_service.active_sessions")
            print(f"📊 Sesiones activas: {len(self.security_service.active_sessions)}")
        else:
            print(f"❌ Servicio '{service_name}' no encontrado")

    def _handle_demo(self):
        """Demostración automática completa"""
        print("\n🎭 DEMOSTRACIÓN AUTOMÁTICA COMPLETA")
        print("=" * 50)
        
        print("\n1️⃣ Creando archivo de prueba...")
        self.fs_service.create_file("demo.txt", "Archivo de demostración", "admin")
        print("✅ Archivo creado")
        
        print("\n2️⃣ Resolviendo DNS...")
        ip = self.net_service.resolve_dns("demo.microkernel.local")
        print(f"🌐 demo.microkernel.local → {ip}")
        
        print("\n3️⃣ Leyendo dispositivo...")
        data = self.driver_service.device_read("hdd0", 64, "admin")
        print(f"💾 Leídos {len(data)} bytes del disco")
        
        print("\n4️⃣ Login de usuario...")
        token = self.security_service.login("admin", "admin123")
        print(f"🔒 Login exitoso - Token: {token[:15]}...")
        
        print("\n5️⃣ Simulando fallo del sistema de archivos...")
        self.fs_service.failed = True
        success = self.fs_service.create_file("fallo.txt", "No debería funcionar", "admin")
        print(f"💥 Crear archivo con servicio fallado: {'❌ FALLÓ' if not success else '✅ FUNCIONÓ'}")
        
        print("\n6️⃣ Recuperando servicio...")
        self.fs_service.failed = False
        success = self.fs_service.create_file("recuperado.txt", "Ahora funciona", "admin")
        print(f"🔄 Crear archivo recuperado: {'✅ FUNCIONÓ' if success else '❌ FALLÓ'}")
        
        if token:
            self.security_service.logout(token)
            print("👋 Logout realizado")
        
        print("\n✅ DEMOSTRACIÓN COMPLETADA")

    def run(self):
        """Ejecutar el microkernel interactivo"""
        print("\n🎮 MICROKERNEL INTERACTIVO")
        print("Escribe 'help' para ver todos los comandos disponibles")
        print("Escribe 'exit' para salir")
        
        while True:
            try:
                command_input = input("\n🎮 microkernel> ").strip()
                
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
                elif command == "demo":
                    self._handle_demo()
                elif command == "exit":
                    print("👋 ¡Hasta luego!")
                    break
                else:
                    print(f"❌ Comando '{command}' no reconocido. Escribe 'help' para ver los comandos disponibles.")
                    
            except KeyboardInterrupt:
                print("\n👋 ¡Hasta luego!")
                break
            except Exception as e:
                print(f"💥 Error: {e}")

def main():
    """Función principal"""
    try:
        microkernel = MicrokernelCompleto()
        microkernel.run()
    except KeyboardInterrupt:
        print("\n👋 Programa interrumpido")
    except Exception as e:
        print(f"💥 Error fatal: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()