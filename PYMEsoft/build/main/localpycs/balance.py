#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================
balance.py - Módulo de Balance Financiero
============================================================
Vista `VistaBalance` que muestra, para un mes/año elegido:

  - Ingresos Netos   : SUM(ventas.total) del período.
  - Gastos Totales   : Gasto en proveedores + Gastos Extras.
  - Ganancia Neta    : Ingresos Netos - Gastos Totales
                       (verde si es positiva, rojo si es negativa).

Además permite registrar y eliminar "Gastos Extras" (alquiler,
luz, sueldos, impuestos, etc.), guardados en la tabla
`gastos_extras` (se crea sola si no existe).

------------------------------------------------------------
CRITERIO DEL "GASTO EN PROVEEDORES / COMPRAS"  (CORREGIDO)
------------------------------------------------------------
Cada importación de Excel queda registrada en la tabla `compras`
(ver compras.py) con su monto total real:

    gasto_proveedores = SUM(compras.monto_total)   del período

Es dinero que efectivamente salió al comprar mercadería, sin
importar cuántas unidades se vendieron después. Ejemplo: comprar
1.000 u. por $100.000 y vender 1 -> gasto de compras = $100.000.

(Antes se calculaba SUM(detalle_ventas.cantidad * precio_costo),
es decir el costo de lo VENDIDO, lo que subestimaba el gasto.)

Gastos totales = compras del período + gastos extras del período.

Uso (igual que VistaClientes / VistaFacturacion):
    VistaBalance(self.area_contenido)

Autor: Estudiante
Fecha: 2026-09-21
============================================================
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from database import query
from compras import crear_tablas_compras, obtener_compras_por_proveedor

# ============================================================
# PALETA DE COLORES (misma que main_window.py / facturacion.py)
# ============================================================
COLOR_VERDE_SIDEBAR      = "#1B4D1B"
COLOR_VERDE_BOTON_ACCION = "#0D2E0D"
COLOR_VERDE_ACCION_HOVER = "#1a5c1a"
COLOR_GRIS_FONDO         = "#A8A8A8"
COLOR_BOTON_ESTANDAR     = "#a6a6a6"
COLOR_BOTON_HOVER        = "#FFFFFF"
COLOR_FONDO_INTERNO      = "#f5f5f5"
COLOR_BLANCO             = "#FFFFFF"
COLOR_NEGRO              = "#000000"
COLOR_ROJO_CERRAR        = "#8B0000"
COLOR_ROJO_HOVER         = "#A52A2A"

MESES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def _moneda(valor):
    """Formatea un número como moneda: $1,234.56"""
    return f"${valor:,.2f}"


def _rango_mes(anio, mes):
    """
    Devuelve (inicio, fin) como texto 'YYYY-MM-DD' para filtrar un mes.
    Se usa  fecha >= inicio AND fecha < fin  (fin es el 1° del mes
    siguiente), que funciona con fechas 'YYYY-MM-DD HH:MM:SS'.
    """
    inicio = f"{anio:04d}-{mes:02d}-01"
    if mes == 12:
        fin = f"{anio + 1:04d}-01-01"
    else:
        fin = f"{anio:04d}-{mes + 1:02d}-01"
    return inicio, fin


