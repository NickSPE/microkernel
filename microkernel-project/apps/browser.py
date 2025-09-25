"""
BROWSER APP - Navegador Web Simulado
====================================
Aplicación que simula un navegador web básico
usando los servicios de red y archivos del microkernel.
"""

import time
import re
from typing import Optional, List, Dict, Any
from kernel.microkernel import get_kernel
from kernel.ipc import get_ipc_manager
from services.net_service import get_net_service
from services.security_service import get_security_service

class WebPage:
    """Representa una página web simple"""
    
    def __init__(self, url: str, title: str, content: str):
        self.url = url
        self.title = title
        self.content = content
        self.loaded_at = time.time()
        self.size = len(content)

class Browser:
    """
    Navegador Web Simulado
    Demuestra el uso de servicios de red y seguridad
    """
    
    def __init__(self):
        self.name = "Browser"
        self.version = "1.0"
        self.process_id = None
        self.session_token = None
        self.current_page = None
        self.history = []
        self.bookmarks = []
        self.running = False
        
        # Cache de páginas
        self.page_cache = {}
        
        # Páginas web simuladas
        self.simulated_sites = {
            "microkernel.local": WebPage(
                "http://microkernel.local",
                "Microkernel OS - Home",
                self._generate_homepage()
            ),
            "docs.microkernel.local": WebPage(
                "http://docs.microkernel.local",
                "Documentación - Microkernel OS",
                self._generate_docs_page()
            ),
            "admin.microkernel.local": WebPage(
                "http://admin.microkernel.local", 
                "Panel de Administración",
                self._generate_admin_page()
            ),
            "services.microkernel.local": WebPage(
                "http://services.microkernel.local",
                "Estado de Servicios",
                self._generate_services_page()
            )
        }
        
        print("🌐 BROWSER: Aplicación inicializada")
    
    def start(self, session_token: str = None):
        """Inicia el navegador"""
        kernel = get_kernel()
        security = get_security_service()
        
        # Verificar autenticación
        if session_token:
            username = security.validate_session(session_token)
            if not username:
                print("❌ BROWSER: Sesión inválida")
                return False
            
            self.session_token = session_token
            print(f"✅ BROWSER: Iniciado por usuario autenticado")
        else:
            print("⚠️  BROWSER: Iniciado sin autenticación (acceso limitado)")
        
        # Crear proceso en el kernel
        self.process_id = kernel.create_process(
            name=f"Browser-{int(time.time())}",
            target_func=self._browser_loop,
            priority=2
        )
        
        if self.process_id:
            kernel.start_process(self.process_id)
            self.running = True
            print(f"🚀 BROWSER: Proceso iniciado (PID: {self.process_id})")
            return True
        
        return False
    
    def stop(self):
        """Detiene el navegador"""
        kernel = get_kernel()
        
        if self.process_id:
            kernel.terminate_process(self.process_id)
        
        self.running = False
        print("⏹️  BROWSER: Navegador cerrado")
    
    def _browser_loop(self):
        """Bucle principal del navegador"""
        print("\n" + "="*60)
        print("🌐 NAVEGADOR WEB DEL MICROKERNEL")
        print("="*60)
        print("Comandos disponibles:")
        print("  • go <url>           - Navegar a URL")
        print("  • back               - Página anterior")
        print("  • forward            - Página siguiente")
        print("  • refresh            - Recargar página")
        print("  • bookmark           - Guardar marcador")
        print("  • bookmarks          - Ver marcadores")
        print("  • history            - Ver historial")
        print("  • search <término>   - Buscar en la página")
        print("  • download <url>     - Descargar archivo")
        print("  • view-source        - Ver código fuente")
        print("  • status             - Estado del navegador")
        print("  • home               - Ir a página principal")
        print("  • help               - Ayuda")
        print("  • quit               - Salir")
        print("="*60)
        
        # Navegar a página principal
        self._navigate_to("microkernel.local")
        
        # Comandos de demostración
        demo_commands = [
            "go microkernel.local",
            "bookmark",
            "go docs.microkernel.local",
            "search arquitectura",
            "back",
            "go services.microkernel.local",
            "refresh",
            "view-source",
            "history",
            "bookmarks",
            "home",
            "status",
            "quit"
        ]
        
        for command in demo_commands:
            if not self.running:
                break
            
            print(f"\n> {command}")
            result = self._process_command(command)
            
            if result:
                print(result)
            
            time.sleep(2)  # Pausa para demostración
        
        self.running = False
    
    def _process_command(self, command_line: str) -> Optional[str]:
        """Procesa un comando del navegador"""
        if not command_line.strip():
            return None
        
        parts = command_line.strip().split()
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        try:
            if command in ['quit', 'exit']:
                self.stop()
                return "👋 Navegador cerrado"
            
            elif command == 'go':
                url = args[0] if args else None
                return self._navigate_to(url)
            
            elif command == 'back':
                return self._go_back()
            
            elif command == 'forward':
                return self._go_forward()
            
            elif command == 'refresh':
                return self._refresh_page()
            
            elif command == 'home':
                return self._navigate_to("microkernel.local")
            
            elif command == 'bookmark':
                return self._add_bookmark()
            
            elif command == 'bookmarks':
                return self._show_bookmarks()
            
            elif command == 'history':
                return self._show_history()
            
            elif command == 'search':
                term = ' '.join(args) if args else None
                return self._search_in_page(term)
            
            elif command == 'download':
                url = args[0] if args else None
                return self._download_file(url)
            
            elif command == 'view-source':
                return self._view_source()
            
            elif command == 'status':
                return self._show_status()
            
            elif command == 'help':
                return self._show_help()
            
            else:
                return f"❌ Comando desconocido: {command}. Use 'help' para ver comandos."
        
        except Exception as e:
            return f"❌ Error ejecutando comando: {e}"
    
    def _navigate_to(self, url: str) -> str:
        """Navega a una URL"""
        if not url:
            return "❌ Especifique una URL"
        
        # Normalizar URL
        if not url.startswith('http'):
            url = f"http://{url}"
        
        print(f"🔍 Conectando a {url}...")
        
        # Simular tiempo de carga
        time.sleep(0.5)
        
        # Verificar si es un sitio simulado
        domain = url.replace('http://', '').replace('https://', '').split('/')[0]
        
        if domain in self.simulated_sites:
            page = self.simulated_sites[domain]
            
            # Verificar permisos para páginas restringidas
            if domain == "admin.microkernel.local" and not self._check_admin_access():
                return "❌ Acceso denegado. Se requiere autenticación de administrador."
            
            # Cargar página
            self.current_page = page
            self.history.append(page.url)
            self.page_cache[page.url] = page
            
            return self._display_page(page)
        
        else:
            # Simular conexión a sitio externo
            return self._simulate_external_request(url)
    
    def _simulate_external_request(self, url: str) -> str:
        """Simula una petición a un sitio externo"""
        net_service = get_net_service()
        
        if not net_service.running:
            return "❌ Servicio de red no disponible"
        
        # Simular resolución DNS
        domain = url.replace('http://', '').replace('https://', '').split('/')[0]
        ip = net_service.resolve_dns(domain)
        
        if not ip:
            return f"❌ No se pudo resolver {domain}"
        
        # Simular conexión
        conn_id = net_service.create_connection("192.168.1.100", ip)
        
        if not conn_id:
            return f"❌ No se pudo conectar a {url}"
        
        # Simular petición HTTP
        request_data = f"GET / HTTP/1.1\\r\\nHost: {domain}\\r\\n\\r\\n"
        success = net_service.send_data(conn_id, request_data)
        
        if success:
            # Simular respuesta
            fake_page = WebPage(url, f"Página Externa - {domain}", 
                               f"Contenido simulado de {url}")
            self.current_page = fake_page
            self.history.append(url)
            
            net_service.close_connection(conn_id)
            
            return self._display_page(fake_page)
        else:
            return f"❌ Error cargando {url}"
    
    def _display_page(self, page: WebPage) -> str:
        """Muestra una página web"""
        display = f"📄 {page.title}\n"
        display += f"🔗 {page.url}\n"
        display += "─" * 50 + "\n"
        display += page.content[:500]  # Primeros 500 caracteres
        
        if len(page.content) > 500:
            display += f"\n... (+{len(page.content) - 500} caracteres más)"
        
        display += f"\n\n📊 Tamaño: {page.size} bytes | Cargada: {time.ctime(page.loaded_at)}"
        
        return display
    
    def _go_back(self) -> str:
        """Navega hacia atrás en el historial"""
        if len(self.history) < 2:
            return "❌ No hay páginas anteriores"
        
        # Remover página actual y ir a la anterior
        self.history.pop()  # Actual
        previous_url = self.history[-1]
        
        return self._navigate_to(previous_url.replace('http://', ''))
    
    def _go_forward(self) -> str:
        """Navega hacia adelante (simplificado)"""
        return "⚠️  Función 'adelante' no implementada en esta demo"
    
    def _refresh_page(self) -> str:
        """Recarga la página actual"""
        if not self.current_page:
            return "❌ No hay página para recargar"
        
        print("🔄 Recargando página...")
        time.sleep(0.3)
        
        # Simular recarga actualizando timestamp
        self.current_page.loaded_at = time.time()
        
        return f"✅ Página recargada: {self.current_page.title}"
    
    def _add_bookmark(self) -> str:
        """Añade la página actual a marcadores"""
        if not self.current_page:
            return "❌ No hay página para marcar"
        
        bookmark = {
            'title': self.current_page.title,
            'url': self.current_page.url,
            'added_at': time.time()
        }
        
        # Verificar si ya existe
        for existing in self.bookmarks:
            if existing['url'] == bookmark['url']:
                return "⚠️  Esta página ya está en marcadores"
        
        self.bookmarks.append(bookmark)
        return f"⭐ Marcador añadido: {self.current_page.title}"
    
    def _show_bookmarks(self) -> str:
        """Muestra los marcadores"""
        if not self.bookmarks:
            return "📚 No hay marcadores guardados"
        
        bookmarks_list = "⭐ MARCADORES:\n"
        for i, bookmark in enumerate(self.bookmarks, 1):
            bookmarks_list += f"  {i}. {bookmark['title']}\n"
            bookmarks_list += f"     {bookmark['url']}\n"
        
        return bookmarks_list.strip()
    
    def _show_history(self) -> str:
        """Muestra el historial de navegación"""
        if not self.history:
            return "📜 Historial vacío"
        
        history_list = "📜 HISTORIAL DE NAVEGACIÓN:\n"
        for i, url in enumerate(reversed(self.history[-10:]), 1):  # Últimas 10
            history_list += f"  {i}. {url}\n"
        
        return history_list.strip()
    
    def _search_in_page(self, term: str) -> str:
        """Busca un término en la página actual"""
        if not self.current_page:
            return "❌ No hay página cargada"
        
        if not term:
            return "❌ Especifique el término a buscar"
        
        content = self.current_page.content.lower()
        term = term.lower()
        
        count = content.count(term)
        if count > 0:
            # Encontrar posiciones
            positions = []
            start = 0
            while start < len(content):
                pos = content.find(term, start)
                if pos == -1:
                    break
                positions.append(pos)
                start = pos + 1
                if len(positions) >= 5:  # Limitar a 5 resultados
                    break
            
            return f"🔍 Encontrado '{term}' {count} veces en posiciones: {positions}"
        else:
            return f"❌ No se encontró '{term}' en la página"
    
    def _download_file(self, url: str) -> str:
        """Simula la descarga de un archivo"""
        if not url:
            return "❌ Especifique la URL del archivo"
        
        if not self.session_token:
            return "❌ Debe estar autenticado para descargar archivos"
        
        print(f"📥 Descargando {url}...")
        time.sleep(1)  # Simular descarga
        
        # Simular guardado en sistema de archivos
        filename = url.split('/')[-1] or "archivo_descargado"
        
        return f"✅ Archivo descargado: {filename}"
    
    def _view_source(self) -> str:
        """Muestra el código fuente de la página actual"""
        if not self.current_page:
            return "❌ No hay página cargada"
        
        source = f"📄 CÓDIGO FUENTE: {self.current_page.title}\n"
        source += "─" * 40 + "\n"
        source += f"<!-- URL: {self.current_page.url} -->\n"
        source += f"<!-- Tamaño: {self.current_page.size} bytes -->\n"
        source += f"<!-- Cargada: {time.ctime(self.current_page.loaded_at)} -->\n"
        source += "<html>\n<head>\n"
        source += f"<title>{self.current_page.title}</title>\n"
        source += "</head>\n<body>\n"
        source += self.current_page.content[:300]  # Primeros 300 caracteres
        if len(self.current_page.content) > 300:
            source += f"\n... (+{len(self.current_page.content) - 300} caracteres más)"
        source += "\n</body>\n</html>"
        
        return source
    
    def _show_status(self) -> str:
        """Muestra el estado del navegador"""
        kernel = get_kernel()
        process = kernel.get_process(self.process_id) if self.process_id else None
        
        status = f"🌐 ESTADO DEL NAVEGADOR\n"
        status += "─" * 30 + "\n"
        status += f"Versión: {self.version}\n"
        status += f"Estado: {'🟢 Activo' if self.running else '🔴 Inactivo'}\n"
        status += f"PID: {self.process_id or 'N/A'}\n"
        status += f"Página actual: {self.current_page.title if self.current_page else 'Ninguna'}\n"
        status += f"Historial: {len(self.history)} páginas\n"
        status += f"Marcadores: {len(self.bookmarks)}\n"
        status += f"Cache: {len(self.page_cache)} páginas\n"
        
        if process:
            status += f"Memoria: {process.memory_allocated} bytes\n"
        
        if self.session_token:
            security = get_security_service()
            username = security.validate_session(self.session_token)
            status += f"Usuario: {username or 'Desconocido'}\n"
        else:
            status += "Usuario: No autenticado\n"
        
        return status
    
    def _check_admin_access(self) -> bool:
        """Verifica si el usuario tiene acceso de administrador"""
        if not self.session_token:
            return False
        
        security = get_security_service()
        username = security.validate_session(self.session_token)
        
        if not username:
            return False
        
        # En un sistema real, verificaríamos permisos específicos
        return security.check_permission(self.session_token, "admin_access")
    
    def _show_help(self) -> str:
        """Muestra la ayuda del navegador"""
        return """
🌐 AYUDA DEL NAVEGADOR

Navegación:
  • go <url>           - Navegar a una URL
  • back               - Página anterior
  • home               - Ir a página principal
  • refresh            - Recargar página actual

Marcadores e Historial:
  • bookmark           - Guardar página actual en marcadores
  • bookmarks          - Ver lista de marcadores
  • history            - Ver historial de navegación

Búsqueda y Contenido:
  • search <término>   - Buscar término en página actual
  • view-source        - Ver código fuente de la página
  • download <url>     - Descargar archivo (requiere autenticación)

Información:
  • status             - Ver estado del navegador
  • help               - Esta ayuda
  • quit               - Salir del navegador

Sitios disponibles:
  • microkernel.local        - Página principal
  • docs.microkernel.local   - Documentación
  • services.microkernel.local - Estado de servicios
  • admin.microkernel.local  - Panel admin (requiere permisos)
        """.strip()
    
    # ==================== PÁGINAS SIMULADAS ====================
    
    def _generate_homepage(self) -> str:
        """Genera la página principal"""
        return """
Bienvenido al Sistema Operativo Microkernel

Este es un sistema operativo experimental que demuestra la
arquitectura microkernel, donde el núcleo mantiene solo las
funcionalidades más básicas y los servicios se ejecutan en
espacio de usuario.

Características:
• Núcleo mínimo con gestión básica de procesos
• Servicios modulares (archivos, red, seguridad, drivers)
• Aplicaciones en espacio de usuario
• Comunicación entre procesos (IPC)
• Sistema de permisos y autenticación

Servicios disponibles:
→ Sistema de archivos virtual
→ Servicio de red simulado  
→ Controladores de dispositivos
→ Sistema de seguridad y autenticación
→ Planificador de procesos

¡Explora las diferentes aplicaciones y servicios!
        """.strip()
    
    def _generate_docs_page(self) -> str:
        """Genera la página de documentación"""
        return """
Documentación del Microkernel

ARQUITECTURA:
El microkernel implementa una arquitectura donde el núcleo
contiene solo las funciones más esenciales:

1. Gestión básica de procesos
2. Gestión mínima de memoria  
3. Comunicación entre procesos (IPC)
4. Carga y descarga de servicios

SERVICIOS:
Los servicios se ejecutan en espacio de usuario:

• FileSystemService: Sistema de archivos virtual
• NetworkService: Gestión de conexiones de red
• DriverService: Controladores de dispositivos
• SecurityService: Autenticación y autorización

APLICACIONES:
Las aplicaciones demuestran el uso de servicios:

• Calculator: Operaciones matemáticas
• TextEditor: Edición de archivos de texto
• Browser: Navegación web simulada

VENTAJAS:
→ Modularidad y extensibilidad
→ Mejor aislamiento de fallos
→ Facilidad de mantenimiento
→ Seguridad mejorada
        """.strip()
    
    def _generate_services_page(self) -> str:
        """Genera la página de estado de servicios"""
        kernel = get_kernel()
        services = kernel.list_services()
        
        content = "Estado de Servicios del Sistema\n\n"
        content += f"Servicios registrados: {len(services)}\n\n"
        
        for service_name in services:
            service = kernel.get_service(service_name)
            if service:
                status = "🟢 Activo" if getattr(service, 'running', False) else "🔴 Inactivo"
                version = getattr(service, 'version', 'N/A')
                content += f"• {service_name}: {status} (v{version})\n"
        
        content += f"\nProcesos activos: {len(kernel.list_processes())}\n"
        
        memory_info = kernel.get_memory_info()
        content += f"Memoria usada: {memory_info['used']}/{memory_info['total']} bytes\n"
        content += f"Uso de memoria: {memory_info['percentage']:.1f}%\n"
        
        return content
    
    def _generate_admin_page(self) -> str:
        """Genera la página de administración"""
        return """
Panel de Administración del Sistema

CONTROLES DEL SISTEMA:
• Gestión de procesos
• Configuración de servicios
• Monitoreo de recursos
• Gestión de usuarios
• Logs del sistema

ESTADÍSTICAS:
→ Tiempo de actividad del sistema
→ Uso de CPU y memoria
→ Operaciones de E/S
→ Conexiones de red activas
→ Eventos de seguridad

CONFIGURACIÓN:
→ Políticas de seguridad
→ Límites de recursos
→ Configuración de red
→ Parámetros del planificador

⚠️  ADVERTENCIA:
Los cambios en esta sección pueden afectar
la estabilidad del sistema. Proceder con
precaución.

Solo usuarios con permisos de administrador
pueden acceder a estas funcionalidades.
        """.strip()

# Funciones de utilidad
def create_browser() -> Browser:
    """Crea una nueva instancia del navegador"""
    return Browser()

def run_browser_demo():
    """Ejecuta una demostración del navegador"""
    print("🎯 Iniciando demostración del Navegador...")
    
    browser = Browser()
    if browser.start():
        return browser
    else:
        print("❌ Error iniciando el navegador")
        return None

if __name__ == "__main__":
    # Si se ejecuta directamente, hacer una demo
    demo_browser = run_browser_demo()
    if demo_browser:
        while demo_browser.running:
            time.sleep(1)