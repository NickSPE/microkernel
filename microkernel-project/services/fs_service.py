"""
FILE SYSTEM SERVICE - Servicio de Sistema de Archivos
=====================================================
Servicio externo que maneja operaciones de archivos.
En un microkernel real, esto correría en espacio de usuario.
"""

import os
import json
import time
import threading
from typing import Dict, List, Optional, Any
from kernel.microkernel import get_kernel

class VirtualFile:
    """Representa un archivo virtual en el sistema"""
    def __init__(self, name: str, content: str = "", owner: str = "system"):
        self.name = name
        self.content = content
        self.owner = owner
        self.created_at = time.time()
        self.modified_at = time.time()
        self.accessed_at = time.time()
        self.size = len(content.encode('utf-8'))
        self.permissions = "rw-rw-r--"  # Unix-style permissions
    
    def read(self, process_id: str) -> Optional[str]:
        """Lee el contenido del archivo"""
        if not self._check_read_permission(process_id):
            print(f"❌ FS: {process_id} sin permisos de lectura para {self.name}")
            return None
        
        self.accessed_at = time.time()
        print(f"📖 FS: {process_id} leyó {self.name}")
        return self.content
    
    def write(self, process_id: str, content: str, append: bool = False) -> bool:
        """Escribe contenido al archivo"""
        if not self._check_write_permission(process_id):
            print(f"❌ FS: {process_id} sin permisos de escritura para {self.name}")
            return False
        
        if append:
            self.content += content
        else:
            self.content = content
        
        self.size = len(self.content.encode('utf-8'))
        self.modified_at = time.time()
        self.accessed_at = time.time()
        
        print(f"✏️  FS: {process_id} escribió en {self.name} ({self.size} bytes)")
        return True
    
    def _check_read_permission(self, process_id: str) -> bool:
        """Verifica permisos de lectura"""
        # Simplificado: el owner y system siempre pueden leer
        return self.owner == process_id or process_id == "system"
    
    def _check_write_permission(self, process_id: str) -> bool:
        """Verifica permisos de escritura"""
        # Simplificado: solo el owner puede escribir
        return self.owner == process_id or process_id == "system"
    
    def get_info(self) -> Dict[str, Any]:
        """Obtiene información del archivo"""
        return {
            'name': self.name,
            'size': self.size,
            'owner': self.owner,
            'permissions': self.permissions,
            'created_at': time.ctime(self.created_at),
            'modified_at': time.ctime(self.modified_at),
            'accessed_at': time.ctime(self.accessed_at)
        }

class VirtualDirectory:
    """Representa un directorio virtual"""
    def __init__(self, name: str, owner: str = "system"):
        self.name = name
        self.owner = owner
        self.files: Dict[str, VirtualFile] = {}
        self.subdirs: Dict[str, 'VirtualDirectory'] = {}
        self.created_at = time.time()
        self.permissions = "rwxrwxr-x"
    
    def add_file(self, file: VirtualFile) -> bool:
        """Añade un archivo al directorio"""
        if file.name in self.files:
            return False
        
        self.files[file.name] = file
        return True
    
    def add_directory(self, directory: 'VirtualDirectory') -> bool:
        """Añade un subdirectorio"""
        if directory.name in self.subdirs:
            return False
        
        self.subdirs[directory.name] = directory
        return True
    
    def list_contents(self) -> List[str]:
        """Lista el contenido del directorio"""
        contents = []
        contents.extend([f"📁 {name}/" for name in self.subdirs.keys()])
        contents.extend([f"📄 {name}" for name in self.files.keys()])
        return contents
    
    def get_size(self) -> int:
        """Calcula el tamaño total del directorio"""
        total = sum(file.size for file in self.files.values())
        total += sum(subdir.get_size() for subdir in self.subdirs.values())
        return total

