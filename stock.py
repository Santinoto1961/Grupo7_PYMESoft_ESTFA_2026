#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================
stock.py - Módulo de Gestión de Stock (PYMEsoft)
============================================================
Módulo robusto y flexible para la gestión de inventario.
Permite:
  - Visualizar productos en tabla con búsqueda en tiempo real
  - Importar archivos Excel heterogéneos de diferentes proveedores
  - Editar manualmente nombre y precio de venta
  - Agregar y eliminar productos

Diseño fiel al mockup adjunto:
  - Panel verde oscuro con título "Stock :"
  - Tabla a la izquierda, panel lateral derecho
  - Botones de acción abajo

Autor: Desarrollador Senior
Fecha: 2026-08-05
============================================================
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import re
import unicodedata

# ============================================================
# IMPORTACIONES OPCIONALES: pandas / openpyxl para Excel
# ============================================================
try:
    import pandas as pd
except ImportError:
    pd = None

try:
    import openpyxl
except ImportError:
    openpyxl = None

from database import query


# ============================================================
# PALETA DE COLORES (idéntica al resto del proyecto)
# ============================================================
COLOR_VERDE_SIDEBAR      = "#1B4D1B"
COLOR_VERDE_BOTON        = "#a6a6a6"
COLOR_VERDE_HOVER        = "#FFFFFF"
COLOR_GRIS_FONDO         = "#A8A8A8"
COLOR_BLANCO             = "#FFFFFF"
COLOR_NEGRO              = "#000000"
COLOR_ROJO_CERRAR        = "#8B0000"
COLOR_ROJO_HOVER         = "#A52A2A"
COLOR_VERDE_BOTON_ACCION = "#0D2E0D"
COLOR_VERDE_TITULO       = "#06370b"


# ============================================================
# FUNCIONES AUXILIARES: NORMALIZACIÓN DE TEXTO
# ============================================================

