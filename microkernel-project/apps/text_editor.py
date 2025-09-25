"""
TEXT EDITOR APP - Editor de Texto
==================================
Aplicación que simula un editor de texto básico
usando los servicios del microkernel.
"""

import time
from typing import Optional, List, Dict, Any
from kernel.microkernel import get_kernel
from kernel.ipc import get_ipc_manager
from services.fs_service import get_fs_service
from services.security_service import get_security_service

class TextEditor:
    """
    Editor de Texto Básico
    Demuestra integración con servicios de archivos y seguridad
    """
    
    def __init__(self):
        self.name = "TextEditor"
        self.version = "1.0"
        self.process_id = None
        self.session_token = None
        self.current_file = None
        self.content = ""
        self.unsaved_changes = False
        self.running = False
        self.clipboard = ""
        
        # Historial de comandos (para deshacer)
        self.command_history = []
        self.undo_stack = []
        
        print("📝 TEXT_EDITOR: Aplicación inicializada")
    
    def start(self, session_token: str = None):
        """Inicia el editor de texto"""
        kernel = get_kernel()
        security = get_security_service()
        
        # Verificar autenticación
        if session_token:
            username = security.validate_session(session_token)
            if not username:
                print("❌ TEXT_EDITOR: Sesión inválida")
                return False
            
            self.session_token = session_token
            print(f"✅ TEXT_EDITOR: Iniciado por usuario autenticado")
        else:
            print("⚠️  TEXT_EDITOR: Iniciado sin autenticación (solo lectura)")
        
        # Crear proceso en el kernel
        self.process_id = kernel.create_process(
            name=f"TextEditor-{int(time.time())}",
            target_func=self._editor_loop,
            priority=2  # Prioridad más alta para responsividad
        )
        
        if self.process_id:
            kernel.start_process(self.process_id)
            self.running = True
            print(f"🚀 TEXT_EDITOR: Proceso iniciado (PID: {self.process_id})")
            return True
        
        return False
    
    def stop(self):
        """Detiene el editor"""
        kernel = get_kernel()
        
        # Advertir sobre cambios sin guardar
        if self.unsaved_changes:
            print("⚠️  Hay cambios sin guardar")
        
        if self.process_id:
            kernel.terminate_process(self.process_id)
        
        self.running = False
        print("⏹️  TEXT_EDITOR: Aplicación detenida")
    
    def _editor_loop(self):
        """Bucle principal del editor"""
        print("\n" + "="*60)
        print("📝 EDITOR DE TEXTO DEL MICROKERNEL")
        print("="*60)
        print("Comandos disponibles:")
        print("  • new                - Nuevo documento")
        print("  • open <archivo>     - Abrir archivo")
        print("  • save [archivo]     - Guardar archivo")
        print("  • write <texto>      - Escribir texto")
        print("  • insert <pos> <texto> - Insertar texto en posición")
        print("  • delete <inicio> <fin> - Eliminar texto")
        print("  • find <texto>       - Buscar texto")
        print("  • replace <old> <new> - Reemplazar texto")
        print("  • copy <inicio> <fin> - Copiar al portapapeles")
        print("  • paste <pos>        - Pegar desde portapapeles")
        print("  • undo               - Deshacer último comando")
        print("  • show               - Mostrar contenido")
        print("  • info               - Información del archivo")
        print("  • list               - Listar archivos")
        print("  • quit               - Salir")
        print("="*60)
        
        # Comandos de demostración
        demo_commands = [
            "new",
            "write Hola mundo desde el microkernel!",
            "write \\nEste es un editor de texto que funciona",
            "write \\ncomo una aplicación en espacio de usuario.",
            "show",
            "save demo.txt",
            "find mundo",
            "replace mundo universo",
            "show",
            "copy 0 20",
            "paste 100",
            "show",
            "info",
            "list",
            "save",
            "quit"
        ]
        
        for command in demo_commands:
            if not self.running:
                break
            
            print(f"\n> {command}")
            result = self._process_command(command)
            
            if result:
                print(result)
            
            time.sleep(1.5)  # Pausa para demostración
        
        self.running = False
    
    def _process_command(self, command_line: str) -> Optional[str]:
        """Procesa un comando del editor"""
        if not command_line.strip():
            return None
        
        parts = command_line.strip().split()
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        # Guardar comando en historial
        self.command_history.append(command_line)
        
        try:
            if command == 'quit' or command == 'exit':
                self.stop()
                return "👋 Editor cerrado"
            
            elif command == 'new':
                return self._new_document()
            
            elif command == 'open':
                filename = args[0] if args else None
                return self._open_file(filename)
            
            elif command == 'save':
                filename = args[0] if args else None
                return self._save_file(filename)
            
            elif command == 'write':
                text = ' '.join(args).replace('\\n', '\n')
                return self._write_text(text)
            
            elif command == 'insert':
                if len(args) < 2:
                    return "❌ Uso: insert <posición> <texto>"
                try:
                    pos = int(args[0])
                    text = ' '.join(args[1:]).replace('\\n', '\n')
                    return self._insert_text(pos, text)
                except ValueError:
                    return "❌ Posición debe ser un número"
            
            elif command == 'delete':
                if len(args) < 2:
                    return "❌ Uso: delete <inicio> <fin>"
                try:
                    start = int(args[0])
                    end = int(args[1])
                    return self._delete_text(start, end)
                except ValueError:
                    return "❌ Las posiciones deben ser números"
            
            elif command == 'find':
                text = ' '.join(args)
                return self._find_text(text)
            
            elif command == 'replace':
                if len(args) < 2:
                    return "❌ Uso: replace <texto_viejo> <texto_nuevo>"
                old_text = args[0]
                new_text = ' '.join(args[1:])
                return self._replace_text(old_text, new_text)
            
            elif command == 'copy':
                if len(args) < 2:
                    return "❌ Uso: copy <inicio> <fin>"
                try:
                    start = int(args[0])
                    end = int(args[1])
                    return self._copy_text(start, end)
                except ValueError:
                    return "❌ Las posiciones deben ser números"
            
            elif command == 'paste':
                if args:
                    try:
                        pos = int(args[0])
                        return self._paste_text(pos)
                    except ValueError:
                        return "❌ La posición debe ser un número"
                else:
                    return self._paste_text()
            
            elif command == 'undo':
                return self._undo()
            
            elif command == 'show':
                return self._show_content()
            
            elif command == 'info':
                return self._show_info()
            
            elif command == 'list':
                return self._list_files()
            
            elif command == 'help':
                return self._show_help()
            
            else:
                return f"❌ Comando desconocido: {command}. Use 'help' para ver comandos disponibles."
        
        except Exception as e:
            return f"❌ Error ejecutando comando: {e}"
    
    def _new_document(self) -> str:
        """Crea un nuevo documento"""
        if self.unsaved_changes:
            # En un editor real, preguntaríamos al usuario
            pass
        
        self.content = ""
        self.current_file = None
        self.unsaved_changes = False
        self.undo_stack.append(('new', self.content))
        
        return "📄 Nuevo documento creado"
    
    def _open_file(self, filename: str) -> str:
        """Abre un archivo"""
        if not filename:
            return "❌ Especifique el nombre del archivo"
        
        fs = get_fs_service()
        if not fs.running:
            return "❌ Servicio de archivos no disponible"
        
        # Obtener username si estamos autenticados
        username = "guest"
        if self.session_token:
            security = get_security_service()
            username = security.validate_session(self.session_token) or "guest"
        
        content = fs.read_file(filename, username)
        if content is None:
            return f"❌ No se pudo abrir el archivo: {filename}"
        
        self.content = content
        self.current_file = filename
        self.unsaved_changes = False
        self.undo_stack.append(('open', self.content, filename))
        
        return f"📂 Archivo abierto: {filename} ({len(self.content)} caracteres)"
    
    def _save_file(self, filename: str = None) -> str:
        """Guarda el archivo"""
        if not self.session_token:
            return "❌ Debe estar autenticado para guardar archivos"
        
        fs = get_fs_service()
        if not fs.running:
            return "❌ Servicio de archivos no disponible"
        
        security = get_security_service()
        username = security.validate_session(self.session_token)
        if not username:
            return "❌ Sesión expirada"
        
        # Usar nombre actual si no se especifica uno
        save_filename = filename or self.current_file
        if not save_filename:
            return "❌ Especifique el nombre del archivo"
        
        success = fs.write_file(save_filename, self.content, username)
        if success:
            self.current_file = save_filename
            self.unsaved_changes = False
            return f"💾 Archivo guardado: {save_filename}"
        else:
            return f"❌ Error guardando archivo: {save_filename}"
    
    def _write_text(self, text: str) -> str:
        """Añade texto al final del documento"""
        old_content = self.content
        self.content += text
        self.unsaved_changes = True
        self.undo_stack.append(('write', old_content))
        
        return f"✏️  Texto añadido ({len(text)} caracteres)"
    
    def _insert_text(self, position: int, text: str) -> str:
        """Inserta texto en una posición específica"""
        if position < 0 or position > len(self.content):
            return f"❌ Posición inválida. Rango válido: 0-{len(self.content)}"
        
        old_content = self.content
        self.content = self.content[:position] + text + self.content[position:]
        self.unsaved_changes = True
        self.undo_stack.append(('insert', old_content, position))
        
        return f"📝 Texto insertado en posición {position}"
    
    def _delete_text(self, start: int, end: int) -> str:
        """Elimina texto entre dos posiciones"""
        if start < 0 or end > len(self.content) or start > end:
            return f"❌ Posiciones inválidas. Rango válido: 0-{len(self.content)}"
        
        old_content = self.content
        deleted_text = self.content[start:end]
        self.content = self.content[:start] + self.content[end:]
        self.unsaved_changes = True
        self.undo_stack.append(('delete', old_content, start, end))
        
        return f"🗑️  Eliminado: '{deleted_text}' ({len(deleted_text)} caracteres)"
    
    def _find_text(self, search_text: str) -> str:
        """Busca texto en el documento"""
        if not search_text:
            return "❌ Especifique el texto a buscar"
        
        positions = []
        start = 0
        while True:
            pos = self.content.find(search_text, start)
            if pos == -1:
                break
            positions.append(pos)
            start = pos + 1
        
        if positions:
            return f"🔍 Encontrado '{search_text}' en posiciones: {positions}"
        else:
            return f"❌ No se encontró '{search_text}'"
    
    def _replace_text(self, old_text: str, new_text: str) -> str:
        """Reemplaza texto en el documento"""
        if not old_text:
            return "❌ Especifique el texto a reemplazar"
        
        old_content = self.content
        count = self.content.count(old_text)
        
        if count == 0:
            return f"❌ No se encontró '{old_text}'"
        
        self.content = self.content.replace(old_text, new_text)
        self.unsaved_changes = True
        self.undo_stack.append(('replace', old_content))
        
        return f"🔄 Reemplazadas {count} ocurrencias de '{old_text}' por '{new_text}'"
    
    def _copy_text(self, start: int, end: int) -> str:
        """Copia texto al portapapeles"""
        if start < 0 or end > len(self.content) or start > end:
            return f"❌ Posiciones inválidas. Rango válido: 0-{len(self.content)}"
        
        self.clipboard = self.content[start:end]
        return f"📋 Copiado al portapapeles: '{self.clipboard}' ({len(self.clipboard)} caracteres)"
    
    def _paste_text(self, position: int = None) -> str:
        """Pega texto desde el portapapeles"""
        if not self.clipboard:
            return "❌ Portapapeles vacío"
        
        if position is None:
            position = len(self.content)  # Al final
        
        return self._insert_text(position, self.clipboard)
    
    def _undo(self) -> str:
        """Deshace el último comando"""
        if not self.undo_stack:
            return "❌ Nada que deshacer"
        
        last_action = self.undo_stack.pop()
        action_type = last_action[0]
        
        if action_type in ['write', 'replace']:
            self.content = last_action[1]  # Restaurar contenido anterior
            self.unsaved_changes = True
            return f"↩️  Deshecho: {action_type}"
        
        elif action_type == 'new':
            return "❌ No se puede deshacer la creación de documento"
        
        elif action_type == 'open':
            self.content = ""
            self.current_file = None
            return "↩️  Deshecho: abrir archivo"
        
        return "↩️  Comando deshecho"
    
    def _show_content(self) -> str:
        """Muestra el contenido del documento"""
        if not self.content:
            return "📄 Documento vacío"
        
        # Mostrar primeras líneas para no saturar la salida
        lines = self.content.split('\n')
        preview_lines = lines[:10]  # Primeras 10 líneas
        
        content_preview = '\n'.join(preview_lines)
        
        info = f"📄 CONTENIDO DEL DOCUMENTO:\n"
        info += "─" * 40 + "\n"
        info += content_preview
        
        if len(lines) > 10:
            info += f"\n... (+{len(lines) - 10} líneas más)"
        
        info += "\n" + "─" * 40
        info += f"\nTotal: {len(self.content)} caracteres, {len(lines)} líneas"
        
        return info
    
    def _show_info(self) -> str:
        """Muestra información del archivo actual"""
        info = "📊 INFORMACIÓN DEL EDITOR\n"
        info += "─" * 30 + "\n"
        info += f"Archivo actual: {self.current_file or 'Sin nombre'}\n"
        info += f"Caracteres: {len(self.content)}\n"
        info += f"Líneas: {len(self.content.split(chr(10)))}\n"
        info += f"Palabras: {len(self.content.split())}\n"
        info += f"Cambios sin guardar: {'✅ Sí' if self.unsaved_changes else '❌ No'}\n"
        info += f"Portapapeles: {len(self.clipboard)} caracteres\n"
        info += f"Historial de comandos: {len(self.command_history)}\n"
        info += f"Acciones para deshacer: {len(self.undo_stack)}\n"
        
        if self.session_token:
            security = get_security_service()
            username = security.validate_session(self.session_token)
            info += f"Usuario: {username or 'Desconocido'}\n"
        else:
            info += "Usuario: No autenticado (solo lectura)\n"
        
        return info
    
    def _list_files(self) -> str:
        """Lista archivos disponibles"""
        fs = get_fs_service()
        if not fs.running:
            return "❌ Servicio de archivos no disponible"
        
        try:
            files = fs.list_directory("/")
            if not files:
                return "📁 No hay archivos en el directorio"
            
            file_list = "📁 ARCHIVOS DISPONIBLES:\n"
            for file_item in files:
                file_list += f"  {file_item}\n"
            
            return file_list.strip()
            
        except Exception as e:
            return f"❌ Error listando archivos: {e}"
    
    def _show_help(self) -> str:
        """Muestra la ayuda del editor"""
        return """
📝 AYUDA DEL EDITOR DE TEXTO

Gestión de archivos:
  • new                - Crear nuevo documento
  • open <archivo>     - Abrir archivo existente
  • save [archivo]     - Guardar documento
  • list               - Listar archivos disponibles

Edición de texto:
  • write <texto>      - Añadir texto al final
  • insert <pos> <texto> - Insertar en posición específica
  • delete <inicio> <fin> - Eliminar rango de texto
  • replace <viejo> <nuevo> - Reemplazar texto

Búsqueda y navegación:
  • find <texto>       - Buscar texto en el documento
  • show               - Mostrar contenido del documento

Portapapeles:
  • copy <inicio> <fin> - Copiar texto al portapapeles
  • paste [pos]        - Pegar desde portapapeles

Utilidades:
  • undo               - Deshacer último comando
  • info               - Información del documento
  • help               - Esta ayuda
  • quit               - Salir del editor

Nota: Use \\n en los textos para representar saltos de línea
        """.strip()

# Funciones de utilidad
def create_text_editor() -> TextEditor:
    """Crea una nueva instancia del editor"""
    return TextEditor()

def run_text_editor_demo():
    """Ejecuta una demostración del editor"""
    print("🎯 Iniciando demostración del Editor de Texto...")
    
    editor = TextEditor()
    if editor.start():
        return editor
    else:
        print("❌ Error iniciando el editor")
        return None

if __name__ == "__main__":
    # Si se ejecuta directamente, hacer una demo
    demo_editor = run_text_editor_demo()
    if demo_editor:
        while demo_editor.running:
            time.sleep(1)