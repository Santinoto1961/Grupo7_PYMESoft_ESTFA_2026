#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================
clientes.py - Módulo de Gestión de Clientes
============================================================
ABM completo de clientes con historial de ventas y detalle
de compras mediante ventanas secundarias Toplevel.

Autor: Estudiante
Fecha: 2026-08-30
============================================================
"""

import tkinter as tk
from tkinter import ttk, messagebox

from database import query
from session import session

# ============================================================
# PALETA DE COLORES
# ============================================================
COLOR_VERDE_SIDEBAR = "#06370b"
COLOR_VERDE_BOTON = "#a6a6a6"
COLOR_VERDE_HOVER = "#FFFFFF"
COLOR_GRIS_FONDO = "#a6a6a6"
COLOR_BLANCO = "#FFFFFF"
COLOR_NEGRO = "#000000"
COLOR_ROJO_CERRAR = "#8B0000"
COLOR_ROJO_HOVER = "#A52A2A"
COLOR_VERDE_BOTON_ACCION = "#0D2E0D"
COLOR_FONDO_INTERNO = "#f5f5f5"


class VistaClientes:
    """
    Clase que construye y gestiona la pantalla de clientes
    dentro del área de contenido de la ventana principal.
    """

    def __init__(self, parent_frame):
        self.parent = parent_frame
        self.cliente_seleccionado = None

        for widget in self.parent.winfo_children():
            widget.destroy()

        self._crear_titulo()
        self._crear_panel_principal()
        self._crear_botones_accion()
        self._cargar_clientes()

    # ============================================================
    # SECCIÓN 1: TÍTULO PRINCIPAL
    # ============================================================

    def _crear_titulo(self):
        self.lbl_titulo = tk.Label(
            self.parent,
            text="CLIENTES:",
            font=("Arial", 32, "bold"),
            fg=COLOR_NEGRO,
            bg=COLOR_GRIS_FONDO
        )
        self.lbl_titulo.pack(anchor="w", padx=40, pady=(30, 15))

    # ============================================================
    # SECCIÓN 2: PANEL PRINCIPAL
    # ============================================================

    def _crear_panel_principal(self):
        self.frame_panel = tk.Frame(
            self.parent,
            bg=COLOR_VERDE_SIDEBAR,
            padx=8,
            pady=8
        )
        self.frame_panel.pack(fill=tk.BOTH, expand=True, padx=40, pady=(0, 20))

        self.lbl_subtitulo = tk.Label(
            self.frame_panel,
            text="Lista de clientes:",
            font=("Arial", 16, "bold"),
            fg=COLOR_BLANCO,
            bg=COLOR_VERDE_SIDEBAR
        )
        self.lbl_subtitulo.pack(anchor="w", pady=(0, 8))

        self.frame_interno = tk.Frame(
            self.frame_panel,
            bg=COLOR_FONDO_INTERNO
        )
        self.frame_interno.pack(fill=tk.BOTH, expand=True)

        self._crear_tabla_clientes()
        self._crear_panel_lateral()

    def _crear_tabla_clientes(self):
        self.frame_tabla = tk.Frame(
            self.frame_interno,
            bg=COLOR_FONDO_INTERNO
        )
        self.frame_tabla.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 2))

        columnas = ("id", "nombre", "apellido", "direccion", "telefono", "email")
        self.tree = ttk.Treeview(
            self.frame_tabla,
            columns=columnas,
            show="headings",
            height=12
        )

        self.tree.heading("id", text="ID")
        self.tree.heading("nombre", text="Nombre")
        self.tree.heading("apellido", text="Apellido")
        self.tree.heading("direccion", text="Dirección")
        self.tree.heading("telefono", text="Teléfono")
        self.tree.heading("email", text="Email")

        self.tree.column("id", width=40, anchor="center")
        self.tree.column("nombre", width=120, anchor="w")
        self.tree.column("apellido", width=120, anchor="w")
        self.tree.column("direccion", width=180, anchor="w")
        self.tree.column("telefono", width=100, anchor="w")
        self.tree.column("email", width=180, anchor="w")

        scrollbar = ttk.Scrollbar(
            self.frame_tabla,
            orient=tk.VERTICAL,
            command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)

        self.tree.bind("<<TreeviewSelect>>", self._on_seleccionar_cliente)

    def _crear_panel_lateral(self):
        self.frame_lateral = tk.Frame(
            self.frame_interno,
            bg=COLOR_FONDO_INTERNO,
            width=280
        )
        self.frame_lateral.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)
        self.frame_lateral.pack_propagate(False)

        self.lbl_info_titulo = tk.Label(
            self.frame_lateral,
            text="Información del cliente:",
            font=("Arial", 12, "bold"),
            fg=COLOR_NEGRO,
            bg=COLOR_FONDO_INTERNO
        )
        self.lbl_info_titulo.pack(anchor="w", pady=(0, 15))

        self.lbl_info_id = tk.Label(
            self.frame_lateral,
            text="ID: —",
            font=("Arial", 11),
            fg=COLOR_NEGRO,
            bg=COLOR_FONDO_INTERNO,
            anchor="w"
        )
        self.lbl_info_id.pack(fill=tk.X, pady=4)

        self.lbl_info_nombre = tk.Label(
            self.frame_lateral,
            text="Nombre: —",
            font=("Arial", 11),
            fg=COLOR_NEGRO,
            bg=COLOR_FONDO_INTERNO,
            anchor="w"
        )
        self.lbl_info_nombre.pack(fill=tk.X, pady=4)

        self.lbl_info_apellido = tk.Label(
            self.frame_lateral,
            text="Apellido: —",
            font=("Arial", 11),
            fg=COLOR_NEGRO,
            bg=COLOR_FONDO_INTERNO,
            anchor="w"
        )
        self.lbl_info_apellido.pack(fill=tk.X, pady=4)

        self.lbl_info_direccion = tk.Label(
            self.frame_lateral,
            text="Dirección: —",
            font=("Arial", 11),
            fg=COLOR_NEGRO,
            bg=COLOR_FONDO_INTERNO,
            anchor="w"
        )
        self.lbl_info_direccion.pack(fill=tk.X, pady=4)

        self.lbl_info_telefono = tk.Label(
            self.frame_lateral,
            text="Teléfono: —",
            font=("Arial", 11),
            fg=COLOR_NEGRO,
            bg=COLOR_FONDO_INTERNO,
            anchor="w"
        )
        self.lbl_info_telefono.pack(fill=tk.X, pady=4)

        self.lbl_info_email = tk.Label(
            self.frame_lateral,
            text="Email: —",
            font=("Arial", 11),
            fg=COLOR_NEGRO,
            bg=COLOR_FONDO_INTERNO,
            anchor="w"
        )
        self.lbl_info_email.pack(fill=tk.X, pady=4)

        tk.Frame(self.frame_lateral, bg="#888888", height=1).pack(fill=tk.X, pady=15)

        self.lbl_nota = tk.Label(
            self.frame_lateral,
            text="Seleccione un cliente de la tabla\npara ver sus detalles.",
            font=("Arial", 9, "italic"),
            fg="#666666",
            bg=COLOR_FONDO_INTERNO,
            justify=tk.LEFT
        )
        self.lbl_nota.pack(anchor="w")

    # ============================================================
    # SECCIÓN 3: BOTONES DE ACCIÓN
    # ============================================================

    def _crear_botones_accion(self):
        self.frame_botones = tk.Frame(
            self.parent,
            bg=COLOR_GRIS_FONDO
        )
        self.frame_botones.pack(fill=tk.X, padx=40, pady=(0, 10))

        self.frame_fila_botones = tk.Frame(
            self.frame_botones,
            bg=COLOR_GRIS_FONDO
        )
        self.frame_fila_botones.pack(fill=tk.X)

        self.btn_editar = tk.Button(
            self.frame_fila_botones,
            text="Editar cliente",
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
            command=self._editar_cliente
        )
        self.btn_editar.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_agregar = tk.Button(
            self.frame_fila_botones,
            text="Agregar cliente",
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
            command=self._mostrar_formulario_agregar
        )
        self.btn_agregar.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_eliminar = tk.Button(
            self.frame_fila_botones,
            text="Eliminar cliente",
            font=("Arial", 11, "bold"),
            bg=COLOR_ROJO_CERRAR,
            fg=COLOR_BLANCO,
            activebackground=COLOR_ROJO_HOVER,
            activeforeground=COLOR_BLANCO,
            relief="flat",
            bd=0,
            cursor="hand2",
            width=16,
            height=2,
            command=self._eliminar_cliente
        )
        self.btn_eliminar.pack(side=tk.LEFT, padx=(0, 10))

        tk.Frame(self.frame_fila_botones, bg=COLOR_GRIS_FONDO).pack(side=tk.LEFT, expand=True)

        self.btn_historial = tk.Button(
            self.frame_fila_botones,
            text="Ver Historial de Ventas",
            font=("Arial", 11, "bold"),
            bg=COLOR_VERDE_BOTON_ACCION,
            fg=COLOR_BLANCO,
            activebackground="#1a5c1a",
            activeforeground=COLOR_BLANCO,
            relief="flat",
            bd=0,
            cursor="hand2",
            width=22,
            height=2,
            command=self._ver_historial_ventas
        )
        self.btn_historial.pack(side=tk.LEFT)

        self.btn_editar.bind("<Enter>", lambda e: self.btn_editar.config(bg=COLOR_VERDE_HOVER))
        self.btn_editar.bind("<Leave>", lambda e: self.btn_editar.config(bg=COLOR_VERDE_BOTON))
        self.btn_agregar.bind("<Enter>", lambda e: self.btn_agregar.config(bg=COLOR_VERDE_HOVER))
        self.btn_agregar.bind("<Leave>", lambda e: self.btn_agregar.config(bg=COLOR_VERDE_BOTON))
        self.btn_eliminar.bind("<Enter>", lambda e: self.btn_eliminar.config(bg=COLOR_ROJO_HOVER))
        self.btn_eliminar.bind("<Leave>", lambda e: self.btn_eliminar.config(bg=COLOR_ROJO_CERRAR))
        self.btn_historial.bind("<Enter>", lambda e: self.btn_historial.config(bg="#1a5c1a"))
        self.btn_historial.bind("<Leave>", lambda e: self.btn_historial.config(bg=COLOR_VERDE_BOTON_ACCION))

    # ============================================================
    # SECCIÓN 4: FORMULARIOS (AGREGAR / EDITAR)
    # ============================================================

    def _mostrar_formulario_agregar(self):
        self.ventana_form = tk.Toplevel(self.parent)
        self.ventana_form.title("Agregar Nuevo Cliente")
        self.ventana_form.configure(bg=COLOR_FONDO_INTERNO)
        self.ventana_form.resizable(False, False)
        self.ventana_form.grab_set()
        self.ventana_form.geometry("420x550")
        self.ventana_form.transient(self.parent)

        # Centrar la ventana respecto a la pantalla
        self.ventana_form.update_idletasks()
        ancho = self.ventana_form.winfo_width()
        alto = self.ventana_form.winfo_height()
        x = (self.ventana_form.winfo_screenwidth() // 2) - (ancho // 2)
        y = (self.ventana_form.winfo_screenheight() // 2) - (alto // 2)
        self.ventana_form.geometry(f"{ancho}x{alto}+{x}+{y}")

        tk.Label(
            self.ventana_form,
            text="Nuevo Cliente",
            font=("Arial", 18, "bold"),
            fg=COLOR_VERDE_SIDEBAR,
            bg=COLOR_FONDO_INTERNO
        ).pack(pady=(20, 15))

        # Frame scrollable por si acaso
        canvas = tk.Canvas(self.ventana_form, bg=COLOR_FONDO_INTERNO, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.ventana_form, orient=tk.VERTICAL, command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=COLOR_FONDO_INTERNO, padx=30)

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        campos = [
            ("Nombre:", "entry_nombre"),
            ("Apellido:", "entry_apellido"),
            ("Dirección:", "entry_direccion"),
            ("Teléfono:", "entry_telefono"),
            ("Email:", "entry_email"),
        ]

        self.entries = {}
        for label_text, attr_name in campos:
            tk.Label(scroll_frame, text=label_text, font=("Arial", 11), fg=COLOR_NEGRO, bg=COLOR_FONDO_INTERNO, anchor="w").pack(fill=tk.X, pady=(12, 3))
            entry = tk.Entry(scroll_frame, font=("Arial", 12), bg=COLOR_BLANCO, fg=COLOR_NEGRO, relief="flat", bd=1)
            entry.pack(fill=tk.X, ipady=8, pady=(0, 5))
            self.entries[attr_name] = entry

        # Espacio antes del botón
        tk.Frame(scroll_frame, bg=COLOR_FONDO_INTERNO, height=20).pack()

        btn_confirmar = tk.Button(
            scroll_frame,
            text="Confirmar",
            font=("Arial", 12, "bold"),
            bg=COLOR_VERDE_BOTON_ACCION,
            fg=COLOR_BLANCO,
            activebackground="#1a5c1a",
            activeforeground=COLOR_BLANCO,
            relief="flat",
            bd=0,
            cursor="hand2",
            width=20,
            height=2,
            command=self._confirmar_agregar
        )
        btn_confirmar.pack(pady=(10, 25))
        btn_confirmar.bind("<Enter>", lambda e: btn_confirmar.config(bg="#1a5c1a"))
        btn_confirmar.bind("<Leave>", lambda e: btn_confirmar.config(bg=COLOR_VERDE_BOTON_ACCION))

    def _confirmar_agregar(self):
        nombre = self.entries["entry_nombre"].get().strip()
        apellido = self.entries["entry_apellido"].get().strip()
        direccion = self.entries["entry_direccion"].get().strip()
        telefono = self.entries["entry_telefono"].get().strip()
        email = self.entries["entry_email"].get().strip()

        if not nombre or not apellido:
            messagebox.showwarning("Campos obligatorios", "El nombre y el apellido son obligatorios.", parent=self.ventana_form)
            return

        consulta = "INSERT INTO clientes (nombre, apellido, direccion, telefono, email) VALUES (?, ?, ?, ?, ?)"
        try:
            query(consulta, (nombre, apellido, direccion, telefono, email))
            messagebox.showinfo("Éxito", f"Cliente '{nombre} {apellido}' creado correctamente.", parent=self.ventana_form)
            self.ventana_form.destroy()
            self._cargar_clientes()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear el cliente.\nError: {str(e)}", parent=self.ventana_form)

    def _editar_cliente(self):
        if self.cliente_seleccionado is None:
            messagebox.showwarning("Sin selección", "Por favor, seleccione un cliente de la tabla para editar.")
            return

        seleccion = self.tree.selection()
        item = self.tree.item(seleccion[0])
        valores = item["values"]

        self.ventana_edit = tk.Toplevel(self.parent)
        self.ventana_edit.title("Editar Cliente")
        self.ventana_edit.configure(bg=COLOR_FONDO_INTERNO)
        self.ventana_edit.resizable(False, False)
        self.ventana_edit.grab_set()
        self.ventana_edit.geometry("420x550")
        self.ventana_edit.transient(self.parent)

        # Centrar la ventana
        self.ventana_edit.update_idletasks()
        ancho = self.ventana_edit.winfo_width()
        alto = self.ventana_edit.winfo_height()
        x = (self.ventana_edit.winfo_screenwidth() // 2) - (ancho // 2)
        y = (self.ventana_edit.winfo_screenheight() // 2) - (alto // 2)
        self.ventana_edit.geometry(f"{ancho}x{alto}+{x}+{y}")

        tk.Label(
            self.ventana_edit,
            text="Editar Cliente",
            font=("Arial", 18, "bold"),
            fg=COLOR_VERDE_SIDEBAR,
            bg=COLOR_FONDO_INTERNO
        ).pack(pady=(20, 15))

        # Frame scrollable
        canvas = tk.Canvas(self.ventana_edit, bg=COLOR_FONDO_INTERNO, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.ventana_edit, orient=tk.VERTICAL, command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=COLOR_FONDO_INTERNO, padx=30)

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        campos = [
            ("Nombre:", "entry_edit_nombre", valores[1]),
            ("Apellido:", "entry_edit_apellido", valores[2]),
            ("Dirección:", "entry_edit_direccion", valores[3] if valores[3] != "—" else ""),
            ("Teléfono:", "entry_edit_telefono", valores[4] if valores[4] != "—" else ""),
            ("Email:", "entry_edit_email", valores[5] if valores[5] != "—" else ""),
        ]

        self.edit_entries = {}
        for label_text, attr_name, valor in campos:
            tk.Label(scroll_frame, text=label_text, font=("Arial", 11), fg=COLOR_NEGRO, bg=COLOR_FONDO_INTERNO, anchor="w").pack(fill=tk.X, pady=(12, 3))
            entry = tk.Entry(scroll_frame, font=("Arial", 12), bg=COLOR_BLANCO, fg=COLOR_NEGRO, relief="flat", bd=1)
            entry.insert(0, valor)
            entry.pack(fill=tk.X, ipady=8, pady=(0, 5))
            self.edit_entries[attr_name] = entry

        tk.Frame(scroll_frame, bg=COLOR_FONDO_INTERNO, height=20).pack()

        btn_guardar = tk.Button(
            scroll_frame,
            text="Guardar Cambios",
            font=("Arial", 12, "bold"),
            bg=COLOR_VERDE_BOTON_ACCION,
            fg=COLOR_BLANCO,
            activebackground="#1a5c1a",
            activeforeground=COLOR_BLANCO,
            relief="flat",
            bd=0,
            cursor="hand2",
            width=20,
            height=2,
            command=lambda: self._confirmar_editar(valores[0])
        )
        btn_guardar.pack(pady=(10, 25))
        btn_guardar.bind("<Enter>", lambda e: btn_guardar.config(bg="#1a5c1a"))
        btn_guardar.bind("<Leave>", lambda e: btn_guardar.config(bg=COLOR_VERDE_BOTON_ACCION))

    def _confirmar_editar(self, cliente_id):
        nombre = self.edit_entries["entry_edit_nombre"].get().strip()
        apellido = self.edit_entries["entry_edit_apellido"].get().strip()
        direccion = self.edit_entries["entry_edit_direccion"].get().strip()
        telefono = self.edit_entries["entry_edit_telefono"].get().strip()
        email = self.edit_entries["entry_edit_email"].get().strip()

        if not nombre or not apellido:
            messagebox.showwarning("Campos obligatorios", "El nombre y el apellido son obligatorios.", parent=self.ventana_edit)
            return

        consulta = "UPDATE clientes SET nombre = ?, apellido = ?, direccion = ?, telefono = ?, email = ? WHERE id = ?"
        try:
            query(consulta, (nombre, apellido, direccion, telefono, email, cliente_id))
            messagebox.showinfo("Éxito", f"Cliente '{nombre} {apellido}' actualizado correctamente.", parent=self.ventana_edit)
            self.ventana_edit.destroy()
            self._cargar_clientes()
            self._resetear_panel_lateral()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo actualizar el cliente.\nError: {str(e)}", parent=self.ventana_edit)

    # ============================================================
    # SECCIÓN 5: OPERACIONES CRUD
    # ============================================================

    def _cargar_clientes(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        consulta = "SELECT id, nombre, apellido, direccion, telefono, email FROM clientes ORDER BY id"
        resultado = query(consulta)

        if resultado:
            for fila in resultado:
                direccion = fila[3] if fila[3] else "—"
                telefono = fila[4] if fila[4] else "—"
                email = fila[5] if fila[5] else "—"
                self.tree.insert("", tk.END, values=(fila[0], fila[1], fila[2], direccion, telefono, email))

    def _on_seleccionar_cliente(self, event):
        seleccion = self.tree.selection()
        if not seleccion:
            return

        item = self.tree.item(seleccion[0])
        valores = item["values"]
        self.cliente_seleccionado = valores[0]

        self.lbl_info_id.config(text=f"ID: {valores[0]}")
        self.lbl_info_nombre.config(text=f"Nombre: {valores[1]}")
        self.lbl_info_apellido.config(text=f"Apellido: {valores[2]}")
        self.lbl_info_direccion.config(text=f"Dirección: {valores[3]}")
        self.lbl_info_telefono.config(text=f"Teléfono: {valores[4]}")
        self.lbl_info_email.config(text=f"Email: {valores[5]}")
        self.lbl_nota.config(text="Cliente seleccionado.\nUse los botones de abajo para editar, eliminar o ver historial.")

    def _eliminar_cliente(self):
        if self.cliente_seleccionado is None:
            messagebox.showwarning("Sin selección", "Por favor, seleccione un cliente de la tabla para eliminar.")
            return

        seleccion = self.tree.selection()
        item = self.tree.item(seleccion[0])
        valores = item["values"]
        cliente_id = valores[0]
        cliente_nombre = f"{valores[1]} {valores[2]}"

        respuesta = messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Está seguro de que desea eliminar al cliente '{cliente_nombre}'?\n\nEsta acción no se puede deshacer."
        )

        if respuesta:
            consulta = "DELETE FROM clientes WHERE id = ?"
            try:
                query(consulta, (cliente_id,))
                messagebox.showinfo("Éxito", f"Cliente '{cliente_nombre}' eliminado correctamente.")
                self.cliente_seleccionado = None
                self._resetear_panel_lateral()
                self._cargar_clientes()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo eliminar el cliente.\nError: {str(e)}")

    # ============================================================
    # SECCIÓN 6: HISTORIAL DE VENTAS Y DETALLE
    # ============================================================

    def _ver_historial_ventas(self):
        if self.cliente_seleccionado is None:
            messagebox.showwarning("Sin selección", "Por favor, seleccione un cliente para ver su historial de ventas.")
            return

        seleccion = self.tree.selection()
        item = self.tree.item(seleccion[0])
        valores = item["values"]
        cliente_id = valores[0]
        cliente_nombre = f"{valores[1]} {valores[2]}"

        ventana_historial = tk.Toplevel(self.parent)
        ventana_historial.title(f"Historial de Ventas - {cliente_nombre}")
        ventana_historial.configure(bg=COLOR_FONDO_INTERNO)
        ventana_historial.geometry("600x450")
        ventana_historial.transient(self.parent)
        ventana_historial.grab_set()

        tk.Label(
            ventana_historial,
            text=f"Historial de Ventas: {cliente_nombre}",
            font=("Arial", 16, "bold"),
            fg=COLOR_VERDE_SIDEBAR,
            bg=COLOR_FONDO_INTERNO
        ).pack(pady=(15, 10))

        frame_tabla = tk.Frame(ventana_historial, bg=COLOR_FONDO_INTERNO)
        frame_tabla.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        columnas = ("id_venta", "fecha", "vendedor", "total")
        tree_ventas = ttk.Treeview(
            frame_tabla,
            columns=columnas,
            show="headings",
            height=10
        )

        tree_ventas.heading("id_venta", text="ID Venta")
        tree_ventas.heading("fecha", text="Fecha")
        tree_ventas.heading("vendedor", text="Vendedor")
        tree_ventas.heading("total", text="Total")

        tree_ventas.column("id_venta", width=80, anchor="center")
        tree_ventas.column("fecha", width=120, anchor="center")
        tree_ventas.column("vendedor", width=150, anchor="w")
        tree_ventas.column("total", width=100, anchor="center")

        scrollbar = ttk.Scrollbar(frame_tabla, orient=tk.VERTICAL, command=tree_ventas.yview)
        tree_ventas.configure(yscrollcommand=scrollbar.set)

        tree_ventas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        consulta = """
            SELECT v.id, v.fecha, u.usuario, v.total 
            FROM ventas v 
            JOIN usuarios u ON v.id_usuario = u.id 
            WHERE v.id_cliente = ? 
            ORDER BY v.fecha DESC
        """
        resultado = query(consulta, (cliente_id,))

        if resultado:
            for fila in resultado:
                tree_ventas.insert("", tk.END, values=(fila[0], fila[1], fila[2], f"${fila[3]:.2f}"))
        else:
            tk.Label(
                ventana_historial,
                text="Este cliente no tiene ventas registradas.",
                font=("Arial", 11, "italic"),
                fg="#666666",
                bg=COLOR_FONDO_INTERNO
            ).pack(pady=10)

        tk.Label(
            ventana_historial,
            text="Doble clic en una venta para ver el detalle",
            font=("Arial", 9, "italic"),
            fg="#888888",
            bg=COLOR_FONDO_INTERNO
        ).pack()

        def _on_doble_clic_venta(event):
            seleccion = tree_ventas.selection()
            if not seleccion:
                return
            item = tree_ventas.item(seleccion[0])
            venta_valores = item["values"]
            self._mostrar_detalle_venta(venta_valores[0], venta_valores[1], venta_valores[3])

        tree_ventas.bind("<Double-1>", _on_doble_clic_venta)

        btn_cerrar = tk.Button(
            ventana_historial,
            text="Cerrar",
            font=("Arial", 11, "bold"),
            bg=COLOR_VERDE_BOTON,
            fg=COLOR_NEGRO,
            activebackground=COLOR_VERDE_HOVER,
            activeforeground=COLOR_NEGRO,
            relief="flat",
            bd=0,
            cursor="hand2",
            width=15,
            height=2,
            command=ventana_historial.destroy
        )
        btn_cerrar.pack(pady=(0, 15))
        btn_cerrar.bind("<Enter>", lambda e: btn_cerrar.config(bg=COLOR_VERDE_HOVER))
        btn_cerrar.bind("<Leave>", lambda e: btn_cerrar.config(bg=COLOR_VERDE_BOTON))

    def _mostrar_detalle_venta(self, id_venta, fecha, total):
        ventana_detalle = tk.Toplevel(self.parent)
        ventana_detalle.title(f"Detalle de Venta #{id_venta}")
        ventana_detalle.configure(bg=COLOR_FONDO_INTERNO)
        ventana_detalle.geometry("550x400")
        ventana_detalle.transient(self.parent)
        ventana_detalle.grab_set()

        tk.Label(
            ventana_detalle,
            text=f"Detalle de Venta #{id_venta}",
            font=("Arial", 16, "bold"),
            fg=COLOR_VERDE_SIDEBAR,
            bg=COLOR_FONDO_INTERNO
        ).pack(pady=(15, 5))

        tk.Label(
            ventana_detalle,
            text=f"Fecha: {fecha}",
            font=("Arial", 11),
            fg="#555555",
            bg=COLOR_FONDO_INTERNO
        ).pack()

        frame_tabla = tk.Frame(ventana_detalle, bg=COLOR_FONDO_INTERNO)
        frame_tabla.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        columnas = ("producto", "cantidad", "precio_unitario", "subtotal")
        tree_detalle = ttk.Treeview(
            frame_tabla,
            columns=columnas,
            show="headings",
            height=8
        )

        tree_detalle.heading("producto", text="Producto")
        tree_detalle.heading("cantidad", text="Cantidad")
        tree_detalle.heading("precio_unitario", text="Precio Unitario")
        tree_detalle.heading("subtotal", text="Subtotal")

        tree_detalle.column("producto", width=180, anchor="w")
        tree_detalle.column("cantidad", width=80, anchor="center")
        tree_detalle.column("precio_unitario", width=100, anchor="center")
        tree_detalle.column("subtotal", width=100, anchor="center")

        scrollbar = ttk.Scrollbar(frame_tabla, orient=tk.VERTICAL, command=tree_detalle.yview)
        tree_detalle.configure(yscrollcommand=scrollbar.set)

        tree_detalle.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        consulta = """
            SELECT p.nombre, d.cantidad, d.precio_unitario 
            FROM detalle_ventas d 
            JOIN productos p ON d.id_producto = p.id 
            WHERE d.id_venta = ? 
            ORDER BY p.nombre
        """
        resultado = query(consulta, (id_venta,))
        total_calculado = 0.0

        if resultado:
            for fila in resultado:
                subtotal = fila[1] * fila[2]
                total_calculado += subtotal
                tree_detalle.insert("", tk.END, values=(
                    fila[0],
                    fila[1],
                    f"${fila[2]:.2f}",
                    f"${subtotal:.2f}"
                ))

        tk.Label(
            ventana_detalle,
            text=f"Total de la venta: ${total_calculado:.2f}",
            font=("Arial", 13, "bold"),
            fg=COLOR_VERDE_SIDEBAR,
            bg=COLOR_FONDO_INTERNO
        ).pack(pady=(5, 10))

        btn_cerrar = tk.Button(
            ventana_detalle,
            text="Cerrar",
            font=("Arial", 11, "bold"),
            bg=COLOR_VERDE_BOTON,
            fg=COLOR_NEGRO,
            activebackground=COLOR_VERDE_HOVER,
            activeforeground=COLOR_NEGRO,
            relief="flat",
            bd=0,
            cursor="hand2",
            width=15,
            height=2,
            command=ventana_detalle.destroy
        )
        btn_cerrar.pack(pady=(0, 15))
        btn_cerrar.bind("<Enter>", lambda e: btn_cerrar.config(bg=COLOR_VERDE_HOVER))
        btn_cerrar.bind("<Leave>", lambda e: btn_cerrar.config(bg=COLOR_VERDE_BOTON))

    def _resetear_panel_lateral(self):
        self.lbl_info_id.config(text="ID: —")
        self.lbl_info_nombre.config(text="Nombre: —")
        self.lbl_info_apellido.config(text="Apellido: —")
        self.lbl_info_direccion.config(text="Dirección: —")
        self.lbl_info_telefono.config(text="Teléfono: —")
        self.lbl_info_email.config(text="Email: —")
        self.lbl_nota.config(text="Seleccione un cliente de la tabla\npara ver sus detalles.")