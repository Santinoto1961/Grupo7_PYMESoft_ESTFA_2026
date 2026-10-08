#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================
stock.py - Módulo de Gestión de Stock (PYMEsoft)
============================================================
Misma estructura que Clientes / Proveedores (título, rectángulo
verde con tabla + panel de información, botones abajo), más:
  - Búsqueda en tiempo real + filtros por proveedor y estado
  - Tabla ordenable por columna, con filas coloreadas según el
    estado del stock
  - Panel lateral con margen de ganancia y resumen del inventario
  - Importación de Excel heterogéneo de proveedores
  - Alta, edición (nombre y precio de venta) y baja de productos

Autor: Desarrollador Senior
Fecha: 2026-09-30
============================================================
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
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
from compras import (
    crear_tablas_compras, registrar_compra, calcular_monto_compra,
    existe_compra_similar,
)


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
COLOR_FONDO_INTERNO      = "#f5f5f5"

# Extras de esta pantalla (hover, texto secundario y alertas de stock)
COLOR_VERDE_ACCION_HOVER = "#1a5c1a"
COLOR_TEXTO_SUAVE        = "#555555"
COLOR_FILA_SIN_STOCK     = "#f3c6c6"
COLOR_FILA_BAJO          = "#f6e7b4"


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
    Debe tener nombre, y algún valor numérico.
    """
    # Verificar que no esté completamente vacía
    if row.isna().all():
        return False

    tiene_nombre = False
    if "nombre" in mapeo:
        val = row[mapeo["nombre"]]
        if pd.notna(val) and str(val).strip() != "":
            tiene_nombre = True

    if not tiene_nombre:
        return False

    # Aceptamos la fila si tiene nombre definido (con o sin valor numérico,
    # puede ser un producto con stock 0)
    return True


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

    if "nombre" not in mapeo:
        return None, (
            "No se pudieron identificar las columnas necesarias en el Excel.\n"
            "Columnas detectadas: " + ", ".join(str(c) for c in df.columns)
        )

    productos = []
    for _, row in df.iterrows():
        if not _es_fila_valida(row, mapeo):
            continue

        producto = {
            "nombre": "",
            "cantidad": 0,
            "precio_compra": 0.0,
            "precio_venta": 0.0,
            "categoria": ""
        }

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

        # Solo agregar si tiene nombre
        if producto["nombre"]:
            productos.append(producto)

    if not productos:
        return None, "No se encontraron productos válidos en el archivo."

    return productos, None


def _guardar_productos_en_bd(productos, id_proveedor):
    """
    Guarda o actualiza los productos en la base de datos, asociados al
    proveedor elegido por el usuario (id_proveedor = PK real de la tabla
    proveedores). No se usa ningún código del Excel para identificar al
    proveedor: el único identificador válido es id_proveedor.
    REGLA ESTRICTA: el precio_venta existente NUNCA se sobrescribe.
    Retorna: (cantidad_insertados, cantidad_actualizados)
    """
    insertados = 0
    actualizados = 0

    for prod in productos:
        nombre = prod["nombre"]
        cantidad = prod["cantidad"]
        precio_compra = prod["precio_compra"]

        # Buscar coincidencia por nombre dentro de los productos del MISMO proveedor
        existente = query(
            "SELECT id, precio_venta FROM productos WHERE nombre = ? AND id_proveedor = ?",
            (nombre, id_proveedor)
        )

        if existente and len(existente) > 0:
            # Actualizar: NO tocar precio_venta
            prod_id = existente[0][0]
            prod["id_producto"] = prod_id   # para el detalle de la compra
            query(
                """UPDATE productos SET
                    nombre = ?,
                    stock = ?,
                    precio_costo = ?,
                    id_proveedor = ?
                   WHERE id = ?""",
                (nombre, cantidad, precio_compra, id_proveedor, prod_id)
            )
            actualizados += 1
        else:
            # Insertar nuevo: precio_venta = 0.0
            query(
                """INSERT INTO productos
                    (nombre, descripcion, stock, precio_costo, precio_venta, categoria, id_proveedor)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (nombre, "", cantidad, precio_compra, 0.0, "", id_proveedor)
            )
            nuevo = query(
                "SELECT id FROM productos WHERE nombre = ? AND id_proveedor = ? "
                "ORDER BY id DESC LIMIT 1", (nombre, id_proveedor))
            prod["id_producto"] = nuevo[0][0] if nuevo else None
            insertados += 1

    return insertados, actualizados


# ============================================================
# CREAR TABLA DE PRODUCTOS (si no existe)
# ============================================================

def _crear_tabla_productos():
    """
    Crea la tabla productos si no existe (con el esquema real de archivo.db:
    nombre, descripcion, precio_costo, precio_venta, stock, categoria, id_proveedor).
    """
    query("""
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            descripcion TEXT,
            precio_costo REAL NOT NULL DEFAULT 0.0,
            precio_venta REAL NOT NULL DEFAULT 0.0,
            stock INTEGER NOT NULL DEFAULT 0,
            categoria TEXT,
            id_proveedor INTEGER
        )
    """)