def _normalizar_texto(texto):
    """
    Normaliza un texto para comparación:
    - Quita tildes (acentos)
    - Convierte a minúsculas
    - Elimina espacios extra
    - Elimina caracteres no alfanuméricos básicos
    """
    if texto is None:
        return ""
    texto = str(texto)
    # Quitar tildes
    texto = unicodedata.normalize('NFKD', texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    # Minúsculas y limpieza
    texto = texto.lower().strip()
    # Reemplazar múltiples espacios por uno solo
    texto = re.sub(r'\s+', ' ', texto)
    return texto


def _limpiar_valor_numerico(valor, tipo="float", default=0.0):
    """
    Limpia y convierte un valor a número.
    Maneja: comas como decimales, signos de moneda, espacios.
    """
    if valor is None:
        return default
    if isinstance(valor, (int, float)):
        if tipo == "int":
            return int(valor)
        return float(valor)

    texto = str(valor).strip()
    if texto == "" or texto.lower() in ("nan", "none", "null", "-"):
        return default

    # Quitar símbolos de moneda y espacios
    texto = re.sub(r'[$€£¥\s]', '', texto)
    # Reemplazar coma decimal por punto
    texto = texto.replace(',', '.')
    # Si hay múltiples puntos, quedarse con el último como decimal
    partes = texto.split('.')
    if len(partes) > 2:
        texto = ''.join(partes[:-1]) + '.' + partes[-1]

    try:
        numero = float(texto)
        if tipo == "int":
            return int(numero)
        return numero
    except (ValueError, TypeError):
        return default


# ============================================================
# FUNCIONES DE IMPORTACIÓN INTELIGENTE DE EXCEL
# ============================================================

def _detectar_header(df_raw, max_filas=15):
    """
    Detecta dinámicamente la fila que contiene los encabezados reales.
    Busca palabras clave como: descripcion, producto, articulo, codigo, stock, etc.
    Retorna el índice de la fila de encabezado (0-based) o None.
    """
    palabras_clave = [
        "descripcion", "producto", "articulo", "codigo", "cod",
        "stock", "unidades", "cantidad", "u x b",
        "costo", "precio", "precio compra", "precio costo",
        "ean", "nombre", "detalle"
    ]

    filas_a_revisar = min(max_filas, len(df_raw))

    for idx in range(filas_a_revisar):
        fila = df_raw.iloc[idx]
        # Contar cuántas palabras clave aparecen en esta fila
        coincidencias = 0
        for celda in fila:
            texto_norm = _normalizar_texto(celda)
            for palabra in palabras_clave:
                if palabra in texto_norm:
                    coincidencias += 1
                    break
        # Si hay al menos 2 coincidencias, es probable que sea el header
        if coincidencias >= 2:
            return idx

    # Fallback: si no se detecta, asumir fila 0
    return 0


def _mapear_columnas(df):
    """
    Mapea las columnas del DataFrame a los campos estándar del sistema.
    Retorna un diccionario: {campo_estandar: nombre_columna_original}
    """
    columnas = df.columns.tolist()
    mapeo = {}

    # Diccionario de búsqueda: campo_estandar -> [sinónimos]
    reglas = {
        "codigo_proveedor": [
            "codigo", "cod", "articulo", "ean", "codigo proveedor",
            "cod. proveedor", "cod prov", "id producto", "sku"
        ],
        "nombre": [
            "producto", "descripcion", "detalle", "nombre",
            "articulo", "desc", "item", "descripcion producto"
        ],
        "cantidad": [
            "stock", "unidades", "cantidad", "u x b", "uxb",
            "cant", "qty", "quantity", "existencia", "disponible"
        ],
        "precio_compra": [
            "costo", "precio", "precio compra", "precio costo",
            "precio unitario", "valor", "importe", "p. costo",
            "precio de compra", "costo unitario"
        ],
    }

    for campo_estandar, sinonimos in reglas.items():
        for col in columnas:
            col_norm = _normalizar_texto(col)
            for sinonimo in sinonimos:
                if sinonimo in col_norm:
                    mapeo[campo_estandar] = col
                    break
            if campo_estandar in mapeo:
                break

    return mapeo


def _es_fila_valida(row, mapeo):
    """
    Determina si una fila es un producto válido (no título de sección, no vacía).
    Debe tener al menos código o nombre, y algún valor numérico.
    """
    # Verificar que no esté completamente vacía
    if row.isna().all():
        return False

    # Debe tener código o nombre
    tiene_codigo = False
    tiene_nombre = False

    if "codigo_proveedor" in mapeo:
        val = row[mapeo["codigo_proveedor"]]
        if pd.notna(val) and str(val).strip() != "":
            tiene_codigo = True

    if "nombre" in mapeo:
        val = row[mapeo["nombre"]]
        if pd.notna(val) and str(val).strip() != "":
            tiene_nombre = True

    if not tiene_codigo and not tiene_nombre:
        return False

    # Debe tener al menos un valor numérico (precio o cantidad)
    tiene_valor_numerico = False
    for campo in ["precio_compra", "cantidad"]:
        if campo in mapeo:
            val = row[mapeo[campo]]
            if pd.notna(val):
                limpio = _limpiar_valor_numerico(val, default=None)
                if limpio is not None and limpio != 0:
                    tiene_valor_numerico = True
                    break

    # Si tiene código+nombre pero no valor numérico, puede ser un producto con stock 0
    # Aceptamos si tiene código o nombre definidos
    return tiene_codigo or tiene_nombre


def _procesar_excel(ruta_archivo):
    """
    Procesa un archivo Excel heterogéneo y retorna una lista de diccionarios
    con los productos normalizados.
    Retorna: (lista_productos, mensaje_error)
    """
    if pd is None:
        return None, "La librería 'pandas' no está instalada. Instálela con: pip install pandas openpyxl"

    try:
        # Leer el archivo sin encabezado para detectar la fila de headers
        df_raw = pd.read_excel(ruta_archivo, header=None, engine="openpyxl")
    except Exception as e:
        return None, f"No se pudo leer el archivo Excel:\n{str(e)}"

    if df_raw.empty:
        return None, "El archivo Excel está vacío."

    # Detectar fila de encabezados
    header_idx = _detectar_header(df_raw)

    # Releer con el header correcto
    try:
        df = pd.read_excel(ruta_archivo, header=header_idx, engine="openpyxl")
    except Exception as e:
        return None, f"Error al procesar encabezados:\n{str(e)}"

    if df.empty:
        return None, "No se encontraron datos después del encabezado."

    # Mapear columnas
    mapeo = _mapear_columnas(df)

    if "nombre" not in mapeo and "codigo_proveedor" not in mapeo:
        return None, (
            "No se pudieron identificar las columnas necesarias en el Excel.\n"
            "Columnas detectadas: " + ", ".join(str(c) for c in df.columns)
        )

    productos = []
    for _, row in df.iterrows():
        if not _es_fila_valida(row, mapeo):
            continue

        producto = {
            "codigo_proveedor": "",
            "nombre": "",
            "cantidad": 0,
            "precio_compra": 0.0,
            "precio_venta": 0.0,
            "categoria": ""
        }

        # Código del proveedor
        if "codigo_proveedor" in mapeo:
            val = row[mapeo["codigo_proveedor"]]
            if pd.notna(val):
                producto["codigo_proveedor"] = str(val).strip()

        # Nombre / Descripción
        if "nombre" in mapeo:
            val = row[mapeo["nombre"]]
            if pd.notna(val):
                producto["nombre"] = str(val).strip()

        # Cantidad / Stock
        if "cantidad" in mapeo:
            val = row[mapeo["cantidad"]]
            producto["cantidad"] = _limpiar_valor_numerico(val, tipo="int", default=0)
        else:
            producto["cantidad"] = 0

        # Precio de Compra / Costo
        if "precio_compra" in mapeo:
            val = row[mapeo["precio_compra"]]
            producto["precio_compra"] = _limpiar_valor_numerico(val, tipo="float", default=0.0)
        else:
            producto["precio_compra"] = 0.0

        # Solo agregar si tiene al menos código o nombre
        if producto["codigo_proveedor"] or producto["nombre"]:
            productos.append(producto)

    if not productos:
        return None, "No se encontraron productos válidos en el archivo."

    return productos, None


def _guardar_productos_en_bd(productos):
    """
    Guarda o actualiza los productos en la base de datos.
    REGLA ESTRICTA: el precio_venta existente NUNCA se sobrescribe.
    Retorna: (cantidad_insertados, cantidad_actualizados)
    """
    insertados = 0
    actualizados = 0

    for prod in productos:
        codigo = prod["codigo_proveedor"]
        nombre = prod["nombre"]
        cantidad = prod["cantidad"]
        precio_compra = prod["precio_compra"]

        # Si tiene código, buscar por código; si no, por nombre
        if codigo:
            existente = query(
                "SELECT id, precio_venta FROM productos WHERE codigo_proveedor = ?",
                (codigo,)
            )
        else:
            existente = query(
                "SELECT id, precio_venta FROM productos WHERE nombre = ?",
                (nombre,)
            )

        if existente and len(existente) > 0:
            # Actualizar: NO tocar precio_venta
            prod_id = existente[0][0]
            query(
                """UPDATE productos SET
                    nombre = ?,
                    cantidad = ?,
                    precio_compra = ?
                   WHERE id = ?""",
                (nombre, cantidad, precio_compra, prod_id)
            )
            actualizados += 1
        else:
            # Insertar nuevo: precio_venta = 0.0
            query(
                """INSERT INTO productos
                    (codigo_proveedor, nombre, cantidad, precio_compra, precio_venta, categoria)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (codigo, nombre, cantidad, precio_compra, 0.0, "")
            )
            insertados += 1

    return insertados, actualizados


# ============================================================
# CREAR TABLA DE PRODUCTOS (si no existe)
# ============================================================

def _crear_tabla_productos():
    """Crea la tabla productos si no existe."""
    query("""
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_proveedor TEXT,
            nombre TEXT NOT NULL,
            cantidad INTEGER DEFAULT 0,
            precio_compra REAL DEFAULT 0.0,
            precio_venta REAL DEFAULT 0.0,
            categoria TEXT
        )
    """)


# Llamar al iniciar el módulo
_crear_tabla_productos()


# ============================================================
# CLASE PRINCIPAL: VistaStock
# ============================================================

class VistaStock(tk.Frame):
    """
    Vista de gestión de stock embebida dentro del área de contenido
    de la ventana principal (main_window.py).
    """

    def __init__(self, parent_frame):
        super().__init__(parent_frame, bg=COLOR_GRIS_FONDO)
        self.parent = parent_frame
        self.producto_seleccionado = None  # ID del producto seleccionado

        # Empaquetar este frame para que ocupe todo el área
        self.pack(fill=tk.BOTH, expand=True)

        # ============================================================
        # 1. TÍTULO PRINCIPAL
        # ============================================================
        self._crear_titulo()

        # ============================================================
        # 2. PANEL PRINCIPAL VERDE (tabla + panel lateral)
        # ============================================================
        self._crear_panel_principal()

        # ============================================================
        # 3. BOTONES DE ACCIÓN
        # ============================================================
        self._crear_botones_accion()

        # ============================================================
        # 4. CARGAR DATOS INICIALES
        # ============================================================
        self._cargar_productos()

    # ============================================================
    # SECCIÓN 1: TÍTULO
    # ============================================================

    def _crear_titulo(self):
        """Crea el título 'Stock :' alineado a la izquierda."""
        self.lbl_titulo = tk.Label(
            self,
            text="Stock :",
            font=("Arial", 32, "bold"),
            fg=COLOR_NEGRO,
            bg=COLOR_GRIS_FONDO
        )
        self.lbl_titulo.pack(anchor="w", padx=40, pady=(25, 12))

    # ============================================================
    # SECCIÓN 2: PANEL PRINCIPAL
    # ============================================================

    def _crear_panel_principal(self):
        """Crea el panel verde oscuro con tabla y panel lateral."""
        # Frame verde exterior
        self.frame_panel = tk.Frame(
            self,
            bg=COLOR_VERDE_SIDEBAR,
            padx=8,
            pady=8
        )
        self.frame_panel.pack(fill=tk.BOTH, expand=True, padx=40, pady=(0, 18))

        # Frame interno gris
        self.frame_interno = tk.Frame(
            self.frame_panel,
            bg=COLOR_GRIS_FONDO
        )
        self.frame_interno.pack(fill=tk.BOTH, expand=True)

        # Sub-secciones
        self._crear_tabla_stock()
        self._crear_panel_lateral()

    def _crear_tabla_stock(self):
        """Crea el Treeview con las columnas de stock."""
        self.frame_tabla = tk.Frame(
            self.frame_interno,
            bg=COLOR_GRIS_FONDO
        )
        self.frame_tabla.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 2))

        # Definir columnas
        columnas = ("id", "codigo", "nombre", "cantidad", "precio_compra", "precio_venta")
        self.tree = ttk.Treeview(
            self.frame_tabla,
            columns=columnas,
            show="headings",
            height=14
        )

        # Configurar encabezados
        self.tree.heading("id", text="ID")
        self.tree.heading("codigo", text="Código Prov.")
        self.tree.heading("nombre", text="Nombre / Producto")
        self.tree.heading("cantidad", text="Cantidad")
        self.tree.heading("precio_compra", text="Precio Compra ($)")
        self.tree.heading("precio_venta", text="Precio Venta ($)")

        # Anchos de columna
        self.tree.column("id", width=50, anchor="center")
        self.tree.column("codigo", width=100, anchor="w")
        self.tree.column("nombre", width=280, anchor="w")
        self.tree.column("cantidad", width=80, anchor="center")
        self.tree.column("precio_compra", width=110, anchor="e")
        self.tree.column("precio_venta", width=110, anchor="e")

        # Scrollbar vertical
        scrollbar = ttk.Scrollbar(
            self.frame_tabla,
            orient=tk.VERTICAL,
            command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)

        # Eventos
        self.tree.bind("<<TreeviewSelect>>", self._on_seleccionar_producto)
        self.tree.bind("<Double-1>", lambda e: self._editar_producto())

    def _crear_panel_lateral(self):
        """Crea el panel derecho con info del producto seleccionado."""
        self.frame_lateral = tk.Frame(
            self.frame_interno,
            bg=COLOR_GRIS_FONDO,
            width=260
        )
        self.frame_lateral.pack(side=tk.RIGHT, fill=tk.Y, padx=12, pady=12)
        self.frame_lateral.pack_propagate(False)

        # Título
        self.lbl_info_titulo = tk.Label(
            self.frame_lateral,
            text="Información del producto:",
            font=("Arial", 12, "bold"),
            fg=COLOR_NEGRO,
            bg=COLOR_GRIS_FONDO
        )
        self.lbl_info_titulo.pack(anchor="w", pady=(0, 15))

        # Campos de info
        self.lbl_info_id = tk.Label(
            self.frame_lateral, text="ID: —",
            font=("Arial", 11), fg=COLOR_NEGRO, bg=COLOR_GRIS_FONDO, anchor="w"
        )
        self.lbl_info_id.pack(fill=tk.X, pady=4)

        self.lbl_info_codigo = tk.Label(
            self.frame_lateral, text="Código Prov.: —",
            font=("Arial", 11), fg=COLOR_NEGRO, bg=COLOR_GRIS_FONDO, anchor="w"
        )
        self.lbl_info_codigo.pack(fill=tk.X, pady=4)

        self.lbl_info_nombre = tk.Label(
            self.frame_lateral, text="Nombre: —",
            font=("Arial", 11), fg=COLOR_NEGRO, bg=COLOR_GRIS_FONDO, anchor="w"
        )
        self.lbl_info_nombre.pack(fill=tk.X, pady=4)

        self.lbl_info_cantidad = tk.Label(
            self.frame_lateral, text="Cantidad: —",
            font=("Arial", 11), fg=COLOR_NEGRO, bg=COLOR_GRIS_FONDO, anchor="w"
        )
        self.lbl_info_cantidad.pack(fill=tk.X, pady=4)

        self.lbl_info_pcompra = tk.Label(
            self.frame_lateral, text="Precio Compra: —",
            font=("Arial", 11), fg=COLOR_NEGRO, bg=COLOR_GRIS_FONDO, anchor="w"
        )
        self.lbl_info_pcompra.pack(fill=tk.X, pady=4)

        self.lbl_info_pventa = tk.Label(
            self.frame_lateral, text="Precio Venta: —",
            font=("Arial", 11), fg=COLOR_NEGRO, bg=COLOR_GRIS_FONDO, anchor="w"
        )
        self.lbl_info_pventa.pack(fill=tk.X, pady=4)

        # Separador
        tk.Frame(self.frame_lateral, bg="#888888", height=1).pack(fill=tk.X, pady=12)

        # Nota
        self.lbl_nota = tk.Label(
            self.frame_lateral,
            text="Seleccione un producto de la tabla\npara ver sus detalles.",
            font=("Arial", 9, "italic"),
            fg="#666666",
            bg=COLOR_GRIS_FONDO,
            justify=tk.LEFT
        )
        self.lbl_nota.pack(anchor="w")

    # ============================================================
    # SECCIÓN 3: BOTONES DE ACCIÓN + BUSCADOR
    # ============================================================

    def _crear_botones_accion(self):
        """Crea los botones y el buscador en la parte inferior."""
        self.frame_botones = tk.Frame(self, bg=COLOR_GRIS_FONDO)
        self.frame_botones.pack(fill=tk.X, padx=40, pady=(0, 20))

        # ── Fila de botones ──
        self.frame_fila = tk.Frame(self.frame_botones, bg=COLOR_GRIS_FONDO)
        self.frame_fila.pack(fill=tk.X)

        # Botón "Importar Excel de Proveedor"
        self.btn_importar = tk.Button(
            self.frame_fila,
            text="Importar Excel de Proveedor",
            font=("Arial", 11, "bold"),
            bg=COLOR_VERDE_BOTON,
            fg=COLOR_NEGRO,
            activebackground=COLOR_VERDE_HOVER,
            activeforeground=COLOR_NEGRO,
            relief="flat",
            bd=0,
            cursor="hand2",
            width=26,
            height=2,
            command=self._importar_excel
        )
        self.btn_importar.pack(side=tk.LEFT, padx=(0, 10))

        # Botón "Agregar producto"
        self.btn_agregar = tk.Button(
            self.frame_fila,
            text="Agregar producto",
            font=("Arial", 11, "bold"),
            bg=COLOR_VERDE_BOTON,
            fg=COLOR_NEGRO,
            activebackground=COLOR_VERDE_HOVER,
            activeforeground=COLOR_NEGRO,
            relief="flat",
            bd=0,
            cursor="hand2",
            width=18,
            height=2,
            command=self._agregar_producto_manual
        )
        self.btn_agregar.pack(side=tk.LEFT, padx=(0, 10))

        # Botón "Borrar producto"
        self.btn_borrar = tk.Button(
            self.frame_fila,
            text="borrar producto",
            font=("Arial", 11, "bold"),
            bg=COLOR_VERDE_BOTON,
            fg=COLOR_NEGRO,
            activebackground=COLOR_ROJO_HOVER,
            activeforeground=COLOR_BLANCO,
            relief="flat",
            bd=0,
            cursor="hand2",
            width=16,
            height=2,
            command=self._borrar_producto
        )
        self.btn_borrar.pack(side=tk.LEFT, padx=(0, 10))

        # Espaciador
        tk.Frame(self.frame_fila, bg=COLOR_GRIS_FONDO).pack(side=tk.LEFT, expand=True)

        # Botón "Editar Producto"
        self.btn_editar = tk.Button(
            self.frame_fila,
            text="Editar Producto",
            font=("Arial", 11, "bold"),
            bg=COLOR_VERDE_BOTON,
            fg=COLOR_NEGRO,
            activebackground=COLOR_VERDE_HOVER,
            activeforeground=COLOR_NEGRO,
            relief="flat",
            bd=0,
            cursor="hand2",
            width=16,
            height=2,
            command=self._editar_producto
        )
        self.btn_editar.pack(side=tk.LEFT, padx=(0, 10))

        # Entry de búsqueda (buscar por id/nombre)
        self.entry_buscar = tk.Entry(
            self.frame_fila,
            font=("Arial", 11),
            bg=COLOR_BLANCO,
            fg=COLOR_NEGRO,
            relief="flat",
            bd=1,
            width=22
        )
        self.entry_buscar.pack(side=tk.LEFT, padx=(0, 0), ipady=8)
        self.entry_buscar.insert(0, "buscar por id/nombre")
        self.entry_buscar.config(fg="#888888")

        # Eventos del buscador
        self.entry_buscar.bind("<FocusIn>", self._on_focus_buscar)
        self.entry_buscar.bind("<FocusOut>", self._on_blur_buscar)
        self.entry_buscar.bind("<KeyRelease>", self._filtrar_tabla)

        # Hover effects
        self.btn_importar.bind("<Enter>", lambda e: self.btn_importar.config(bg=COLOR_VERDE_HOVER))
        self.btn_importar.bind("<Leave>", lambda e: self.btn_importar.config(bg=COLOR_VERDE_BOTON))
        self.btn_agregar.bind("<Enter>", lambda e: self.btn_agregar.config(bg=COLOR_VERDE_HOVER))
        self.btn_agregar.bind("<Leave>", lambda e: self.btn_agregar.config(bg=COLOR_VERDE_BOTON))
        self.btn_borrar.bind("<Enter>", lambda e: self.btn_borrar.config(bg=COLOR_ROJO_HOVER, fg=COLOR_BLANCO))
        self.btn_borrar.bind("<Leave>", lambda e: self.btn_borrar.config(bg=COLOR_VERDE_BOTON, fg=COLOR_NEGRO))
        self.btn_editar.bind("<Enter>", lambda e: self.btn_editar.config(bg=COLOR_VERDE_HOVER))
        self.btn_editar.bind("<Leave>", lambda e: self.btn_editar.config(bg=COLOR_VERDE_BOTON))

    # ============================================================
    # BÚSQUEDA EN TIEMPO REAL
    # ============================================================

    def _on_focus_buscar(self, event):
        if self.entry_buscar.get() == "buscar por id/nombre":
            self.entry_buscar.delete(0, tk.END)
            self.entry_buscar.config(fg=COLOR_NEGRO)

    def _on_blur_buscar(self, event):
        if not self.entry_buscar.get().strip():
            self.entry_buscar.insert(0, "buscar por id/nombre")
            self.entry_buscar.config(fg="#888888")

    def _filtrar_tabla(self, event=None):
        """Filtra la tabla dinámicamente por ID, código o nombre."""
        texto = self.entry_buscar.get().strip().lower()
        if texto == "buscar por id/nombre" or not texto:
            self._cargar_productos()
            return

        # Limpiar tabla
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Consulta con filtro
        consulta = """
            SELECT id, codigo_proveedor, nombre, cantidad, precio_compra, precio_venta
            FROM productos
            WHERE CAST(id AS TEXT) LIKE ?
               OR LOWER(codigo_proveedor) LIKE ?
               OR LOWER(nombre) LIKE ?
            ORDER BY id
        """
        patron = f"%{texto}%"
        resultado = query(consulta, (patron, patron, patron))

        if resultado:
            for fila in resultado:
                self.tree.insert("", tk.END, values=(
                    fila[0],
                    fila[1] if fila[1] else "",
                    fila[2],
                    fila[3],
                    f"{fila[4]:,.2f}",
                    f"{fila[5]:,.2f}"
                ))

    # ============================================================
    # CARGAR PRODUCTOS EN TABLA
    # ============================================================

    def _cargar_productos(self):
        """Carga todos los productos desde la BD al Treeview."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        consulta = """
            SELECT id, codigo_proveedor, nombre, cantidad, precio_compra, precio_venta
            FROM productos
            ORDER BY id
        """
        resultado = query(consulta)

        if resultado:
            for fila in resultado:
                self.tree.insert("", tk.END, values=(
                    fila[0],
                    fila[1] if fila[1] else "",
                    fila[2],
                    fila[3],
                    f"{fila[4]:,.2f}",
                    f"{fila[5]:,.2f}"
                ))

    # ============================================================
    # SELECCIÓN DE PRODUCTO
    # ============================================================

    def _on_seleccionar_producto(self, event):
        """Actualiza el panel lateral al seleccionar una fila."""
        seleccion = self.tree.selection()
        if not seleccion:
            return

        item = self.tree.item(seleccion[0])
        valores = item["values"]
        self.producto_seleccionado = valores[0]

        self.lbl_info_id.config(text=f"ID: {valores[0]}")
        self.lbl_info_codigo.config(text=f"Código Prov.: {valores[1]}")
        self.lbl_info_nombre.config(text=f"Nombre: {valores[2]}")
        self.lbl_info_cantidad.config(text=f"Cantidad: {valores[3]}")
        self.lbl_info_pcompra.config(text=f"Precio Compra: {valores[4]}")
        self.lbl_info_pventa.config(text=f"Precio Venta: {valores[5]}")
        self.lbl_nota.config(text="Producto seleccionado.\nDoble clic o 'Editar' para modificar.")

    # ============================================================
    # IMPORTAR EXCEL
    # ============================================================

    def _importar_excel(self):
        """Abre diálogo para seleccionar Excel y lo procesa."""
        if pd is None:
            messagebox.showerror(
                "Librería faltante",
                "Se requiere instalar 'pandas' y 'openpyxl'.\n\n"
                "Ejecute: pip install pandas openpyxl"
            )
            return

        ruta = filedialog.askopenfilename(
            title="Seleccionar Excel de Proveedor",
            filetypes=[("Archivos Excel", "*.xlsx *.xls"), ("Todos los archivos", "*.*")]
        )

        if not ruta:
            return

        productos, error = _procesar_excel(ruta)

        if error:
            messagebox.showerror("Error al importar", error)
            return

        if not productos:
            messagebox.showwarning("Sin productos", "No se encontraron productos válidos en el archivo.")
            return

        # Confirmar importación
        respuesta = messagebox.askyesno(
            "Confirmar importación",
            f"Se detectaron {len(productos)} productos válidos.\n\n"
            f"¿Desea importarlos a la base de datos?\n\n"
            f"Los productos existentes se actualizarán (cantidad y precio de compra).\n"
            f"El precio de venta existente NO se modificará."
        )

        if not respuesta:
            return

        # Guardar en BD
        try:
            insertados, actualizados = _guardar_productos_en_bd(productos)
            total = insertados + actualizados

            messagebox.showinfo(
                "Importación exitosa",
                f"✓ Importación completada.\n\n"
                f"Productos nuevos: {insertados}\n"
                f"Productos actualizados: {actualizados}\n"
                f"Total procesados: {total}"
            )
            self._cargar_productos()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron guardar los productos:\n{str(e)}")

    # ============================================================
    # AGREGAR PRODUCTO MANUAL
    # ============================================================

    def _agregar_producto_manual(self):
        """Abre diálogo para agregar un producto manualmente."""
        ventana = tk.Toplevel(self)
        ventana.title("Agregar Producto")
        ventana.configure(bg=COLOR_GRIS_FONDO)
        ventana.resizable(False, False)
        ventana.grab_set()
        ventana.geometry("380x420")

        tk.Label(
            ventana, text="Nuevo Producto",
            font=("Arial", 18, "bold"),
            fg=COLOR_VERDE_SIDEBAR, bg=COLOR_GRIS_FONDO
        ).pack(pady=(18, 18))

        frame_form = tk.Frame(ventana, bg=COLOR_GRIS_FONDO, padx=28)
        frame_form.pack(fill=tk.X)

        # Campos
        campos = [
            ("Código Proveedor:", "entry_codigo", False),
            ("Nombre / Producto:*", "entry_nombre", False),
            ("Cantidad:", "entry_cantidad", False),
            ("Precio Compra ($):", "entry_pcompra", False),
            ("Precio Venta ($):", "entry_pventa", False),
        ]

        self._campos_agregar = {}
        for label_text, attr_name, _ in campos:
            tk.Label(
                frame_form, text=label_text,
                font=("Arial", 11), fg=COLOR_NEGRO, bg=COLOR_GRIS_FONDO, anchor="w"
            ).pack(fill=tk.X, pady=(10, 2))

            entry = tk.Entry(
                frame_form, font=("Arial", 12),
                bg=COLOR_BLANCO, fg=COLOR_NEGRO, relief="flat", bd=1
            )
            entry.pack(fill=tk.X, ipady=6)
            self._campos_agregar[attr_name] = entry

        # Valores por defecto
        self._campos_agregar["entry_cantidad"].insert(0, "0")
        self._campos_agregar["entry_pcompra"].insert(0, "0.00")
        self._campos_agregar["entry_pventa"].insert(0, "0.00")

        tk.Frame(ventana, bg=COLOR_GRIS_FONDO, height=15).pack()

        btn_confirmar = tk.Button(
            ventana, text="Confirmar",
            font=("Arial", 12, "bold"),
            bg=COLOR_VERDE_BOTON_ACCION, fg=COLOR_BLANCO,
            activebackground="#1a5c1a", activeforeground=COLOR_BLANCO,
            relief="flat", bd=0, cursor="hand2",
            width=18, height=2,
            command=lambda: self._confirmar_agregar(ventana)
        )
        btn_confirmar.pack(pady=(0, 18))

        btn_confirmar.bind("<Enter>", lambda e: btn_confirmar.config(bg="#1a5c1a"))
        btn_confirmar.bind("<Leave>", lambda e: btn_confirmar.config(bg=COLOR_VERDE_BOTON_ACCION))

    def _confirmar_agregar(self, ventana):
        """Valida e inserta el producto manual en la BD."""
        codigo = self._campos_agregar["entry_codigo"].get().strip()
        nombre = self._campos_agregar["entry_nombre"].get().strip()
        cantidad = _limpiar_valor_numerico(
            self._campos_agregar["entry_cantidad"].get(), tipo="int", default=0
        )
        pcompra = _limpiar_valor_numerico(
            self._campos_agregar["entry_pcompra"].get(), tipo="float", default=0.0
        )
        pventa = _limpiar_valor_numerico(
            self._campos_agregar["entry_pventa"].get(), tipo="float", default=0.0
        )

        if not nombre:
            messagebox.showwarning("Campo obligatorio", "El nombre del producto es obligatorio.", parent=ventana)
            return

        try:
            query(
                """INSERT INTO productos
                    (codigo_proveedor, nombre, cantidad, precio_compra, precio_venta, categoria)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (codigo, nombre, cantidad, pcompra, pventa, "")
            )
            messagebox.showinfo("Éxito", f"Producto '{nombre}' agregado correctamente.", parent=ventana)
            ventana.destroy()
            self._cargar_productos()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo agregar el producto.\n{str(e)}", parent=ventana)

    # ============================================================
    # BORRAR PRODUCTO
    # ============================================================

    def _borrar_producto(self):
        """Elimina el producto seleccionado de la BD."""
        if self.producto_seleccionado is None:
            messagebox.showwarning("Sin selección", "Seleccione un producto de la tabla para borrar.")
            return

        # Obtener nombre para el mensaje
        seleccion = self.tree.selection()
        item = self.tree.item(seleccion[0])
        valores = item["values"]
        nombre_prod = valores[2]

        respuesta = messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Está seguro de que desea eliminar el producto '{nombre_prod}'?\n\n"
            "Esta acción no se puede deshacer."
        )

        if respuesta:
            try:
                query("DELETE FROM productos WHERE id = ?", (self.producto_seleccionado,))
                messagebox.showinfo("Éxito", f"Producto '{nombre_prod}' eliminado correctamente.")
                self.producto_seleccionado = None
                self._resetear_panel_lateral()
                self._cargar_productos()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo eliminar el producto.\n{str(e)}")

    # ============================================================
    # EDITAR PRODUCTO (DIÁLOGO EMERGENTE)
    # ============================================================

    def _editar_producto(self):
        """Abre diálogo para editar nombre y precio de venta del producto seleccionado."""
        if self.producto_seleccionado is None:
            messagebox.showwarning("Sin selección", "Seleccione un producto de la tabla para editar.")
            return

        # Obtener datos actuales
        seleccion = self.tree.selection()
        item = self.tree.item(seleccion[0])
        valores = item["values"]

        prod_id = valores[0]
        codigo = valores[1]
        nombre_actual = valores[2]
        cantidad = valores[3]
        pcompra = valores[4]
        pventa_actual = valores[5]

        # Limpiar formato de moneda para edición
        pventa_limpio = str(pventa_actual).replace(",", "").replace("$", "").strip()

        ventana = tk.Toplevel(self)
        ventana.title(f"Editar Producto - ID {prod_id}")
        ventana.configure(bg=COLOR_GRIS_FONDO)
        ventana.resizable(False, False)
        ventana.grab_set()
        ventana.geometry("380x480")

        tk.Label(
            ventana, text="Editar Producto",
            font=("Arial", 18, "bold"),
            fg=COLOR_VERDE_SIDEBAR, bg=COLOR_GRIS_FONDO
        ).pack(pady=(18, 10))

        # Info de campos bloqueados
        tk.Label(
            ventana,
            text="Los campos bloqueados solo se modifican vía importación de Excel.",
            font=("Arial", 9, "italic"),
            fg="#666666", bg=COLOR_GRIS_FONDO,
            wraplength=340, justify=tk.CENTER
        ).pack(pady=(0, 10))

        frame_form = tk.Frame(ventana, bg=COLOR_GRIS_FONDO, padx=28)
        frame_form.pack(fill=tk.X)

        # ID (bloqueado)
        tk.Label(frame_form, text="ID:", font=("Arial", 11), fg=COLOR_NEGRO, bg=COLOR_GRIS_FONDO, anchor="w").pack(fill=tk.X, pady=(8, 2))
        entry_id = tk.Entry(frame_form, font=("Arial", 12), bg="#e0e0e0", fg="#666666", relief="flat", bd=1)
        entry_id.pack(fill=tk.X, ipady=6)
        entry_id.insert(0, str(prod_id))
        entry_id.config(state="disabled")

        # Código Proveedor (bloqueado)
        tk.Label(frame_form, text="Código Proveedor:", font=("Arial", 11), fg=COLOR_NEGRO, bg=COLOR_GRIS_FONDO, anchor="w").pack(fill=tk.X, pady=(8, 2))
        entry_codigo = tk.Entry(frame_form, font=("Arial", 12), bg="#e0e0e0", fg="#666666", relief="flat", bd=1)
        entry_codigo.pack(fill=tk.X, ipady=6)
        entry_codigo.insert(0, str(codigo))
        entry_codigo.config(state="disabled")

        # Nombre (editable)
        tk.Label(frame_form, text="Nombre / Producto:*", font=("Arial", 11), fg=COLOR_NEGRO, bg=COLOR_GRIS_FONDO, anchor="w").pack(fill=tk.X, pady=(8, 2))
        entry_nombre = tk.Entry(frame_form, font=("Arial", 12), bg=COLOR_BLANCO, fg=COLOR_NEGRO, relief="flat", bd=1)
        entry_nombre.pack(fill=tk.X, ipady=6)
        entry_nombre.insert(0, nombre_actual)

        # Cantidad (bloqueada)
        tk.Label(frame_form, text="Cantidad:", font=("Arial", 11), fg=COLOR_NEGRO, bg=COLOR_GRIS_FONDO, anchor="w").pack(fill=tk.X, pady=(8, 2))
        entry_cantidad = tk.Entry(frame_form, font=("Arial", 12), bg="#e0e0e0", fg="#666666", relief="flat", bd=1)
        entry_cantidad.pack(fill=tk.X, ipady=6)
        entry_cantidad.insert(0, str(cantidad))
        entry_cantidad.config(state="disabled")

        # Precio Compra (bloqueado)
        tk.Label(frame_form, text="Precio Compra ($):", font=("Arial", 11), fg=COLOR_NEGRO, bg=COLOR_GRIS_FONDO, anchor="w").pack(fill=tk.X, pady=(8, 2))
        entry_pcompra = tk.Entry(frame_form, font=("Arial", 12), bg="#e0e0e0", fg="#666666", relief="flat", bd=1)
        entry_pcompra.pack(fill=tk.X, ipady=6)
        entry_pcompra.insert(0, str(pcompra))
        entry_pcompra.config(state="disabled")

        # Precio Venta (editable)
        tk.Label(frame_form, text="Precio Venta ($):*", font=("Arial", 11), fg=COLOR_NEGRO, bg=COLOR_GRIS_FONDO, anchor="w").pack(fill=tk.X, pady=(8, 2))
        entry_pventa = tk.Entry(frame_form, font=("Arial", 12), bg=COLOR_BLANCO, fg=COLOR_NEGRO, relief="flat", bd=1)
        entry_pventa.pack(fill=tk.X, ipady=6)
        entry_pventa.insert(0, pventa_limpio)

        tk.Frame(ventana, bg=COLOR_GRIS_FONDO, height=15).pack()

        btn_guardar = tk.Button(
            ventana, text="Guardar Cambios",
            font=("Arial", 12, "bold"),
            bg=COLOR_VERDE_BOTON_ACCION, fg=COLOR_BLANCO,
            activebackground="#1a5c1a", activeforeground=COLOR_BLANCO,
            relief="flat", bd=0, cursor="hand2",
            width=18, height=2,
            command=lambda: self._confirmar_edicion(ventana, prod_id, entry_nombre, entry_pventa)
        )
        btn_guardar.pack(pady=(0, 18))

        btn_guardar.bind("<Enter>", lambda e: btn_guardar.config(bg="#1a5c1a"))
        btn_guardar.bind("<Leave>", lambda e: btn_guardar.config(bg=COLOR_VERDE_BOTON_ACCION))

    def _confirmar_edicion(self, ventana, prod_id, entry_nombre, entry_pventa):
        """Guarda los cambios de edición (solo nombre y precio venta)."""
        nuevo_nombre = entry_nombre.get().strip()
        nuevo_pventa = _limpiar_valor_numerico(entry_pventa.get(), tipo="float", default=0.0)

        if not nuevo_nombre:
            messagebox.showwarning("Campo obligatorio", "El nombre del producto es obligatorio.", parent=ventana)
            return

        try:
            query(
                "UPDATE productos SET nombre = ?, precio_venta = ? WHERE id = ?",
                (nuevo_nombre, nuevo_pventa, prod_id)
            )
            messagebox.showinfo("Éxito", "Producto actualizado correctamente.", parent=ventana)
            ventana.destroy()
            self._cargar_productos()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo actualizar el producto.\n{str(e)}", parent=ventana)

    def _resetear_panel_lateral(self):
        """Limpia la info del panel lateral."""
        self.lbl_info_id.config(text="ID: —")
        self.lbl_info_codigo.config(text="Código Prov.: —")
        self.lbl_info_nombre.config(text="Nombre: —")
        self.lbl_info_cantidad.config(text="Cantidad: —")
        self.lbl_info_pcompra.config(text="Precio Compra: —")
        self.lbl_info_pventa.config(text="Precio Venta: —")
        self.lbl_nota.config(text="Seleccione un producto de la tabla\npara ver sus detalles.")