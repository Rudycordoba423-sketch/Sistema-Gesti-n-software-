"""
UNAD — Curso: Programación 213023
Ejercicio 1: Sistema Integral de Gestión — Empresa Software FJ
Estudiante: Rubeidy Cordoba
Fecha: 27/10/2026
Descripción: Gestión de clientes, servicios y reservas con manejo de excepciones
"""

from abc import ABC, abstractmethod
from datetime import datetime

# ==================================================
# SISTEMA DE LOGS Y EXCEPCIONES PERSONALIZADAS
# ==================================================
class RegistroLogs:
    ARCHIVO = "registro_sistema.log"

    @staticmethod
    def escribir(tipo, mensaje):
        marca = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        linea = f"[{marca}] [{tipo.upper()}] {mensaje}\n"
        try:
            with open(RegistroLogs.ARCHIVO, "a", encoding="utf-8") as f:
                f.write(linea)
        except IOError:
            print("⚠️ No se pudo escribir en el archivo de registro")

    @staticmethod
    def iniciar():
        with open(RegistroLogs.ARCHIVO, "w", encoding="utf-8") as f:
            f.write(f"=== INICIO DEL SISTEMA — {datetime.now()}\n")


class ErrorSistemaGestion(Exception): pass
class DatoInvalidoError(ErrorSistemaGestion): pass
class ClienteDuplicadoError(ErrorSistemaGestion): pass
class ServicioNoDisponibleError(ErrorSistemaGestion): pass
class ReservaInvalidaError(ErrorSistemaGestion): pass
class EstadoReservaError(ErrorSistemaGestion): pass


# ==================================================
# CLASE ABSTRACTA BASE
# ==================================================
class EntidadBase(ABC):
    @abstractmethod
    def validar_datos(self): pass
    @abstractmethod
    def __str__(self): pass


# ==================================================
# CLASE CLIENTE
# ==================================================
class Cliente(EntidadBase):
    def __init__(self, identificacion, nombre, correo, telefono=""):
        self.__identificacion = identificacion
        self.__nombre = nombre
        self.__correo = correo
        self.__telefono = telefono
        self._activo = True
        self.validar_datos()

    def validar_datos(self):
        try:
            if not self.__identificacion or len(self.__identificacion) < 5:
                raise DatoInvalidoError("Identificación inválida (mínimo 5 caracteres)")
            if not self.__nombre or len(self.__nombre.strip()) < 3:
                raise DatoInvalidoError("Nombre inválido (mínimo 3 caracteres)")
            if "@" not in self.__correo or "." not in self.__correo:
                raise DatoInvalidoError(f"Correo con formato incorrecto: {self.__correo}")
            RegistroLogs.escribir("info", f"Cliente registrado: {self.__nombre}")
        except DatoInvalidoError:
            raise
        except Exception as e:
            RegistroLogs.escribir("error", f"Error validando cliente: {e}")
            raise DatoInvalidoError(str(e)) from e

    @property
    def identificacion(self): return self.__identificacion
    @property
    def nombre(self): return self.__nombre
    @property
    def correo(self): return self.__correo
    @property
    def telefono(self): return self.__telefono
    @property
    def activo(self): return self._activo

    def desactivar(self):
        self._activo = False
        RegistroLogs.escribir("aviso", f"Cliente desactivado: {self.__nombre}")

    def __str__(self):
        estado = "Activo" if self._activo else "Inactivo"
        return f"Cliente: {self.__nombre} | ID: {self.__identificacion} | Correo: {self.__correo} | {estado}"


class GestorClientes:
    def __init__(self):
        self._clientes = []

    def registrar(self, cliente):
        try:
            if not isinstance(cliente, Cliente):
                raise TypeError("Se esperaba un objeto de tipo Cliente")
            for c in self._clientes:
                if c.identificacion == cliente.identificacion:
                    raise ClienteDuplicadoError(f"Ya existe cliente con ID: {cliente.identificacion}")
            self._clientes.append(cliente)
            RegistroLogs.escribir("exito", f"Cliente agregado: {cliente.nombre}")
            return True
        except (ClienteDuplicadoError, TypeError) as e:
            RegistroLogs.escribir("error", f"Fallo al registrar cliente: {e}")
            raise

    def buscar(self, identificacion):
        for c in self._clientes:
            if c.identificacion == identificacion:
                return c
        RegistroLogs.escribir("aviso", f"Cliente no encontrado: {identificacion}")
        return None

    def listar_todos(self):
        return self._clientes.copy()