# Llamar al iniciar el módulo
_crear_tabla_productos()
crear_tablas_compras()


# ============================================================
# CONSTANTES DE LA PANTALLA
# ============================================================

STOCK_BAJO_UMBRAL = 5                      # <= a este valor se considera "stock bajo"
PLACEHOLDER_BUSCAR = "Buscar por ID o nombre..."
FILTRO_TODOS_PROV = "Todos los proveedores"
FILTRO_SIN_PROV = "(sin proveedor)"
FILTRO_TODOS_ESTADO = "Todos los estados"

# (clave, título, ancho, alineación, se estira)
COLUMNAS = [
    ("id",            "ID",          40,  "center", False),
    ("nombre",        "Producto",    160, "w",      True),
    ("proveedor",     "Proveedor",   100, "w",      False),
    ("cantidad",      "Cantidad",    80,  "center", False),
    ("precio_compra", "Compra ($)",  90, "e",      False),
    ("precio_venta",  "Venta ($)",   90, "e",      False),
    ("estado",        "Estado",      100, "center", False),
]

# Índice de la tupla de datos por la que se ordena cada columna
INDICE_ORDEN = {
    "id": 0, "nombre": 1, "proveedor": 2, "cantidad": 3,
    "precio_compra": 4, "precio_venta": 5, "estado": 3,
}


def _estado_stock(stock):
    """Devuelve (texto, tag) según la cantidad disponible."""
    if stock <= 0:
        return "⚠ Sin stock", "sin_stock"
    if stock <= STOCK_BAJO_UMBRAL:
        return "⚡ Stock bajo", "stock_bajo"
    return "✔ Disponible", ""


# ============================================================
# CLASE PRINCIPAL: VistaStock
# ============================================================

