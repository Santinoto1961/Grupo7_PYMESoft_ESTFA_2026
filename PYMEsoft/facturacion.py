#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================
facturacion.py - Módulo de Facturación y Ventas
============================================================
Formulario de nueva venta con selección de cliente, tabla
interactiva de productos (usando precio_venta), cálculo en
tiempo real de totales, y guardado en ventas/detalle_ventas
con descuento de stock.

Autor: Estudiante
Fecha: 2026-08-30
============================================================
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from database import query
from session import session

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

# ============================================================
# BORRADOR DE FACTURA
# ============================================================
# Vive a nivel de módulo (no dentro de la vista) para sobrevivir cuando
# main_window destruye y recrea VistaFacturacion al cambiar de pantalla.
_borrador = {"id_usuario": None, "items": [], "cliente": None}


def _parsear_precio(texto):
    """Acepta '1500', '1500.50', '1500,50' y '1.500,50'. ValueError si no es número."""
    s = texto.strip().replace("$", "").replace(" ", "")
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", ".")
    return float(s)


def limpiar_borrador():
    """Descarta el borrador de factura (al cerrar sesión o terminar la venta)."""
    _borrador["id_usuario"] = None
    _borrador["items"] = []
    _borrador["cliente"] = None


class VistaFacturacion:
    def __init__(self, parent_frame):
        self.parent = parent_frame
        self.items_factura = []
        self.total = 0.0

        for widget in self.parent.winfo_children():
            widget.destroy()

        self._cargar_clientes()
        self._cargar_productos_disponibles()
        self._crear_titulo()
        self._crear_notebook()
        self._restaurar_borrador()

    def _cargar_clientes(self):
        self.clientes_dict = {0: "Consumidor Final"}
        res = query("SELECT id, nombre, apellido FROM clientes ORDER BY nombre, apellido")
        if res:
            for fila in res:
                self.clientes_dict[fila[0]] = f"{fila[1]} {fila[2]}"

    def _cargar_productos_disponibles(self):
        self.productos_disponibles = []
        res = query("SELECT id, nombre, descripcion, precio_venta, stock FROM productos ORDER BY nombre")
        if res:
            self.productos_disponibles = res

    def _crear_titulo(self):
        self.lbl_titulo = tk.Label(
            self.parent, text="FACTURACIÓN:", font=("Arial", 32, "bold"),
            fg=COLOR_NEGRO, bg=COLOR_GRIS_FONDO
        )
        self.lbl_titulo.pack(anchor="w", padx=40, pady=(30, 15))

    def _crear_notebook(self):
        self.notebook = ttk.Notebook(self.parent)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=40, pady=(0, 20))

        self.tab_nueva = tk.Frame(self.notebook, bg=COLOR_GRIS_FONDO)
        self.notebook.add(self.tab_nueva, text="  Nueva Venta  ")
        self._construir_tab_nueva()

        self.tab_historial = tk.Frame(self.notebook, bg=COLOR_GRIS_FONDO)
        self.notebook.add(self.tab_historial, text="  Historial de Ventas  ")
        self._construir_tab_historial()

    def _construir_tab_nueva(self):
        frame_info = tk.Frame(self.tab_nueva, bg=COLOR_VERDE_SIDEBAR, padx=15, pady=15)
        frame_info.pack(fill=tk.X, pady=(0, 10))

        tk.Label(frame_info, text="Cliente:", font=("Arial", 11, "bold"),
            fg=COLOR_BLANCO, bg=COLOR_VERDE_SIDEBAR).grid(row=0, column=0, sticky="w", padx=(0, 10))

        self.combo_cliente = ttk.Combobox(
            frame_info,
            values=[f"{k} - {v}" for k, v in self.clientes_dict.items()],
            font=("Arial", 11), state="readonly", width=35
        )
        self.combo_cliente.grid(row=0, column=1, sticky="w", padx=(0, 30))
        self.combo_cliente.current(0)
        self.combo_cliente.bind("<<ComboboxSelected>>", lambda e: self._guardar_borrador())

        tk.Label(frame_info, text="Fecha:", font=("Arial", 11, "bold"),
            fg=COLOR_BLANCO, bg=COLOR_VERDE_SIDEBAR).grid(row=0, column=2, sticky="w", padx=(0, 10))

        self.lbl_fecha = tk.Label(frame_info, text=datetime.now().strftime("%d/%m/%Y %H:%M"),
            font=("Arial", 11), fg=COLOR_BLANCO, bg=COLOR_VERDE_SIDEBAR)
        self.lbl_fecha.grid(row=0, column=3, sticky="w", padx=(0, 30))

        tk.Label(frame_info, text="Vendedor:", font=("Arial", 11, "bold"),
            fg=COLOR_BLANCO, bg=COLOR_VERDE_SIDEBAR).grid(row=0, column=4, sticky="w", padx=(0, 10))

        nombre_vendedor = session.nombre or session.usuario or "Usuario"
        tk.Label(frame_info, text=nombre_vendedor, font=("Arial", 11),
            fg=COLOR_BLANCO, bg=COLOR_VERDE_SIDEBAR).grid(row=0, column=5, sticky="w")

        frame_medio = tk.Frame(self.tab_nueva, bg=COLOR_GRIS_FONDO)
        frame_medio.pack(fill=tk.BOTH, expand=True)

        # Izquierda: Productos disponibles
        frame_prod = tk.Frame(frame_medio, bg=COLOR_FONDO_INTERNO, padx=8, pady=8)
        frame_prod.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        tk.Label(frame_prod, text="Productos Disponibles", font=("Arial", 13, "bold"),
            fg=COLOR_VERDE_SIDEBAR, bg=COLOR_FONDO_INTERNO).pack(anchor="w", pady=(0, 8))

        self.entry_buscar = tk.Entry(frame_prod, font=("Arial", 11), bg=COLOR_BLANCO, fg="#888888",
            relief="flat", bd=1)
        self.entry_buscar.insert(0, "buscar producto por nombre...")
        self.entry_buscar.pack(fill=tk.X, ipady=6, pady=(0, 8))
        self.entry_buscar.bind("<FocusIn>", self._on_focus_buscar_prod)
        self.entry_buscar.bind("<FocusOut>", self._on_blur_buscar_prod)
        self.entry_buscar.bind("<KeyRelease>", self._filtrar_productos)

        columnas_prod = ("id", "nombre", "precio_venta", "stock")
        self.tree_prod = ttk.Treeview(frame_prod, columns=columnas_prod, show="headings", height=10)
        self.tree_prod.heading("id", text="ID")
        self.tree_prod.heading("nombre", text="Nombre")
        self.tree_prod.heading("precio_venta", text="Precio Venta")
        self.tree_prod.heading("stock", text="Stock")
        self.tree_prod.column("id", width=40, anchor="center")
        self.tree_prod.column("nombre", width=180, anchor="w")
        self.tree_prod.column("precio_venta", width=90, anchor="center")
        self.tree_prod.column("stock", width=60, anchor="center")

        scroll_prod = ttk.Scrollbar(frame_prod, orient=tk.VERTICAL, command=self.tree_prod.yview)
        self.tree_prod.configure(yscrollcommand=scroll_prod.set)
        self.tree_prod.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_prod.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree_prod.bind("<Double-1>", self._on_doble_clic_producto)
        # Productos agotados (rojo) y sin precio de venta (amarillo)
        self.tree_prod.tag_configure("sin_stock", background="#f3c6c6")
        self.tree_prod.tag_configure("sin_precio", background="#f6e7b4")

        # Derecha: Items de factura
        frame_factura = tk.Frame(frame_medio, bg=COLOR_FONDO_INTERNO, padx=8, pady=8)
        frame_factura.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))

        tk.Label(frame_factura, text="Items de la Factura", font=("Arial", 13, "bold"),
            fg=COLOR_VERDE_SIDEBAR, bg=COLOR_FONDO_INTERNO).pack(anchor="w", pady=(0, 8))

        columnas_fact = ("producto", "cantidad", "precio", "subtotal")
        self.tree_factura = ttk.Treeview(frame_factura, columns=columnas_fact, show="headings", height=10)
        self.tree_factura.heading("producto", text="Producto")
        self.tree_factura.heading("cantidad", text="Cantidad")
        self.tree_factura.heading("precio", text="Precio Unit.")
        self.tree_factura.heading("subtotal", text="Subtotal")
        self.tree_factura.column("producto", width=200, anchor="w")
        self.tree_factura.column("cantidad", width=80, anchor="center")
        self.tree_factura.column("precio", width=90, anchor="center")
        self.tree_factura.column("subtotal", width=90, anchor="center")

        scroll_fact = ttk.Scrollbar(frame_factura, orient=tk.VERTICAL, command=self.tree_factura.yview)
        self.tree_factura.configure(yscrollcommand=scroll_fact.set)
        self.tree_factura.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_fact.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree_factura.bind("<Double-1>", self._on_doble_clic_item_factura)

        # ── Fila de botones de acción (Agregar / Quitar / Limpiar), bien visible ──
        frame_btns_items = tk.Frame(self.tab_nueva, bg=COLOR_GRIS_FONDO)
        frame_btns_items.pack(fill=tk.X, pady=(10, 0))

        btn_agregar = tk.Button(
            frame_btns_items, text="Agregar a Factura", font=("Arial", 11, "bold"),
            bg=COLOR_VERDE_BOTON_ACCION, fg=COLOR_BLANCO, activebackground="#1a5c1a",
            activeforeground=COLOR_BLANCO, relief="flat", bd=0, cursor="hand2",
            width=20, height=2, command=self._agregar_producto_factura
        )
        btn_agregar.pack(side=tk.LEFT, padx=(0, 10))
        btn_agregar.bind("<Enter>", lambda e: btn_agregar.config(bg="#1a5c1a"))
        btn_agregar.bind("<Leave>", lambda e: btn_agregar.config(bg=COLOR_VERDE_BOTON_ACCION))

        btn_quitar = tk.Button(
            frame_btns_items, text="Quitar Item", font=("Arial", 11, "bold"),
            bg=COLOR_ROJO_CERRAR, fg=COLOR_BLANCO, activebackground=COLOR_ROJO_HOVER,
            activeforeground=COLOR_BLANCO, relief="flat", bd=0, cursor="hand2",
            width=16, height=2, command=self._quitar_item_factura
        )
        btn_quitar.pack(side=tk.LEFT, padx=(0, 10))
        btn_quitar.bind("<Enter>", lambda e: btn_quitar.config(bg=COLOR_ROJO_HOVER))
        btn_quitar.bind("<Leave>", lambda e: btn_quitar.config(bg=COLOR_ROJO_CERRAR))

        btn_limpiar = tk.Button(
            frame_btns_items, text="Limpiar Todo", font=("Arial", 11, "bold"),
            bg=COLOR_VERDE_BOTON, fg=COLOR_NEGRO, activebackground=COLOR_VERDE_HOVER,
            activeforeground=COLOR_NEGRO, relief="flat", bd=0, cursor="hand2",
            width=16, height=2, command=self._limpiar_factura
        )
        btn_limpiar.pack(side=tk.LEFT)
        btn_limpiar.bind("<Enter>", lambda e: btn_limpiar.config(bg=COLOR_VERDE_HOVER))
        btn_limpiar.bind("<Leave>", lambda e: btn_limpiar.config(bg=COLOR_VERDE_BOTON))

        # Frame inferior: Total y Finalizar
        frame_total = tk.Frame(self.tab_nueva, bg=COLOR_VERDE_SIDEBAR, padx=15, pady=15)
        frame_total.pack(fill=tk.X, pady=(10, 0))

        self.lbl_total = tk.Label(frame_total, text="TOTAL: $0.00", font=("Arial", 20, "bold"),
            fg=COLOR_BLANCO, bg=COLOR_VERDE_SIDEBAR)
        self.lbl_total.pack(side=tk.LEFT)

        btn_finalizar = tk.Button(
            frame_total, text="FINALIZAR VENTA", font=("Arial", 14, "bold"),
            bg=COLOR_VERDE_BOTON, fg=COLOR_NEGRO, activebackground=COLOR_VERDE_HOVER,
            activeforeground=COLOR_NEGRO, relief="flat", bd=0, cursor="hand2",
            width=20, height=2, command=self._finalizar_venta
        )
        btn_finalizar.pack(side=tk.RIGHT)
        btn_finalizar.bind("<Enter>", lambda e: btn_finalizar.config(bg=COLOR_VERDE_HOVER))
        btn_finalizar.bind("<Leave>", lambda e: btn_finalizar.config(bg=COLOR_VERDE_BOTON))

        btn_ver_ventas = tk.Button(
            frame_total, text="Ver Ventas", font=("Arial", 12, "bold"),
            bg=COLOR_VERDE_BOTON, fg=COLOR_NEGRO, activebackground=COLOR_VERDE_HOVER,
            activeforeground=COLOR_NEGRO, relief="flat", bd=0, cursor="hand2",
            width=14, height=2, command=self._abrir_ventana_ventas
        )
        btn_ver_ventas.pack(side=tk.RIGHT, padx=(0, 10))
        btn_ver_ventas.bind("<Enter>", lambda e: btn_ver_ventas.config(bg=COLOR_VERDE_HOVER))
        btn_ver_ventas.bind("<Leave>", lambda e: btn_ver_ventas.config(bg=COLOR_VERDE_BOTON))

        self._cargar_tree_productos()

    def _cargar_tree_productos(self, filtro=""):
        for item in self.tree_prod.get_children():
            self.tree_prod.delete(item)

        for prod in self.productos_disponibles:
            id_p, nombre, desc, precio_venta, stock = prod
            if filtro.lower() in nombre.lower():
                stock = stock or 0
                precio_venta = precio_venta or 0.0
                if stock <= 0:
                    tag = ("sin_stock",)
                elif precio_venta <= 0:
                    tag = ("sin_precio",)
                else:
                    tag = ()
                self.tree_prod.insert("", tk.END, tags=tag,
                                      values=(id_p, nombre, f"${precio_venta:.2f}", stock))

    def _on_focus_buscar_prod(self, event):
        if self.entry_buscar.get() == "buscar producto por nombre...":
            self.entry_buscar.delete(0, tk.END)
            self.entry_buscar.config(fg=COLOR_NEGRO)

    def _on_blur_buscar_prod(self, event):
        if not self.entry_buscar.get().strip():
            self.entry_buscar.insert(0, "buscar producto por nombre...")
            self.entry_buscar.config(fg="#888888")

    def _filtrar_productos(self, event):
        texto = self.entry_buscar.get()
        if texto == "buscar producto por nombre...":
            texto = ""
        self._cargar_tree_productos(texto)

    def _on_doble_clic_producto(self, event):
        self._agregar_producto_factura()

    def _agregar_producto_factura(self):
        seleccion = self.tree_prod.selection()
        if not seleccion:
            messagebox.showwarning("Sin selección", "Por favor, seleccione un producto de la lista.")
            return

        item = self.tree_prod.item(seleccion[0])
        valores = item["values"]
        id_prod = valores[0]
        nombre = valores[1]
        precio_venta = float(valores[2].replace("$", "").replace(",", "."))
        stock = int(valores[3])

        for i, item_fact in enumerate(self.items_factura):
            if item_fact["id"] == id_prod:
                if item_fact["cantidad"] + 1 > stock:
                    messagebox.showwarning("Stock insuficiente",
                        f"No hay suficiente stock de '{nombre}'. Disponible: {stock}")
                    return
                self.items_factura[i]["cantidad"] += 1
                self._actualizar_tree_factura()
                return

        if stock < 1:
            messagebox.showwarning("Sin stock", f"El producto '{nombre}' no tiene stock disponible.")
            return

        if precio_venta <= 0:
            opcion = self._dialogo_sin_precio(nombre)
            if opcion == "cancelar":
                return
            if opcion == "cambiar":
                nuevo_precio = self._pedir_cambio_precio(id_prod, nombre)
                if nuevo_precio is None:
                    return
                precio_venta = nuevo_precio
                # Refrescar la lista para que muestre el precio nuevo
                self._cargar_productos_disponibles()
                filtro = self.entry_buscar.get()
                if filtro == "buscar producto por nombre...":
                    filtro = ""
                self._cargar_tree_productos(filtro)

        self.items_factura.append({
            "id": id_prod,
            "nombre": nombre,
            "precio": precio_venta,
            "cantidad": 1,
            "stock": stock
        })
        self._actualizar_tree_factura()

    # ------------------------------------------------------------
    # Producto sin precio: cambio rápido con clave de administrador
    # ------------------------------------------------------------
    def _centrar_dialogo(self, v):
        v.update_idletasks()
        root = self.parent.winfo_toplevel()
        w, h = v.winfo_reqwidth(), v.winfo_reqheight()
        x = root.winfo_rootx() + (root.winfo_width() - w) // 2
        y = root.winfo_rooty() + (root.winfo_height() - h) // 2
        v.geometry(f"{w}x{h}+{max(x, 0)}+{max(y, 0)}")

    def _boton_dialogo(self, parent, texto, comando, bg, fg, hover, ancho=16):
        btn = tk.Button(
            parent, text=texto, font=("Arial", 11, "bold"), bg=bg, fg=fg,
            activebackground=hover, activeforeground=fg, relief="flat", bd=0,
            cursor="hand2", width=ancho, height=2, command=comando
        )
        btn.bind("<Enter>", lambda e: btn.config(bg=hover))
        btn.bind("<Leave>", lambda e: btn.config(bg=bg))
        return btn

    def _dialogo_sin_precio(self, nombre):
        """Cartel de producto sin precio. Devuelve 'cambiar', 'igual' o 'cancelar'."""
        resultado = {"op": "cancelar"}

        v = tk.Toplevel(self.parent)
        v.title("Producto sin precio de venta")
        v.configure(bg=COLOR_FONDO_INTERNO)
        v.resizable(False, False)
        v.transient(self.parent.winfo_toplevel())

        def elegir(op):
            resultado["op"] = op
            v.destroy()

        tk.Label(v, text="⚠ Producto sin precio", font=("Arial", 16, "bold"),
                 fg=COLOR_ROJO_CERRAR, bg=COLOR_FONDO_INTERNO).pack(pady=(20, 6), padx=30)
        tk.Label(v, text=f"'{nombre}' tiene precio de venta $0.00.\n"
                         "Si lo agrega igual, se facturará sin costo.",
                 font=("Arial", 11), fg=COLOR_NEGRO, bg=COLOR_FONDO_INTERNO,
                 justify=tk.CENTER).pack(padx=30, pady=(0, 16))

        fila = tk.Frame(v, bg=COLOR_FONDO_INTERNO)
        fila.pack(padx=20, pady=(0, 18))
        self._boton_dialogo(fila, "Cambiar precio", lambda: elegir("cambiar"),
                            COLOR_VERDE_BOTON_ACCION, COLOR_BLANCO, "#1a5c1a").pack(side=tk.LEFT, padx=4)
        self._boton_dialogo(fila, "Agregar igual", lambda: elegir("igual"),
                            COLOR_VERDE_BOTON, COLOR_NEGRO, COLOR_VERDE_HOVER).pack(side=tk.LEFT, padx=4)
        self._boton_dialogo(fila, "Cancelar", lambda: elegir("cancelar"),
                            COLOR_ROJO_CERRAR, COLOR_BLANCO, COLOR_ROJO_HOVER).pack(side=tk.LEFT, padx=4)

        v.protocol("WM_DELETE_WINDOW", lambda: elegir("cancelar"))
        self._centrar_dialogo(v)
        v.grab_set()
        self.parent.wait_window(v)
        return resultado["op"]

    def _verificar_clave_admin(self, clave):
        """True si la clave corresponde a un usuario administrador."""
        if not clave:
            return False
        res = query(
            "SELECT id FROM usuarios WHERE rol = 'administrador' AND contraseña = ?",
            (clave,)
        )
        return bool(res)

    def _pedir_cambio_precio(self, id_prod, nombre):
        """
        Pide el precio nuevo y la clave del administrador (si quien está
        logueado es empleado) y actualiza productos.precio_venta.
        Devuelve el precio nuevo, o None si se canceló.
        """
        resultado = {"precio": None}
        intentos = {"n": 0}
        es_admin = session.is_admin()

        v = tk.Toplevel(self.parent)
        v.title("Cambiar precio de venta")
        v.configure(bg=COLOR_FONDO_INTERNO)
        v.resizable(False, False)
        v.transient(self.parent.winfo_toplevel())

        tk.Label(v, text="Cambiar precio", font=("Arial", 16, "bold"),
                 fg=COLOR_VERDE_SIDEBAR, bg=COLOR_FONDO_INTERNO).pack(pady=(18, 2), padx=30)
        tk.Label(v, text=nombre, font=("Arial", 11, "italic"), fg="#555555",
                 bg=COLOR_FONDO_INTERNO, wraplength=320).pack(padx=30, pady=(0, 6))

        form = tk.Frame(v, bg=COLOR_FONDO_INTERNO, padx=30)
        form.pack(fill=tk.X)

        def campo(etiqueta, show=""):
            tk.Label(form, text=etiqueta, font=("Arial", 11), fg=COLOR_NEGRO,
                     bg=COLOR_FONDO_INTERNO, anchor="w").pack(fill=tk.X, pady=(10, 2))
            e = tk.Entry(form, font=("Arial", 12), bg=COLOR_BLANCO, fg=COLOR_NEGRO,
                         relief="flat", bd=0, highlightthickness=1,
                         highlightbackground="#888888", highlightcolor=COLOR_VERDE_SIDEBAR,
                         show=show, width=28)
            e.pack(fill=tk.X, ipady=6)
            return e

        e_precio = campo("Nuevo precio de venta ($):")
        e_clave = None
        if not es_admin:
            e_clave = campo("Contraseña del administrador:", show="*")

        def confirmar(event=None):
            try:
                nuevo = _parsear_precio(e_precio.get())
            except ValueError:
                messagebox.showwarning("Precio inválido", "Ingrese un precio numérico.", parent=v)
                e_precio.focus()
                return
            if nuevo <= 0:
                messagebox.showwarning("Precio inválido", "El precio debe ser mayor a 0.", parent=v)
                e_precio.focus()
                return

            if not es_admin and not self._verificar_clave_admin(e_clave.get()):
                intentos["n"] += 1
                if intentos["n"] >= 3:
                    messagebox.showerror("Acceso denegado",
                                         "Demasiados intentos fallidos.", parent=v)
                    v.destroy()
                    return
                messagebox.showerror(
                    "Contraseña incorrecta",
                    f"Contraseña de administrador incorrecta. "
                    f"Intentos restantes: {3 - intentos['n']}", parent=v)
                e_clave.delete(0, tk.END)
                e_clave.focus()
                return

            try:
                query("UPDATE productos SET precio_venta = ? WHERE id = ?", (nuevo, id_prod))
            except Exception as ex:
                messagebox.showerror("Error", f"No se pudo guardar el precio.\n{ex}", parent=v)
                return
            resultado["precio"] = nuevo
            v.destroy()

        fila = tk.Frame(v, bg=COLOR_FONDO_INTERNO)
        fila.pack(pady=(20, 18))
        self._boton_dialogo(fila, "Guardar", confirmar, COLOR_VERDE_BOTON_ACCION,
                            COLOR_BLANCO, "#1a5c1a", ancho=14).pack(side=tk.LEFT, padx=4)
        self._boton_dialogo(fila, "Cancelar", v.destroy, COLOR_ROJO_CERRAR,
                            COLOR_BLANCO, COLOR_ROJO_HOVER, ancho=14).pack(side=tk.LEFT, padx=4)

        v.bind("<Return>", confirmar)
        v.bind("<Escape>", lambda e: v.destroy())
        self._centrar_dialogo(v)
        v.grab_set()
        e_precio.focus()
        self.parent.wait_window(v)
        return resultado["precio"]

    def _actualizar_tree_factura(self):
        for item in self.tree_factura.get_children():
            self.tree_factura.delete(item)

        self.total = 0.0
        for item in self.items_factura:
            subtotal = item["cantidad"] * item["precio"]
            self.total += subtotal
            self.tree_factura.insert("", tk.END, values=(
                item["nombre"],
                item["cantidad"],
                f"${item['precio']:.2f}",
                f"${subtotal:.2f}"
            ))

        self.lbl_total.config(text=f"TOTAL: ${self.total:.2f}")
        self._guardar_borrador()

    # ------------------------------------------------------------
    # Borrador: se guarda en cada cambio y se recupera al volver
    # ------------------------------------------------------------
    def _guardar_borrador(self):
        _borrador["id_usuario"] = session.id_usuario
        _borrador["items"] = [dict(i) for i in self.items_factura]
        _borrador["cliente"] = self.combo_cliente.get()

    def _restaurar_borrador(self):
        """
        Recupera la factura en curso. Revalida contra la base: si mientras
        tanto se cargó un precio, cambió el stock o se eliminó un producto,
        el borrador se ajusta y se avisa.
        """
        if _borrador["id_usuario"] != session.id_usuario:
            limpiar_borrador()
            return

        if _borrador["cliente"] in self.combo_cliente.cget("values"):
            self.combo_cliente.set(_borrador["cliente"])

        if not _borrador["items"]:
            return

        avisos = []
        for it in _borrador["items"]:
            res = query("SELECT nombre, precio_venta, stock FROM productos WHERE id = ?", (it["id"],))
            if not res:
                avisos.append(f"• '{it['nombre']}' ya no existe: se quitó.")
                continue
            nombre, precio, stock = res[0]
            precio = float(precio or 0.0)
            stock = int(stock or 0)
            if stock < 1:
                avisos.append(f"• '{nombre}' se quedó sin stock: se quitó.")
                continue
            cantidad = it["cantidad"]
            if cantidad > stock:
                cantidad = stock
                avisos.append(f"• '{nombre}': cantidad ajustada a {stock} (stock disponible).")
            if abs(precio - it["precio"]) > 0.005:
                avisos.append(f"• '{nombre}': precio actualizado de ${it['precio']:.2f} a ${precio:.2f}.")
            self.items_factura.append({
                "id": it["id"], "nombre": nombre, "precio": precio,
                "cantidad": cantidad, "stock": stock,
            })

        self._actualizar_tree_factura()

        texto = f"📝 Se recuperó tu factura en curso ({len(self.items_factura)} item(s))."
        if avisos:
            texto += "\n\nCambios desde que saliste de la pantalla:\n" + "\n".join(avisos)
        self.parent.after(150, lambda: messagebox.showinfo("Borrador de factura", texto))

    def _on_doble_clic_item_factura(self, event):
        seleccion = self.tree_factura.selection()
        if not seleccion:
            return

        idx = self.tree_factura.index(seleccion[0])
        item = self.items_factura[idx]

        ventana = tk.Toplevel(self.parent)
        ventana.title("Modificar Cantidad")
        ventana.configure(bg=COLOR_FONDO_INTERNO)
        ventana.resizable(False, False)
        ventana.grab_set()
        ventana.geometry("300x180")
        ventana.transient(self.parent)

        tk.Label(ventana, text=f"Producto: {item['nombre']}", font=("Arial", 11),
            fg=COLOR_NEGRO, bg=COLOR_FONDO_INTERNO).pack(pady=(15, 5))
        tk.Label(ventana, text="Nueva cantidad:", font=("Arial", 11),
            fg=COLOR_NEGRO, bg=COLOR_FONDO_INTERNO).pack()

        entry_cant = tk.Entry(ventana, font=("Arial", 14), bg=COLOR_BLANCO, fg=COLOR_NEGRO,
            relief="flat", bd=1, justify="center")
        entry_cant.insert(0, str(item["cantidad"]))
        entry_cant.pack(pady=10, ipadx=10, ipady=5)
        entry_cant.select_range(0, tk.END)
        entry_cant.focus()

        def guardar():
            try:
                nueva = int(entry_cant.get())
            except ValueError:
                messagebox.showwarning("Inválido", "La cantidad debe ser un número entero.", parent=ventana)
                return

            if nueva <= 0:
                self.items_factura.pop(idx)
            elif nueva > item["stock"]:
                messagebox.showwarning("Stock insuficiente",
                    f"Stock máximo disponible: {item['stock']}", parent=ventana)
                return
            else:
                self.items_factura[idx]["cantidad"] = nueva

            self._actualizar_tree_factura()
            ventana.destroy()

        btn_ok = tk.Button(ventana, text="Aceptar", font=("Arial", 11, "bold"),
            bg=COLOR_VERDE_BOTON_ACCION, fg=COLOR_BLANCO, activebackground="#1a5c1a",
            activeforeground=COLOR_BLANCO, relief="flat", bd=0, cursor="hand2",
            width=12, height=2, command=guardar)
        btn_ok.pack(pady=(5, 10))
        btn_ok.bind("<Enter>", lambda e: btn_ok.config(bg="#1a5c1a"))
        btn_ok.bind("<Leave>", lambda e: btn_ok.config(bg=COLOR_VERDE_BOTON_ACCION))

    def _quitar_item_factura(self):
        seleccion = self.tree_factura.selection()
        if not seleccion:
            messagebox.showwarning("Sin selección", "Seleccione un item para quitar.")
            return
        idx = self.tree_factura.index(seleccion[0])
        self.items_factura.pop(idx)
        self._actualizar_tree_factura()

    def _limpiar_factura(self):
        self.items_factura.clear()
        self._actualizar_tree_factura()

    def _finalizar_venta(self):
        if not self.items_factura:
            messagebox.showwarning("Factura vacía", "No hay productos en la factura.")
            return

        cliente_sel = self.combo_cliente.get()
        if not cliente_sel:
            messagebox.showwarning("Sin cliente", "Seleccione un cliente.")
            return

        id_cliente = int(cliente_sel.split(" - ")[0])
        id_usuario = session.id_usuario
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for item in self.items_factura:
            res = query("SELECT stock FROM productos WHERE id = ?", (item["id"],))
            if not res or res[0][0] < item["cantidad"]:
                disponible = res[0][0] if res else 0
                messagebox.showerror("Stock insuficiente",
                    f"No hay suficiente stock de '{item['nombre']}'. Disponible: {disponible}")
                return

        sin_precio = [i["nombre"] for i in self.items_factura if i["precio"] <= 0]
        if sin_precio:
            if not messagebox.askyesno(
                "Items sin precio de venta",
                "⚠ Estos productos tienen precio $0.00 y se facturarán gratis:\n\n"
                + "\n".join(f"• {n}" for n in sin_precio)
                + "\n\n¿Desea finalizar la venta igual?",
                icon="warning", default="no"
            ):
                return

        respuesta = messagebox.askyesno("Confirmar venta",
            f"¿Desea finalizar la venta por un total de ${self.total:.2f}?")
        if not respuesta:
            return

        try:
            query("INSERT INTO ventas (fecha, id_cliente, id_usuario, total) VALUES (?, ?, ?, ?)",
                  (fecha, id_cliente, id_usuario, self.total))

            res = query("SELECT id FROM ventas WHERE fecha = ? AND id_usuario = ? ORDER BY id DESC LIMIT 1",
                        (fecha, id_usuario))
            if not res:
                raise Exception("No se pudo obtener el ID de la venta")
            id_venta = res[0][0]

            for item in self.items_factura:
                query("""
                    INSERT INTO detalle_ventas (id_venta, id_producto, cantidad, precio_unitario)
                    VALUES (?, ?, ?, ?)
                """, (id_venta, item["id"], item["cantidad"], item["precio"]))
                query("UPDATE productos SET stock = stock - ? WHERE id = ?",
                      (item["cantidad"], item["id"]))

            messagebox.showinfo("Venta exitosa",
                f"Venta #{id_venta} registrada correctamente.\nTotal: ${self.total:.2f}")
            self._limpiar_factura()
            self._cargar_productos_disponibles()
            self._cargar_tree_productos()
            self._cargar_historial()

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo registrar la venta.\nError: {str(e)}")

    def _construir_tab_historial(self):
        frame_historial = tk.Frame(self.tab_historial, bg=COLOR_FONDO_INTERNO, padx=8, pady=8)
        frame_historial.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame_historial, text="Historial de Ventas", font=("Arial", 16, "bold"),
            fg=COLOR_VERDE_SIDEBAR, bg=COLOR_FONDO_INTERNO).pack(anchor="w", pady=(0, 10))

        columnas_hist = ("id", "fecha", "cliente", "vendedor", "total")
        self.tree_historial = ttk.Treeview(frame_historial, columns=columnas_hist, show="headings", height=15)
        self.tree_historial.heading("id", text="ID Venta")
        self.tree_historial.heading("fecha", text="Fecha")
        self.tree_historial.heading("cliente", text="Cliente")
        self.tree_historial.heading("vendedor", text="Vendedor")
        self.tree_historial.heading("total", text="Total")
        self.tree_historial.column("id", width=60, anchor="center")
        self.tree_historial.column("fecha", width=130, anchor="center")
        self.tree_historial.column("cliente", width=180, anchor="w")
        self.tree_historial.column("vendedor", width=120, anchor="w")
        self.tree_historial.column("total", width=100, anchor="center")

        scroll_hist = ttk.Scrollbar(frame_historial, orient=tk.VERTICAL, command=self.tree_historial.yview)
        self.tree_historial.configure(yscrollcommand=scroll_hist.set)
        self.tree_historial.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        scroll_hist.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree_historial.bind("<Double-1>", self._on_doble_clic_historial)

        btn_ver_detalle = tk.Button(
            frame_historial, text="Ver Detalle", font=("Arial", 11, "bold"),
            bg=COLOR_VERDE_BOTON_ACCION, fg=COLOR_BLANCO, activebackground="#1a5c1a",
            activeforeground=COLOR_BLANCO, relief="flat", bd=0, cursor="hand2",
            width=15, height=2, command=self._ver_detalle_historial
        )
        btn_ver_detalle.pack(anchor="e", pady=(10, 0))
        btn_ver_detalle.bind("<Enter>", lambda e: btn_ver_detalle.config(bg="#1a5c1a"))
        btn_ver_detalle.bind("<Leave>", lambda e: btn_ver_detalle.config(bg=COLOR_VERDE_BOTON_ACCION))

        self._cargar_historial()

    def _cargar_historial(self):
        for item in self.tree_historial.get_children():
            self.tree_historial.delete(item)

        consulta = """
            SELECT v.id, v.fecha,
                   COALESCE(c.nombre || ' ' || c.apellido, 'Consumidor Final') as cliente,
                   u.usuario, v.total
            FROM ventas v
            LEFT JOIN clientes c ON v.id_cliente = c.id
            JOIN usuarios u ON v.id_usuario = u.id
            ORDER BY v.fecha DESC
        """
        res = query(consulta)
        if res:
            for fila in res:
                cliente = fila[2] if fila[2] else "Consumidor Final"
                self.tree_historial.insert("", tk.END, values=(
                    fila[0], fila[1], cliente, fila[3], f"${fila[4]:.2f}"
                ))

    def _on_doble_clic_historial(self, event):
        self._ver_detalle_historial()

    def _ver_detalle_historial(self):
        seleccion = self.tree_historial.selection()
        if not seleccion:
            messagebox.showwarning("Sin selección", "Seleccione una venta del historial.")
            return

        item = self.tree_historial.item(seleccion[0])
        valores = item["values"]
        self._mostrar_detalle_venta(valores[0], valores[1], valores[4])

    def _mostrar_detalle_venta(self, id_venta, fecha, total):
        """Ventana con el detalle de items de una venta puntual."""
        ventana = tk.Toplevel(self.parent)
        ventana.title(f"Detalle de Venta #{id_venta}")
        ventana.configure(bg=COLOR_FONDO_INTERNO)
        ventana.geometry("550x450")
        ventana.transient(self.parent)
        ventana.grab_set()

        tk.Label(ventana, text=f"Venta #{id_venta}", font=("Arial", 18, "bold"),
            fg=COLOR_VERDE_SIDEBAR, bg=COLOR_FONDO_INTERNO).pack(pady=(15, 5))
        tk.Label(ventana, text=f"Fecha: {fecha}", font=("Arial", 11),
            fg="#555555", bg=COLOR_FONDO_INTERNO).pack()
        tk.Label(ventana, text=f"Total: {total}", font=("Arial", 13, "bold"),
            fg=COLOR_VERDE_SIDEBAR, bg=COLOR_FONDO_INTERNO).pack(pady=(5, 10))

        frame_tabla = tk.Frame(ventana, bg=COLOR_FONDO_INTERNO)
        frame_tabla.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

        columnas = ("producto", "cantidad", "precio", "subtotal")
        tree_det = ttk.Treeview(frame_tabla, columns=columnas, show="headings", height=10)
        tree_det.heading("producto", text="Producto")
        tree_det.heading("cantidad", text="Cantidad")
        tree_det.heading("precio", text="Precio Unit.")
        tree_det.heading("subtotal", text="Subtotal")
        tree_det.column("producto", width=200, anchor="w")
        tree_det.column("cantidad", width=80, anchor="center")
        tree_det.column("precio", width=100, anchor="center")
        tree_det.column("subtotal", width=100, anchor="center")

        scroll = ttk.Scrollbar(frame_tabla, orient=tk.VERTICAL, command=tree_det.yview)
        tree_det.configure(yscrollcommand=scroll.set)
        tree_det.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        consulta = """
            SELECT COALESCE(p.nombre, '(producto eliminado)'), d.cantidad, d.precio_unitario
            FROM detalle_ventas d
            LEFT JOIN productos p ON d.id_producto = p.id
            WHERE d.id_venta = ?
        """
        res = query(consulta, (id_venta,))
        if res:
            for fila in res:
                subtotal = fila[1] * fila[2]
                tree_det.insert("", tk.END, values=(
                    fila[0], fila[1], f"${fila[2]:.2f}", f"${subtotal:.2f}"
                ))

        btn_cerrar = tk.Button(
            ventana, text="Cerrar", font=("Arial", 11, "bold"),
            bg=COLOR_VERDE_BOTON, fg=COLOR_NEGRO, activebackground=COLOR_VERDE_HOVER,
            activeforeground=COLOR_NEGRO, relief="flat", bd=0, cursor="hand2",
            width=15, height=2, command=ventana.destroy
        )
        btn_cerrar.pack(pady=(0, 15))
        btn_cerrar.bind("<Enter>", lambda e: btn_cerrar.config(bg=COLOR_VERDE_HOVER))
        btn_cerrar.bind("<Leave>", lambda e: btn_cerrar.config(bg=COLOR_VERDE_BOTON))

    # ============================================================
    # VENTANA EMERGENTE: TODAS LAS VENTAS (buscador por fecha)
    # ============================================================

    def _abrir_ventana_ventas(self):
        """Abre una ventana aparte con todas las ventas, buscables por fecha."""
        ventana = tk.Toplevel(self.parent)
        ventana.title("Ventas Realizadas")
        ventana.configure(bg=COLOR_FONDO_INTERNO)
        ventana.geometry("700x520")
        ventana.minsize(600, 420)
        ventana.transient(self.parent)
        ventana.grab_set()

        tk.Label(ventana, text="Ventas Realizadas", font=("Arial", 18, "bold"),
            fg=COLOR_VERDE_SIDEBAR, bg=COLOR_FONDO_INTERNO).pack(pady=(15, 10))

        frame_buscar = tk.Frame(ventana, bg=COLOR_FONDO_INTERNO, padx=20)
        frame_buscar.pack(fill=tk.X)

        tk.Label(frame_buscar, text="Buscar por fecha:", font=("Arial", 11),
            fg=COLOR_NEGRO, bg=COLOR_FONDO_INTERNO).pack(side=tk.LEFT, padx=(0, 8))

        entry_fecha = tk.Entry(frame_buscar, font=("Arial", 11), bg=COLOR_BLANCO, fg=COLOR_NEGRO,
            relief="flat", bd=1)
        entry_fecha.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)
        entry_fecha.insert(0, "")

        frame_tabla = tk.Frame(ventana, bg=COLOR_FONDO_INTERNO, padx=20)
        frame_tabla.pack(fill=tk.BOTH, expand=True, pady=(12, 0))

        columnas = ("id", "fecha", "cliente", "vendedor", "total")
        tree_ventas = ttk.Treeview(frame_tabla, columns=columnas, show="headings", height=14)
        tree_ventas.heading("id", text="ID")
        tree_ventas.heading("fecha", text="Fecha")
        tree_ventas.heading("cliente", text="Cliente")
        tree_ventas.heading("vendedor", text="Vendedor")
        tree_ventas.heading("total", text="Total")
        tree_ventas.column("id", width=50, anchor="center")
        tree_ventas.column("fecha", width=130, anchor="center")
        tree_ventas.column("cliente", width=180, anchor="w")
        tree_ventas.column("vendedor", width=120, anchor="w")
        tree_ventas.column("total", width=100, anchor="center")

        scroll_ventas = ttk.Scrollbar(frame_tabla, orient=tk.VERTICAL, command=tree_ventas.yview)
        tree_ventas.configure(yscrollcommand=scroll_ventas.set)
        tree_ventas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_ventas.pack(side=tk.RIGHT, fill=tk.Y)

        def cargar(filtro_fecha=""):
            for item in tree_ventas.get_children():
                tree_ventas.delete(item)

            consulta = """
                SELECT v.id, v.fecha,
                       COALESCE(c.nombre || ' ' || c.apellido, 'Consumidor Final') as cliente,
                       u.usuario, v.total
                FROM ventas v
                LEFT JOIN clientes c ON v.id_cliente = c.id
                JOIN usuarios u ON v.id_usuario = u.id
            """
            parametros = ()
            if filtro_fecha.strip():
                consulta += " WHERE v.fecha LIKE ?"
                parametros = (f"%{filtro_fecha.strip()}%",)
            consulta += " ORDER BY v.fecha DESC"

            res = query(consulta, parametros)
            if res:
                for fila in res:
                    cliente = fila[2] if fila[2] else "Consumidor Final"
                    tree_ventas.insert("", tk.END, values=(
                        fila[0], fila[1], cliente, fila[3], f"${fila[4]:.2f}"
                    ))

        def filtrar(event=None):
            cargar(entry_fecha.get())

        entry_fecha.bind("<KeyRelease>", filtrar)

        def ver_detalle_seleccionado(event=None):
            seleccion = tree_ventas.selection()
            if not seleccion:
                messagebox.showwarning("Sin selección", "Seleccione una venta.", parent=ventana)
                return
            valores = tree_ventas.item(seleccion[0])["values"]
            self._mostrar_detalle_venta(valores[0], valores[1], valores[4])

        tree_ventas.bind("<Double-1>", ver_detalle_seleccionado)

        frame_botones_v = tk.Frame(ventana, bg=COLOR_FONDO_INTERNO, padx=20)
        frame_botones_v.pack(fill=tk.X, pady=(10, 15))

        btn_ver = tk.Button(
            frame_botones_v, text="Ver Detalle", font=("Arial", 11, "bold"),
            bg=COLOR_VERDE_BOTON_ACCION, fg=COLOR_BLANCO, activebackground="#1a5c1a",
            activeforeground=COLOR_BLANCO, relief="flat", bd=0, cursor="hand2",
            width=15, height=2, command=ver_detalle_seleccionado
        )
        btn_ver.pack(side=tk.LEFT, padx=(0, 10))
        btn_ver.bind("<Enter>", lambda e: btn_ver.config(bg="#1a5c1a"))
        btn_ver.bind("<Leave>", lambda e: btn_ver.config(bg=COLOR_VERDE_BOTON_ACCION))

        btn_cerrar_v = tk.Button(
            frame_botones_v, text="Cerrar", font=("Arial", 11, "bold"),
            bg=COLOR_VERDE_BOTON, fg=COLOR_NEGRO, activebackground=COLOR_VERDE_HOVER,
            activeforeground=COLOR_NEGRO, relief="flat", bd=0, cursor="hand2",
            width=15, height=2, command=ventana.destroy
        )
        btn_cerrar_v.pack(side=tk.LEFT)
        btn_cerrar_v.bind("<Enter>", lambda e: btn_cerrar_v.config(bg=COLOR_VERDE_HOVER))
        btn_cerrar_v.bind("<Leave>", lambda e: btn_cerrar_v.config(bg=COLOR_VERDE_BOTON))

        cargar()