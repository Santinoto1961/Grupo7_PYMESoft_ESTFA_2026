# PYMEsoft — Sistema de Gestión Comercial para PyMEs

**PYMEsoft** es una aplicación de escritorio orientada a la gestión comercial integral de pequeñas y medianas empresas. Permite centralizar en un único sistema el proceso de facturación, control de stock e inventario, administración de clientes y proveedores, y el seguimiento del balance financiero del negocio.

Desarrollado originalmente tomando como cliente de referencia al *Vivero Los Tilos*, el proyecto fue diseñado de manera modular y genérica para adaptarse a la operatoria cotidiana de cualquier PyME comercial.

---

## 🚀 Descripción del Proyecto

El objetivo principal de PYMEsoft es resolver los problemas habituales que enfrentan las PyMEs al utilizar métodos manuales o herramientas desconectadas (cuadernos, planillas sueltas), los cuales suelen provocar inconsistencias en el inventario, comprobantes incompletos y un control financiero poco fiable.

### Módulos Principales:
* 🧾 **Facturación:** Emisión de comprobantes de venta, asignación de clientes/productos y consulta del historial.
* 📦 **Stock e Inventario:** Control de existencias, alta/modificación de productos, precios y seguimiento de mercadería.
* 👥 **Clientes:** Administración de la cartera de clientes, datos de contacto y seguimiento de cuentas corrientes.
* 🚚 **Proveedores:** Gestión de proveedores, historial de compras y saldos pendientes.
* 📊 **Balance Financiero:** Resumen de ingresos, egresos, ganancias netas y reportes por períodos.

---

## 🛠️ Lenguajes y Tecnologías

* **Frontend:** React (Interfaz visual para aplicación de escritorio)
* **Backend:** Python (Lógica de negocio, controladores y servicios API)
* **Base de Datos:** MySQL (Persistencia y modelo relacional de datos)

---

## 👥 Integrantes del Grupo

* **Grupo 7 — ESTFA 2026**

---

## 💡 Ejemplos de Uso

### Caso 1: Registro de una Venta
1. El usuario navega al módulo de **Facturación**.
2. Selecciona un cliente registrado y añade los productos del catálogo especificando cantidades.
3. Al confirmar la venta, el sistema descuenta automáticamente del inventario las unidades vendidas y actualiza el saldo de ingresos en el **Balance Financiero**.

### Caso 2: Recepción de Mercadería de Proveedores
1. El encargado ingresa al módulo de **Proveedores** y selecciona la orden de compra recibida.
2. Ingresa las cantidades que ingresaron al depósito.
3. El sistema actualiza inmediatamente el **Stock** con las nuevas unidades y registra el costo total como un egreso en la gestión financiera.

### Caso 3: Consulta de Balance Financiero
1. El usuario con perfil administrativo o dueño ingresa al módulo de **Balance**.
2. Define un rango de fechas (por ejemplo, el último mes transcurrido).
3. Visualiza los ingresos, egresos y calcula la ganancia neta estimada del período.
