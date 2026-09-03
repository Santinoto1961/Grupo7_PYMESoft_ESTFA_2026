#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================
proveedores.py - Módulo de Gestión de Proveedores
============================================================
ABM completo de proveedores con visualización de productos
asociados mediante ventana secundaria Toplevel.

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


class VistaProveedores:
    """
    Clase que construye y gestiona la pantalla de proveedores
    dentro del área de contenido de la ventana principal.
    """

    def __init__(self, parent_frame):
        self.parent = parent_frame
        self.proveedor_seleccionado = None

        for widget in self.parent.winfo_children():
            widget.destroy()

        self._crear_titulo()
        self._crear_panel_principal()
        self._crear_botones_accion()
        self._cargar_proveedores()

    # ============================================================
    # SECCIÓN 1: TÍTULO PRINCIPAL
    # ============================================================

    def _crear_titulo(self):
        self.lbl_titulo = tk.Label(
            self.parent,
            text="PROVEEDORES:",
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
            text="Lista de proveedores:",
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

        self._crear_tabla_proveedores()
        self._crear_panel_lateral()

    def _crear_tabla_proveedores(self):
        self.frame_tabla = tk.Frame(
            self.frame_interno,
            bg=COLOR_FONDO_INTERNO
        )
        self.frame_tabla.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 2))

        columnas = ("id", "nombre", "telefono", "direccion")
        self.tree = ttk.Treeview(
            self.frame_tabla,
            columns=columnas,
            show="headings",
            height=12
        )

        self.tree.heading("id", text="ID")
        self.tree.heading("nombre", text="Nombre")
        self.tree.heading("telefono", text="Teléfono")
        self.tree.heading("direccion", text="Dirección")

        self.tree.column("id", width=50, anchor="center")
        self.tree.column("nombre", width=200, anchor="w")
        self.tree.column("telefono", width=120, anchor="w")
        self.tree.column("direccion", width=250, anchor="w")

        scrollbar = ttk.Scrollbar(
            self.frame_tabla,
            orient=tk.VERTICAL,
            command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)

        self.tree.bind("<<TreeviewSelect>>", self._on_seleccionar_proveedor)

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
            text="Información del proveedor:",
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
        self.lbl_info_id.pack(fill=tk.X, pady=5)

        self.lbl_info_nombre = tk.Label(
            self.frame_lateral,
            text="Nombre: —",
            font=("Arial", 11),
            fg=COLOR_NEGRO,
            bg=COLOR_FONDO_INTERNO,
            anchor="w"
        )
        self.lbl_info_nombre.pack(fill=tk.X, pady=5)

        self.lbl_info_telefono = tk.Label(
            self.frame_lateral,
            text="Teléfono: —",
            font=("Arial", 11),
            fg=COLOR_NEGRO,
            bg=COLOR_FONDO_INTERNO,
            anchor="w"
        )
        self.lbl_info_telefono.pack(fill=tk.X, pady=5)

        self.lbl_info_direccion = tk.Label(
            self.frame_lateral,
            text="Dirección: —",
            font=("Arial", 11),
            fg=COLOR_NEGRO,
            bg=COLOR_FONDO_INTERNO,
            anchor="w"
        )
        self.lbl_info_direccion.pack(fill=tk.X, pady=5)

        tk.Frame(self.frame_lateral, bg="#888888", height=1).pack(fill=tk.X, pady=15)

        self.lbl_nota = tk.Label(
            self.frame_lateral,
            text="Seleccione un proveedor de la tabla\npara ver sus detalles.",
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
            text="Editar proveedor",
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
            command=self._editar_proveedor
        )
        self.btn_editar.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_agregar = tk.Button(
            self.frame_fila_botones,
            text="Agregar proveedor",
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
            command=self._mostrar_formulario_agregar
        )
        self.btn_agregar.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_eliminar = tk.Button(
            self.frame_fila_botones,
            text="Eliminar proveedor",
            font=("Arial", 11, "bold"),
            bg=COLOR_ROJO_CERRAR,
            fg=COLOR_BLANCO,
            activebackground=COLOR_ROJO_HOVER,
            activeforeground=COLOR_BLANCO,
            relief="flat",
            bd=0,
            cursor="hand2",
            width=18,
            height=2,
            command=self._eliminar_proveedor
        )
        self.btn_eliminar.pack(side=tk.LEFT, padx=(0, 10))

        tk.Frame(self.frame_fila_botones, bg=COLOR_GRIS_FONDO).pack(side=tk.LEFT, expand=True)

        self.btn_ver_productos = tk.Button(
            self.frame_fila_botones,
            text="Ver Productos Provistos",
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
            command=self._ver_productos_provistos
        )
        self.btn_ver_productos.pack(side=tk.LEFT)

        self.btn_editar.bind("<Enter>", lambda e: self.btn_editar.config(bg=COLOR_VERDE_HOVER))
        self.btn_editar.bind("<Leave>", lambda e: self.btn_editar.config(bg=COLOR_VERDE_BOTON))
        self.btn_agregar.bind("<Enter>", lambda e: self.btn_agregar.config(bg=COLOR_VERDE_HOVER))
        self.btn_agregar.bind("<Leave>", lambda e: self.btn_agregar.config(bg=COLOR_VERDE_BOTON))
        self.btn_eliminar.bind("<Enter>", lambda e: self.btn_eliminar.config(bg=COLOR_ROJO_HOVER))
        self.btn_eliminar.bind("<Leave>", lambda e: self.btn_eliminar.config(bg=COLOR_ROJO_CERRAR))
        self.btn_ver_productos.bind("<Enter>", lambda e: self.btn_ver_productos.config(bg="#1a5c1a"))
        self.btn_ver_productos.bind("<Leave>", lambda e: self.btn_ver_productos.config(bg=COLOR_VERDE_BOTON_ACCION))

    # ============================================================
    # SECCIÓN 4: FORMULARIOS (AGREGAR / EDITAR)
    # ============================================================

    def _mostrar_formulario_agregar(self):
        self.ventana_form = tk.Toplevel(self.parent)
        self.ventana_form.title("Agregar Nuevo Proveedor")
        self.ventana_form.configure(bg=COLOR_FONDO_INTERNO)
        self.ventana_form.resizable(False, False)
        self.ventana_form.grab_set()
        self.ventana_form.geometry("400x350")
        self.ventana_form.transient(self.parent)

        tk.Label(
            self.ventana_form,
            text="Nuevo Proveedor",
            font=("Arial", 18, "bold"),
            fg=COLOR_VERDE_SIDEBAR,
            bg=COLOR_FONDO_INTERNO
        ).pack(pady=(20, 20))

        frame_form = tk.Frame(self.ventana_form, bg=COLOR_FONDO_INTERNO, padx=30)
        frame_form.pack(fill=tk.X)

        tk.Label(frame_form, text="Nombre:", font=("Arial", 11), fg=COLOR_NEGRO, bg=COLOR_FONDO_INTERNO, anchor="w").pack(fill=tk.X, pady=(10, 2))
        self.entry_nombre = tk.Entry(frame_form, font=("Arial", 12), bg=COLOR_BLANCO, fg=COLOR_NEGRO, relief="flat", bd=1)
        self.entry_nombre.pack(fill=tk.X, ipady=6)

        tk.Label(frame_form, text="Teléfono:", font=("Arial", 11), fg=COLOR_NEGRO, bg=COLOR_FONDO_INTERNO, anchor="w").pack(fill=tk.X, pady=(10, 2))
        self.entry_telefono = tk.Entry(frame_form, font=("Arial", 12), bg=COLOR_BLANCO, fg=COLOR_NEGRO, relief="flat", bd=1)
        self.entry_telefono.pack(fill=tk.X, ipady=6)

        tk.Label(frame_form, text="Dirección:", font=("Arial", 11), fg=COLOR_NEGRO, bg=COLOR_FONDO_INTERNO, anchor="w").pack(fill=tk.X, pady=(10, 2))
        self.entry_direccion = tk.Entry(frame_form, font=("Arial", 12), bg=COLOR_BLANCO, fg=COLOR_NEGRO, relief="flat", bd=1)
        self.entry_direccion.pack(fill=tk.X, ipady=6)

        tk.Frame(self.ventana_form, bg=COLOR_FONDO_INTERNO, height=20).pack()

        btn_confirmar = tk.Button(
            self.ventana_form,
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
        btn_confirmar.pack(pady=(0, 20))
        btn_confirmar.bind("<Enter>", lambda e: btn_confirmar.config(bg="#1a5c1a"))
        btn_confirmar.bind("<Leave>", lambda e: btn_confirmar.config(bg=COLOR_VERDE_BOTON_ACCION))

    def _confirmar_agregar(self):
        nombre = self.entry_nombre.get().strip()
        telefono = self.entry_telefono.get().strip()
        direccion = self.entry_direccion.get().strip()

        if not nombre:
            messagebox.showwarning("Campo obligatorio", "El nombre del proveedor es obligatorio.", parent=self.ventana_form)
            return

        consulta = "INSERT INTO proveedores (nombre, telefono, direccion) VALUES (?, ?, ?)"
        try:
            query(consulta, (nombre, telefono, direccion))
            messagebox.showinfo("Éxito", f"Proveedor '{nombre}' creado correctamente.", parent=self.ventana_form)
            self.ventana_form.destroy()
            self._cargar_proveedores()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear el proveedor.\nError: {str(e)}", parent=self.ventana_form)

    def _editar_proveedor(self):
        if self.proveedor_seleccionado is None:
            messagebox.showwarning("Sin selección", "Por favor, seleccione un proveedor de la tabla para editar.")
            return

        seleccion = self.tree.selection()
        item = self.tree.item(seleccion[0])
        valores = item["values"]

        self.ventana_edit = tk.Toplevel(self.parent)
        self.ventana_edit.title("Editar Proveedor")
        self.ventana_edit.configure(bg=COLOR_FONDO_INTERNO)
        self.ventana_edit.resizable(False, False)
        self.ventana_edit.grab_set()
        self.ventana_edit.geometry("400x350")
        self.ventana_edit.transient(self.parent)

        tk.Label(
            self.ventana_edit,
            text="Editar Proveedor",
            font=("Arial", 18, "bold"),
            fg=COLOR_VERDE_SIDEBAR,
            bg=COLOR_FONDO_INTERNO
        ).pack(pady=(20, 20))

        frame_form = tk.Frame(self.ventana_edit, bg=COLOR_FONDO_INTERNO, padx=30)
        frame_form.pack(fill=tk.X)

        tk.Label(frame_form, text="Nombre:", font=("Arial", 11), fg=COLOR_NEGRO, bg=COLOR_FONDO_INTERNO, anchor="w").pack(fill=tk.X, pady=(10, 2))
        self.entry_edit_nombre = tk.Entry(frame_form, font=("Arial", 12), bg=COLOR_BLANCO, fg=COLOR_NEGRO, relief="flat", bd=1)
        self.entry_edit_nombre.insert(0, valores[1])
        self.entry_edit_nombre.pack(fill=tk.X, ipady=6)

        tk.Label(frame_form, text="Teléfono:", font=("Arial", 11), fg=COLOR_NEGRO, bg=COLOR_FONDO_INTERNO, anchor="w").pack(fill=tk.X, pady=(10, 2))
        self.entry_edit_telefono = tk.Entry(frame_form, font=("Arial", 12), bg=COLOR_BLANCO, fg=COLOR_NEGRO, relief="flat", bd=1)
        self.entry_edit_telefono.insert(0, valores[2] if valores[2] else "")
        self.entry_edit_telefono.pack(fill=tk.X, ipady=6)

        tk.Label(frame_form, text="Dirección:", font=("Arial", 11), fg=COLOR_NEGRO, bg=COLOR_FONDO_INTERNO, anchor="w").pack(fill=tk.X, pady=(10, 2))
        self.entry_edit_direccion = tk.Entry(frame_form, font=("Arial", 12), bg=COLOR_BLANCO, fg=COLOR_NEGRO, relief="flat", bd=1)
        self.entry_edit_direccion.insert(0, valores[3] if valores[3] else "")
        self.entry_edit_direccion.pack(fill=tk.X, ipady=6)

        tk.Frame(self.ventana_edit, bg=COLOR_FONDO_INTERNO, height=20).pack()

        btn_guardar = tk.Button(
            self.ventana_edit,
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
        btn_guardar.pack(pady=(0, 20))
        btn_guardar.bind("<Enter>", lambda e: btn_guardar.config(bg="#1a5c1a"))
        btn_guardar.bind("<Leave>", lambda e: btn_guardar.config(bg=COLOR_VERDE_BOTON_ACCION))

    def _confirmar_editar(self, proveedor_id):
        nombre = self.entry_edit_nombre.get().strip()
        telefono = self.entry_edit_telefono.get().strip()
        direccion = self.entry_edit_direccion.get().strip()

        if not nombre:
            messagebox.showwarning("Campo obligatorio", "El nombre del proveedor es obligatorio.", parent=self.ventana_edit)
            return

        consulta = "UPDATE proveedores SET nombre = ?, telefono = ?, direccion = ? WHERE id = ?"
        try:
            query(consulta, (nombre, telefono, direccion, proveedor_id))
            messagebox.showinfo("Éxito", f"Proveedor '{nombre}' actualizado correctamente.", parent=self.ventana_edit)
            self.ventana_edit.destroy()
            self._cargar_proveedores()
            self._resetear_panel_lateral()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo actualizar el proveedor.\nError: {str(e)}", parent=self.ventana_edit)

    # ============================================================
    # SECCIÓN 5: OPERACIONES CRUD Y PRODUCTOS
    # ============================================================

    def _cargar_proveedores(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        consulta = "SELECT id, nombre, telefono, direccion FROM proveedores ORDER BY id"
        resultado = query(consulta)

        if resultado:
            for fila in resultado:
                telefono = fila[2] if fila[2] else "—"
                direccion = fila[3] if fila[3] else "—"
                self.tree.insert("", tk.END, values=(fila[0], fila[1], telefono, direccion))

    def _on_seleccionar_proveedor(self, event):
        seleccion = self.tree.selection()
        if not seleccion:
            return

        item = self.tree.item(seleccion[0])
        valores = item["values"]
        self.proveedor_seleccionado = valores[0]

        self.lbl_info_id.config(text=f"ID: {valores[0]}")
        self.lbl_info_nombre.config(text=f"Nombre: {valores[1]}")
        self.lbl_info_telefono.config(text=f"Teléfono: {valores[2]}")
        self.lbl_info_direccion.config(text=f"Dirección: {valores[3]}")
        self.lbl_nota.config(text="Proveedor seleccionado.\nUse los botones de abajo para editar, eliminar o ver productos.")

    def _eliminar_proveedor(self):
        if self.proveedor_seleccionado is None:
            messagebox.showwarning("Sin selección", "Por favor, seleccione un proveedor de la tabla para eliminar.")
            return

        seleccion = self.tree.selection()
        item = self.tree.item(seleccion[0])
        valores = item["values"]
        proveedor_id = valores[0]
        proveedor_nombre = valores[1]

        respuesta = messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Está seguro de que desea eliminar al proveedor '{proveedor_nombre}'?\n\nEsta acción no se puede deshacer."
        )

        if respuesta:
            consulta = "DELETE FROM proveedores WHERE id = ?"
            try:
                query(consulta, (proveedor_id,))
                messagebox.showinfo("Éxito", f"Proveedor '{proveedor_nombre}' eliminado correctamente.")
                self.proveedor_seleccionado = None
                self._resetear_panel_lateral()
                self._cargar_proveedores()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo eliminar el proveedor.\nError: {str(e)}")

    def _ver_productos_provistos(self):
        if self.proveedor_seleccionado is None:
            messagebox.showwarning("Sin selección", "Por favor, seleccione un proveedor para ver sus productos.")
            return

        seleccion = self.tree.selection()
        item = self.tree.item(seleccion[0])
        valores = item["values"]
        proveedor_id = valores[0]
        proveedor_nombre = valores[1]

        ventana_productos = tk.Toplevel(self.parent)
        ventana_productos.title(f"Productos de {proveedor_nombre}")
        ventana_productos.configure(bg=COLOR_FONDO_INTERNO)
        ventana_productos.geometry("650x400")
        ventana_productos.transient(self.parent)
        ventana_productos.grab_set()

        tk.Label(
            ventana_productos,
            text=f"Productos provistos por: {proveedor_nombre}",
            font=("Arial", 16, "bold"),
            fg=COLOR_VERDE_SIDEBAR,
            bg=COLOR_FONDO_INTERNO
        ).pack(pady=(15, 10))

        frame_tabla = tk.Frame(ventana_productos, bg=COLOR_FONDO_INTERNO)
        frame_tabla.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        columnas = ("id", "nombre", "descripcion", "precio", "stock", "categoria")
        tree_prod = ttk.Treeview(
            frame_tabla,
            columns=columnas,
            show="headings",
            height=10
        )

        tree_prod.heading("id", text="ID")
        tree_prod.heading("nombre", text="Nombre")
        tree_prod.heading("descripcion", text="Descripción")
        tree_prod.heading("precio", text="Precio")
        tree_prod.heading("stock", text="Stock")
        tree_prod.heading("categoria", text="Categoría")

        tree_prod.column("id", width=40, anchor="center")
        tree_prod.column("nombre", width=120, anchor="w")
        tree_prod.column("descripcion", width=180, anchor="w")
        tree_prod.column("precio", width=80, anchor="center")
        tree_prod.column("stock", width=60, anchor="center")
        tree_prod.column("categoria", width=100, anchor="w")

        scrollbar = ttk.Scrollbar(frame_tabla, orient=tk.VERTICAL, command=tree_prod.yview)
        tree_prod.configure(yscrollcommand=scrollbar.set)

        tree_prod.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        consulta = "SELECT id, nombre, descripcion, precio, stock, categoria FROM productos WHERE id_proveedor = ? ORDER BY id"
        resultado = query(consulta, (proveedor_id,))

        if resultado:
            for fila in resultado:
                descripcion = fila[2] if fila[2] else "—"
                categoria = fila[5] if fila[5] else "—"
                tree_prod.insert("", tk.END, values=(fila[0], fila[1], descripcion, f"${fila[3]:.2f}", fila[4], categoria))
        else:
            tk.Label(
                ventana_productos,
                text="Este proveedor no tiene productos asociados.",
                font=("Arial", 11, "italic"),
                fg="#666666",
                bg=COLOR_FONDO_INTERNO
            ).pack(pady=10)

        btn_cerrar = tk.Button(
            ventana_productos,
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
            command=ventana_productos.destroy
        )
        btn_cerrar.pack(pady=(0, 15))
        btn_cerrar.bind("<Enter>", lambda e: btn_cerrar.config(bg=COLOR_VERDE_HOVER))
        btn_cerrar.bind("<Leave>", lambda e: btn_cerrar.config(bg=COLOR_VERDE_BOTON))

    def _resetear_panel_lateral(self):
        self.lbl_info_id.config(text="ID: —")
        self.lbl_info_nombre.config(text="Nombre: —")
        self.lbl_info_telefono.config(text="Teléfono: —")
        self.lbl_info_direccion.config(text="Dirección: —")
        self.lbl_nota.config(text="Seleccione un proveedor de la tabla\npara ver sus detalles.")