def _fecha_legible(fecha_txt):
    """Convierte 'YYYY-MM-DD HH:MM:SS' a 'DD/MM/YYYY HH:MM'."""
    try:
        return datetime.strptime(fecha_txt, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M")
    except (ValueError, TypeError):
        return fecha_txt or ""


def _parsear_monto(texto):
    """
    Convierte el texto ingresado a float.
    Acepta '1500', '1500.50', '1500,50' y '1.500,50'.
    Lanza ValueError si no es un número válido.
    """
    t = texto.strip().replace("$", "").replace(" ", "")
    if "," in t and "." in t:
        t = t.replace(".", "").replace(",", ".")   # 1.500,50 -> 1500.50
    else:
        t = t.replace(",", ".")                    # 1500,50  -> 1500.50
    return float(t)


class VistaBalance:
    """Vista de Balance: KPIs del mes + gestión de gastos extras."""

    def __init__(self, parent_frame):
        self.parent = parent_frame

        # Limpiar el contenido previo del área principal
        for widget in self.parent.winfo_children():
            widget.destroy()

        # Crear la tabla de gastos extras si todavía no existe
        self._crear_tabla_gastos()
        crear_tablas_compras()

        # Período por defecto: mes actual
        hoy = datetime.now()
        self.periodo_anio = hoy.year
        self.periodo_mes = hoy.month

        self._configurar_estilos()
        self._crear_titulo()
        self._crear_filtros()
        self._crear_tarjetas()
        self._crear_paneles_inferiores()

        self._recalcular()

    # ============================================================
    # BASE DE DATOS
    # ============================================================

    def _crear_tabla_gastos(self):
        query("""
            CREATE TABLE IF NOT EXISTS gastos_extras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descripcion TEXT NOT NULL,
                monto REAL NOT NULL,
                fecha TEXT NOT NULL
            )
        """)

    def _obtener_ingresos(self, inicio, fin):
        """Devuelve (suma_total_ventas, cantidad_de_ventas) del período."""
        res = query(
            """
            SELECT COALESCE(SUM(total), 0), COUNT(*)
            FROM ventas
            WHERE fecha >= ? AND fecha < ?
            """,
            (inicio, fin),
        )
        if res:
            return float(res[0][0]), int(res[0][1])
        return 0.0, 0

    def _obtener_compras_por_proveedor(self, inicio, fin):
        """
        Compras reales (importaciones de Excel) del período, por proveedor.
        Devuelve lista de (proveedor, cantidad_de_compras, monto_total).
        """
        return obtener_compras_por_proveedor(inicio, fin)

    def _obtener_gastos_extras(self, inicio, fin):
        res = query(
            """
            SELECT id, fecha, descripcion, monto
            FROM gastos_extras
            WHERE fecha >= ? AND fecha < ?
            ORDER BY fecha DESC
            """,
            (inicio, fin),
        )
        return res or []

    def _anios_disponibles(self):
        """Años desde el primer registro (ventas o gastos) hasta el actual."""
        anio_actual = datetime.now().year
        minimo = anio_actual
        for tabla in ("ventas", "gastos_extras", "compras"):
            res = query(f"SELECT MIN(substr(fecha, 1, 4)) FROM {tabla}")
            if res and res[0][0] and str(res[0][0]).isdigit():
                minimo = min(minimo, int(res[0][0]))
        return list(range(minimo, anio_actual + 1))

    # ============================================================
    # CONSTRUCCIÓN DE LA INTERFAZ
    # ============================================================

    def _configurar_estilos(self):
        estilo = ttk.Style()
        estilo.configure("Balance.Treeview", rowheight=24, font=("Arial", 10))
        estilo.configure("Balance.Treeview.Heading", font=("Arial", 10, "bold"))

    def _crear_titulo(self):
        tk.Label(
            self.parent, text="BALANCE:", font=("Arial", 32, "bold"),
            fg=COLOR_NEGRO, bg=COLOR_GRIS_FONDO
        ).pack(anchor="w", padx=40, pady=(30, 15))

    def _crear_boton(self, parent, texto, comando, bg, hover, fg=COLOR_BLANCO, ancho=20):
        btn = tk.Button(
            parent, text=texto, font=("Arial", 11, "bold"),
            bg=bg, fg=fg, activebackground=hover, activeforeground=fg,
            relief="flat", bd=0, cursor="hand2", width=ancho, height=2,
            command=comando
        )
        btn.bind("<Enter>", lambda e: btn.config(bg=hover))
        btn.bind("<Leave>", lambda e: btn.config(bg=bg))
        return btn

    def _crear_filtros(self):
        frame = tk.Frame(self.parent, bg=COLOR_VERDE_SIDEBAR, padx=15, pady=12)
        frame.pack(fill=tk.X, padx=40, pady=(0, 12))

        tk.Label(frame, text="Mes:", font=("Arial", 11, "bold"),
                 fg=COLOR_BLANCO, bg=COLOR_VERDE_SIDEBAR).pack(side=tk.LEFT, padx=(0, 8))

        self.combo_mes = ttk.Combobox(frame, values=MESES, state="readonly",
                                      font=("Arial", 11), width=14)
        self.combo_mes.current(self.periodo_mes - 1)
        self.combo_mes.pack(side=tk.LEFT, padx=(0, 20))

        tk.Label(frame, text="Año:", font=("Arial", 11, "bold"),
                 fg=COLOR_BLANCO, bg=COLOR_VERDE_SIDEBAR).pack(side=tk.LEFT, padx=(0, 8))

        anios = self._anios_disponibles()
        self.combo_anio = ttk.Combobox(frame, values=[str(a) for a in anios],
                                       state="readonly", font=("Arial", 11), width=8)
        self.combo_anio.set(str(self.periodo_anio))
        self.combo_anio.pack(side=tk.LEFT, padx=(0, 20))

        # Botón estándar (gris) con hover blanco
        self._crear_boton(
            frame, "Filtrar / Recalcular", self._filtrar,
            COLOR_BOTON_ESTANDAR, COLOR_BOTON_HOVER, fg=COLOR_NEGRO, ancho=20
        ).pack(side=tk.LEFT)

        self.lbl_periodo = tk.Label(frame, text="", font=("Arial", 12, "bold"),
                                    fg=COLOR_BLANCO, bg=COLOR_VERDE_SIDEBAR)
        self.lbl_periodo.pack(side=tk.RIGHT)

    def _crear_tarjeta(self, parent, columna, titulo):
        """Crea una tarjeta KPI. Devuelve (encabezado, lbl_valor, lbl_detalle)."""
        card = tk.Frame(parent, bg=COLOR_FONDO_INTERNO)
        card.grid(row=0, column=columna, sticky="nsew",
                  padx=(0, 10) if columna < 2 else 0)

        encabezado = tk.Label(card, text=titulo, font=("Arial", 12, "bold"),
                              fg=COLOR_BLANCO, bg=COLOR_VERDE_SIDEBAR, pady=6)
        encabezado.pack(fill=tk.X)

        lbl_valor = tk.Label(card, text="$0.00", font=("Arial", 26, "bold"),
                             fg=COLOR_NEGRO, bg=COLOR_FONDO_INTERNO)
        lbl_valor.pack(pady=(14, 4))

        lbl_detalle = tk.Label(card, text="", font=("Arial", 10),
                               fg="#555555", bg=COLOR_FONDO_INTERNO, pady=0)
        lbl_detalle.pack(pady=(0, 12))

        return encabezado, lbl_valor, lbl_detalle

    def _crear_tarjetas(self):
        frame = tk.Frame(self.parent, bg=COLOR_GRIS_FONDO)
        frame.pack(fill=tk.X, padx=40, pady=(0, 12))
        for c in range(3):
            frame.columnconfigure(c, weight=1, uniform="kpi")

        _, self.lbl_ingresos, self.lbl_ingresos_det = \
            self._crear_tarjeta(frame, 0, "INGRESOS NETOS (VENTAS)")
        _, self.lbl_gastos, self.lbl_gastos_det = \
            self._crear_tarjeta(frame, 1, "GASTOS TOTALES")
        self.hdr_ganancia, self.lbl_ganancia, self.lbl_ganancia_det = \
            self._crear_tarjeta(frame, 2, "GANANCIA NETA (UTILIDAD)")

    def _crear_paneles_inferiores(self):
        frame = tk.Frame(self.parent, bg=COLOR_GRIS_FONDO)
        frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=(0, 20))
        frame.columnconfigure(0, weight=3, uniform="pnl")
        frame.columnconfigure(1, weight=2, uniform="pnl")
        frame.rowconfigure(0, weight=1)

        self._crear_panel_gastos_extras(frame)
        self._crear_panel_proveedores(frame)

    def _crear_panel_gastos_extras(self, contenedor):
        panel = tk.Frame(contenedor, bg=COLOR_FONDO_INTERNO, padx=8, pady=8)
        panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        tk.Label(panel, text="Gastos Extras del Mes", font=("Arial", 13, "bold"),
                 fg=COLOR_VERDE_SIDEBAR, bg=COLOR_FONDO_INTERNO).pack(anchor="w", pady=(0, 8))

        # Botones (se empaquetan primero abajo para que siempre se vean)
        frame_botones = tk.Frame(panel, bg=COLOR_FONDO_INTERNO)
        frame_botones.pack(side=tk.BOTTOM, fill=tk.X, pady=(8, 0))

        self.lbl_total_extras = tk.Label(frame_botones, text="Total: $0.00",
                                         font=("Arial", 11, "bold"),
                                         fg=COLOR_NEGRO, bg=COLOR_FONDO_INTERNO)
        self.lbl_total_extras.pack(side=tk.LEFT)

        self._crear_boton(
            frame_botones, "Eliminar Gasto", self._eliminar_gasto,
            COLOR_ROJO_CERRAR, COLOR_ROJO_HOVER, ancho=16
        ).pack(side=tk.RIGHT)
        self._crear_boton(
            frame_botones, "Registrar Gasto Extra", self._abrir_form_gasto,
            COLOR_VERDE_BOTON_ACCION, COLOR_VERDE_ACCION_HOVER, ancho=22
        ).pack(side=tk.RIGHT, padx=(0, 10))

        # Tabla
        frame_tabla = tk.Frame(panel, bg=COLOR_FONDO_INTERNO)
        frame_tabla.pack(fill=tk.BOTH, expand=True)

        columnas = ("id", "fecha", "descripcion", "monto")
        self.tree_gastos = ttk.Treeview(frame_tabla, columns=columnas, show="headings",
                                        height=8, style="Balance.Treeview",
                                        selectmode="browse")
        self.tree_gastos.heading("id", text="ID")
        self.tree_gastos.heading("fecha", text="Fecha")
        self.tree_gastos.heading("descripcion", text="Descripción")
        self.tree_gastos.heading("monto", text="Monto")
        self.tree_gastos.column("id", width=50, anchor="center", stretch=False)
        self.tree_gastos.column("fecha", width=130, anchor="center", stretch=False)
        self.tree_gastos.column("descripcion", width=220, anchor="w")
        self.tree_gastos.column("monto", width=110, anchor="e", stretch=False)

        scroll = ttk.Scrollbar(frame_tabla, orient=tk.VERTICAL, command=self.tree_gastos.yview)
        self.tree_gastos.configure(yscrollcommand=scroll.set)
        self.tree_gastos.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def _crear_panel_proveedores(self, contenedor):
        panel = tk.Frame(contenedor, bg=COLOR_FONDO_INTERNO, padx=8, pady=8)
        panel.grid(row=0, column=1, sticky="nsew")

        tk.Label(panel, text="Gasto en Proveedores",
                 font=("Arial", 13, "bold"),
                 fg=COLOR_VERDE_SIDEBAR, bg=COLOR_FONDO_INTERNO).pack(anchor="w")
        tk.Label(panel, text="Compras (importaciones de Excel) registradas en el mes",
                 font=("Arial", 9), fg="#555555",
                 bg=COLOR_FONDO_INTERNO).pack(anchor="w", pady=(0, 8))

        self.lbl_total_prov = tk.Label(panel, text="Total: $0.00", font=("Arial", 11, "bold"),
                                       fg=COLOR_NEGRO, bg=COLOR_FONDO_INTERNO)
        self.lbl_total_prov.pack(side=tk.BOTTOM, anchor="w", pady=(8, 0))

        frame_tabla = tk.Frame(panel, bg=COLOR_FONDO_INTERNO)
        frame_tabla.pack(fill=tk.BOTH, expand=True)

        columnas = ("proveedor", "unidades", "costo")
        self.tree_prov = ttk.Treeview(frame_tabla, columns=columnas, show="headings",
                                      height=8, style="Balance.Treeview",
                                      selectmode="none")
        self.tree_prov.heading("proveedor", text="Proveedor")
        self.tree_prov.heading("unidades", text="Compras")
        self.tree_prov.heading("costo", text="Monto")
        self.tree_prov.column("proveedor", width=160, anchor="w")
        self.tree_prov.column("unidades", width=80, anchor="center", stretch=False)
        self.tree_prov.column("costo", width=110, anchor="e", stretch=False)

        scroll = ttk.Scrollbar(frame_tabla, orient=tk.VERTICAL, command=self.tree_prov.yview)
        self.tree_prov.configure(yscrollcommand=scroll.set)
        self.tree_prov.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

    # ============================================================
    # CÁLCULO Y ACTUALIZACIÓN DE LA PANTALLA
    # ============================================================

    def _filtrar(self):
        """Toma el mes/año elegidos en los combos y recalcula."""
        self.periodo_mes = self.combo_mes.current() + 1
        self.periodo_anio = int(self.combo_anio.get())
        self._recalcular()

    def _recalcular(self):
        """Recalcula KPIs y tablas para el período (self.periodo_*)."""
        inicio, fin = _rango_mes(self.periodo_anio, self.periodo_mes)

        # --- Ingresos ---
        ingresos, cant_ventas = self._obtener_ingresos(inicio, fin)

        # --- Gasto en proveedores: monto TOTAL de las compras del período ---
        filas_prov = self._obtener_compras_por_proveedor(inicio, fin)
        gasto_prov = sum(float(f[2] or 0) for f in filas_prov)

        # --- Gastos extras ---
        filas_extras = self._obtener_gastos_extras(inicio, fin)
        gasto_extras = sum(float(f[3]) for f in filas_extras)

        # --- Totales ---
        gastos_totales = gasto_prov + gasto_extras
        ganancia = ingresos - gastos_totales

        # --- Tarjetas ---
        self.lbl_periodo.config(text=f"{MESES[self.periodo_mes - 1]} {self.periodo_anio}")

        self.lbl_ingresos.config(text=_moneda(ingresos))
        self.lbl_ingresos_det.config(
            text=f"{cant_ventas} venta{'s' if cant_ventas != 1 else ''} en el período")

        self.lbl_gastos.config(text=_moneda(gastos_totales))
        self.lbl_gastos_det.config(
            text=f"Compras: {_moneda(gasto_prov)}\nExtras: {_moneda(gasto_extras)}")

        color = COLOR_VERDE_SIDEBAR if ganancia >= 0 else COLOR_ROJO_CERRAR
        self.lbl_ganancia.config(text=_moneda(ganancia), fg=color)
        self.hdr_ganancia.config(bg=color)
        self.lbl_ganancia_det.config(
            text="Resultado positivo" if ganancia > 0
            else ("Resultado negativo (pérdida)" if ganancia < 0 else "Sin ganancia ni pérdida"))

        # --- Tabla de proveedores ---
        for item in self.tree_prov.get_children():
            self.tree_prov.delete(item)
        for proveedor, n_compras, costo in filas_prov:
            self.tree_prov.insert("", tk.END, values=(
                proveedor, int(n_compras or 0), _moneda(float(costo or 0))))
        self.lbl_total_prov.config(text=f"Total: {_moneda(gasto_prov)}")

        # --- Tabla de gastos extras ---
        for item in self.tree_gastos.get_children():
            self.tree_gastos.delete(item)
        for id_g, fecha, descripcion, monto in filas_extras:
            self.tree_gastos.insert("", tk.END, values=(
                id_g, _fecha_legible(fecha), descripcion, _moneda(float(monto))))
        self.lbl_total_extras.config(text=f"Total: {_moneda(gasto_extras)}")

    # ============================================================
    # GASTOS EXTRAS: REGISTRAR / ELIMINAR
    # ============================================================

    def _abrir_form_gasto(self):
        ventana = tk.Toplevel(self.parent)
        ventana.title("Registrar Gasto Extra")
        ventana.configure(bg=COLOR_FONDO_INTERNO)
        ventana.resizable(False, False)
        ventana.transient(self.parent.winfo_toplevel())
        ventana.grab_set()
        ventana.geometry("400x400")

        # Centrar la ventana respecto a la pantalla
        ventana.update_idletasks()
        ancho = ventana.winfo_width()
        alto = ventana.winfo_height()
        x = (ventana.winfo_screenwidth() // 2) - (ancho // 2)
        y = (ventana.winfo_screenheight() // 2) - (alto // 2)
        ventana.geometry(f"{ancho}x{alto}+{x}+{y}")

        tk.Label(ventana, text="Nuevo Gasto Extra", font=("Arial", 18, "bold"),
                 fg=COLOR_VERDE_SIDEBAR, bg=COLOR_FONDO_INTERNO).pack(pady=(20, 15))

        def crear_campo(etiqueta, valor_inicial=""):
            tk.Label(ventana, text=etiqueta, font=("Arial", 11, "bold"),
                     fg=COLOR_NEGRO, bg=COLOR_FONDO_INTERNO).pack(anchor="w", padx=30)
            entry = tk.Entry(ventana, font=("Arial", 12), bg=COLOR_BLANCO, fg=COLOR_NEGRO,
                             relief="flat", bd=1, highlightthickness=1,
                             highlightbackground=COLOR_GRIS_FONDO)
            entry.insert(0, valor_inicial)
            entry.pack(fill=tk.X, padx=30, ipady=6, pady=(2, 10))
            return entry

        entry_desc = crear_campo("Nombre / Descripción (ej. Alquiler, Luz):")
        entry_monto = crear_campo("Monto ($):")

        # Fecha: hoy si el mes visualizado es el actual; si no, el día 1 del mes visualizado.
        hoy = datetime.now()
        if (hoy.year, hoy.month) == (self.periodo_anio, self.periodo_mes):
            fecha_inicial = hoy.strftime("%Y-%m-%d")
        else:
            fecha_inicial = f"{self.periodo_anio:04d}-{self.periodo_mes:02d}-01"
        entry_fecha = crear_campo("Fecha (AAAA-MM-DD):", fecha_inicial)

        def guardar():
            descripcion = entry_desc.get().strip()
            if not descripcion:
                messagebox.showwarning("Campo vacío", "Ingrese una descripción.", parent=ventana)
                entry_desc.focus()
                return

            try:
                monto = _parsear_monto(entry_monto.get())
            except ValueError:
                messagebox.showwarning("Monto inválido",
                                       "Ingrese un monto numérico válido.", parent=ventana)
                entry_monto.focus()
                return
            if monto <= 0:
                messagebox.showwarning("Monto inválido",
                                       "El monto debe ser mayor a 0.", parent=ventana)
                entry_monto.focus()
                return

            try:
                dia = datetime.strptime(entry_fecha.get().strip(), "%Y-%m-%d")
            except ValueError:
                messagebox.showwarning("Fecha inválida",
                                       "Use el formato AAAA-MM-DD (ej. 2026-09-21).",
                                       parent=ventana)
                entry_fecha.focus()
                return

            # Se guarda con la hora actual: formato YYYY-MM-DD HH:MM:SS
            fecha = f"{dia.strftime('%Y-%m-%d')} {datetime.now().strftime('%H:%M:%S')}"

            query(
                "INSERT INTO gastos_extras (descripcion, monto, fecha) VALUES (?, ?, ?)",
                (descripcion, monto, fecha),
            )
            ventana.destroy()
            self._recalcular()

            if (dia.year, dia.month) != (self.periodo_anio, self.periodo_mes):
                messagebox.showinfo(
                    "Gasto registrado",
                    "El gasto se guardó con una fecha de otro mes, por lo que no "
                    "aparece en el período que está viendo.")

        botones = tk.Frame(ventana, bg=COLOR_FONDO_INTERNO)
        botones.pack(pady=(10, 0))

        self._crear_boton(botones, "Guardar", guardar, COLOR_VERDE_BOTON_ACCION,
                          COLOR_VERDE_ACCION_HOVER, ancho=12).pack(side=tk.LEFT, padx=(0, 10))
        self._crear_boton(botones, "Cancelar", ventana.destroy, COLOR_ROJO_CERRAR,
                          COLOR_ROJO_HOVER, ancho=12).pack(side=tk.LEFT)

        ventana.bind("<Return>", lambda e: guardar())
        ventana.bind("<Escape>", lambda e: ventana.destroy())
        entry_desc.focus()

    def _eliminar_gasto(self):
        seleccion = self.tree_gastos.selection()
        if not seleccion:
            messagebox.showwarning("Sin selección",
                                   "Seleccione un gasto de la tabla para eliminarlo.")
            return

        valores = self.tree_gastos.item(seleccion[0], "values")
        id_gasto = int(valores[0])

        if messagebox.askyesno(
            "Eliminar gasto",
            f"¿Desea eliminar el gasto '{valores[2]}' por {valores[3]}?\n"
            "Esta acción no se puede deshacer."
        ):
            query("DELETE FROM gastos_extras WHERE id = ?", (id_gasto,))
            self._recalcular()