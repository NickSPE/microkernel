"""
LOGGER UTILITY - Sistema de Logging del Microkernel
===================================================
Utilidad para registrar eventos, errores y actividades
del sistema de manera centralizada.
"""

import time
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

class LogLevel(Enum):
    """Niveles de logging"""
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4

class LogFormatter:
    """Formateador de mensajes de log"""
    
    @staticmethod
    def format_message(level: LogLevel, source: str, message: str, 
                      timestamp: float = None) -> str:
        """Formatea un mensaje de log"""
        if timestamp is None:
            timestamp = time.time()
        
        dt = datetime.fromtimestamp(timestamp)
        time_str = dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # Milisegundos
        
        level_symbols = {
            LogLevel.DEBUG: "🐛",
            LogLevel.INFO: "ℹ️ ",
            LogLevel.WARNING: "⚠️ ",
            LogLevel.ERROR: "❌",
            LogLevel.CRITICAL: "💥"
        }
        
        symbol = level_symbols.get(level, "📝")
        level_name = level.name.ljust(8)
        source_name = source.ljust(15)
        
        return f"[{time_str}] {symbol} {level_name} {source_name} | {message}"

class LogEntry:
    """Entrada de log"""
    
    def __init__(self, level: LogLevel, source: str, message: str, 
                 data: Dict[str, Any] = None):
        self.timestamp = time.time()
        self.level = level
        self.source = source
        self.message = message
        self.data = data or {}
        self.thread_id = os.getpid()  # Simulación de thread ID
    
    def __str__(self):
        return LogFormatter.format_message(self.level, self.source, 
                                         self.message, self.timestamp)

