"""
CALCULATOR APP - Aplicación Calculadora
=======================================
Aplicación de usuario que demuestra cómo las apps
interactúan con el microkernel y sus servicios.
"""

import time
import math
import re
from typing import Optional, Dict, Any
from kernel.microkernel import get_kernel
from kernel.ipc import get_ipc_manager
from services.security_service import get_security_service

class Calculator:
    """
    Aplicación Calculadora
    Demuestra el uso de servicios del microkernel
    """
    
    def __init__(self):
        self.name = "Calculator"
        self.version = "1.0"
        self.process_id = None
        self.session_token = None
        self.history = []
        self.memory_value = 0
        self.running = False
        
        # Operaciones soportadas
        self.operations = {
            '+': self._add,
            '-': self._subtract,
            '*': self._multiply,
            '/': self._divide,
            '**': self._power,
            '%': self._modulo,
            'sqrt': self._sqrt,
            'sin': self._sin,
            'cos': self._cos,
            'tan': self._tan,
            'log': self._log,
            'ln': self._natural_log,
        }
        
        print("🔢 CALCULATOR: Aplicación inicializada")
    
    def start(self, session_token: str = None):
        """Inicia la aplicación calculadora"""
        kernel = get_kernel()
        security = get_security_service()
        
        # Autenticación si se proporciona token
        if session_token:
            username = security.validate_session(session_token)
            if not username:
                print("❌ CALCULATOR: Sesión inválida")
                return False
            
            self.session_token = session_token
            print(f"✅ CALCULATOR: Iniciada por usuario autenticado")
        else:
            print("⚠️  CALCULATOR: Iniciada sin autenticación (modo invitado)")
        
        # Crear proceso en el kernel
        self.process_id = kernel.create_process(
            name=f"Calculator-{int(time.time())}",
            target_func=self._calculator_loop,
            priority=1
        )
        
        if self.process_id:
            kernel.start_process(self.process_id)
            self.running = True
            print(f"🚀 CALCULATOR: Proceso iniciado (PID: {self.process_id})")
            return True
        
        return False
    
    def stop(self):
        """Detiene la aplicación"""
        kernel = get_kernel()
        
        if self.process_id:
            kernel.terminate_process(self.process_id)
        
        self.running = False
        print("⏹️  CALCULATOR: Aplicación detenida")
    
    def _calculator_loop(self):
        """Bucle principal de la calculadora"""
        print("\n" + "="*50)
        print("🔢 CALCULADORA DEL MICROKERNEL")
        print("="*50)
        print("Comandos disponibles:")
        print("  • Operaciones: +, -, *, /, **, % (ej: 5 + 3)")
        print("  • Funciones: sqrt(x), sin(x), cos(x), tan(x), log(x), ln(x)")
        print("  • Memoria: M+ (guardar), MR (recuperar), MC (limpiar)")
        print("  • Historial: history (ver), clear (limpiar)")
        print("  • Ayuda: help")
        print("  • Salir: quit, exit")
        print("="*50)
        
        while self.running:
            try:
                # Simular entrada del usuario
                expressions = [
                    "5 + 3",
                    "10 * 2",
                    "sqrt(16)",
                    "15 / 3",
                    "2 ** 3",
                    "sin(0)",
                    "history",
                    "M+",
                    "MR",
                    "clear",
                    "quit"
                ]
                
                for expr in expressions:
                    if not self.running:
                        break
                    
                    print(f"\n> {expr}")
                    result = self._process_input(expr.strip())
                    
                    if result is not None:
                        if isinstance(result, str):
                            print(result)
                        else:
                            print(f"= {result}")
                            self.history.append(f"{expr} = {result}")
                    
                    time.sleep(1)  # Simular pausa entre operaciones
                
                self.running = False
                
            except Exception as e:
                print(f"❌ CALCULATOR ERROR: {e}")
                time.sleep(1)
    
    def _process_input(self, input_text: str) -> Optional[Any]:
        """Procesa la entrada del usuario"""
        input_text = input_text.lower().strip()
        
        # Comandos especiales
        if input_text in ['quit', 'exit']:
            self.stop()
            return "👋 ¡Hasta luego!"
        
        elif input_text == 'help':
            return self._show_help()
        
        elif input_text == 'history':
            return self._show_history()
        
        elif input_text == 'clear':
            self.history.clear()
            return "📋 Historial limpiado"
        
        elif input_text == 'm+':
            return self._memory_add()
        
        elif input_text == 'mr':
            return self._memory_recall()
        
        elif input_text == 'mc':
            self.memory_value = 0
            return "🧠 Memoria limpiada"
        
        elif input_text == 'status':
            return self._show_status()
        
        # Evaluar expresión matemática
        else:
            return self._evaluate_expression(input_text)
    
    def _evaluate_expression(self, expression: str) -> Optional[float]:
        """Evalúa una expresión matemática"""
        try:
            # Limpiar y preparar la expresión
            expression = expression.replace(' ', '')
            
            # Manejar funciones especiales
            expression = self._replace_functions(expression)
            
            # Evaluar la expresión de forma segura
            result = eval(expression, {"__builtins__": {}}, {
                "sqrt": math.sqrt,
                "sin": math.sin,
                "cos": math.cos,
                "tan": math.tan,
                "log": math.log10,
                "ln": math.log,
                "pi": math.pi,
                "e": math.e
            })
            
            # Enviar estadísticas al kernel si estamos autenticados
            if self.session_token:
                self._send_usage_stats("calculation", {"expression": expression, "result": result})
            
            return round(result, 8) if isinstance(result, float) else result
            
        except ZeroDivisionError:
            return "❌ Error: División por cero"
        except ValueError as e:
            return f"❌ Error de valor: {e}"
        except Exception as e:
            return f"❌ Error en la expresión: {e}"
    
    def _replace_functions(self, expression: str) -> str:
        """Reemplaza funciones personalizadas en la expresión"""
        # Reemplazar funciones matemáticas
        expression = re.sub(r'sqrt\(([^)]+)\)', r'sqrt(\1)', expression)
        expression = re.sub(r'log\(([^)]+)\)', r'log(\1)', expression)
        expression = re.sub(r'ln\(([^)]+)\)', r'ln(\1)', expression)
        
        return expression
    
    def _memory_add(self) -> str:
        """Guarda el último resultado en memoria"""
        if self.history:
            last_calculation = self.history[-1]
            try:
                # Extraer el resultado del último cálculo
                result_part = last_calculation.split('=')[-1].strip()
                self.memory_value = float(result_part)
                return f"🧠 Guardado en memoria: {self.memory_value}"
            except:
                return "❌ No hay resultado válido para guardar"
        else:
            return "❌ No hay cálculos previos"
    
    def _memory_recall(self) -> float:
        """Recupera el valor de memoria"""
        return self.memory_value
    
    def _show_help(self) -> str:
        """Muestra la ayuda de la calculadora"""
        help_text = """
🔢 AYUDA DE LA CALCULADORA

Operaciones básicas:
  • 5 + 3    (suma)
  • 10 - 4   (resta)
  • 6 * 7    (multiplicación)
  • 15 / 3   (división)
  • 2 ** 3   (potencia)
  • 17 % 5   (módulo)

Funciones matemáticas:
  • sqrt(16)  (raíz cuadrada)
  • sin(0)    (seno)
  • cos(0)    (coseno)
  • tan(0)    (tangente)
  • log(100)  (logaritmo base 10)
  • ln(2.718) (logaritmo natural)

Memoria:
  • M+        (guardar último resultado)
  • MR        (recuperar de memoria)
  • MC        (limpiar memoria)

Comandos:
  • history   (ver historial)
  • clear     (limpiar historial)
  • status    (ver estado)
  • help      (esta ayuda)
  • quit      (salir)
        """
        return help_text.strip()
    
    def _show_history(self) -> str:
        """Muestra el historial de cálculos"""
        if not self.history:
            return "📋 Historial vacío"
        
        history_text = "\n📋 HISTORIAL DE CÁLCULOS:"
        for i, calc in enumerate(self.history[-10:], 1):  # Últimos 10
            history_text += f"\n  {i:2d}. {calc}"
        
        return history_text
    
    def _show_status(self) -> str:
        """Muestra el estado de la aplicación"""
        kernel = get_kernel()
        process = kernel.get_process(self.process_id) if self.process_id else None
        
        status = f"""
📊 ESTADO DE LA CALCULADORA

Aplicación:
  • Versión: {self.version}
  • Estado: {'🟢 Activa' if self.running else '🔴 Inactiva'}
  • PID: {self.process_id or 'N/A'}
  • Estado del proceso: {process.state.value if process else 'N/A'}

Datos:
  • Cálculos realizados: {len(self.history)}
  • Valor en memoria: {self.memory_value}
  • Sesión autenticada: {'✅ Sí' if self.session_token else '❌ No'}

Sistema:
  • Memoria del proceso: {process.memory_allocated if process else 0} bytes
  • Tiempo de actividad: {time.time() - process.created_at:.1f}s (aprox.)
        """
        return status.strip()
    
    def _send_usage_stats(self, event_type: str, data: Dict[str, Any]):
        """Envía estadísticas de uso al kernel"""
        if not self.session_token:
            return
        
        try:
            ipc = get_ipc_manager()
            security = get_security_service()
            
            username = security.validate_session(self.session_token)
            if username:
                # Enviar mensaje con estadísticas
                stats_message = {
                    'app': self.name,
                    'user': username,
                    'event': event_type,
                    'data': data,
                    'timestamp': time.time()
                }
                
                # En un sistema real, esto se enviaría a un servicio de estadísticas
                print(f"📊 STATS: {event_type} por {username}")
        
        except Exception as e:
            print(f"⚠️  Error enviando estadísticas: {e}")
    
    # ==================== OPERACIONES MATEMÁTICAS ====================
    
    def _add(self, a: float, b: float) -> float:
        return a + b
    
    def _subtract(self, a: float, b: float) -> float:
        return a - b
    
    def _multiply(self, a: float, b: float) -> float:
        return a * b
    
    def _divide(self, a: float, b: float) -> float:
        if b == 0:
            raise ZeroDivisionError("División por cero")
        return a / b
    
    def _power(self, a: float, b: float) -> float:
        return a ** b
    
    def _modulo(self, a: float, b: float) -> float:
        return a % b
    
    def _sqrt(self, x: float) -> float:
        if x < 0:
            raise ValueError("No se puede calcular raíz cuadrada de número negativo")
        return math.sqrt(x)
    
    def _sin(self, x: float) -> float:
        return math.sin(x)
    
    def _cos(self, x: float) -> float:
        return math.cos(x)
    
    def _tan(self, x: float) -> float:
        return math.tan(x)
    
    def _log(self, x: float) -> float:
        if x <= 0:
            raise ValueError("Logaritmo no definido para números <= 0")
        return math.log10(x)
    
    def _natural_log(self, x: float) -> float:
        if x <= 0:
            raise ValueError("Logaritmo natural no definido para números <= 0")
        return math.log(x)

# Funciones de utilidad
def create_calculator() -> Calculator:
    """Crea una nueva instancia de la calculadora"""
    return Calculator()

def run_calculator_demo():
    """Ejecuta una demostración de la calculadora"""
    print("🎯 Iniciando demostración de la Calculadora...")
    
    calc = Calculator()
    if calc.start():
        # La calculadora se ejecutará en su propio hilo
        return calc
    else:
        print("❌ Error iniciando la calculadora")
        return None

if __name__ == "__main__":
    # Si se ejecuta directamente, hacer una demo
    demo_calc = run_calculator_demo()
    if demo_calc:
        # Esperar a que termine
        while demo_calc.running:
            time.sleep(1)