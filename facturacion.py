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

COLOR_VERDE_SIDEBAR      = "#06370b"
COLOR_VERDE_BOTON        = "#a6a6a6"
COLOR_VERDE_HOVER        = "#FFFFFF"
COLOR_GRIS_FONDO         = "#a6a6a6"
COLOR_BLANCO             = "#FFFFFF"
COLOR_NEGRO              = "#000000"
COLOR_ROJO_CERRAR        = "#8B0000"
COLOR_ROJO_HOVER         = "#A52A2A"
COLOR_VERDE_BOTON_ACCION = "#0D2E0D"
COLOR_FONDO_INTERNO      = "#f5f5f5"


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

    def _cargar_clientes(self):
        self.clientes_dict = {0: "Consumidor Final"}
        res = query("SELECT id, nombre, apellido FROM clientes ORDER BY nombre, apellido")
        if res:
            for fila in res:
                self.clientes_dict[fila[0]] = f"{fila[1]} {fila[2]}"

    def _cargar_productos_disponibles(self):
        self.productos_disponibles = []
        res = query("SELECT id, nombre, descripcion, precio_venta, stock FROM productos WHERE stock > 0 ORDER BY nombre")
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

        self.entry_buscar = tk.Entry(frame_prod, font=("Arial", 11), bg=COLOR_BLANCO, fg=COLOR_NEGRO,
            relief="flat", bd=1)
        self.entry_buscar.pack(fill=tk.X, pady=(0, 8))
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

        btn_agregar = tk.Button(
            frame_prod, text="Agregar a Factura", font=("Arial", 10, "bold"),
            bg=COLOR_VERDE_BOTON_ACCION, fg=COLOR_BLANCO, activebackground="#1a5c1a",
            activeforeground=COLOR_BLANCO, relief="flat", bd=0, cursor="hand2",
            height=2, command=self._agregar_producto_factura
        )
        btn_agregar.pack(fill=tk.X, pady=(8, 0))
        btn_agregar.bind("<Enter>", lambda e: btn_agregar.config(bg="#1a5c1a"))
        btn_agregar.bind("<Leave>", lambda e: btn_agregar.config(bg=COLOR_VERDE_BOTON_ACCION))

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

        frame_btns_items = tk.Frame(frame_factura, bg=COLOR_FONDO_INTERNO)
        frame_btns_items.pack(fill=tk.X, pady=(8, 0))

        btn_quitar = tk.Button(
            frame_btns_items, text="Quitar Item", font=("Arial", 10, "bold"),
            bg=COLOR_ROJO_CERRAR, fg=COLOR_BLANCO, activebackground=COLOR_ROJO_HOVER,
            activeforeground=COLOR_BLANCO, relief="flat", bd=0, cursor="hand2",
            height=2, command=self._quitar_item_factura
        )
        btn_quitar.pack(side=tk.LEFT, padx=(0, 5))
        btn_quitar.bind("<Enter>", lambda e: btn_quitar.config(bg=COLOR_ROJO_HOVER))
        btn_quitar.bind("<Leave>", lambda e: btn_quitar.config(bg=COLOR_ROJO_CERRAR))

        btn_limpiar = tk.Button(
            frame_btns_items, text="Limpiar Todo", font=("Arial", 10, "bold"),
            bg=COLOR_VERDE_BOTON, fg=COLOR_NEGRO, activebackground=COLOR_VERDE_HOVER,
            activeforeground=COLOR_NEGRO, relief="flat", bd=0, cursor="hand2",
            height=2, command=self._limpiar_factura
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

        self._cargar_tree_productos()

    def _cargar_tree_productos(self, filtro=""):
        for item in self.tree_prod.get_children():
            self.tree_prod.delete(item)

        for prod in self.productos_disponibles:
            id_p, nombre, desc, precio_venta, stock = prod
            if filtro.lower() in nombre.lower():
                self.tree_prod.insert("", tk.END, values=(id_p, nombre, f"${precio_venta:.2f}", stock))

    def _filtrar_productos(self, event):
        texto = self.entry_buscar.get()
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

        self.items_factura.append({
            "id": id_prod,
            "nombre": nombre,
            "precio": precio_venta,
            "cantidad": 1,
            "stock": stock
        })
        self._actualizar_tree_factura()

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
        id_venta = valores[0]
        fecha = valores[1]
        total = valores[4]

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
            SELECT p.nombre, d.cantidad, d.precio_unitario
            FROM detalle_ventas d
            JOIN productos p ON d.id_producto = p.id
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