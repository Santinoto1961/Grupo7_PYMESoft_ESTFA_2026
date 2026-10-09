# PYMEsoft Guía de Instalación

Sistema de gestión para PYMEs hecho con Python + Tkinter + SQLite.

**Módulos:** Facturación | Stock | Clientes | Proveedores | Balance | Usuarios

---

## Requisitos

| Componente             | Versión             | Para qué                    |
| ---------------------- | ------------------- | --------------------------- |
| Python                 | 3.9 o superior      | Ejecutar el programa        |
| Tkinter                | Incluido con Python | Interfaz gráfica            |
| SQLite3                | Incluido con Python | Base de datos               |
| pandas                 | Última              | Importar Excel en **Stock** |
| openpyxl               | Última              | Leer archivos `.xlsx`       |
| xlrd (opcional)        | Última              | Leer archivos `.xls` viejos |
| pyinstaller (opcional) | Última              | Generar el `.exe`           |

> ⚠️ **Importante:** sin `pandas` y `openpyxl`, la importación de Excel en Stock **no funciona**. El resto del programa sí abre.

---

## Paso a paso

### 1. Instalar Python

**Windows**

1. Entrá a https://www.python.org/downloads/
2. Descargá la última versión de Python 3.
3. Al abrir el instalador, **tildá "Add Python to PATH"** (abajo de todo).
4. Hacé clic en **Install Now**.
5. Verificá en una terminal (`cmd` o PowerShell):

```bash
python --version
pip --version
```

**Linux (Ubuntu/Debian)**

⚠️ Tkinter se instala aparte:

```bash
sudo apt update
sudo apt install python3 python3-pip python3-tk
```

**macOS**

```bash
brew install python python-tk
```

---

### 2. Descargar el proyecto

Poné todos los archivos en la **misma carpeta**:

```text
pymesoft/
├── main.py
├── login.py
├── main_window.py
├── session.py
├── database.py
├── database.db
├── balance.py
├── clientes.py
├── compras.py
├── facturacion.py
├── proveedores.py
├── stock.py
├── usuarios.py
└── assets/
    ├── logo.png
    └── logo2.png
```

> 📁 La carpeta `assets/` es **opcional**. Si no existe, el programa muestra un texto en lugar del logo.
>
> 🗄️ `database.db` **tiene que estar en la misma carpeta desde donde se ejecuta el programa**, ya que se abre con una ruta relativa.

Abrí una terminal dentro de esa carpeta:

```bash
cd ruta/a/pymesoft
```

---

### 3. Crear un entorno virtual (recomendado)

**Windows**

```bash
python -m venv venv
venv\Scripts\activate
```

**Linux / macOS**

```bash
python3 -m venv venv
source venv/bin/activate
```

🎯 Vas a ver `(venv)` al inicio de la línea de la terminal.

---

### 4. Instalar las librerías

```bash
pip install --upgrade pip
pip install pandas openpyxl
```

🔧 Opcional (solo si vas a importar archivos Excel viejos `.xls`):

```bash
pip install xlrd
```

🔍 Verificá que todo quedó bien:

```bash
python -c "import tkinter, sqlite3, pandas, openpyxl; print('Todo OK')"
```

---

### 5. Ejecutar el programa

```bash
python main.py
```

🔐 Se abre la pantalla de **Login**. Ingresá con un usuario existente en la tabla `usuarios` de `database.db`.

* 👑 **Administrador:** accede a todos los módulos, incluido **USUARIOS**.
* 👤 **Empleado:** accede a todos los módulos excepto **USUARIOS**.

---

## Formato del Excel para importar en Stock

* 📄 Archivo `.xlsx` (o `.xls` si instalaste `xlrd`).
* 📑 Debe tener una fila de encabezados con columnas de producto, cantidad y precio de compra.
* 🏢 Antes de importar, elegí el **proveedor** al que corresponde la compra.
* 🔁 Si importás dos veces el mismo archivo, del mismo proveedor y con el mismo monto, el sistema te avisa de una posible duplicación.

---

## Generar el ejecutable (.exe) — opcional

```bash
pip install pyinstaller
pyinstaller main.spec
```

📂 El `.exe` queda en la carpeta `dist/`.

⚠️ **Antes de abrirlo, copiá junto al `.exe`:**

* 🗄️ `database.db`
* 🖼️ La carpeta `assets/` (si usás logos).

> 💡 Si el `.exe` no importa Excel, volvé a generarlo con el entorno virtual activado y con `pandas` y `openpyxl` instalados, así PyInstaller los incluye.
>
> 🛠️ Si aun así falla, agregalos en `main.spec` → `hiddenimports=['pandas', 'openpyxl']`.

---

## Problemas comunes

| Error                                            | Solución                                                      |
| ------------------------------------------------ | ------------------------------------------------------------- |
| `ModuleNotFoundError: No module named 'tkinter'` | Linux: `sudo apt install python3-tk`                          |
| `ModuleNotFoundError: No module named 'pandas'`  | `pip install pandas openpyxl`                                 |
| `'python' no se reconoce como comando`           | Reinstalá Python tildando **Add to PATH**                     |
| `sqlite3.OperationalError: no such table`        | Ejecutá el programa desde la carpeta donde está `database.db` |
| 🖼️ Logo no aparece                              | Creá `assets/logo.png` y `assets/logo2.png` (son opcionales)  |
| 📊 Importar `.xls` falla                         | `pip install xlrd`                                            |
| 🔑 Usuario o contraseña incorrectos              | Revisá la tabla `usuarios` en `database.db`                   |

---

## Tablas de la base de datos

`usuarios`, `clientes`, `proveedores`, `productos`, `ventas`, `detalle_ventas`, `gastos_extras`, `compras`, `detalle_compras`

🔧 Las tablas `compras` y `detalle_compras` se crean solas si no existen.

---

✨ ¡Listo! Con esto funcionan **todos** los módulos del sistema. 🎉
