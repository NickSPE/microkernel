"""
SECURITY SERVICE - Servicio de Seguridad del Sistema
====================================================
Maneja autenticación, autorización, cifrado,
auditoría y políticas de    def start(self):
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
import time
import threading
import hashlib
import secrets
import json
from typing import Dict, List, Optional, Any, Set
from enum import Enum
from kernel.microkernel import get_kernel

class SecurityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class UserRole(Enum):
    GUEST = "guest"
    USER = "user"
    ADMIN = "admin"
    SYSTEM = "system"

class AuditEventType(Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    ACCESS_DENIED = "access_denied"
    PERMISSION_GRANTED = "permission_granted"
    SECURITY_VIOLATION = "security_violation"
    POLICY_CHANGE = "policy_change"

class User:
    """Representa un usuario del sistema"""
    
    def __init__(self, username: str, password_hash: str, role: UserRole = UserRole.USER):
        self.username = username
        self.password_hash = password_hash
        self.role = role
        self.created_at = time.time()
        self.last_login = None
        self.login_count = 0
        self.failed_attempts = 0
        self.is_locked = False
        self.permissions: Set[str] = set()
        self.session_token = None
        self.session_expires = None
        
        # Permisos por defecto según el rol
        self._set_default_permissions()
    
    def _set_default_permissions(self):
        """Establece permisos por defecto según el rol"""
        if self.role == UserRole.GUEST:
            self.permissions.update(['read_public'])
        elif self.role == UserRole.USER:
            self.permissions.update(['read_public', 'read_own', 'write_own'])
        elif self.role == UserRole.ADMIN:
            self.permissions.update(['read_public', 'read_own', 'write_own', 
                                   'read_all', 'write_all', 'manage_users'])
        elif self.role == UserRole.SYSTEM:
            self.permissions.update(['*'])  # Todos los permisos
    
    def check_password(self, password: str) -> bool:
        """Verifica la contraseña del usuario"""
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        return password_hash == self.password_hash
    
    def has_permission(self, permission: str) -> bool:
        """Verifica si el usuario tiene un permiso específico"""
        return '*' in self.permissions or permission in self.permissions
    
    def get_info(self) -> Dict[str, Any]:
        """Obtiene información del usuario (sin datos sensibles)"""
        return {
            'username': self.username,
            'role': self.role.value,
            'created_at': time.ctime(self.created_at),
            'last_login': time.ctime(self.last_login) if self.last_login else 'Never',
            'login_count': self.login_count,
            'is_locked': self.is_locked,
            'permissions': sorted(list(self.permissions)),
            'has_active_session': self.session_token is not None
        }

class SecurityPolicy:
    """Política de seguridad del sistema"""
    
    def __init__(self):
        self.max_failed_attempts = 3
        self.lockout_duration = 300  # 5 minutos
        self.session_timeout = 3600  # 1 hora
        self.password_min_length = 8
        self.password_require_special = True
        self.audit_level = SecurityLevel.MEDIUM
        self.encryption_required = False
        self.two_factor_enabled = False
        self.security_questions_required = False

class AuditEvent:
    """Evento de auditoría del sistema"""
    
    def __init__(self, event_type: AuditEventType, user: str, details: str, severity: SecurityLevel = SecurityLevel.LOW):
        self.event_type = event_type
        self.user = user
        self.details = details
        self.severity = severity
        self.timestamp = time.time()
        self.id = f"{int(self.timestamp * 1000000)}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el evento a diccionario"""
        return {
            'id': self.id,
            'type': self.event_type.value,
            'user': self.user,
            'details': self.details,
            'severity': self.severity.value,
            'timestamp': time.ctime(self.timestamp),
            'timestamp_unix': self.timestamp
        }