# ==================================================
# CLASE ABSTRACTA SERVICIO
# ==================================================
class Servicio(ABC):
    def __init__(self, codigo, nombre, descripcion, precio_base):
        self.codigo = codigo
        self.nombre = nombre
        self.descripcion = descripcion
        self.precio_base = precio_base
        self.disponible = True
        self.validar_datos()

    @abstractmethod
    def validar_datos(self): pass

    @abstractmethod
    def calcular_costo(self, **kwargs): pass

    @abstractmethod
    def describir(self): pass

    def marcar_no_disponible(self):
        self.disponible = False
        RegistroLogs.escribir("aviso", f"Servicio no disponible: {self.codigo} - {self.nombre}")

    def __str__(self):
        disp = "✅ Disponible" if self.disponible else "❌ No disponible"
        return f"[{self.codigo}] {self.nombre} — Precio base: ${self.precio_base:,.2f} | {disp}"


# ==================================================
# SERVICIO 1: RESERVA DE SALA
# ==================================================
class ReservaSala(Servicio):
    def __init__(self, codigo, nombre, descripcion, precio_base, capacidad, tarifa_extra=0):
        self.capacidad = capacidad
        self.tarifa_extra = tarifa_extra
        super().__init__(codigo, nombre, descripcion, precio_base)

    def validar_datos(self):
        if self.capacidad <= 0 or self.precio_base < 0:
            raise DatoInvalidoError("Valores deben ser positivos")

    def calcular_costo(self, duracion, personas=0, descuento=0, **kwargs):
        try:
            if duracion <= 0:
                raise ValueError("Duración debe ser mayor a cero")
            total = self.precio_base * duracion
            if personas > self.capacidad * 0.7:
                total *= 1.10
            if duracion > 4:
                total += (duracion - 4) * self.tarifa_extra
            if 0 <= descuento <= 0.5:
                total *= (1 - descuento)
            return round(total, 2)
        except TypeError:
            raise ReservaInvalidaError("Parámetros deben ser numéricos")

    def describir(self):
        return f"Sala: {self.nombre} — Capacidad: {self.capacidad} personas | Precio/hora: ${self.precio_base:,.2f}"


# ==================================================
# SERVICIO 2: ALQUILER DE EQUIPOS
# ==================================================
class AlquilerEquipos(Servicio):
    def __init__(self, codigo, nombre, descripcion, precio_base, deposito, stock):
        self.deposito = deposito
        self.stock = stock
        super().__init__(codigo, nombre, descripcion, precio_base)

    def validar_datos(self):
        if self.deposito < 0 or self.stock < 0:
            raise DatoInvalidoError("Valores no pueden ser negativos")

    def calcular_costo(self, dias, cantidad=1, incluir_deposito=False, **kwargs):
        try:
            if dias <= 0 or cantidad < 1:
                raise ValueError("Valores deben ser positivos")
            if cantidad > self.stock:
                raise ValueError(f"Solo hay {self.stock} unidades disponibles")
            total = self.precio_base * dias * cantidad
            if incluir_deposito:
                total += self.deposito * cantidad
            return round(total, 2)
        except ValueError as e:
            raise ReservaInvalidaError(str(e))

    def describir(self):
        return f"Equipo: {self.nombre} — Stock: {self.stock} | Tarifa/día: ${self.precio_base:,.2f}"

    def reservar_unidad(self):
        if self.stock <= 0:
            raise ServicioNoDisponibleError("Sin stock disponible")
        self.stock -= 1

    def devolver_unidad(self):
        self.stock += 1


# ==================================================
# SERVICIO 3: ASESORÍA ESPECIALIZADA
# ==================================================
class AsesoriaEspecializada(Servicio):
    def __init__(self, codigo, nombre, descripcion, precio_base, nivel, modalidad):
        self.nivel = nivel.upper()
        self.modalidad = modalidad.upper()
        super().__init__(codigo, nombre, descripcion, precio_base)

    def validar_datos(self):
        if self.nivel not in ["JUNIOR", "SENIOR", "EXPERTO"]:
            raise DatoInvalidoError("Nivel inválido")
        if self.modalidad not in ["PRESENCIAL", "VIRTUAL"]:
            raise DatoInvalidoError("Modalidad inválida")

    def calcular_costo(self, horas, **kwargs):
        try:
            if horas <= 0:
                raise ValueError("Horas deben ser positivas")
            factor = {"JUNIOR": 1, "SENIOR": 1.5, "EXPERTO": 2}[self.nivel]
            return round(self.precio_base * horas * factor, 2)
        except TypeError:
            raise ReservaInvalidaError("Horas debe ser un número")

    def describir(self):
        return f"Asesoría: {self.nivel} ({self.modalidad}) — Tarifa base: ${self.precio_base:,.2f}/hora"


class GestorServicios:
    def __init__(self):
        self._servicios = {}

    def registrar(self, servicio):
        try:
            if servicio.codigo in self._servicios:
                raise DatoInvalidoError(f"Código duplicado: {servicio.codigo}")
            self._servicios[servicio.codigo] = servicio
            RegistroLogs.escribir("exito", f"Servicio agregado: {servicio.codigo}")
        except Exception as e:
            RegistroLogs.escribir("error", f"Fallo al registrar servicio: {e}")
            raise

    def buscar(self, codigo):
        return self._servicios.get(codigo)

    def listar_todos(self):
        return list(self._servicios.values())