class VistaStock(tk.Frame):
    """
    Vista de gestión de stock embebida en el área de contenido de
    main_window.py. Misma estructura que Clientes / Proveedores:

      - Título grande arriba
      - Rectángulo verde con la lista (tabla a la izquierda,
        panel de información a la derecha)
      - Botones de acción abajo

    Extras de Stock: búsqueda + filtros, orden por columna, filas
    coloreadas según el estado del stock, margen de ganancia y
    resumen del inventario.
    """

    def __init__(self, parent_frame):
        super().__init__(parent_frame, bg=COLOR_GRIS_FONDO)
        self.parent = parent_frame
        self.producto_seleccionado = None   # ID del producto seleccionado
        self._filas = []                    # filas actuales (tuplas crudas de la BD)
        self._filas_por_id = {}             # id -> tupla cruda
        self._orden_col = None
        self._orden_desc = False
        self._total_productos = 0

        self._configurar_estilos()
        self.pack(fill=tk.BOTH, expand=True)

        self._crear_titulo()
        # Los botones se empaquetan ANTES (side=BOTTOM) para que queden
        # siempre visibles y el rectángulo verde ocupe el espacio sobrante.
        self._crear_botones_accion()
        self._crear_panel_principal()

        self._cargar_filtro_proveedores()
        self._refrescar()

    # ------------------------------------------------------------
    # Estilo de la tabla (no cambia el tema global de ttk)
    # ------------------------------------------------------------
    def _configurar_estilos(self):
        style = ttk.Style()

        def mapa_sin_bug(opcion):
            # Evita el bug de Tk 8.6.9 donde los tags pisan la selección
            return [e for e in style.map("Treeview", query_opt=opcion)
                    if e[:2] != ("!disabled", "!selected")]

        style.configure("Stock.Treeview", rowheight=24)
        style.map(
            "Stock.Treeview",
            foreground=mapa_sin_bug("foreground"),
            background=mapa_sin_bug("background")
        )

    # ------------------------------------------------------------
    # Helpers de UI
    # ------------------------------------------------------------
    def _boton(self, parent, texto, comando, bg, fg, hover, hover_fg=None, ancho=None):
        hover_fg = hover_fg or fg
        btn = tk.Button(
            parent, text=texto, font=("Arial", 11, "bold"),
            bg=bg, fg=fg, activebackground=hover, activeforeground=hover_fg,
            relief="flat", bd=0, cursor="hand2", command=comando
        )
        if ancho:
            btn.config(width=ancho, height=2)
        else:
            btn.config(padx=16, pady=8)
        btn.bind("<Enter>", lambda e: btn.config(bg=hover, fg=hover_fg))
        btn.bind("<Leave>", lambda e: btn.config(bg=bg, fg=fg))
        return btn

    def _crear_dialogo(self, titulo, subtitulo=""):
        v = tk.Toplevel(self)
        v.title(titulo)
        v.configure(bg=COLOR_FONDO_INTERNO)
        v.resizable(False, False)
        v.transient(self.winfo_toplevel())
        tk.Label(
            v, text=titulo, font=("Arial", 18, "bold"),
            fg=COLOR_VERDE_SIDEBAR, bg=COLOR_FONDO_INTERNO
        ).pack(pady=(20, 4 if subtitulo else 12), padx=30)
        if subtitulo:
            tk.Label(
                v, text=subtitulo, font=("Arial", 9, "italic"),
                fg="#666666", bg=COLOR_FONDO_INTERNO,
                wraplength=340, justify=tk.CENTER
            ).pack(pady=(0, 8), padx=30)
        return v

    def _mostrar_dialogo(self, v, ancho=420):
        """Centra el diálogo sobre la ventana principal y lo hace modal."""
        v.update_idletasks()
        root = self.winfo_toplevel()
        w = max(v.winfo_reqwidth(), ancho)
        h = v.winfo_reqheight()
        x = root.winfo_rootx() + (root.winfo_width() - w) // 2
        y = root.winfo_rooty() + (root.winfo_height() - h) // 2
        v.geometry(f"{w}x{h}+{max(x, 0)}+{max(y, 0)}")
        v.grab_set()

    def _campo(self, parent, etiqueta, valor="", bloqueado=False):
        tk.Label(
            parent, text=etiqueta, font=("Arial", 11),
            fg=COLOR_NEGRO, bg=COLOR_FONDO_INTERNO, anchor="w"
        ).pack(fill=tk.X, pady=(10, 2))
        e = tk.Entry(
            parent, font=("Arial", 12), bg=COLOR_BLANCO, fg=COLOR_NEGRO,
            relief="flat", bd=0, highlightthickness=1,
            highlightbackground="#888888", highlightcolor=COLOR_VERDE_SIDEBAR
        )
        e.insert(0, str(valor))
        e.pack(fill=tk.X, ipady=6)
        if bloqueado:
            e.config(state="disabled", disabledbackground="#e0e0e0",
                     disabledforeground="#666666")
        return e

    # ============================================================
    # SECCIÓN 1: TÍTULO
    # ============================================================

    def _crear_titulo(self):
        self.lbl_titulo = tk.Label(
            self, text="STOCK:", font=("Arial", 32, "bold"),
            fg=COLOR_NEGRO, bg=COLOR_GRIS_FONDO
        )
        self.lbl_titulo.pack(anchor="w", padx=40, pady=(30, 15))

    # ============================================================
    # SECCIÓN 2: PANEL PRINCIPAL (rectángulo verde)
    # ============================================================

    def _crear_panel_principal(self):
        self.frame_panel = tk.Frame(self, bg=COLOR_VERDE_SIDEBAR, padx=8, pady=8)
        self.frame_panel.pack(fill=tk.BOTH, expand=True, padx=40, pady=(0, 20))

        # Encabezado del rectángulo: subtítulo + contador de resultados
        cab = tk.Frame(self.frame_panel, bg=COLOR_VERDE_SIDEBAR)
        cab.pack(fill=tk.X, pady=(0, 8))
        self.lbl_subtitulo = tk.Label(
            cab, text="Lista de productos:", font=("Arial", 16, "bold"),
            fg=COLOR_BLANCO, bg=COLOR_VERDE_SIDEBAR
        )
        self.lbl_subtitulo.pack(side=tk.LEFT)
        self.lbl_contador = tk.Label(
            cab, text="", font=("Arial", 11, "bold"),
            fg=COLOR_BLANCO, bg=COLOR_VERDE_SIDEBAR
        )
        self.lbl_contador.pack(side=tk.RIGHT, anchor="s")

        self.frame_interno = tk.Frame(self.frame_panel, bg=COLOR_FONDO_INTERNO)
        self.frame_interno.pack(fill=tk.BOTH, expand=True)

        self._crear_panel_lateral()
        self._crear_tabla_stock()

    # ------------------------------------------------------------
    # Tabla + filtros
    # ------------------------------------------------------------
    def _crear_tabla_stock(self):
        self.frame_tabla = tk.Frame(self.frame_interno, bg=COLOR_FONDO_INTERNO)
        self.frame_tabla.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 2))

        # ---- Fila de búsqueda y filtros ----
        filtros = tk.Frame(self.frame_tabla, bg=COLOR_FONDO_INTERNO)
        filtros.pack(fill=tk.X, padx=10, pady=(10, 0))

        self.entry_buscar = tk.Entry(
            filtros, font=("Arial", 11), bg=COLOR_BLANCO, fg="#888888",
            relief="flat", bd=0, width=20, highlightthickness=1,
            highlightbackground="#888888", highlightcolor=COLOR_VERDE_SIDEBAR
        )
        self.entry_buscar.insert(0, PLACEHOLDER_BUSCAR)
        self.entry_buscar.pack(side=tk.LEFT, ipady=5, padx=(0, 8))
        self.entry_buscar.bind("<FocusIn>", self._on_focus_buscar)
        self.entry_buscar.bind("<FocusOut>", self._on_blur_buscar)
        self.entry_buscar.bind("<KeyRelease>", lambda e: self._cargar_productos())

        self.combo_proveedor = ttk.Combobox(
            filtros, font=("Arial", 10), state="readonly", width=20,
            values=[FILTRO_TODOS_PROV]
        )
        self.combo_proveedor.current(0)
        self.combo_proveedor.pack(side=tk.LEFT, ipady=3, padx=(0, 8))
        self.combo_proveedor.bind("<<ComboboxSelected>>", lambda e: self._cargar_productos())

        self.combo_estado = ttk.Combobox(
            filtros, font=("Arial", 10), state="readonly", width=16,
            values=[FILTRO_TODOS_ESTADO, "Con stock", "Stock bajo", "Sin stock"]
        )
        self.combo_estado.current(0)
        self.combo_estado.pack(side=tk.LEFT, ipady=3)
        self.combo_estado.bind("<<ComboboxSelected>>", lambda e: self._cargar_productos())

        # ---- Tabla ----
        lista = tk.Frame(self.frame_tabla, bg=COLOR_FONDO_INTERNO)
        lista.pack(fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(
            lista, style="Stock.Treeview",
            columns=[c[0] for c in COLUMNAS],
            show="headings", height=12, selectmode="browse"
        )
        for clave, titulo, ancho, ancla, estira in COLUMNAS:
            self.tree.heading(clave, text=titulo, command=lambda c=clave: self._ordenar_por(c))
            self.tree.column(clave, width=ancho, minwidth=40, anchor=ancla, stretch=estira)

        scroll = ttk.Scrollbar(lista, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=10)

        # Colores por estado / filas alternadas
        self.tree.tag_configure("par", background=COLOR_BLANCO)
        self.tree.tag_configure("impar", background=COLOR_FONDO_INTERNO)
        self.tree.tag_configure("stock_bajo", background=COLOR_FILA_BAJO)
        self.tree.tag_configure("sin_stock", background=COLOR_FILA_SIN_STOCK)

        self.tree.bind("<<TreeviewSelect>>", self._on_seleccionar_producto)
        self.tree.bind("<Double-1>", lambda e: self._editar_producto())

    # ------------------------------------------------------------
    # Panel lateral: información del producto + resumen
    # ------------------------------------------------------------
    def _crear_panel_lateral(self):
        self.frame_lateral = tk.Frame(self.frame_interno, bg=COLOR_FONDO_INTERNO, width=280)
        self.frame_lateral.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)
        self.frame_lateral.pack_propagate(False)

        tk.Label(
            self.frame_lateral, text="Información del producto:",
            font=("Arial", 12, "bold"), fg=COLOR_NEGRO, bg=COLOR_FONDO_INTERNO
        ).pack(anchor="w", pady=(0, 8))

        self._titulos_det = {
            "id": "ID", "nombre": "Nombre", "proveedor": "Proveedor",
            "cantidad": "Cantidad", "pcompra": "Precio compra",
            "pventa": "Precio venta", "margen": "Margen",
        }
        self.det = {}
        for clave, titulo in self._titulos_det.items():
            lbl = tk.Label(
                self.frame_lateral, text=f"{titulo}: —", font=("Arial", 11),
                fg=COLOR_NEGRO, bg=COLOR_FONDO_INTERNO, anchor="w",
                justify=tk.LEFT, wraplength=250
            )
            lbl.pack(fill=tk.X, pady=2)
            self.det[clave] = lbl

        tk.Frame(self.frame_lateral, bg="#888888", height=1).pack(fill=tk.X, pady=10)

        tk.Label(
            self.frame_lateral, text="Resumen del inventario:",
            font=("Arial", 12, "bold"), fg=COLOR_NEGRO, bg=COLOR_FONDO_INTERNO
        ).pack(anchor="w", pady=(0, 6))

        self._titulos_res = {
            "productos": "Productos", "unidades": "Unidades",
            "sin_stock": "⚠ Sin stock", "bajo": f"⚡ Stock bajo (≤{STOCK_BAJO_UMBRAL})",
            "valor": "Valor a costo",
        }
        colores_res = {"sin_stock": COLOR_ROJO_CERRAR, "bajo": "#8a5a00"}
        self.res = {}
        for clave, titulo in self._titulos_res.items():
            lbl = tk.Label(
                self.frame_lateral, text=f"{titulo}: —", font=("Arial", 10),
                fg=colores_res.get(clave, COLOR_NEGRO), bg=COLOR_FONDO_INTERNO, anchor="w"
            )
            lbl.pack(fill=tk.X, pady=1)
            self.res[clave] = lbl

    def _set_det(self, clave, valor, color=COLOR_NEGRO):
        self.det[clave].config(text=f"{self._titulos_det[clave]}: {valor}", fg=color)

    def _resetear_detalle(self):
        for clave in self.det:
            self._set_det(clave, "—")

    def _mostrar_detalle(self, pid):
        fila = self._filas_por_id.get(pid)
        if not fila:
            self._resetear_detalle()
            return
        _, nombre, prov, stock, pc, pv = fila

        self._set_det("id", pid)
        self._set_det("nombre", nombre)
        self._set_det("proveedor", prov or "—")
        self._set_det("cantidad", stock)
        self._set_det("pcompra", f"$ {pc:,.2f}")
        self._set_det("pventa", f"$ {pv:,.2f}")

        if pv <= 0:
            self._set_det("margen", "⚠ sin precio de venta", COLOR_ROJO_CERRAR)
        elif pc > 0:
            margen = (pv - pc) / pc * 100
            self._set_det("margen", f"{margen:,.1f} %",
                          COLOR_ROJO_CERRAR if margen < 0 else COLOR_VERDE_SIDEBAR)
        else:
            self._set_det("margen", "—")

    def _on_seleccionar_producto(self, event):
        seleccion = self.tree.selection()
        if not seleccion:
            return
        self.producto_seleccionado = int(seleccion[0])
        self._mostrar_detalle(self.producto_seleccionado)

    def _actualizar_resumen(self):
        res = query(
            """SELECT COUNT(*),
                      COALESCE(SUM(stock), 0),
                      COALESCE(SUM(CASE WHEN stock <= 0 THEN 1 ELSE 0 END), 0),
                      COALESCE(SUM(CASE WHEN stock > 0 AND stock <= ? THEN 1 ELSE 0 END), 0),
                      COALESCE(SUM(stock * precio_costo), 0)
               FROM productos""",
            (STOCK_BAJO_UMBRAL,)
        )
        total, unidades, sin_stock, bajo, valor = res[0] if res else (0, 0, 0, 0, 0)
        valores = {
            "productos": f"{total:,}", "unidades": f"{unidades:,}",
            "sin_stock": f"{sin_stock:,}", "bajo": f"{bajo:,}",
            "valor": f"$ {valor:,.2f}",
        }
        for clave, texto in valores.items():
            self.res[clave].config(text=f"{self._titulos_res[clave]}: {texto}")
        self._total_productos = total

    # ============================================================
    # SECCIÓN 3: BOTONES DE ACCIÓN
    # ============================================================

    def _crear_botones_accion(self):
        self.frame_botones = tk.Frame(self, bg=COLOR_GRIS_FONDO)
        self.frame_botones.pack(side=tk.BOTTOM, fill=tk.X, padx=40, pady=(0, 10))

        fila = tk.Frame(self.frame_botones, bg=COLOR_GRIS_FONDO)
        fila.pack(fill=tk.X)

        self._boton(
            fila, "Editar producto", self._editar_producto,
            COLOR_VERDE_BOTON, COLOR_NEGRO, COLOR_VERDE_HOVER, COLOR_NEGRO, ancho=18
        ).pack(side=tk.LEFT, padx=(0, 10))
        self._boton(
            fila, "Agregar producto", self._agregar_producto_manual,
            COLOR_VERDE_BOTON, COLOR_NEGRO, COLOR_VERDE_HOVER, COLOR_NEGRO, ancho=18
        ).pack(side=tk.LEFT, padx=(0, 10))
        self._boton(
            fila, "Eliminar producto", self._borrar_producto,
            COLOR_ROJO_CERRAR, COLOR_BLANCO, COLOR_ROJO_HOVER, ancho=18
        ).pack(side=tk.LEFT, padx=(0, 10))

        tk.Frame(fila, bg=COLOR_GRIS_FONDO).pack(side=tk.LEFT, expand=True)

        self._boton(
            fila, "Importar Excel de Proveedor", self._importar_excel,
            COLOR_VERDE_BOTON_ACCION, COLOR_BLANCO, COLOR_VERDE_ACCION_HOVER, ancho=26
        ).pack(side=tk.LEFT)

    # ============================================================
    # BÚSQUEDA, FILTROS Y ORDEN
    # ============================================================

    def _on_focus_buscar(self, event):
        if self.entry_buscar.get() == PLACEHOLDER_BUSCAR:
            self.entry_buscar.delete(0, tk.END)
            self.entry_buscar.config(fg=COLOR_NEGRO)

    def _on_blur_buscar(self, event):
        if not self.entry_buscar.get().strip():
            self.entry_buscar.delete(0, tk.END)
            self.entry_buscar.insert(0, PLACEHOLDER_BUSCAR)
            self.entry_buscar.config(fg="#888888")

    def _texto_busqueda(self):
        texto = self.entry_buscar.get().strip()
        return "" if texto == PLACEHOLDER_BUSCAR else texto.lower()

    def _cargar_filtro_proveedores(self):
        """Rellena el combo de proveedores conservando la selección actual."""
        actual = self.combo_proveedor.get()
        proveedores = query("SELECT id, nombre FROM proveedores ORDER BY nombre") or []
        valores = [FILTRO_TODOS_PROV, FILTRO_SIN_PROV] + [f"{pid} - {n}" for pid, n in proveedores]
        self.combo_proveedor.config(values=valores)
        self.combo_proveedor.set(actual if actual in valores else FILTRO_TODOS_PROV)

    def _actualizar_encabezados(self):
        for clave, titulo, *_ in COLUMNAS:
            flecha = ""
            if clave == self._orden_col:
                flecha = " ▼" if self._orden_desc else " ▲"
            self.tree.heading(clave, text=titulo + flecha)

    def _ordenar_por(self, columna):
        if self._orden_col == columna:
            self._orden_desc = not self._orden_desc
        else:
            self._orden_col = columna
            self._orden_desc = False
        self._pintar_filas()

    # ------------------------------------------------------------
    # Carga de datos (aplica búsqueda + filtros)
    # ------------------------------------------------------------
    def _cargar_productos(self):
        condiciones, params = [], []

        texto = self._texto_busqueda()
        if texto:
            condiciones.append("(CAST(p.id AS TEXT) LIKE ? OR LOWER(p.nombre) LIKE ?)")
            params += [f"%{texto}%", f"%{texto}%"]

        prov = self.combo_proveedor.get()
        if prov == FILTRO_SIN_PROV:
            condiciones.append("p.id_proveedor IS NULL")
        elif prov and prov != FILTRO_TODOS_PROV:
            condiciones.append("p.id_proveedor = ?")
            params.append(int(prov.split(" - ")[0]))

        estado = self.combo_estado.get()
        if estado == "Sin stock":
            condiciones.append("p.stock <= 0")
        elif estado == "Stock bajo":
            condiciones.append("p.stock > 0 AND p.stock <= ?")
            params.append(STOCK_BAJO_UMBRAL)
        elif estado == "Con stock":
            condiciones.append("p.stock > 0")

        where = (" WHERE " + " AND ".join(condiciones)) if condiciones else ""
        filas = query(
            f"""SELECT p.id, p.nombre, pr.nombre, p.stock, p.precio_costo, p.precio_venta
                FROM productos p
                LEFT JOIN proveedores pr ON p.id_proveedor = pr.id
                {where}
                ORDER BY p.id""",
            tuple(params)
        ) or []

        self._filas = [
            (f[0], f[1], f[2], f[3] or 0, f[4] or 0.0, f[5] or 0.0) for f in filas
        ]
        self._filas_por_id = {f[0]: f for f in self._filas}
        self._pintar_filas()

    def _pintar_filas(self):
        previo = self.producto_seleccionado

        for item in self.tree.get_children():
            self.tree.delete(item)

        filas = list(self._filas)
        if self._orden_col:
            idx = INDICE_ORDEN[self._orden_col]

            def clave(f):
                v = f[idx]
                if idx in (1, 2):
                    return (v or "").lower()
                return v if v is not None else 0

            filas.sort(key=clave, reverse=self._orden_desc)

        for n, (pid, nombre, prov, stock, pc, pv) in enumerate(filas):
            texto_estado, tag_estado = _estado_stock(stock)
            tag = tag_estado or ("par" if n % 2 == 0 else "impar")
            self.tree.insert(
                "", tk.END, iid=str(pid), tags=(tag,),
                values=(pid, nombre, prov or "—", stock,
                        f"{pc:,.2f}", f"{pv:,.2f}", texto_estado)
            )

        self._actualizar_encabezados()
        self.lbl_contador.config(text=f"{len(filas)} de {self._total_productos} productos")

        # Conservar la selección si el producto sigue visible
        if previo is not None and str(previo) in self.tree.get_children():
            self.tree.selection_set(str(previo))
            self.tree.see(str(previo))
        else:
            self.producto_seleccionado = None
            self._resetear_detalle()

    def _refrescar(self):
        """Recalcula el resumen y la tabla."""
        self._actualizar_resumen()
        self._cargar_productos()