class Logger:
    """
    Sistema de Logging del Microkernel
    Proporciona logging centralizado para todo el sistema
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.log_entries = []
            self.max_entries = 10000
            self.min_level = LogLevel.INFO
            self.file_path = None
            self.file_handle = None
            self.console_output = True
            self.startup_time = time.time()
            
            # Estadísticas
            self.stats = {
                'total_logs': 0,
                'by_level': {level: 0 for level in LogLevel},
                'by_source': {},
                'errors_last_hour': 0,
                'last_error_time': None
            }
            
            Logger._initialized = True
    
    def configure(self, min_level: LogLevel = LogLevel.INFO, 
                  max_entries: int = 10000, log_file: str = None,
                  console_output: bool = True):
        """Configura el logger"""
        self.min_level = min_level
        self.max_entries = max_entries
        self.console_output = console_output
        
        if log_file:
            self.set_log_file(log_file)
        
        self.info("LOGGER", f"Logger configurado - Nivel: {min_level.name}, "
                           f"Entradas máximas: {max_entries}")
    
    def set_log_file(self, file_path: str):
        """Establece el archivo de log"""
        try:
            # Cerrar archivo anterior si existe
            if self.file_handle:
                self.file_handle.close()
            
            self.file_path = file_path
            
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Abrir archivo en modo append
            self.file_handle = open(file_path, 'a', encoding='utf-8')
            
            self.info("LOGGER", f"Archivo de log establecido: {file_path}")
            
        except Exception as e:
            self.error("LOGGER", f"Error estableciendo archivo de log: {e}")
    
    def log(self, level: LogLevel, source: str, message: str, 
            data: Dict[str, Any] = None):
        """Registra un mensaje de log"""
        if level.value < self.min_level.value:
            return  # Filtrar por nivel mínimo
        
        # Crear entrada de log
        entry = LogEntry(level, source, message, data)
        
        # Añadir a la lista (con límite)
        self.log_entries.append(entry)
        if len(self.log_entries) > self.max_entries:
            self.log_entries.pop(0)  # Remover el más antiguo
        
        # Actualizar estadísticas
        self._update_stats(entry)
        
        # Salida por consola
        if self.console_output:
            print(str(entry))
        
        # Salida a archivo
        if self.file_handle:
            try:
                self.file_handle.write(str(entry) + '\n')
                self.file_handle.flush()
            except Exception as e:
                print(f"❌ Error escribiendo al archivo de log: {e}")
    
    def _update_stats(self, entry: LogEntry):
        """Actualiza las estadísticas del logger"""
        self.stats['total_logs'] += 1
        self.stats['by_level'][entry.level] += 1
        
        if entry.source in self.stats['by_source']:
            self.stats['by_source'][entry.source] += 1
        else:
            self.stats['by_source'][entry.source] = 1
        
        # Contar errores de la última hora
        if entry.level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            current_time = time.time()
            if (self.stats['last_error_time'] is None or 
                current_time - self.stats['last_error_time'] < 3600):
                self.stats['errors_last_hour'] += 1
            else:
                self.stats['errors_last_hour'] = 1
            
            self.stats['last_error_time'] = current_time
    
    # Métodos de conveniencia para cada nivel
    def debug(self, source: str, message: str, data: Dict[str, Any] = None):
        """Log nivel DEBUG"""
        self.log(LogLevel.DEBUG, source, message, data)
    
    def info(self, source: str, message: str, data: Dict[str, Any] = None):
        """Log nivel INFO"""
        self.log(LogLevel.INFO, source, message, data)
    
    def warning(self, source: str, message: str, data: Dict[str, Any] = None):
        """Log nivel WARNING"""
        self.log(LogLevel.WARNING, source, message, data)
    
    def error(self, source: str, message: str, data: Dict[str, Any] = None):
        """Log nivel ERROR"""
        self.log(LogLevel.ERROR, source, message, data)
    
    def critical(self, source: str, message: str, data: Dict[str, Any] = None):
        """Log nivel CRITICAL"""
        self.log(LogLevel.CRITICAL, source, message, data)
    
    # Métodos de consulta
    def get_recent_logs(self, count: int = 50, level: LogLevel = None) -> List[LogEntry]:
        """Obtiene los logs más recientes"""
        logs = self.log_entries[-count:] if count else self.log_entries[:]
        
        if level:
            logs = [entry for entry in logs if entry.level == level]
        
        return logs
    
    def get_logs_by_source(self, source: str, count: int = None) -> List[LogEntry]:
        """Obtiene logs de una fuente específica"""
        logs = [entry for entry in self.log_entries if entry.source == source]
        
        if count:
            logs = logs[-count:]
        
        return logs
    
    def get_logs_by_level(self, level: LogLevel, count: int = None) -> List[LogEntry]:
        """Obtiene logs de un nivel específico"""
        logs = [entry for entry in self.log_entries if entry.level == level]
        
        if count:
            logs = logs[-count:]
        
        return logs
    
    def get_logs_since(self, timestamp: float) -> List[LogEntry]:
        """Obtiene logs desde un timestamp"""
        return [entry for entry in self.log_entries 
                if entry.timestamp >= timestamp]
    
    def search_logs(self, query: str, case_sensitive: bool = False) -> List[LogEntry]:
        """Busca en los logs por texto"""
        if not case_sensitive:
            query = query.lower()
        
        results = []
        for entry in self.log_entries:
            message = entry.message if case_sensitive else entry.message.lower()
            source = entry.source if case_sensitive else entry.source.lower()
            
            if query in message or query in source:
                results.append(entry)
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del logger"""
        uptime = time.time() - self.startup_time
        
        stats = self.stats.copy()
        stats.update({
            'uptime_seconds': uptime,
            'uptime_formatted': self._format_uptime(uptime),
            'total_entries': len(self.log_entries),
            'memory_usage_estimate': len(self.log_entries) * 200,  # bytes aprox
            'top_sources': self._get_top_sources(5),
            'avg_logs_per_minute': self.stats['total_logs'] / (uptime / 60) if uptime > 0 else 0
        })
        
        return stats
    
    def _format_uptime(self, seconds: float) -> str:
        """Formatea el tiempo de actividad"""
        hours, remainder = divmod(int(seconds), 3600)
        minutes, secs = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def _get_top_sources(self, count: int) -> List[tuple]:
        """Obtiene las fuentes más activas"""
        sorted_sources = sorted(self.stats['by_source'].items(), 
                               key=lambda x: x[1], reverse=True)
        return sorted_sources[:count]
    
    def clear_logs(self):
        """Limpia todos los logs"""
        count = len(self.log_entries)
        self.log_entries.clear()
        
        # Reiniciar algunas estadísticas
        self.stats['by_level'] = {level: 0 for level in LogLevel}
        self.stats['by_source'].clear()
        self.stats['total_logs'] = 0
        
        self.info("LOGGER", f"Logs limpiados - {count} entradas eliminadas")
    
    def export_logs(self, file_path: str, format_type: str = "text") -> bool:
        """Exporta logs a un archivo"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                if format_type.lower() == "json":
                    import json
                    logs_data = []
                    for entry in self.log_entries:
                        logs_data.append({
                            'timestamp': entry.timestamp,
                            'level': entry.level.name,
                            'source': entry.source,
                            'message': entry.message,
                            'data': entry.data
                        })
                    json.dump(logs_data, f, indent=2)
                
                else:  # text format
                    f.write(f"# LOGS EXPORTADOS DEL MICROKERNEL\n")
                    f.write(f"# Fecha de exportación: {datetime.now()}\n")
                    f.write(f"# Total de entradas: {len(self.log_entries)}\n\n")
                    
                    for entry in self.log_entries:
                        f.write(str(entry) + '\n')
            
            self.info("LOGGER", f"Logs exportados a {file_path}")
            return True
            
        except Exception as e:
            self.error("LOGGER", f"Error exportando logs: {e}")
            return False
    
    def shutdown(self):
        """Cierra el logger correctamente"""
        if self.file_handle:
            try:
                self.info("LOGGER", "Logger cerrándose...")
                self.file_handle.close()
                self.file_handle = None
            except Exception as e:
                print(f"Error cerrando archivo de log: {e}")
        
        self.console_output = False

# Instancia global del logger
_global_logger = None

def get_logger() -> Logger:
    """Obtiene la instancia global del logger"""
    global _global_logger
    if _global_logger is None:
        _global_logger = Logger()
    return _global_logger

def configure_logger(min_level: LogLevel = LogLevel.INFO, 
                    max_entries: int = 10000, log_file: str = None,
                    console_output: bool = True):
    """Configura el logger global"""
    logger = get_logger()
    logger.configure(min_level, max_entries, log_file, console_output)

# Funciones de conveniencia globales
def log_debug(source: str, message: str, data: Dict[str, Any] = None):
    get_logger().debug(source, message, data)

def log_info(source: str, message: str, data: Dict[str, Any] = None):
    get_logger().info(source, message, data)

def log_warning(source: str, message: str, data: Dict[str, Any] = None):
    get_logger().warning(source, message, data)

def log_error(source: str, message: str, data: Dict[str, Any] = None):
    get_logger().error(source, message, data)

def log_critical(source: str, message: str, data: Dict[str, Any] = None):
    get_logger().critical(source, message, data)

if __name__ == "__main__":
    # Demo del logger
    print("🎯 Demostración del Sistema de Logging")
    print("=" * 50)
    
    # Configurar logger
    configure_logger(LogLevel.DEBUG, log_file="system.log")
    
    logger = get_logger()
    
    # Generar algunos logs de ejemplo
    logger.info("SYSTEM", "Sistema iniciado correctamente")
    logger.debug("KERNEL", "Cargando configuración inicial")
    logger.warning("MEMORY", "Uso de memoria alto: 85%")
    logger.error("NETWORK", "Error de conexión temporal")
    logger.critical("FILESYSTEM", "Error crítico en disco")
    
    # Mostrar estadísticas
    print("\n📊 ESTADÍSTICAS:")
    stats = logger.get_stats()
    for key, value in stats.items():
        if key != 'by_source':
            print(f"  {key}: {value}")
    
    print("\n🔍 LOGS RECIENTES:")
    recent = logger.get_recent_logs(3)
    for entry in recent:
        print(f"  {entry}")
    
    print("\n❌ LOGS DE ERROR:")
    errors = logger.get_logs_by_level(LogLevel.ERROR)
    for entry in errors:
        print(f"  {entry}")
    
    # Limpiar
    logger.shutdown()