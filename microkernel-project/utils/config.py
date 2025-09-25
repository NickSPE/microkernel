"""
CONFIG UTILITY - Sistema de Configuración del Microkernel
=========================================================
Utilidad para gestionar la configuración del sistema
de manera centralizada y flexible.
"""

import json
import os
import time
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

class ConfigSection:
    """Sección de configuración"""
    
    def __init__(self, name: str, data: Dict[str, Any] = None):
        self.name = name
        self.data = data or {}
        self.modified = False
        self.last_update = time.time()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Obtiene un valor de configuración"""
        return self.data.get(key, default)
    
    def set(self, key: str, value: Any):
        """Establece un valor de configuración"""
        self.data[key] = value
        self.modified = True
        self.last_update = time.time()
    
    def has(self, key: str) -> bool:
        """Verifica si existe una clave"""
        return key in self.data
    
    def remove(self, key: str) -> bool:
        """Elimina una clave"""
        if key in self.data:
            del self.data[key]
            self.modified = True
            self.last_update = time.time()
            return True
        return False
    
    def keys(self) -> List[str]:
        """Obtiene todas las claves"""
        return list(self.data.keys())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la sección a diccionario"""
        return self.data.copy()

class ConfigManager:
    """
    Gestor de Configuración del Microkernel
    Maneja configuraciones del sistema de forma centralizada
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.config_file = None
            self.sections = {}
            self.auto_save = True
            self.backup_enabled = True
            self.created_at = time.time()
            
            # Cargar configuración por defecto
            self._load_default_config()
            
            ConfigManager._initialized = True
    
    def _load_default_config(self):
        """Carga la configuración por defecto del microkernel"""
        
        # Configuración del kernel
        kernel_config = ConfigSection("kernel", {
            "max_processes": 1000,
            "memory_limit": 1024 * 1024 * 512,  # 512 MB
            "process_time_slice": 10,  # ms
            "default_priority": 5,
            "enable_preemption": True,
            "debug_mode": False
        })
        
        # Configuración del planificador
        scheduler_config = ConfigSection("scheduler", {
            "algorithm": "round_robin",
            "time_quantum": 50,  # ms
            "max_priority": 10,
            "aging_enabled": True,
            "aging_factor": 1
        })
        
        # Configuración de IPC
        ipc_config = ConfigSection("ipc", {
            "max_message_size": 4096,  # bytes
            "max_shared_memory": 1024 * 1024,  # 1 MB
            "max_semaphores": 256,
            "max_pipes": 128,
            "message_timeout": 5.0  # segundos
        })
        
        # Configuración del sistema de archivos
        fs_config = ConfigSection("filesystem", {
            "max_file_size": 10 * 1024 * 1024,  # 10 MB
            "max_files": 10000,
            "max_directories": 1000,
            "case_sensitive": True,
            "auto_backup": True
        })
        
        # Configuración de red
        network_config = ConfigSection("network", {
            "max_connections": 100,
            "default_timeout": 30.0,  # segundos
            "max_packet_size": 65536,  # bytes
            "enable_dns": True,
            "dns_cache_size": 1000
        })
        
        # Configuración de seguridad
        security_config = ConfigSection("security", {
            "max_login_attempts": 3,
            "session_timeout": 3600,  # 1 hora
            "password_min_length": 6,
            "enable_audit": True,
            "audit_max_events": 10000
        })
        
        # Configuración de logging
        logging_config = ConfigSection("logging", {
            "level": "INFO",
            "max_entries": 10000,
            "log_to_file": True,
            "log_file": "microkernel.log",
            "console_output": True,
            "rotation_enabled": True,
            "max_file_size": 10 * 1024 * 1024  # 10 MB
        })
        
        # Configuración de aplicaciones
        apps_config = ConfigSection("applications", {
            "max_running_apps": 50,
            "auto_start": [],
            "resource_limits": {
                "memory_per_app": 10 * 1024 * 1024,  # 10 MB
                "cpu_time_limit": 60.0  # segundos
            }
        })
        
        # Configuración del sistema
        system_config = ConfigSection("system", {
            "system_name": "MicrokernelOS",
            "version": "1.0.0",
            "timezone": "UTC",
            "language": "es",
            "startup_delay": 2.0,  # segundos
            "shutdown_timeout": 30.0  # segundos
        })
        
        # Añadir todas las secciones
        self.sections.update({
            "kernel": kernel_config,
            "scheduler": scheduler_config,
            "ipc": ipc_config,
            "filesystem": fs_config,
            "network": network_config,
            "security": security_config,
            "logging": logging_config,
            "applications": apps_config,
            "system": system_config
        })
    
    def load_from_file(self, file_path: str) -> bool:
        """Carga configuración desde un archivo JSON"""
        try:
            self.config_file = file_path
            
            if not os.path.exists(file_path):
                print(f"⚠️  Archivo de configuración no encontrado: {file_path}")
                return False
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Cargar cada sección
            for section_name, section_data in data.items():
                if section_name in self.sections:
                    # Actualizar sección existente
                    self.sections[section_name].data.update(section_data)
                else:
                    # Crear nueva sección
                    self.sections[section_name] = ConfigSection(section_name, section_data)
                
                self.sections[section_name].modified = False
            
            print(f"✅ Configuración cargada desde {file_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error cargando configuración: {e}")
            return False
    
    def save_to_file(self, file_path: str = None) -> bool:
        """Guarda la configuración en un archivo JSON"""
        try:
            target_file = file_path or self.config_file
            
            if not target_file:
                print("❌ No se especificó archivo de destino")
                return False
            
            # Crear backup si está habilitado
            if self.backup_enabled and os.path.exists(target_file):
                backup_file = f"{target_file}.backup"
                try:
                    import shutil
                    shutil.copy2(target_file, backup_file)
                except:
                    pass  # Continuar aunque falle el backup
            
            # Preparar datos para guardar
            config_data = {}
            for section_name, section in self.sections.items():
                config_data[section_name] = section.to_dict()
            
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(target_file), exist_ok=True)
            
            # Guardar archivo
            with open(target_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            # Marcar secciones como no modificadas
            for section in self.sections.values():
                section.modified = False
            
            print(f"✅ Configuración guardada en {target_file}")
            return True
            
        except Exception as e:
            print(f"❌ Error guardando configuración: {e}")
            return False
    
    def get_section(self, section_name: str) -> Optional[ConfigSection]:
        """Obtiene una sección de configuración"""
        return self.sections.get(section_name)
    
    def create_section(self, section_name: str) -> ConfigSection:
        """Crea una nueva sección de configuración"""
        section = ConfigSection(section_name)
        self.sections[section_name] = section
        return section
    
    def has_section(self, section_name: str) -> bool:
        """Verifica si existe una sección"""
        return section_name in self.sections
    
    def remove_section(self, section_name: str) -> bool:
        """Elimina una sección"""
        if section_name in self.sections:
            del self.sections[section_name]
            return True
        return False
    
    def get_value(self, section_name: str, key: str, default: Any = None) -> Any:
        """Obtiene un valor de configuración (método de conveniencia)"""
        section = self.get_section(section_name)
        if section:
            return section.get(key, default)
        return default
    
    def set_value(self, section_name: str, key: str, value: Any):
        """Establece un valor de configuración (método de conveniencia)"""
        section = self.get_section(section_name)
        if not section:
            section = self.create_section(section_name)
        
        section.set(key, value)
        
        # Auto-guardado si está habilitado
        if self.auto_save and self.config_file:
            self.save_to_file()
    
    def get_kernel_config(self) -> Dict[str, Any]:
        """Obtiene la configuración del kernel"""
        section = self.get_section("kernel")
        return section.to_dict() if section else {}
    
    def get_scheduler_config(self) -> Dict[str, Any]:
        """Obtiene la configuración del planificador"""
        section = self.get_section("scheduler")
        return section.to_dict() if section else {}
    
    def get_ipc_config(self) -> Dict[str, Any]:
        """Obtiene la configuración de IPC"""
        section = self.get_section("ipc")
        return section.to_dict() if section else {}
    
    def get_security_config(self) -> Dict[str, Any]:
        """Obtiene la configuración de seguridad"""
        section = self.get_section("security")
        return section.to_dict() if section else {}
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Obtiene la configuración de logging"""
        section = self.get_section("logging")
        return section.to_dict() if section else {}
    
    def list_sections(self) -> List[str]:
        """Lista todas las secciones"""
        return list(self.sections.keys())
    
    def get_modified_sections(self) -> List[str]:
        """Obtiene las secciones modificadas"""
        return [name for name, section in self.sections.items() if section.modified]
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de la configuración"""
        total_keys = sum(len(section.data) for section in self.sections.values())
        modified_count = len(self.get_modified_sections())
        
        return {
            "total_sections": len(self.sections),
            "total_keys": total_keys,
            "modified_sections": modified_count,
            "config_file": self.config_file,
            "auto_save": self.auto_save,
            "backup_enabled": self.backup_enabled,
            "created_at": self.created_at,
            "age_seconds": time.time() - self.created_at
        }
    
    def validate_config(self) -> Dict[str, List[str]]:
        """Valida la configuración y devuelve errores/advertencias"""
        errors = []
        warnings = []
        
        # Validar configuración del kernel
        kernel = self.get_section("kernel")
        if kernel:
            if kernel.get("max_processes", 0) <= 0:
                errors.append("kernel.max_processes debe ser mayor que 0")
            if kernel.get("memory_limit", 0) <= 0:
                errors.append("kernel.memory_limit debe ser mayor que 0")
            if kernel.get("process_time_slice", 0) <= 0:
                warnings.append("kernel.process_time_slice muy pequeño")
        
        # Validar configuración del planificador
        scheduler = self.get_section("scheduler")
        if scheduler:
            valid_algorithms = ["round_robin", "priority", "fifo"]
            if scheduler.get("algorithm") not in valid_algorithms:
                errors.append(f"scheduler.algorithm debe ser uno de: {valid_algorithms}")
        
        # Validar configuración de IPC
        ipc = self.get_section("ipc")
        if ipc:
            if ipc.get("max_message_size", 0) <= 0:
                errors.append("ipc.max_message_size debe ser mayor que 0")
            if ipc.get("message_timeout", 0) <= 0:
                warnings.append("ipc.message_timeout muy pequeño")
        
        # Validar configuración de seguridad
        security = self.get_section("security")
        if security:
            if security.get("password_min_length", 0) < 4:
                warnings.append("security.password_min_length muy pequeño (recomendado >= 6)")
            if security.get("session_timeout", 0) <= 0:
                errors.append("security.session_timeout debe ser mayor que 0")
        
        return {
            "errors": errors,
            "warnings": warnings,
            "is_valid": len(errors) == 0
        }
    
    def reset_to_defaults(self):
        """Restaura la configuración a valores por defecto"""
        self.sections.clear()
        self._load_default_config()
        print("🔄 Configuración restaurada a valores por defecto")
    
    def export_config(self, file_path: str, format_type: str = "json") -> bool:
        """Exporta la configuración en diferentes formatos"""
        try:
            if format_type.lower() == "json":
                return self.save_to_file(file_path)
            
            elif format_type.lower() == "ini":
                # Exportar en formato INI
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("# Configuración del Microkernel\n")
                    f.write(f"# Generado: {time.ctime()}\n\n")
                    
                    for section_name, section in self.sections.items():
                        f.write(f"[{section_name}]\n")
                        for key, value in section.data.items():
                            f.write(f"{key} = {value}\n")
                        f.write("\n")
                
                print(f"✅ Configuración exportada (INI) a {file_path}")
                return True
            
            elif format_type.lower() == "yaml":
                # Exportar en formato YAML (simplificado)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("# Configuración del Microkernel\n")
                    f.write(f"# Generado: {time.ctime()}\n\n")
                    
                    for section_name, section in self.sections.items():
                        f.write(f"{section_name}:\n")
                        for key, value in section.data.items():
                            f.write(f"  {key}: {value}\n")
                        f.write("\n")
                
                print(f"✅ Configuración exportada (YAML) a {file_path}")
                return True
            
            else:
                print(f"❌ Formato no soportado: {format_type}")
                return False
                
        except Exception as e:
            print(f"❌ Error exportando configuración: {e}")
            return False

# Instancia global del gestor de configuración
_global_config = None

def get_config() -> ConfigManager:
    """Obtiene la instancia global del gestor de configuración"""
    global _global_config
    if _global_config is None:
        _global_config = ConfigManager()
    return _global_config

def load_config(file_path: str) -> bool:
    """Carga configuración desde archivo"""
    return get_config().load_from_file(file_path)

def save_config(file_path: str = None) -> bool:
    """Guarda configuración en archivo"""
    return get_config().save_to_file(file_path)

# Funciones de conveniencia
def get_kernel_config() -> Dict[str, Any]:
    return get_config().get_kernel_config()

def get_scheduler_config() -> Dict[str, Any]:
    return get_config().get_scheduler_config()

def get_ipc_config() -> Dict[str, Any]:
    return get_config().get_ipc_config()

def get_security_config() -> Dict[str, Any]:
    return get_config().get_security_config()

def get_logging_config() -> Dict[str, Any]:
    return get_config().get_logging_config()

if __name__ == "__main__":
    # Demo del gestor de configuración
    print("🎯 Demostración del Sistema de Configuración")
    print("=" * 50)
    
    config = get_config()
    
    # Mostrar configuración por defecto
    print("\n📋 SECCIONES DE CONFIGURACIÓN:")
    for section_name in config.list_sections():
        section = config.get_section(section_name)
        print(f"  • {section_name}: {len(section.data)} claves")
    
    # Mostrar algunos valores
    print("\n⚙️  CONFIGURACIÓN DEL KERNEL:")
    kernel_config = config.get_kernel_config()
    for key, value in list(kernel_config.items())[:5]:
        print(f"  {key}: {value}")
    
    # Modificar algunos valores
    config.set_value("kernel", "debug_mode", True)
    config.set_value("system", "language", "en")
    
    # Validar configuración
    print("\n✅ VALIDACIÓN:")
    validation = config.validate_config()
    print(f"  Válida: {validation['is_valid']}")
    print(f"  Errores: {len(validation['errors'])}")
    print(f"  Advertencias: {len(validation['warnings'])}")
    
    # Mostrar estadísticas
    print("\n📊 ESTADÍSTICAS:")
    stats = config.get_stats()
    for key, value in stats.items():
        if key != 'created_at':
            print(f"  {key}: {value}")
    
    # Guardar configuración
    config.save_to_file("microkernel_config.json")
    
    print("\n✅ Demostración completada")