# ==================================================
# CLASE RESERVA
# ==================================================
class Reserva:
    ESTADOS = {"PENDIENTE", "CONFIRMADA", "CANCELADA", "COMPLETADA"}

    def __init__(self, numero_reserva, cliente, servicio, duracion, **parametros):
        self.numero = numero_reserva
        self.cliente = cliente
        self.servicio = servicio
        self.duracion = duracion
        self.parametros = parametros
        self.estado = "PENDIENTE"
        self.costo_final = 0
        self._validar_relaciones()

    def _validar_relaciones(self):
        try:
            if not isinstance(self.cliente, Cliente):
                raise TypeError("Se requiere un objeto Cliente válido")
            if not isinstance(self.servicio, Servicio):
                raise TypeError("Se requiere un objeto Servicio válido")
            if not self.servicio.disponible:
                raise ServicioNoDisponibleError("Servicio no disponible")
            if self.duracion <= 0:
                raise ReservaInvalidaError("Duración debe ser mayor a cero")
            RegistroLogs.escribir("info", f"Reserva creada Nº{self.numero}")
        except Exception as e:
            RegistroLogs.escribir("error", f"Fallo en creación de reserva: {e}")
            raise

    def confirmar(self):
        try:
            if self.estado != "PENDIENTE":
                raise EstadoReservaError(f"No se puede confirmar en estado: {self.estado}")
            self.costo_final = self.servicio.calcular_costo(self.duracion, **self.parametros)
            if hasattr(self.servicio, "reservar_unidad"):
                self.servicio.reservar_unidad()
            self.estado = "CONFIRMADA"
            RegistroLogs.escribir("exito", f"Reserva confirmada Nº{self.numero} — Costo: ${self.costo_final}")
            return f"✅ Reserva {self.numero} confirmada. Total: ${self.costo_final:,.2f}"
        except Exception as e:
            RegistroLogs.escribir("error", f"Fallo al confirmar: {e}")
            raise

    def cancelar(self):
        try:
            if self.estado in ["COMPLETADA", "CANCELADA"]:
                raise EstadoReservaError(f"No se puede cancelar: estado {self.estado}")
            if hasattr(self.servicio, "devolver_unidad") and self.estado == "CONFIRMADA":
                self.servicio.devolver_unidad()
            self.estado = "CANCELADA"
            RegistroLogs.escribir("aviso", f"Reserva cancelada Nº{self.numero}")
            return f"❌ Reserva {self.numero} cancelada"
        except Exception as e:
            RegistroLogs.escribir("error", f"Fallo al cancelar: {e}")
            raise

    def __str__(self):
        return f"Reserva Nº{self.numero} | Cliente: {self.cliente.nombre} | Servicio: {self.servicio.nombre} | Estado: {self.estado} | Costo: ${self.costo_final:,.2f}"


class GestorReservas:
    def __init__(self):
        self._reservas = []
        self._contador = 1

    def crear(self, cliente, servicio, duracion, **params):
        reserva = Reserva(self._contador, cliente, servicio, duracion, **params)
        self._reservas.append(reserva)
        self._contador += 1
        return reserva

    def listar_todas(self):
        return self._reservas.copy()


# ==================================================
# EJECUCIÓN DE PRUEBAS
# ==================================================
def main():
    RegistroLogs.iniciar()
    print("=" * 60)
    print("SISTEMA INTEGRAL DE GESTIÓN — EMPRESA SOFTWARE FJ")
    print("=" * 60)

    gestor_clientes = GestorClientes()
    gestor_servicios = GestorServicios()
    gestor_reservas = GestorReservas()

    print("\n📌 REGISTRO DE CLIENTES")
    try:
        c1 = Cliente("123456789", "María López", "maria@email.com", "3001234567")
        gestor_clientes.registrar(c1)
        print(f"✅ {c1}")
    except Exception as e:
        print(f"❌ Error: {e}")

    try:
        c2 = Cliente("12345", "J Pérez", "correo_invalido")
        gestor_clientes.registrar(c2)
        print(f"✅ {c2}")
    except DatoInvalidoError as e:
        print(f"❌ Error esperado: {e}")

    print("\n📌 REGISTRO DE SERVICIOS")
    try:
        sala = ReservaSala("S001", "Sala de Conferencias", "Capacidad para reuniones", 50000, 30, 15000)
        gestor_servicios.registrar(sala)
        print(f"✅ {sala}")
        print(f"   {sala.describir()}")
    except Exception as e:
        print(f"❌ Error: {e}")

    try:
        equipo = AlquilerEquipos("E001", "Laptop Diseño", "Equipo de alto rendimiento", 25000, 500000, 5)
        gestor_servicios.registrar(equipo)
        print(f"✅ {equipo}")
        print(f"   {equipo.describir()}")
    except 
