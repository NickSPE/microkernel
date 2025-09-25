"""
SECURITY SERVICE - Servicio de Seguridad del Microkernel
========================================================
Proporciona autenticación, autorización y auditoría
para el sistema operativo microkernel.
"""

import time
import hashlib
import secrets
import threading
from typing import Dict, List, Optional, Set, Any
from enum import Enum

class SecurityLevel(Enum):
    """Niveles de seguridad"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class AuditEventType(Enum):
    """Tipos de eventos de auditoría"""
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"
    PERMISSION_CHANGED = "permission_changed"
    USER_CREATED = "user_created"
    USER_DELETED = "user_deleted"
    SECURITY_VIOLATION = "security_violation"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"

class User:
    """Representa un usuario del sistema"""
    
    def __init__(self, username: str, password_hash: str, permissions: Set[str] = None):
        self.username = username
        self.password_hash = password_hash
        self.permissions = permissions or set()
        self.created_at = time.time()
        self.last_login = None
        self.failed_login_attempts = 0
        self.is_locked = False
        self.session_tokens: Set[str] = set()
        self.security_level = SecurityLevel.MEDIUM
    
    def check_password(self, password: str) -> bool:
        """Verifica la contraseña del usuario"""
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        return password_hash == self.password_hash
    
    def has_permission(self, permission: str) -> bool:
        """Verifica si el usuario tiene un permiso específico"""
        return permission in self.permissions or "admin_access" in self.permissions
    
    def add_permission(self, permission: str):
        """Añade un permiso al usuario"""
        self.permissions.add(permission)
    
    def remove_permission(self, permission: str):
        """Elimina un permiso del usuario"""
        self.permissions.discard(permission)
    
    def lock_account(self):
        """Bloquea la cuenta del usuario"""
        self.is_locked = True
    
    def unlock_account(self):
        """Desbloquea la cuenta del usuario"""
        self.is_locked = False
        self.failed_login_attempts = 0

class AuditEvent:
    """Evento de auditoría"""
    
    def __init__(self, event_type: AuditEventType, username: str = None, 
                 details: str = None, data: Dict[str, Any] = None):
        self.timestamp = time.time()
        self.event_type = event_type
        self.username = username
        self.details = details or ""
        self.data = data or {}
        self.event_id = self._generate_event_id()
    
    def _generate_event_id(self) -> str:
        """Genera un ID único para el evento"""
        return f"audit_{int(self.timestamp)}_{secrets.token_hex(4)}"
    
    def __str__(self):
        time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.timestamp))
        user_str = f" [{self.username}]" if self.username else ""
        return f"[{time_str}]{user_str} {self.event_type.value}: {self.details}"

class SecurityService:
    """
    Servicio de Seguridad del Sistema
    Maneja autenticación, autorización y auditoría
    """
    
    def __init__(self):
        self.name = "SecurityService"
        self.version = "1.0"
        self.running = False
        self.failed = False  # Para simulación de fallos
        self.users: Dict[str, User] = {}
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.audit_log: List[AuditEvent] = []
        self.security_policy = {
            "max_failed_attempts": 3,
            "session_timeout": 3600,  # 1 hora
            "password_min_length": 6,
            "require_strong_passwords": False,
            "audit_level": "HIGH",
            "max_concurrent_sessions": 5
        }
        self.security_stats = {
            "total_logins": 0,
            "failed_logins": 0,
            "active_sessions": 0,
            "blocked_accounts": 0,
            "audit_events": 0,
            "access_denied_count": 0,
            "security_violations": 0
        }
        self.security_lock = threading.RLock()
        self.monitoring_thread: Optional[threading.Thread] = None
        
        # Crear usuarios por defecto
        self._create_default_users()
        
        print("🔒 SECURITY_SERVICE: Servicio de seguridad inicializado")
    
    def _create_default_users(self):
        """Crea usuarios por defecto del sistema"""
        # Usuario administrador
        admin_hash = hashlib.sha256("admin123".encode()).hexdigest()
        admin = User("admin", admin_hash, {"admin_access", "system_control", "file_write", "file_read"})
        admin.security_level = SecurityLevel.HIGH
        self.users["admin"] = admin
        
        # Usuario normal
        user_hash = hashlib.sha256("user123".encode()).hexdigest()
        user = User("user", user_hash, {"file_read", "file_write"})
        self.users["user"] = user
        
        # Usuario invitado
        guest_hash = hashlib.sha256("guest".encode()).hexdigest()
        guest = User("guest", guest_hash, {"file_read"})
        guest.security_level = SecurityLevel.LOW
        self.users["guest"] = guest
        
        print(f"🔒 SECURITY: {len(self.users)} usuarios por defecto creados")
    
    def _check_service_health(self) -> bool:
        """Verifica si el servicio está en estado funcional"""
        if self.failed:
            print("❌ SECURITY_SERVICE: Servicio ha fallado - Operación rechazada")
            return False
        
        if not self.running:
            print("⚠️  SECURITY_SERVICE: Servicio no está iniciado")
            return False
            
        return True
    
    def start(self):
        """Inicia el servicio de seguridad"""
        with self.security_lock:
            if self.running:
                return True
            
            self.running = True
            
            # Iniciar monitoreo de seguridad
            self.monitoring_thread = threading.Thread(target=self._security_monitoring_loop)
            self.monitoring_thread.daemon = True
            self.monitoring_thread.start()
            
            print("🟢 SECURITY_SERVICE: Servicio de seguridad iniciado")
            return True
    
    def stop(self):
        """Detiene el servicio de seguridad"""
        with self.security_lock:
            self.running = False
            
            # Cerrar todas las sesiones
            for session_token in list(self.active_sessions.keys()):
                self.logout(session_token)
            
            print("🔴 SECURITY_SERVICE: Servicio de seguridad detenido")
    
    def _security_monitoring_loop(self):
        """Bucle de monitoreo de seguridad"""
        while self.running:
            try:
                # Verificar sesiones expiradas
                self._check_expired_sessions()
                
                # Detectar actividad sospechosa
                self._detect_suspicious_activity()
                
                # Limpiar logs antiguos
                self._cleanup_old_logs()
                
                # Pausa
                time.sleep(30)  # Verificar cada 30 segundos
                
            except Exception as e:
                print(f"❌ SECURITY MONITOR ERROR: {e}")
    
    def _check_expired_sessions(self):
        """Verifica y cierra sesiones expiradas"""
        current_time = time.time()
        expired_sessions = []
        
        for token, session_data in self.active_sessions.items():
            if current_time - session_data['created_at'] > self.security_policy['session_timeout']:
                expired_sessions.append(token)
        
        for token in expired_sessions:
            self.logout(token)
            self._log_audit_event(
                AuditEventType.LOGOUT,
                details="Sesión expirada automáticamente"
            )
    
    def _detect_suspicious_activity(self):
        """Detecta actividad sospechosa en el sistema"""
        # Verificar múltiples intentos de login fallidos
        recent_failures = [event for event in self.audit_log[-100:]
                          if event.event_type == AuditEventType.LOGIN_FAILURE
                          and time.time() - event.timestamp < 300]  # Últimos 5 minutos
        
        if len(recent_failures) > 10:
            self._log_audit_event(
                AuditEventType.SUSPICIOUS_ACTIVITY,
                details=f"Múltiples intentos de login fallidos detectados: {len(recent_failures)}"
            )
    
    def _cleanup_old_logs(self):
        """Limpia logs antiguos para evitar uso excesivo de memoria"""
        max_logs = 10000
        if len(self.audit_log) > max_logs:
            # Mantener solo los más recientes
            self.audit_log = self.audit_log[-max_logs:]
    
    # ==================== AUTENTICACIÓN ====================
    
    def create_user(self, username: str, password: str, permissions: List[str] = None) -> bool:
        """Crea un nuevo usuario"""
        with self.security_lock:
            if username in self.users:
                print(f"❌ SECURITY: Usuario {username} ya existe")
                return False
            
            # Validar contraseña
            if not self._validate_password(password):
                print(f"❌ SECURITY: Contraseña no cumple políticas de seguridad")
                return False
            
            # Crear usuario
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            user = User(username, password_hash, set(permissions or []))
            self.users[username] = user
            
            # Log de auditoría
            self._log_audit_event(
                AuditEventType.USER_CREATED,
                username,
                f"Usuario creado con permisos: {permissions or []}"
            )
            
            print(f"✅ SECURITY: Usuario {username} creado")
            return True
    
    def delete_user(self, username: str, admin_token: str) -> bool:
        """Elimina un usuario (requiere permisos de admin)"""
        with self.security_lock:
            if not self.check_permission(admin_token, "admin_access"):
                self._log_audit_event(
                    AuditEventType.ACCESS_DENIED,
                    username,
                    "Intento de eliminar usuario sin permisos"
                )
                return False
            
            if username not in self.users:
                return False
            
            # Cerrar todas las sesiones del usuario
            user = self.users[username]
            for token in list(user.session_tokens):
                self.logout(token)
            
            del self.users[username]
            
            self._log_audit_event(
                AuditEventType.USER_DELETED,
                username,
                "Usuario eliminado por administrador"
            )
            
            print(f"🗑️ SECURITY: Usuario {username} eliminado")
            return True
    
    def login(self, username: str, password: str) -> Optional[str]:
        """Autenticar usuario y crear sesión"""
        if not self._check_service_health():
            return None
            
        with self.security_lock:
            if username not in self.users:
                self._log_audit_event(
                    AuditEventType.LOGIN_FAILURE,
                    username,
                    "Usuario no encontrado"
                )
                self.security_stats['failed_logins'] += 1
                return None
            
            user = self.users[username]
            
            # Verificar si la cuenta está bloqueada
            if user.is_locked:
                self._log_audit_event(
                    AuditEventType.LOGIN_FAILURE,
                    username,
                    "Cuenta bloqueada"
                )
                return None
            
            # Verificar contraseña
            if not user.check_password(password):
                user.failed_login_attempts += 1
                
                # Bloquear cuenta si supera intentos máximos
                if user.failed_login_attempts >= self.security_policy['max_failed_attempts']:
                    user.lock_account()
                    self.security_stats['blocked_accounts'] += 1
                    self._log_audit_event(
                        AuditEventType.SECURITY_VIOLATION,
                        username,
                        "Cuenta bloqueada por múltiples intentos fallidos"
                    )
                
                self._log_audit_event(
                    AuditEventType.LOGIN_FAILURE,
                    username,
                    f"Contraseña incorrecta (intento {user.failed_login_attempts})"
                )
                self.security_stats['failed_logins'] += 1
                return None
            
            # Login exitoso
            user.failed_login_attempts = 0
            user.last_login = time.time()
            
            # Crear token de sesión
            session_token = self._generate_session_token()
            session_data = {
                'username': username,
                'created_at': time.time(),
                'last_activity': time.time(),
                'permissions': user.permissions.copy(),
                'security_level': user.security_level
            }
            
            self.active_sessions[session_token] = session_data
            user.session_tokens.add(session_token)
            
            self.security_stats['total_logins'] += 1
            self.security_stats['active_sessions'] = len(self.active_sessions)
            
            self._log_audit_event(
                AuditEventType.LOGIN_SUCCESS,
                username,
                f"Login exitoso desde token {session_token[:8]}..."
            )
            
            print(f"🔓 SECURITY: Login exitoso para {username}")
            return session_token
    
    def logout(self, session_token: str) -> bool:
        """Cerrar sesión"""
        with self.security_lock:
            if session_token not in self.active_sessions:
                return False
            
            session_data = self.active_sessions[session_token]
            username = session_data['username']
            
            # Remover token del usuario
            if username in self.users:
                self.users[username].session_tokens.discard(session_token)
            
            # Remover sesión activa
            del self.active_sessions[session_token]
            self.security_stats['active_sessions'] = len(self.active_sessions)
            
            self._log_audit_event(
                AuditEventType.LOGOUT,
                username,
                "Logout exitoso"
            )
            
            print(f"🔒 SECURITY: Logout para {username}")
            return True
    
    def validate_session(self, session_token: str) -> Optional[str]:
        """Validar token de sesión y retornar username"""
        with self.security_lock:
            if session_token not in self.active_sessions:
                return None
            
            session_data = self.active_sessions[session_token]
            
            # Verificar si la sesión ha expirado
            current_time = time.time()
            if current_time - session_data['created_at'] > self.security_policy['session_timeout']:
                self.logout(session_token)
                return None
            
            # Actualizar última actividad
            session_data['last_activity'] = current_time
            
            return session_data['username']
    
    def _generate_session_token(self) -> str:
        """Genera un token de sesión seguro"""
        return f"session_{int(time.time())}_{secrets.token_hex(16)}"
    
    def _validate_password(self, password: str) -> bool:
        """Valida una contraseña según políticas de seguridad"""
        if len(password) < self.security_policy['password_min_length']:
            return False
        
        if self.security_policy['require_strong_passwords']:
            # Verificar complejidad (mayúsculas, números, símbolos)
            has_upper = any(c.isupper() for c in password)
            has_digit = any(c.isdigit() for c in password)
            has_symbol = any(c in "!@#$%^&*()_+-=" for c in password)
            
            return has_upper and has_digit and has_symbol
        
        return True
    
    # ==================== AUTORIZACIÓN ====================
    
    def check_permission(self, session_token: str, permission: str) -> bool:
        """Verifica si una sesión tiene un permiso específico"""
        with self.security_lock:
            if session_token not in self.active_sessions:
                self._log_audit_event(
                    AuditEventType.ACCESS_DENIED,
                    None,
                    f"Token de sesión inválido para permiso {permission}"
                )
                self.security_stats['access_denied_count'] += 1
                return False
            
            session_data = self.active_sessions[session_token]
            username = session_data['username']
            
            if permission in session_data['permissions'] or "admin_access" in session_data['permissions']:
                self._log_audit_event(
                    AuditEventType.ACCESS_GRANTED,
                    username,
                    f"Acceso concedido para {permission}"
                )
                return True
            else:
                self._log_audit_event(
                    AuditEventType.ACCESS_DENIED,
                    username,
                    f"Acceso denegado para {permission}"
                )
                self.security_stats['access_denied_count'] += 1
                return False
    
    def grant_permission(self, username: str, permission: str, admin_token: str) -> bool:
        """Otorga un permiso a un usuario (requiere admin)"""
        with self.security_lock:
            if not self.check_permission(admin_token, "admin_access"):
                return False
            
            if username not in self.users:
                return False
            
            user = self.users[username]
            user.add_permission(permission)
            
            self._log_audit_event(
                AuditEventType.PERMISSION_CHANGED,
                username,
                f"Permiso {permission} otorgado"
            )
            
            print(f"✅ SECURITY: Permiso {permission} otorgado a {username}")
            return True
    
    def revoke_permission(self, username: str, permission: str, admin_token: str) -> bool:
        """Revoca un permiso de un usuario (requiere admin)"""
        with self.security_lock:
            if not self.check_permission(admin_token, "admin_access"):
                return False
            
            if username not in self.users:
                return False
            
            user = self.users[username]
            user.remove_permission(permission)
            
            self._log_audit_event(
                AuditEventType.PERMISSION_CHANGED,
                username,
                f"Permiso {permission} revocado"
            )
            
            print(f"❌ SECURITY: Permiso {permission} revocado de {username}")
            return True
    
    # ==================== AUDITORÍA ====================
    
    def _log_audit_event(self, event_type: AuditEventType, username: str = None, 
                        details: str = None, data: Dict[str, Any] = None):
        """Registra un evento de auditoría"""
        event = AuditEvent(event_type, username, details, data)
        self.audit_log.append(event)
        self.security_stats['audit_events'] += 1
        
        # Imprimir eventos importantes
        if event_type in [AuditEventType.LOGIN_FAILURE, AuditEventType.ACCESS_DENIED, 
                         AuditEventType.SECURITY_VIOLATION]:
            print(f"🚨 AUDIT: {event}")
    
    def get_audit_logs(self, limit: int = 100, event_type: AuditEventType = None,
                      username: str = None) -> List[AuditEvent]:
        """Obtiene logs de auditoría"""
        with self.security_lock:
            logs = self.audit_log[:]
            
            # Filtrar por tipo de evento
            if event_type:
                logs = [log for log in logs if log.event_type == event_type]
            
            # Filtrar por usuario
            if username:
                logs = [log for log in logs if log.username == username]
            
            # Limitar resultados
            return logs[-limit:] if limit else logs
    
    def export_audit_logs(self, file_path: str) -> bool:
        """Exporta logs de auditoría a un archivo"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("# SECURITY AUDIT LOG\n")
                f.write(f"# Generated: {time.ctime()}\n")
                f.write(f"# Total events: {len(self.audit_log)}\n\n")
                
                for event in self.audit_log:
                    f.write(str(event) + '\n')
            
            print(f"📄 SECURITY: Audit logs exportados a {file_path}")
            return True
            
        except Exception as e:
            print(f"❌ SECURITY: Error exportando logs: {e}")
            return False
    
    # ==================== INFORMACIÓN Y ESTADÍSTICAS ====================
    
    def get_security_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de seguridad"""
        return {
            'service_running': self.running,
            'total_users': len(self.users),
            'active_sessions': len(self.active_sessions),
            'blocked_accounts': sum(1 for user in self.users.values() if user.is_locked),
            'audit_events': len(self.audit_log),
            'statistics': self.security_stats.copy(),
            'security_policy': self.security_policy.copy()
        }
    
    def list_users(self, admin_token: str) -> List[Dict[str, Any]]:
        """Lista todos los usuarios (requiere admin)"""
        if not self.check_permission(admin_token, "admin_access"):
            return []
        
        users_info = []
        for username, user in self.users.items():
            users_info.append({
                'username': username,
                'permissions': list(user.permissions),
                'created_at': time.ctime(user.created_at),
                'last_login': time.ctime(user.last_login) if user.last_login else 'Never',
                'is_locked': user.is_locked,
                'failed_attempts': user.failed_login_attempts,
                'active_sessions': len(user.session_tokens),
                'security_level': user.security_level.name
            })
        
        return users_info
    
    def list_active_sessions(self, admin_token: str) -> List[Dict[str, Any]]:
        """Lista sesiones activas (requiere admin)"""
        if not self.check_permission(admin_token, "admin_access"):
            return []
        
        sessions_info = []
        for token, session_data in self.active_sessions.items():
            duration = time.time() - session_data['created_at']
            last_activity = time.time() - session_data['last_activity']
            
            sessions_info.append({
                'token': token[:16] + "...",  # Mostrar solo parte del token
                'username': session_data['username'],
                'duration_seconds': duration,
                'last_activity_seconds_ago': last_activity,
                'permissions': list(session_data['permissions']),
                'security_level': session_data['security_level'].name
            })
        
        return sessions_info
    
    def print_security_status(self):
        """Imprime el estado del servicio de seguridad"""
        stats = self.get_security_stats()
        
        print("\n" + "-"*50)
        print("🔒 ESTADO DEL SERVICIO DE SEGURIDAD")
        print("-"*50)
        print(f"🟢 Estado: {'Activo' if stats['service_running'] else 'Inactivo'}")
        print(f"👥 Usuarios totales: {stats['total_users']}")
        print(f"🔓 Sesiones activas: {stats['active_sessions']}")
        print(f"🔒 Cuentas bloqueadas: {stats['blocked_accounts']}")
        print(f"📋 Eventos de auditoría: {stats['audit_events']}")
        
        print(f"\n📊 Estadísticas:")
        print(f"   • Logins totales: {stats['statistics']['total_logins']}")
        print(f"   • Logins fallidos: {stats['statistics']['failed_logins']}")
        print(f"   • Accesos denegados: {stats['statistics']['access_denied_count']}")
        print(f"   • Violaciones de seguridad: {stats['statistics']['security_violations']}")
        
        print(f"\n⚙️  Política de seguridad:")
        print(f"   • Máx. intentos fallidos: {stats['security_policy']['max_failed_attempts']}")
        print(f"   • Timeout de sesión: {stats['security_policy']['session_timeout']}s")
        print(f"   • Nivel de auditoría: {stats['security_policy']['audit_level']}")
        print("-"*50)

# Instancia global del servicio de seguridad
security_service = SecurityService()

def get_security_service():
    """Obtiene la instancia global del servicio de seguridad"""
    return security_service