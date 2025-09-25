"""
REAL FILE SYSTEM SERVICE - Servicio de Sistema de Archivos REAL
===============================================================
Servicio híbrido que maneja archivos virtuales Y archivos reales.
Los archivos se crean tanto en memoria como en el disco duro.
"""

import os
import json
import time
import threading
from typing import Dict, List, Optional, Any
from kernel.microkernel import get_kernel

class RealVirtualFile:
    """Archivo que existe tanto virtual como realmente en disco"""
    def __init__(self, name: str, content: str = "", owner: str = "system", real_path: str = ""):
        self.name = name
        self.content = content
        self.owner = owner
        self.real_path = real_path  # Ruta real en disco
        self.created_at = time.time()
        self.modified_at = time.time()
        self.accessed_at = time.time()
        self.size = len(content.encode('utf-8'))
        self.permissions = "rw-rw-r--"
    
    def read(self, process_id: str) -> Optional[str]:
        """Lee el contenido del archivo (sincroniza desde disco)"""
        if not self._check_read_permission(process_id):
            print(f"❌ FS: {process_id} sin permisos de lectura para {self.name}")
            return None
        
        # Si existe archivo real, sincronizar contenido
        if self.real_path and os.path.exists(self.real_path):
            try:
                with open(self.real_path, 'r', encoding='utf-8') as f:
                    self.content = f.read()
                    self.size = len(self.content.encode('utf-8'))
            except Exception as e:
                print(f"⚠️  FS: Error leyendo archivo real {self.real_path}: {e}")
        
        self.accessed_at = time.time()
        print(f"📖 FS: {process_id} leyó {self.name} (virtual + disco)")
        return self.content
    
    def write(self, process_id: str, content: str, append: bool = False) -> bool:
        """Escribe contenido al archivo (virtual Y disco)"""
        if not self._check_write_permission(process_id):
            print(f"❌ FS: {process_id} sin permisos de escritura para {self.name}")
            return False
        
        # Actualizar contenido virtual
        if append:
            self.content += content
        else:
            self.content = content
        
        self.size = len(self.content.encode('utf-8'))
        self.modified_at = time.time()
        self.accessed_at = time.time()
        
        # Escribir al archivo real
        if self.real_path:
            try:
                mode = 'a' if append else 'w'
                with open(self.real_path, mode, encoding='utf-8') as f:
                    if append:
                        f.write(content)
                    else:
                        f.write(self.content)
                print(f"💾 FS: Archivo {self.name} guardado en disco: {self.real_path}")
            except Exception as e:
                print(f"❌ FS: Error escribiendo archivo real {self.real_path}: {e}")
                return False
        
        print(f"✏️  FS: {process_id} escribió en {self.name} ({self.size} bytes) [VIRTUAL + DISCO]")
        return True
    
    def _check_read_permission(self, process_id: str) -> bool:
        """Verifica permisos de lectura"""
        return self.owner == process_id or process_id == "system" or process_id == "admin"
    
    def _check_write_permission(self, process_id: str) -> bool:
        """Verifica permisos de escritura"""
        return self.owner == process_id or process_id == "system" or process_id == "admin"

class RealVirtualDirectory:
    """Directorio que maneja archivos virtuales y reales"""
    def __init__(self, name: str, owner: str = "system", real_path: str = ""):
        self.name = name
        self.owner = owner
        self.real_path = real_path
        self.files: Dict[str, RealVirtualFile] = {}
        self.subdirs: Dict[str, 'RealVirtualDirectory'] = {}
        self.created_at = time.time()
        self.permissions = "rwxrwxr-x"
        
        # Crear directorio real si no existe
        if self.real_path and not os.path.exists(self.real_path):
            try:
                os.makedirs(self.real_path, exist_ok=True)
                print(f"📁 FS: Directorio real creado: {self.real_path}")
            except Exception as e:
                print(f"❌ FS: Error creando directorio real {self.real_path}: {e}")
    
    def add_file(self, file: RealVirtualFile) -> bool:
        """Añade un archivo al directorio"""
        if file.name in self.files:
            return False
        
        self.files[file.name] = file
        return True
    
    def list_contents(self) -> List[str]:
        """Lista el contenido del directorio"""
        contents = []
        contents.extend([f"📁 {name}/" for name in self.subdirs.keys()])
        contents.extend([f"📄 {name}" for name in self.files.keys()])
        return contents