# ============================================================
    # IMPORTAR EXCEL
    # ============================================================

    def _importar_excel(self):
        """Punto de entrada: primero elige el proveedor, luego el archivo."""
        if pd is None:
            messagebox.showerror(
                "Librería faltante",
                "Se requiere instalar 'pandas' y 'openpyxl'.\n\n"
                "Ejecute: pip install pandas openpyxl"
            )
            return
        self._elegir_proveedor(self._continuar_importar_excel)

    def _elegir_proveedor(self, on_elegido):
        """
        Ventana para elegir a qué proveedor pertenece el Excel. Permite
        cargar un proveedor nuevo al vuelo. `on_elegido` recibe el id.
        """
        proveedores = query("SELECT id, nombre FROM proveedores ORDER BY nombre") or []

        v = self._crear_dialogo(
            "Seleccionar proveedor",
            "¿A qué proveedor pertenece este archivo de Excel?"
        )
        form = tk.Frame(v, bg=COLOR_FONDO_INTERNO, padx=28)
        form.pack(fill=tk.X, pady=(6, 0))

        tk.Label(
            form, text="Proveedor existente:", font=("Arial", 11),
            fg=COLOR_NEGRO, bg=COLOR_FONDO_INTERNO, anchor="w"
        ).pack(fill=tk.X, pady=(10, 4))

        valores = [f"{pid} - {nombre}" for pid, nombre in proveedores]
        combo = ttk.Combobox(form, values=valores, font=("Arial", 11), state="readonly")
        combo.pack(fill=tk.X, ipady=4)
        if valores:
            combo.current(0)
        else:
            combo.set("(no hay proveedores cargados todavía)")

        tk.Label(
            form, text="— o cargar uno nuevo —", font=("Arial", 9, "italic"),
            fg=COLOR_TEXTO_SUAVE, bg=COLOR_FONDO_INTERNO
        ).pack(pady=(14, 4))

        entry_nuevo = tk.Entry(
            form, font=("Arial", 11), bg=COLOR_BLANCO, fg="#888888",
            relief="flat", bd=0, highlightthickness=1,
            highlightbackground="#888888", highlightcolor=COLOR_VERDE_SIDEBAR
        )
        entry_nuevo.insert(0, "nombre del proveedor nuevo")
        entry_nuevo.pack(fill=tk.X, ipady=6)

        def limpiar_ph(event):
            if entry_nuevo.get() == "nombre del proveedor nuevo":
                entry_nuevo.delete(0, tk.END)
                entry_nuevo.config(fg=COLOR_NEGRO)

        entry_nuevo.bind("<FocusIn>", limpiar_ph)

        def confirmar():
            texto_nuevo = entry_nuevo.get().strip()
            if texto_nuevo and texto_nuevo != "nombre del proveedor nuevo":
                query("INSERT INTO proveedores (nombre) VALUES (?)", (texto_nuevo,))
                res = query(
                    "SELECT id FROM proveedores WHERE nombre = ? ORDER BY id DESC LIMIT 1",
                    (texto_nuevo,)
                )
                id_proveedor = res[0][0] if res else None
                self._cargar_filtro_proveedores()
            elif valores:
                id_proveedor = int(combo.get().split(" - ")[0])
            else:
                messagebox.showwarning(
                    "Falta proveedor",
                    "Seleccione un proveedor existente o cargue el nombre de uno nuevo.",
                    parent=v
                )
                return
            v.destroy()
            on_elegido(id_proveedor)

        self._boton(
            v, "Continuar", confirmar,
            COLOR_VERDE_BOTON_ACCION, COLOR_BLANCO, COLOR_VERDE_ACCION_HOVER
        ).pack(pady=(20, 18))
        self._mostrar_dialogo(v, 420)

    def _continuar_importar_excel(self, id_proveedor):
        """Pide el archivo Excel, lo procesa y guarda los productos."""
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

        monto_compra = calcular_monto_compra(productos)
        nombre_archivo = os.path.basename(ruta)
        aviso_dup = ""
        if existe_compra_similar(id_proveedor, nombre_archivo, monto_compra):
            aviso_dup = (
                "\n⚠ ATENCIÓN: ya existe una compra de este proveedor con el "
                "mismo archivo y el mismo monto. ¿Es una importación duplicada?\n"
            )

        if not messagebox.askyesno(
            "Confirmar importación",
            f"Se detectaron {len(productos)} productos válidos.\n"
            f"Monto total de la compra: ${monto_compra:,.2f}\n"
            f"{aviso_dup}\n"
            f"¿Desea importarlos a la base de datos?\n\n"
            f"Los productos existentes se actualizarán (cantidad y precio de compra).\n"
            f"El precio de venta existente NO se modificará."
        ):
            return

        try:
            insertados, actualizados = _guardar_productos_en_bd(productos, id_proveedor)
            # Registrar la compra en el historial (alimenta el Balance)
            _, monto_registrado = registrar_compra(id_proveedor, nombre_archivo, productos)
            messagebox.showinfo(
                "Importación exitosa",
                f"✓ Importación completada.\n\n"
                f"Compra registrada por: ${monto_registrado:,.2f}\n"
                f"Productos nuevos: {insertados}\n"
                f"Productos actualizados: {actualizados}\n"
                f"Total procesados: {insertados + actualizados}"
            )
            self._cargar_filtro_proveedores()
            self._refrescar()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron guardar los productos:\n{str(e)}")

    # ============================================================
    # AGREGAR PRODUCTO MANUAL
    # ============================================================

    def _agregar_producto_manual(self):
        v = self._crear_dialogo("Nuevo producto", "Los campos con * son obligatorios.")
        form = tk.Frame(v, bg=COLOR_FONDO_INTERNO, padx=28)
        form.pack(fill=tk.X, pady=(4, 0))

        e_nombre = self._campo(form, "Nombre / Producto:*")
        e_cant = self._campo(form, "Cantidad:", "0")
        e_pc = self._campo(form, "Precio compra ($):", "0.00")
        e_pv = self._campo(form, "Precio venta ($):", "0.00")

        tk.Label(
            form, text="Proveedor:", font=("Arial", 11),
            fg=COLOR_NEGRO, bg=COLOR_FONDO_INTERNO, anchor="w"
        ).pack(fill=tk.X, pady=(10, 2))
        proveedores = query("SELECT id, nombre FROM proveedores ORDER BY nombre") or []
        combo = ttk.Combobox(
            form, font=("Arial", 12), state="readonly",
            values=["(sin proveedor)"] + [f"{pid} - {n}" for pid, n in proveedores]
        )
        combo.current(0)
        combo.pack(fill=tk.X, ipady=4)

        def confirmar():
            nombre = e_nombre.get().strip()
            if not nombre:
                messagebox.showwarning("Campo obligatorio", "El nombre del producto es obligatorio.", parent=v)
                return
            cantidad = _limpiar_valor_numerico(e_cant.get(), tipo="int", default=0)
            pcompra = _limpiar_valor_numerico(e_pc.get(), tipo="float", default=0.0)
            pventa = _limpiar_valor_numerico(e_pv.get(), tipo="float", default=0.0)

            sel = combo.get()
            id_prov = None if sel == "(sin proveedor)" else int(sel.split(" - ")[0])

            try:
                query(
                    """INSERT INTO productos
                        (nombre, descripcion, stock, precio_costo, precio_venta, categoria, id_proveedor)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (nombre, "", cantidad, pcompra, pventa, "", id_prov)
                )
                messagebox.showinfo("Éxito", f"Producto '{nombre}' agregado correctamente.", parent=v)
                v.destroy()
                self._refrescar()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo agregar el producto.\n{str(e)}", parent=v)

        self._boton(
            v, "Confirmar", confirmar,
            COLOR_VERDE_BOTON_ACCION, COLOR_BLANCO, COLOR_VERDE_ACCION_HOVER
        ).pack(pady=(22, 18))
        self._mostrar_dialogo(v, 420)
        e_nombre.focus()

    # ============================================================
    # EDITAR PRODUCTO
    # ============================================================

    def _editar_producto(self):
        """Edita nombre y precio de venta (el resto solo vía Excel)."""
        if self.producto_seleccionado is None:
            messagebox.showwarning("Sin selección", "Seleccione un producto de la tabla para editar.")
            return
        fila = self._filas_por_id.get(self.producto_seleccionado)
        if not fila:
            return
        prod_id, nombre, prov, stock, pc, pv = fila

        v = self._crear_dialogo(
            f"Editar producto · ID {prod_id}",
            "Los campos bloqueados solo se modifican vía importación de Excel."
        )
        form = tk.Frame(v, bg=COLOR_FONDO_INTERNO, padx=28)
        form.pack(fill=tk.X, pady=(4, 0))

        self._campo(form, "ID:", prod_id, bloqueado=True)
        e_nombre = self._campo(form, "Nombre / Producto:*", nombre)
        self._campo(form, "Cantidad:", stock, bloqueado=True)
        self._campo(form, "Precio compra ($):", f"{pc:.2f}", bloqueado=True)
        e_pv = self._campo(form, "Precio venta ($):*", f"{pv:.2f}")

        def guardar():
            nuevo_nombre = e_nombre.get().strip()
            nuevo_pv = _limpiar_valor_numerico(e_pv.get(), tipo="float", default=0.0)
            if not nuevo_nombre:
                messagebox.showwarning("Campo obligatorio", "El nombre del producto es obligatorio.", parent=v)
                return
            try:
                query(
                    "UPDATE productos SET nombre = ?, precio_venta = ? WHERE id = ?",
                    (nuevo_nombre, nuevo_pv, prod_id)
                )
                messagebox.showinfo("Éxito", "Producto actualizado correctamente.", parent=v)
                v.destroy()
                self._refrescar()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo actualizar el producto.\n{str(e)}", parent=v)

        self._boton(
            v, "Guardar cambios", guardar,
            COLOR_VERDE_BOTON_ACCION, COLOR_BLANCO, COLOR_VERDE_ACCION_HOVER
        ).pack(pady=(22, 18))
        self._mostrar_dialogo(v, 420)
        e_nombre.focus()

    # ============================================================
    # BORRAR PRODUCTO
    # ============================================================

    def _borrar_producto(self):
        if self.producto_seleccionado is None:
            messagebox.showwarning("Sin selección", "Seleccione un producto de la tabla para borrar.")
            return
        fila = self._filas_por_id.get(self.producto_seleccionado)
        nombre_prod = fila[1] if fila else f"ID {self.producto_seleccionado}"

        if not messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Está seguro de que desea eliminar el producto '{nombre_prod}'?\n\n"
            "Esta acción no se puede deshacer."
        ):
            return
        try:
            query("DELETE FROM productos WHERE id = ?", (self.producto_seleccionado,))
            messagebox.showinfo("Éxito", f"Producto '{nombre_prod}' eliminado correctamente.")
            self.producto_seleccionado = None
            self._refrescar()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo eliminar el producto.\n{str(e)}")