class SecurityService:
    """
    Servicio de Seguridad del Sistema
    Proporciona autenticación, autorización y auditoría
    """
    
    def __init__(self):
        self.name = "SecurityService"
        self.version = "1.0"
        self.running = False
        self.users: Dict[str, User] = {}
        self.active_sessions: Dict[str, str] = {}  # token -> username
        self.audit_log: List[AuditEvent] = []
        self.security_policy = SecurityPolicy()
        self.security_lock = threading.RLock()
        self.monitoring_thread: Optional[threading.Thread] = None
        
        # Estadísticas de seguridad
        self.security_stats = {
            'login_attempts': 0,
            'successful_logins': 0,
            'failed_logins': 0,
            'access_denied_count': 0,
            'security_violations': 0,
            'active_sessions': 0,
            'audit_events': 0
        }
        
        # Crear usuarios por defecto
        self._create_default_users()
        
        print("🔒 SECURITY_SERVICE: Servicio de seguridad inicializado")
    
    def _create_default_users(self):
        """Crea usuarios por defecto del sistema"""
        # Usuario administrador
        admin_hash = hashlib.sha256("admin123".encode()).hexdigest()
        admin = User("admin", admin_hash, UserRole.ADMIN)
        self.users["admin"] = admin
        
        # Usuario del sistema
        system_hash = hashlib.sha256("system".encode()).hexdigest()
        system_user = User("system", system_hash, UserRole.SYSTEM)
        self.users["system"] = system_user
        
        # Usuario invitado
        guest_hash = hashlib.sha256("guest".encode()).hexdigest()
        guest = User("guest", guest_hash, UserRole.GUEST)
        self.users["guest"] = guest
        
        # Usuario demo
        demo_hash = hashlib.sha256("demo123".encode()).hexdigest()
        demo = User("demo", demo_hash, UserRole.USER)
        self.users["demo"] = demo
        
        print(f"🔒 SECURITY: {len(self.users)} usuarios por defecto creados")
    
    def start(self, kernel):
        """Inicia el servicio de seguridad"""
        with self.security_lock:
            if self.running:
                return
            
            self.kernel = kernel
            self.running = True
            
            # Registrarse como servicio
            kernel.register_service("security", self)
            
            # Iniciar monitoreo de seguridad
            self.monitoring_thread = threading.Thread(target=self._security_monitoring_loop)
            self.monitoring_thread.daemon = True
            self.monitoring_thread.start()
            
            # Evento de auditoría
            self._audit_event(AuditEventType.POLICY_CHANGE, "system", 
                            "Security service started", SecurityLevel.MEDIUM)
            
            print("🟢 SECURITY_SERVICE: Servicio de seguridad iniciado")
    
    def stop(self):
        """Detiene el servicio de seguridad"""
        with self.security_lock:
            self.running = False
            
            # Cerrar todas las sesiones activas
            self._terminate_all_sessions()
            
            # Evento de auditoría
            self._audit_event(AuditEventType.POLICY_CHANGE, "system", 
                            "Security service stopped", SecurityLevel.MEDIUM)
            
            print("🔴 SECURITY_SERVICE: Servicio de seguridad detenido")
    
    def _security_monitoring_loop(self):
        """Bucle de monitoreo de seguridad"""
        while self.running:
            try:
                # Verificar sesiones expiradas
                self._cleanup_expired_sessions()
                
                # Desbloquear usuarios si ha pasado el tiempo
                self._unlock_expired_users()
                
                # Verificar eventos sospechosos
                self._analyze_security_threats()
                
                # Pausa de monitoreo
                time.sleep(30.0)
                
            except Exception as e:
                print(f"❌ SECURITY_SERVICE MONITOR ERROR: {e}")
    
    def _cleanup_expired_sessions(self):
        """Limpia sesiones expiradas"""
        current_time = time.time()
        expired_sessions = []
        
        for token, username in self.active_sessions.items():
            user = self.users.get(username)
            if user and user.session_expires and current_time > user.session_expires:
                expired_sessions.append(token)
        
        for token in expired_sessions:
            self._terminate_session(token)
            self._audit_event(AuditEventType.LOGOUT, self.active_sessions.get(token, "unknown"), 
                            "Session expired", SecurityLevel.LOW)
    
    def _unlock_expired_users(self):
        """Desbloquea usuarios cuyo período de bloqueo ha expirado"""
        # Implementación simplificada
        for user in self.users.values():
            if user.is_locked and user.failed_attempts > 0:
                # En un sistema real, habría un timestamp de bloqueo
                # Por simplicidad, desbloqueamos después de un tiempo
                user.is_locked = False
                user.failed_attempts = 0
    
    def _analyze_security_threats(self):
        """Analiza amenazas de seguridad basándose en eventos recientes"""
        recent_events = [e for e in self.audit_log if time.time() - e.timestamp < 300]  # Últimos 5 minutos
        
        # Detectar múltiples intentos fallidos
        failed_attempts = [e for e in recent_events if e.event_type == AuditEventType.ACCESS_DENIED]
        if len(failed_attempts) > 10:
            self._audit_event(AuditEventType.SECURITY_VIOLATION, "system", 
                            f"Multiple failed access attempts detected: {len(failed_attempts)}", 
                            SecurityLevel.HIGH)
    
    # ==================== GESTIÓN DE USUARIOS ====================
    
    def create_user(self, username: str, password: str, role: UserRole = UserRole.USER, creator: str = "system") -> bool:
        """Crea un nuevo usuario"""
        with self.security_lock:
            if username in self.users:
                self._audit_event(AuditEventType.ACCESS_DENIED, creator, 
                                f"Attempt to create existing user: {username}", SecurityLevel.MEDIUM)
                return False
            
            # Validar contraseña
            if not self._validate_password(password):
                return False
            
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            user = User(username, password_hash, role)
            self.users[username] = user
            
            self._audit_event(AuditEventType.PERMISSION_GRANTED, creator, 
                            f"User created: {username} with role {role.value}", SecurityLevel.MEDIUM)
            
            print(f"👤 SECURITY: Usuario {username} creado con rol {role.value}")
            return True
    
    def delete_user(self, username: str, deleter: str = "system") -> bool:
        """Elimina un usuario"""
        with self.security_lock:
            if username not in self.users:
                return False
            
            # No permitir eliminar usuarios del sistema
            if self.users[username].role == UserRole.SYSTEM:
                self._audit_event(AuditEventType.ACCESS_DENIED, deleter, 
                                f"Attempt to delete system user: {username}", SecurityLevel.HIGH)
                return False
            
            # Terminar sesión activa si la tiene
            if self.users[username].session_token:
                self._terminate_session(self.users[username].session_token)
            
            del self.users[username]
            
            self._audit_event(AuditEventType.PERMISSION_GRANTED, deleter, 
                            f"User deleted: {username}", SecurityLevel.MEDIUM)
            
            print(f"🗑️  SECURITY: Usuario {username} eliminado")
            return True
    
    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """Cambia la contraseña de un usuario"""
        with self.security_lock:
            if username not in self.users:
                return False
            
            user = self.users[username]
            
            # Verificar contraseña actual
            if not user.check_password(old_password):
                self._audit_event(AuditEventType.ACCESS_DENIED, username, 
                                "Failed password change attempt", SecurityLevel.MEDIUM)
                return False
            
            # Validar nueva contraseña
            if not self._validate_password(new_password):
                return False
            
            user.password_hash = hashlib.sha256(new_password.encode()).hexdigest()
            
            self._audit_event(AuditEventType.PERMISSION_GRANTED, username, 
                            "Password changed successfully", SecurityLevel.LOW)
            
            print(f"🔑 SECURITY: Contraseña cambiada para {username}")
            return True
    
    def _validate_password(self, password: str) -> bool:
        """Valida una contraseña según la política de seguridad"""
        if len(password) < self.security_policy.password_min_length:
            return False
        
        if self.security_policy.password_require_special:
            special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
            if not any(c in special_chars for c in password):
                return False
        
        return True
    
    # ==================== AUTENTICACIÓN ====================
    
    def authenticate(self, username: str, password: str, source: str = "local") -> Optional[str]:
        """Autentica un usuario y retorna un token de sesión"""
        with self.security_lock:
            self.security_stats['login_attempts'] += 1
            
            if username not in self.users:
                self._audit_event(AuditEventType.ACCESS_DENIED, username, 
                                f"Login attempt with non-existent user from {source}", SecurityLevel.MEDIUM)
                self.security_stats['failed_logins'] += 1
                return None
            
            user = self.users[username]
            
            # Verificar si está bloqueado
            if user.is_locked:
                self._audit_event(AuditEventType.ACCESS_DENIED, username, 
                                f"Login attempt on locked account from {source}", SecurityLevel.HIGH)
                self.security_stats['failed_logins'] += 1
                return None
            
            # Verificar contraseña
            if not user.check_password(password):
                user.failed_attempts += 1
                
                # Bloquear cuenta si se exceden los intentos
                if user.failed_attempts >= self.security_policy.max_failed_attempts:
                    user.is_locked = True
                    self._audit_event(AuditEventType.SECURITY_VIOLATION, username, 
                                    f"Account locked due to {user.failed_attempts} failed attempts", 
                                    SecurityLevel.HIGH)
                
                self._audit_event(AuditEventType.ACCESS_DENIED, username, 
                                f"Failed login attempt from {source}", SecurityLevel.MEDIUM)
                self.security_stats['failed_logins'] += 1
                return None
            
            # Autenticación exitosa
            user.failed_attempts = 0
            user.last_login = time.time()
            user.login_count += 1
            
            # Crear token de sesión
            session_token = secrets.token_urlsafe(32)
            user.session_token = session_token
            user.session_expires = time.time() + self.security_policy.session_timeout
            
            self.active_sessions[session_token] = username
            self.security_stats['successful_logins'] += 1
            self.security_stats['active_sessions'] = len(self.active_sessions)
            
            self._audit_event(AuditEventType.LOGIN, username, 
                            f"Successful login from {source}", SecurityLevel.LOW)
            
            print(f"🔓 SECURITY: Usuario {username} autenticado exitosamente")
            return session_token
    
    def logout(self, session_token: str) -> bool:
        """Cierra la sesión de un usuario"""
        return self._terminate_session(session_token)
    
    def _terminate_session(self, session_token: str) -> bool:
        """Termina una sesión específica"""
        with self.security_lock:
            if session_token not in self.active_sessions:
                return False
            
            username = self.active_sessions[session_token]
            user = self.users.get(username)
            
            if user:
                user.session_token = None
                user.session_expires = None
            
            del self.active_sessions[session_token]
            self.security_stats['active_sessions'] = len(self.active_sessions)
            
            self._audit_event(AuditEventType.LOGOUT, username, 
                            "Session terminated", SecurityLevel.LOW)
            
            print(f"🚪 SECURITY: Sesión cerrada para {username}")
            return True
    
    def _terminate_all_sessions(self):
        """Termina todas las sesiones activas"""
        sessions_to_close = list(self.active_sessions.keys())
        for token in sessions_to_close:
            self._terminate_session(token)
    
    def validate_session(self, session_token: str) -> Optional[str]:
        """Valida un token de sesión y retorna el username"""
        with self.security_lock:
            if session_token not in self.active_sessions:
                return None
            
            username = self.active_sessions[session_token]
            user = self.users.get(username)
            
            if not user or not user.session_expires:
                return None
            
            # Verificar si la sesión ha expirado
            if time.time() > user.session_expires:
                self._terminate_session(session_token)
                return None
            
            return username
    
    # ==================== AUTORIZACIÓN ====================
    
    def check_permission(self, session_token: str, permission: str, resource: str = "") -> bool:
        """Verifica si un usuario tiene permisos para realizar una acción"""
        username = self.validate_session(session_token)
        if not username:
            self._audit_event(AuditEventType.ACCESS_DENIED, "unknown", 
                            f"Permission check failed - invalid session for {permission}", SecurityLevel.MEDIUM)
            self.security_stats['access_denied_count'] += 1
            return False
        
        user = self.users[username]
        has_permission = user.has_permission(permission)
        
        if has_permission:
            self._audit_event(AuditEventType.PERMISSION_GRANTED, username, 
                            f"Permission granted: {permission} on {resource}", SecurityLevel.LOW)
        else:
            self._audit_event(AuditEventType.ACCESS_DENIED, username, 
                            f"Permission denied: {permission} on {resource}", SecurityLevel.MEDIUM)
            self.security_stats['access_denied_count'] += 1
        
        return has_permission
    
    def grant_permission(self, username: str, permission: str, granter: str = "system") -> bool:
        """Otorga un permiso a un usuario"""
        with self.security_lock:
            if username not in self.users:
                return False
            
            user = self.users[username]
            user.permissions.add(permission)
            
            self._audit_event(AuditEventType.PERMISSION_GRANTED, granter, 
                            f"Permission '{permission}' granted to {username}", SecurityLevel.MEDIUM)
            
            print(f"✅ SECURITY: Permiso '{permission}' otorgado a {username}")
            return True
    
    def revoke_permission(self, username: str, permission: str, revoker: str = "system") -> bool:
        """Revoca un permiso de un usuario"""
        with self.security_lock:
            if username not in self.users:
                return False
            
            user = self.users[username]
            if permission in user.permissions:
                user.permissions.remove(permission)
                
                self._audit_event(AuditEventType.PERMISSION_GRANTED, revoker, 
                                f"Permission '{permission}' revoked from {username}", SecurityLevel.MEDIUM)
                
                print(f"❌ SECURITY: Permiso '{permission}' revocado de {username}")
                return True
            
            return False
    
    # ==================== AUDITORÍA ====================
    
    def _audit_event(self, event_type: AuditEventType, user: str, details: str, severity: SecurityLevel):
        """Registra un evento de auditoría"""
        if self.security_policy.audit_level.value in ['low', 'medium', 'high', 'critical']:
            event = AuditEvent(event_type, user, details, severity)
            self.audit_log.append(event)
            self.security_stats['audit_events'] += 1
            
            # Mantener solo los últimos 1000 eventos para evitar usar demasiada memoria
            if len(self.audit_log) > 1000:
                self.audit_log = self.audit_log[-1000:]
            
            # Log crítico en consola
            if severity == SecurityLevel.CRITICAL:
                print(f"🚨 SECURITY CRITICAL: {user} - {details}")
            elif severity == SecurityLevel.HIGH:
                print(f"⚠️  SECURITY WARNING: {user} - {details}")
    
    def get_audit_log(self, limit: int = 100, event_type: Optional[AuditEventType] = None) -> List[Dict[str, Any]]:
        """Obtiene eventos de auditoría"""
        events = self.audit_log[-limit:]
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        return [e.to_dict() for e in events]
    
    # ==================== INFORMACIÓN Y ESTADÍSTICAS ====================
    
    def get_security_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de seguridad"""
        user_stats = {}
        for role in UserRole:
            user_stats[role.value] = len([u for u in self.users.values() if u.role == role])
        
        return {
            'service_running': self.running,
            'total_users': len(self.users),
            'user_roles': user_stats,
            'locked_users': len([u for u in self.users.values() if u.is_locked]),
            'active_sessions': len(self.active_sessions),
            'audit_events_total': len(self.audit_log),
            'security_policy': {
                'max_failed_attempts': self.security_policy.max_failed_attempts,
                'session_timeout': self.security_policy.session_timeout,
                'audit_level': self.security_policy.audit_level.value,
                'encryption_required': self.security_policy.encryption_required
            },
            'statistics': self.security_stats.copy()
        }
    
    def print_security_status(self):
        """Imprime el estado del servicio de seguridad"""
        stats = self.get_security_stats()
        
        print("\n" + "-"*50)
        print("🔒 ESTADO DEL SERVICIO DE SEGURIDAD")
        print("-"*50)
        print(f"🟢 Estado: {'Activo' if stats['service_running'] else 'Inactivo'}")
        print(f"👥 Usuarios totales: {stats['total_users']}")
        
        print("🏷️  Usuarios por rol:")
        for role, count in stats['user_roles'].items():
            icon = {"guest": "👤", "user": "👤", "admin": "👑", "system": "🤖"}.get(role, "👤")
            print(f"   {icon} {role.capitalize()}: {count}")
        
        print(f"🔒 Usuarios bloqueados: {stats['locked_users']}")
        print(f"🔑 Sesiones activas: {stats['active_sessions']}")
        print(f"📋 Eventos de auditoría: {stats['audit_events_total']}")
        
        print("📊 Estadísticas de acceso:")
        print(f"   • Intentos de login: {stats['statistics']['login_attempts']}")
        print(f"   • Logins exitosos: {stats['statistics']['successful_logins']}")
        print(f"   • Logins fallidos: {stats['statistics']['failed_logins']}")
        print(f"   • Accesos denegados: {stats['statistics']['access_denied_count']}")
        print(f"   • Violaciones de seguridad: {stats['statistics']['security_violations']}")
        
        print("⚙️  Política de seguridad:")
        print(f"   • Máx. intentos fallidos: {stats['security_policy']['max_failed_attempts']}")
        print(f"   • Timeout de sesión: {stats['security_policy']['session_timeout']}s")
        print(f"   • Nivel de auditoría: {stats['security_policy']['audit_level']}")
        print("-"*50)

# Instancia global del servicio de seguridad
security_service = SecurityService()

def get_security_service():
    """Obtiene la instancia global del servicio de seguridad"""
    return security_service