class FileSystemService:
    """
    Servicio de Sistema de Archivos
    Proporciona operaciones de archivos para el sistema
    """
    
    def __init__(self):
        self.name = "FileSystemService"
        self.version = "1.0"
        self.running = False
        self.root_dir = VirtualDirectory("/", "system")
        self.current_dir = "/"
        self.file_handles: Dict[str, Dict] = {}  # Handles de archivos abiertos
        self.fs_lock = threading.RLock()
        
        # Crear estructura de directorios básica
        self._create_basic_structure()
        
        print("📁 FS_SERVICE: Sistema de archivos inicializado")
    
    def _create_basic_structure(self):
        """Crea la estructura básica de directorios"""
        # Crear directorios básicos
        home_dir = VirtualDirectory("home", "system")
        tmp_dir = VirtualDirectory("tmp", "system")
        etc_dir = VirtualDirectory("etc", "system")
        
        self.root_dir.add_directory(home_dir)
        self.root_dir.add_directory(tmp_dir)
        self.root_dir.add_directory(etc_dir)
        
        # Crear algunos archivos de ejemplo
        readme = VirtualFile("README.txt", "Bienvenido al Sistema de Archivos Virtual", "system")
        config = VirtualFile("system.conf", "kernel_debug=true\nmax_processes=100", "system")
        
        self.root_dir.add_file(readme)
        etc_dir.add_file(config)
        
        print("📁 FS_SERVICE: Estructura básica creada")
    
    def start(self):
        """Inicia el servicio de archivos"""
        with self.fs_lock:
            if self.running:
                return True
            
            self.running = True
            print("🟢 FS_SERVICE: Servicio iniciado")
            return True
    
    def stop(self):
        """Detiene el servicio"""
        with self.fs_lock:
            self.running = False
            
            # Cerrar todos los handles de archivos
            self.file_handles.clear()
            
            print("🔴 FS_SERVICE: Servicio detenido")
    
    def _resolve_path(self, path: str) -> tuple:
        """Resuelve una ruta y retorna (directorio_padre, nombre_archivo)"""
        if path.startswith('/'):
            # Ruta absoluta
            parts = path.strip('/').split('/')
        else:
            # Ruta relativa al directorio actual
            current_parts = self.current_dir.strip('/').split('/') if self.current_dir != '/' else []
            parts = current_parts + path.split('/')
        
        # Navegar por los directorios
        current_dir = self.root_dir
        
        for i, part in enumerate(parts[:-1]):
            if not part:  # Parte vacía
                continue
            
            if part not in current_dir.subdirs:
                return None, None
            
            current_dir = current_dir.subdirs[part]
        
        filename = parts[-1] if parts and parts[-1] else None
        return current_dir, filename
    
    # ==================== OPERACIONES DE ARCHIVOS ====================
    
    def create_file(self, path: str, content: str = "", owner: str = "system") -> bool:
        """Crea un nuevo archivo"""
        with self.fs_lock:
            parent_dir, filename = self._resolve_path(path)
            
            if not parent_dir or not filename:
                print(f"❌ FS: Ruta inválida: {path}")
                return False
            
            if filename in parent_dir.files:
                print(f"❌ FS: El archivo {path} ya existe")
                return False
            
            new_file = VirtualFile(filename, content, owner)
            parent_dir.add_file(new_file)
            
            print(f"✅ FS: Archivo creado: {path}")
            return True
    
    def read_file(self, path: str, process_id: str = "system") -> Optional[str]:
        """Lee el contenido de un archivo"""
        with self.fs_lock:
            parent_dir, filename = self._resolve_path(path)
            
            if not parent_dir or not filename or filename not in parent_dir.files:
                print(f"❌ FS: Archivo no encontrado: {path}")
                return None
            
            file = parent_dir.files[filename]
            return file.read(process_id)
    
    def write_file(self, path: str, content: str, process_id: str = "system", append: bool = False) -> bool:
        """Escribe contenido a un archivo"""
        with self.fs_lock:
            parent_dir, filename = self._resolve_path(path)
            
            if not parent_dir or not filename:
                print(f"❌ FS: Ruta inválida: {path}")
                return False
            
            # Si el archivo no existe, crearlo
            if filename not in parent_dir.files:
                new_file = VirtualFile(filename, "", process_id)
                parent_dir.add_file(new_file)
            
            file = parent_dir.files[filename]
            return file.write(process_id, content, append)
    
    def delete_file(self, path: str, process_id: str = "system") -> bool:
        """Elimina un archivo"""
        with self.fs_lock:
            parent_dir, filename = self._resolve_path(path)
            
            if not parent_dir or not filename or filename not in parent_dir.files:
                print(f"❌ FS: Archivo no encontrado: {path}")
                return False
            
            file = parent_dir.files[filename]
            if file.owner != process_id and process_id != "system":
                print(f"❌ FS: Sin permisos para eliminar {path}")
                return False
            
            del parent_dir.files[filename]
            print(f"🗑️  FS: Archivo eliminado: {path}")
            return True
    
    def copy_file(self, source: str, destination: str, process_id: str = "system") -> bool:
        """Copia un archivo"""
        content = self.read_file(source, process_id)
        if content is None:
            return False
        
        return self.write_file(destination, content, process_id)
    
    def move_file(self, source: str, destination: str, process_id: str = "system") -> bool:
        """Mueve un archivo"""
        if self.copy_file(source, destination, process_id):
            return self.delete_file(source, process_id)
        return False
    
    def get_file_info(self, path: str) -> Optional[Dict[str, Any]]:
        """Obtiene información de un archivo"""
        with self.fs_lock:
            parent_dir, filename = self._resolve_path(path)
            
            if not parent_dir or not filename or filename not in parent_dir.files:
                return None
            
            file = parent_dir.files[filename]
            return file.get_info()
    
    # ==================== OPERACIONES DE DIRECTORIOS ====================
    
    def create_directory(self, path: str, owner: str = "system") -> bool:
        """Crea un nuevo directorio"""
        with self.fs_lock:
            parent_dir, dirname = self._resolve_path(path)
            
            if not parent_dir or not dirname:
                print(f"❌ FS: Ruta inválida: {path}")
                return False
            
            if dirname in parent_dir.subdirs:
                print(f"❌ FS: El directorio {path} ya existe")
                return False
            
            new_dir = VirtualDirectory(dirname, owner)
            parent_dir.add_directory(new_dir)
            
            print(f"📁 FS: Directorio creado: {path}")
            return True
    
    def list_directory(self, path: str = "/") -> List[str]:
        """Lista el contenido de un directorio"""
        with self.fs_lock:
            if path == "/":
                directory = self.root_dir
            else:
                parent_dir, dirname = self._resolve_path(path)
                if not parent_dir or not dirname or dirname not in parent_dir.subdirs:
                    print(f"❌ FS: Directorio no encontrado: {path}")
                    return []
                directory = parent_dir.subdirs[dirname]
            
            return directory.list_contents()
    
    def change_directory(self, path: str) -> bool:
        """Cambia el directorio actual"""
        with self.fs_lock:
            if path == "/":
                self.current_dir = "/"
                return True
            
            parent_dir, dirname = self._resolve_path(path)
            if not parent_dir or not dirname or dirname not in parent_dir.subdirs:
                print(f"❌ FS: Directorio no encontrado: {path}")
                return False
            
            self.current_dir = path
            print(f"📁 FS: Directorio cambiado a: {path}")
            return True
    
    def get_current_directory(self) -> str:
        """Obtiene el directorio actual"""
        return self.current_dir
    
    # ==================== INFORMACIÓN Y ESTADÍSTICAS ====================
    
    def get_fs_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del sistema de archivos"""
        def count_items(directory: VirtualDirectory) -> tuple:
            files = len(directory.files)
            dirs = len(directory.subdirs)
            
            for subdir in directory.subdirs.values():
                sub_files, sub_dirs = count_items(subdir)
                files += sub_files
                dirs += sub_dirs
            
            return files, dirs
        
        total_files, total_dirs = count_items(self.root_dir)
        total_size = self.root_dir.get_size()
        
        return {
            'running': self.running,
            'current_directory': self.current_dir,
            'total_files': total_files,
            'total_directories': total_dirs,
            'total_size_bytes': total_size,
            'open_file_handles': len(self.file_handles)
        }
    
    def print_fs_status(self):
        """Imprime el estado del sistema de archivos"""
        stats = self.get_fs_stats()
        
        print("\n" + "-"*40)
        print("📁 ESTADO DEL SISTEMA DE ARCHIVOS")
        print("-"*40)
        print(f"🟢 Estado: {'Activo' if stats['running'] else 'Inactivo'}")
        print(f"📍 Directorio actual: {stats['current_directory']}")
        print(f"📄 Archivos totales: {stats['total_files']}")
        print(f"📁 Directorios totales: {stats['total_directories']}")
        print(f"💾 Tamaño total: {stats['total_size_bytes']} bytes")
        print(f"🔗 Handles abiertos: {stats['open_file_handles']}")
        print("-"*40)
    
    def print_directory_tree(self, directory: VirtualDirectory = None, prefix: str = "", level: int = 0):
        """Imprime el árbol de directorios"""
        if directory is None:
            directory = self.root_dir
            print("\n📁 ÁRBOL DEL SISTEMA DE ARCHIVOS")
            print("/")
            level = 0
            prefix = ""
        
        if level > 3:  # Limitar profundidad para evitar salida muy larga
            return
        
        # Mostrar subdirectorios
        subdirs = list(directory.subdirs.items())
        files = list(directory.files.items())
        
        for i, (name, subdir) in enumerate(subdirs):
            is_last_dir = (i == len(subdirs) - 1 and not files)
            current_prefix = "└── " if is_last_dir else "├── "
            print(f"{prefix}{current_prefix}📁 {name}/")
            
            next_prefix = prefix + ("    " if is_last_dir else "│   ")
            self.print_directory_tree(subdir, next_prefix, level + 1)
        
        # Mostrar archivos
        for i, (name, file) in enumerate(files):
            is_last = (i == len(files) - 1)
            current_prefix = "└── " if is_last else "├── "
            size_str = f" ({file.size}B)" if file.size > 0 else ""
            print(f"{prefix}{current_prefix}📄 {name}{size_str}")

# Instancia global del servicio de archivos
fs_service = FileSystemService()

def get_fs_service():
    """Obtiene la instancia global del servicio de archivos"""
    return fs_service