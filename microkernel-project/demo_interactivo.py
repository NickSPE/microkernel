"""
DEMO INTERACTIVO - Usar servicios directamente
==============================================
Este script demuestra cómo interactuar directamente
con los servicios del microkernel.
"""

import sys
import os
import time

# Agregar el directorio actual al path
sys.path.insert(0, os.path.abspath('.'))

# Importar servicios
from services.fs_service import FileSystemService
from services.net_service import NetworkService
from services.driver_service import DriverService
from services.security_service import SecurityService

def demo_filesystem():
    """Demostrar interacción directa con sistema de archivos"""
    print("\n" + "="*50)
    print("📁 DEMO: SISTEMA DE ARCHIVOS DIRECTO")
    print("="*50)
    
    # Crear servicio
    fs = FileSystemService()
    fs.start()
    
    print("1️⃣ Creando archivo 'mi_documento.txt'...")
    success = fs.create_file("mi_documento.txt", "¡Hola desde el microkernel!", "usuario1")
    print(f"   Resultado: {'✅ Éxito' if success else '❌ Falló'}")
    
    print("2️⃣ Leyendo el archivo creado...")
    content = fs.read_file("mi_documento.txt", "usuario1")
    if content:
        print(f"   📄 Contenido: '{content}'")
    
    print("3️⃣ Agregando más contenido...")
    success = fs.write_file("mi_documento.txt", "\nLínea adicional agregada", "usuario1", append=True)
    print(f"   Resultado: {'✅ Éxito' if success else '❌ Falló'}")
    
    print("4️⃣ Leyendo contenido final...")
    content = fs.read_file("mi_documento.txt", "usuario1")
    if content:
        print(f"   📄 Contenido final:")
        print("   " + "-"*30)
        for line in content.split('\n'):
            print(f"   {line}")
        print("   " + "-"*30)
    
    print("5️⃣ Listando archivos...")
    files = fs.list_directory("/")
    print("   📂 Archivos disponibles:")
    for file_info in files:
        print(f"     • {file_info}")
    
    print("\n🎯 El archivo se guardó en memoria como objeto VirtualFile")
    print("🗂️ Ubicación: fs.root_dir.files['mi_documento.txt'].content")
    
    # Mostrar dónde está realmente guardado
    if "mi_documento.txt" in fs.root_dir.files:
        file_obj = fs.root_dir.files["mi_documento.txt"]
        print(f"🔍 Archivo real en memoria:")
        print(f"   • Nombre: {file_obj.name}")
        print(f"   • Tamaño: {file_obj.size} bytes")
        print(f"   • Owner: {file_obj.owner}")
        print(f"   • Contenido: '{file_obj.content}'")

def demo_network():
    """Demostrar interacción directa con servicio de red"""
    print("\n" + "="*50)
    print("🌐 DEMO: SERVICIO DE RED DIRECTO")
    print("="*50)
    
    # Crear servicio
    net = NetworkService()
    net.start()
    time.sleep(0.5)  # Dar tiempo al hilo de red
    
    print("1️⃣ Resolviendo DNS: google.com")
    ip = net.resolve_dns("google.com")
    print(f"   📍 google.com → {ip}")
    
    print("2️⃣ Resolviendo DNS: microkernel.local")
    ip2 = net.resolve_dns("microkernel.local")
    print(f"   📍 microkernel.local → {ip2}")
    
    print("3️⃣ Mostrando interfaces de red:")
    for iface, info in net.network_interfaces.items():
        status = "🟢" if info['status'] == 'up' else "🔴"
        print(f"   {status} {iface}: {info['address']} (MTU: {info['mtu']})")
    
    print("4️⃣ Mostrando caché DNS:")
    print("   🗄️ Entradas en caché:")
    for domain, ip in net.dns_cache.items():
        print(f"     • {domain} → {ip}")
    
    print("5️⃣ Estadísticas de red:")
    for stat, value in net.network_stats.items():
        print(f"   📊 {stat}: {value}")
    
    print("\n🎯 La información se guarda en diccionarios de Python")
    print("🌐 DNS Cache: net.dns_cache[domain] = ip")
    print("🔌 Interfaces: net.network_interfaces[name] = config")

def demo_drivers():
    """Demostrar interacción directa con controladores"""
    print("\n" + "="*50)
    print("🔧 DEMO: CONTROLADORES DIRECTOS")
    print("="*50)
    
    # Crear servicio
    driver = DriverService()
    driver.start()
    time.sleep(1)  # Dar tiempo a inicializar dispositivos
    
    print("1️⃣ Listando dispositivos disponibles:")
    devices = driver.list_devices()
    for device in devices:
        status = "🟢" if device.state.value == 'online' else "🔴"
        print(f"   {status} {device.device_id}: {device.name} ({device.device_type.value})")
    
    print("2️⃣ Leyendo del disco duro (hdd0)...")
    data = driver.device_read("hdd0", 512, "usuario1")
    if data:
        print(f"   📖 Leídos {len(data)} bytes")
        print(f"   🔢 Primeros 20 bytes: {data[:20]}")
    
    print("3️⃣ Escribiendo datos al SSD (ssd0)...")
    test_data = b"Datos de prueba para el microkernel"
    success = driver.device_write("ssd0", test_data, "usuario1")
    print(f"   Resultado: {'✅ Éxito' if success else '❌ Falló'}")
    
    print("4️⃣ Estado del disco duro:")
    device = driver.get_device("hdd0")
    if device:
        print(f"   📋 {device.name}:")
        print(f"     • Estado: {device.state.value}")
        print(f"     • Operaciones: {device.operations_count}")
        print(f"     • Errores: {device.error_count}")
        print(f"     • Bytes leídos: {device.stats.get('bytes_read', 0)}")
        print(f"     • Bytes escritos: {device.stats.get('bytes_written', 0)}")
    
    print("\n🎯 Los dispositivos son objetos VirtualDevice en memoria")
    print("💾 Ubicación: driver.devices[device_id]")
    
    # Mostrar dónde está realmente
    if "hdd0" in driver.devices:
        device = driver.devices["hdd0"]
        print(f"🔍 Dispositivo real en memoria:")
        print(f"   • ID: {device.device_id}")
        print(f"   • Tipo: {device.device_type}")
        print(f"   • Propiedades: {device.properties}")