class RealFileSystemService:
    """
    Servicio de Sistema de Archivos HÍBRIDO
    Los archivos existen tanto virtualmente como realmente en disco
    """
    
    def __init__(self, real_base_path: str = "./microkernel_files"):
        self.name = "RealFileSystemService"
        self.version = "2.0"
        self.running = False
        self.failed = False
        
        # Configurar rutas
        self.real_base_path = os.path.abspath(real_base_path)
        
        # Crear directorio base si no existe
        os.makedirs(self.real_base_path, exist_ok=True)
        
        self.root_dir = RealVirtualDirectory("/", "system", self.real_base_path)
        self.current_dir = "/"
        self.file_handles: Dict[str, Dict] = {}
        self.fs_lock = threading.RLock()
        
        # Crear estructura básica
        self._create_basic_structure()
        
        print(f"📁 REAL_FS_SERVICE: Sistema híbrido inicializado")
        print(f"🗂️  REAL_FS_SERVICE: Archivos reales en: {self.real_base_path}")
    
    def _create_basic_structure(self):
        """Crea la estructura básica de directorios"""
        # Crear directorios básicos (virtuales y reales)
        home_path = os.path.join(self.real_base_path, "home")
        tmp_path = os.path.join(self.real_base_path, "tmp")
        etc_path = os.path.join(self.real_base_path, "etc")
        
        home_dir = RealVirtualDirectory("home", "system", home_path)
        tmp_dir = RealVirtualDirectory("tmp", "system", tmp_path)
        etc_dir = RealVirtualDirectory("etc", "system", etc_path)
        
        self.root_dir.subdirs["home"] = home_dir
        self.root_dir.subdirs["tmp"] = tmp_dir
        self.root_dir.subdirs["etc"] = etc_dir
        
        # Crear archivos básicos (virtuales y reales)
        readme_path = os.path.join(self.real_base_path, "README.txt")
        config_path = os.path.join(etc_path, "system.conf")
        
        readme = RealVirtualFile("README.txt", "Bienvenido al Sistema de Archivos HÍBRIDO\nArchivos reales + virtuales", "system", readme_path)
        config = RealVirtualFile("system.conf", "kernel_debug=true\nmax_processes=100\nreal_files=true", "system", config_path)
        
        # Escribir archivos reales inmediatamente
        readme.write("system", readme.content)
        config.write("system", config.content)
        
        self.root_dir.add_file(readme)
        etc_dir.add_file(config)
        
        print("📁 REAL_FS_SERVICE: Estructura básica creada (virtual + disco)")
    
    def start(self):
        """Inicia el servicio"""
        with self.fs_lock:
            if self.running:
                return True
            
            self.running = True
            print("🟢 REAL_FS_SERVICE: Servicio híbrido iniciado")
            return True
    
    def stop(self):
        """Detiene el servicio"""
        with self.fs_lock:
            self.running = False
            self.file_handles.clear()
            print("🔴 REAL_FS_SERVICE: Servicio híbrido detenido")
    
    def _check_service_health(self) -> bool:
        """Verifica si el servicio está funcional"""
        if self.failed:
            print("❌ REAL_FS_SERVICE: Servicio ha fallado - Operación rechazada")
            return False
        if not self.running:
            print("❌ REAL_FS_SERVICE: Servicio no está ejecutándose")
            return False
        return True
    
    def create_file(self, filename: str, content: str = "", owner: str = "system") -> bool:
        """Crea un archivo (virtual Y real)"""
        if not self._check_service_health():
            return False
        
        with self.fs_lock:
            if filename in self.root_dir.files:
                print(f"❌ FS: El archivo {filename} ya existe")
                return False
            
            # Crear archivo real
            real_path = os.path.join(self.real_base_path, filename)
            
            # Crear archivo híbrido
            virtual_file = RealVirtualFile(filename, content, owner, real_path)
            
            # Escribir contenido al disco
            success = virtual_file.write("system", content)
            if not success:
                return False
            
            # Añadir a la estructura virtual
            self.root_dir.add_file(virtual_file)
            
            print(f"✅ REAL_FS: Archivo creado: {filename}")
            print(f"🗂️  REAL_FS: Ruta real: {real_path}")
            return True
    
    def read_file(self, filename: str, process_id: str) -> Optional[str]:
        """Lee un archivo (sincroniza desde disco)"""
        if not self._check_service_health():
            return None
        
        with self.fs_lock:
            if filename not in self.root_dir.files:
                print(f"❌ FS: Archivo {filename} no encontrado")
                return None
            
            file_obj = self.root_dir.files[filename]
            return file_obj.read(process_id)
    
    def write_file(self, filename: str, content: str, process_id: str, append: bool = False) -> bool:
        """Escribe a un archivo (virtual Y disco)"""
        if not self._check_service_health():
            return False
        
        with self.fs_lock:
            if filename not in self.root_dir.files:
                print(f"❌ FS: Archivo {filename} no encontrado")
                return False
            
            file_obj = self.root_dir.files[filename]
            return file_obj.write(process_id, content, append)
    
    def list_directory(self, directory: str = "/") -> List[str]:
        """Lista el contenido de un directorio"""
        if not self._check_service_health():
            return []
        
        with self.fs_lock:
            return self.root_dir.list_contents()
    
    def delete_file(self, filename: str, process_id: str) -> bool:
        """Elimina un archivo (virtual Y real)"""
        if not self._check_service_health():
            return False
        
        with self.fs_lock:
            if filename not in self.root_dir.files:
                print(f"❌ FS: Archivo {filename} no encontrado")
                return False
            
            file_obj = self.root_dir.files[filename]
            
            # Verificar permisos
            if not file_obj._check_write_permission(process_id):
                print(f"❌ FS: {process_id} sin permisos para eliminar {filename}")
                return False
            
            # Eliminar archivo real
            if file_obj.real_path and os.path.exists(file_obj.real_path):
                try:
                    os.remove(file_obj.real_path)
                    print(f"🗑️ FS: Archivo real eliminado: {file_obj.real_path}")
                except Exception as e:
                    print(f"❌ FS: Error eliminando archivo real: {e}")
            
            # Eliminar de estructura virtual
            del self.root_dir.files[filename]
            
            print(f"✅ FS: Archivo {filename} eliminado completamente")
            return True
    
    def get_file_info(self, filename: str) -> Optional[Dict[str, Any]]:
        """Obtiene información de un archivo"""
        if not self._check_service_health():
            return None
        
        with self.fs_lock:
            if filename not in self.root_dir.files:
                return None
            
            file_obj = self.root_dir.files[filename]
            info = {
                'name': file_obj.name,
                'size': file_obj.size,
                'owner': file_obj.owner,
                'permissions': file_obj.permissions,
                'created_at': time.ctime(file_obj.created_at),
                'modified_at': time.ctime(file_obj.modified_at),
                'accessed_at': time.ctime(file_obj.accessed_at),
                'real_path': file_obj.real_path,
                'exists_on_disk': os.path.exists(file_obj.real_path) if file_obj.real_path else False
            }
            return info
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del sistema de archivos"""
        total_files = len(self.root_dir.files)
        total_size = sum(f.size for f in self.root_dir.files.values())
        
        real_files_count = 0
        for file_obj in self.root_dir.files.values():
            if file_obj.real_path and os.path.exists(file_obj.real_path):
                real_files_count += 1
        
        return {
            'service_name': self.name,
            'version': self.version,
            'running': self.running,
            'failed': self.failed,
            'total_files': total_files,
            'real_files': real_files_count,
            'total_size_bytes': total_size,
            'real_base_path': self.real_base_path,
            'current_directory': self.current_dir
        }