def demo_security():
    """Demostrar interacción directa con seguridad"""
    print("\n" + "="*50)
    print("🔒 DEMO: SEGURIDAD DIRECTA")
    print("="*50)
    
    # Crear servicio
    security = SecurityService()
    security.start()
    
    print("1️⃣ Intentando login como admin...")
    token = security.login("admin", "admin123")
    if token:
        print(f"   ✅ Login exitoso")
        print(f"   🔑 Token: {token[:20]}...")
    
    print("2️⃣ Verificando sesión...")
    if token:
        valid = security.validate_session(token)
        print(f"   Sesión válida: {'✅ Sí' if valid else '❌ No'}")
    
    print("3️⃣ Listando usuarios del sistema:")
    for username, user in security.users.items():
        status = "🔒" if user.is_locked else "🔓"
        last_login = "Nunca" if not user.last_login else "Recientemente"
        print(f"   {status} {username} - Último login: {last_login}")
    
    print("4️⃣ Sesiones activas:")
    print(f"   💼 Total: {len(security.active_sessions)} sesiones")
    
    print("5️⃣ Estadísticas de seguridad:")
    for stat, value in security.security_stats.items():
        print(f"   📊 {stat}: {value}")
    
    if token:
        print("6️⃣ Haciendo logout...")
        success = security.logout(token)
        print(f"   Resultado: {'✅ Éxito' if success else '❌ Falló'}")
    
    print("\n🎯 Los usuarios y sesiones se guardan en diccionarios")
    print("👤 Usuarios: security.users[username] = User object")
    print("🔑 Sesiones: security.active_sessions[token] = session_info")

def demo_failures():
    """Demostrar cómo funcionan los fallos"""
    print("\n" + "="*50)
    print("💥 DEMO: SIMULACIÓN DE FALLOS")
    print("="*50)
    
    fs = FileSystemService()
    fs.start()
    
    print("1️⃣ Estado normal - Creando archivo...")
    success = fs.create_file("test.txt", "Contenido de prueba", "admin")
    print(f"   Resultado: {'✅ Funcionó' if success else '❌ Falló'}")
    
    print("2️⃣ Simulando fallo del servicio...")
    fs.failed = True  # ← Aquí se simula el fallo
    print("   💥 fs.failed = True")
    
    print("3️⃣ Intentando crear archivo con servicio fallado...")
    success = fs.create_file("test2.txt", "Otro contenido", "admin")
    print(f"   Resultado: {'✅ Funcionó' if success else '❌ Falló como se esperaba'}")
    
    print("4️⃣ Recuperando el servicio...")
    fs.failed = False  # ← Aquí se recupera
    print("   🔄 fs.failed = False")
    
    print("5️⃣ Probando de nuevo...")
    success = fs.create_file("test3.txt", "Después de recuperación", "admin")
    print(f"   Resultado: {'✅ Funcionó' if success else '❌ Falló'}")
    
    print("\n🎯 CLAVE: El atributo 'failed' controla todo")
    print("🔧 fs.failed = True  → Todas las operaciones fallan")
    print("🔧 fs.failed = False → Todas las operaciones funcionan")
    
    # Mostrar el mecanismo interno
    print("\n🔍 MECANISMO INTERNO:")
    print("def create_file(self, ...):")
    print("    if not self._check_service_health():  ← Verifica 'failed'")
    print("        return False  ← Sale inmediatamente si failed=True")
    print("    # ... resto del código complejo solo se ejecuta si failed=False")

def main():
    """Función principal de demostración"""
    print("🎯 DEMOSTRACIÓN INTERACTIVA DE SERVICIOS")
    print("="*60)
    print("Este script muestra cómo interactuar DIRECTAMENTE con")
    print("cada servicio del microkernel, dónde se guardan los datos")
    print("y cómo funciona realmente la simulación de fallos.")
    print("="*60)
    
    try:
        demo_filesystem()
        time.sleep(1)
        
        demo_network()
        time.sleep(1)
        
        demo_drivers()
        time.sleep(1)
        
        demo_security()
        time.sleep(1)
        
        demo_failures()
        
        print("\n" + "="*60)
        print("✅ DEMOSTRACIÓN COMPLETADA")
        print("="*60)
        print("🎓 CONCLUSIONES CLAVE:")
        print("• Los servicios SON reales, no solo mensajes")
        print("• Los datos se guardan en objetos Python complejos")
        print("• Los fallos se simulan con un simple 'failed = True'")
        print("• Cuando 'failed = True', NO se ejecuta código real")
        print("• Cada servicio tiene cientos de líneas de lógica real")
        print("="*60)
        
    except Exception as e:
        print(f"💥 Error en demostración: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()