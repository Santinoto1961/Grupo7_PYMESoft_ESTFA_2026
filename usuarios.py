#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================
usuarios.py - Módulo de Gestión de Usuarios (Admin)
============================================================
Pantalla de administración de usuarios accesible solo para
administradores. Permite:
  - Visualizar la lista de usuarios en una tabla (Treeview)
  - Agregar nuevos usuarios mediante un formulario
  - Editar usuarios existentes (usuario, nombre_completo, contraseña, rol)
  - Eliminar usuarios seleccionados de la base de datos

Todas las operaciones de BD usan la función query() del
módulo database.py.

Autor: Estudiante
Fecha: 2026-08-30
============================================================
"""

import tkinter as tk
from tkinter import ttk, messagebox

from database import query
from session import session


# ============================================================
# PALETA DE COLORES (idéntica a main_window.py)
# ============================================================
COLOR_VERDE_SIDEBAR = "#1B4D1B"
COLOR_VERDE_BOTON   = "#a6a6a6"
COLOR_VERDE_HOVER   = "#FFFFFF"
COLOR_GRIS_FONDO    = "#A8A8A8"
COLOR_BLANCO        = "#FFFFFF"
COLOR_NEGRO         = "#000000"
COLOR_ROJO_CERRAR   = "#8B0000"
COLOR_ROJO_HOVER    = "#A52A2A"
COLOR_VERDE_BOTON_ACCION = "#0D2E0D"
COLOR_FONDO_INTERNO = "#f5f5f5"


class VistaUsuarios:
    """
    Clase que construye y gestiona la pantalla de usuarios
    dentro del área de contenido de la ventana principal.
    """

    def __init__(self, parent_frame):
        self.parent = parent_frame
        self.usuario_seleccionado = None

        for widget in self.parent.winfo_children():
            widget.destroy()

        self._crear_titulo()
        self._crear_panel_principal()
        self._crear_botones_accion()
        self._cargar_usuarios()

    # ============================================================
    # SECCIÓN 1: TÍTULO PRINCIPAL
    # ============================================================

    def _crear_titulo(self):
        self.lbl_titulo = tk.Label(
            self.parent,
            text="USUARIOS:",
            font=("Arial", 32, "bold"),
            fg=COLOR_NEGRO,
            bg=COLOR_GRIS_FONDO
        )
        self.lbl_titulo.pack(anchor="w", padx=40, pady=(30, 15))

    # ============================================================
    # SECCIÓN 2: PANEL PRINCIPAL (verde oscuro)
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
            text="Lista de usuarios:",
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

        self._crear_tabla_usuarios()
        self._crear_panel_lateral()

    def _crear_tabla_usuarios(self):
        self.frame_tabla = tk.Frame(
            self.frame_interno,
            bg=COLOR_FONDO_INTERNO
        )
        self.frame_tabla.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 2))

        columnas = ("id", "usuario", "nombre_completo", "rol")
        self.tree = ttk.Treeview(
            self.frame_tabla,
            columns=columnas,
            show="headings",
            height=12
        )

        self.tree.heading("id", text="ID")
        self.tree.heading("usuario", text="Usuario")
        self.tree.heading("nombre_completo", text="Nombre Completo")
        self.tree.heading("rol", text="Rol")

        self.tree.column("id", width=50, anchor="center")
        self.tree.column("usuario", width=120, anchor="w")
        self.tree.column("nombre_completo", width=200, anchor="w")
        self.tree.column("rol", width=100, anchor="center")

        scrollbar = ttk.Scrollbar(
            self.frame_tabla,
            orient=tk.VERTICAL,
            command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)

        self.tree.bind("<<TreeviewSelect>>", self._on_seleccionar_usuario)

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
            text="Información del usuario:",
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

        self.lbl_info_usuario = tk.Label(
            self.frame_lateral,
            text="Usuario: —",
            font=("Arial", 11),
            fg=COLOR_NEGRO,
            bg=COLOR_FONDO_INTERNO,
            anchor="w"
        )
        self.lbl_info_usuario.pack(fill=tk.X, pady=5)

        self.lbl_info_nombre = tk.Label(
            self.frame_lateral,
            text="Nombre: —",
            font=("Arial", 11),
            fg=COLOR_NEGRO,
            bg=COLOR_FONDO_INTERNO,
            anchor="w"
        )
        self.lbl_info_nombre.pack(fill=tk.X, pady=5)

        self.lbl_info_rol = tk.Label(
            self.frame_lateral,
            text="Rol: —",
            font=("Arial", 11),
            fg=COLOR_NEGRO,
            bg=COLOR_FONDO_INTERNO,
            anchor="w"
        )
        self.lbl_info_rol.pack(fill=tk.X, pady=5)

        tk.Frame(self.frame_lateral, bg="#888888", height=1).pack(fill=tk.X, pady=15)

        self.lbl_nota = tk.Label(
            self.frame_lateral,
            text="Seleccione un usuario de la tabla\npara ver sus detalles.",
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
            text="Editar usuario",
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
            command=self._editar_usuario
        )
        self.btn_editar.pack(side=tk.LEFT, padx=(0, 10))

        tk.Frame(self.frame_fila_botones, bg=COLOR_GRIS_FONDO).pack(side=tk.LEFT, expand=True)

        self.btn_agregar = tk.Button(
            self.frame_fila_botones,
            text="Agregar usuario",
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
            text="Eliminar usuario",
            font=("Arial", 11, "bold"),
            bg=COLOR_VERDE_BOTON_ACCION,
            fg=COLOR_BLANCO,
            activebackground="#1a5c1a",
            activeforeground=COLOR_BLANCO,
            relief="flat",
            bd=0,
            cursor="hand2",
            width=18,
            height=2,
            command=self._eliminar_usuario
        )
        self.btn_eliminar.pack(side=tk.LEFT)

        self.btn_editar.bind("<Enter>", lambda e: self.btn_editar.config(bg=COLOR_VERDE_HOVER))
        self.btn_editar.bind("<Leave>", lambda e: self.btn_editar.config(bg=COLOR_VERDE_BOTON))
        self.btn_agregar.bind("<Enter>", lambda e: self.btn_agregar.config(bg=COLOR_VERDE_HOVER))
        self.btn_agregar.bind("<Leave>", lambda e: self.btn_agregar.config(bg=COLOR_VERDE_BOTON))
        self.btn_eliminar.bind("<Enter>", lambda e: self.btn_eliminar.config(bg="#1a5c1a"))
        self.btn_eliminar.bind("<Leave>", lambda e: self.btn_eliminar.config(bg=COLOR_VERDE_BOTON_ACCION))

    # ============================================================
    # SECCIÓN 4: FORMULARIO AGREGAR USUARIO
    # ============================================================

    def _mostrar_formulario_agregar(self):
        self.ventana_agregar = tk.Toplevel(self.parent)
        self.ventana_agregar.title("Agregar Nuevo Usuario")
        self.ventana_agregar.configure(bg=COLOR_FONDO_INTERNO)
        self.ventana_agregar.resizable(False, False)
        self.ventana_agregar.grab_set()
        self.ventana_agregar.geometry("400x400")
        self.ventana_agregar.transient(self.parent)

        tk.Label(
            self.ventana_agregar,
            text="Nuevo Usuario",
            font=("Arial", 18, "bold"),
            fg=COLOR_VERDE_SIDEBAR,
            bg=COLOR_FONDO_INTERNO
        ).pack(pady=(20, 20))

        frame_form = tk.Frame(self.ventana_agregar, bg=COLOR_FONDO_INTERNO, padx=30)
        frame_form.pack(fill=tk.X)

        tk.Label(frame_form, text="Usuario:", font=("Arial", 11), fg=COLOR_NEGRO, bg=COLOR_FONDO_INTERNO, anchor="w").pack(fill=tk.X, pady=(10, 2))
        self.entry_nuevo_usuario = tk.Entry(frame_form, font=("Arial", 12), bg=COLOR_BLANCO, fg=COLOR_NEGRO, relief="flat", bd=1)
        self.entry_nuevo_usuario.pack(fill=tk.X, ipady=6)

        tk.Label(frame_form, text="Nombre Completo:", font=("Arial", 11), fg=COLOR_NEGRO, bg=COLOR_FONDO_INTERNO, anchor="w").pack(fill=tk.X, pady=(10, 2))
        self.entry_nuevo_nombre = tk.Entry(frame_form, font=("Arial", 12), bg=COLOR_BLANCO, fg=COLOR_NEGRO, relief="flat", bd=1)
        self.entry_nuevo_nombre.pack(fill=tk.X, ipady=6)

        tk.Label(frame_form, text="Contraseña:", font=("Arial", 11), fg=COLOR_NEGRO, bg=COLOR_FONDO_INTERNO, anchor="w").pack(fill=tk.X, pady=(10, 2))
        self.entry_nueva_contrasena = tk.Entry(frame_form, font=("Arial", 12), bg=COLOR_BLANCO, fg=COLOR_NEGRO, relief="flat", bd=1, show="*")
        self.entry_nueva_contrasena.pack(fill=tk.X, ipady=6)

        tk.Label(frame_form, text="Rol:", font=("Arial", 11), fg=COLOR_NEGRO, bg=COLOR_FONDO_INTERNO, anchor="w").pack(fill=tk.X, pady=(10, 2))
        self.combo_rol = ttk.Combobox(
            frame_form,
            values=["admin", "empleado"],
            font=("Arial", 12),
            state="readonly",
            height=2
        )
        self.combo_rol.set("empleado")
        self.combo_rol.pack(fill=tk.X, ipady=4)

        tk.Frame(self.ventana_agregar, bg=COLOR_FONDO_INTERNO, height=20).pack()

        self.btn_confirmar = tk.Button(
            self.ventana_agregar,
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
        self.btn_confirmar.pack(pady=(0, 20))
        self.btn_confirmar.bind("<Enter>", lambda e: self.btn_confirmar.config(bg="#1a5c1a"))
        self.btn_confirmar.bind("<Leave>", lambda e: self.btn_confirmar.config(bg=COLOR_VERDE_BOTON_ACCION))

    def _confirmar_agregar(self):
        usuario = self.entry_nuevo_usuario.get().strip()
        nombre_completo = self.entry_nuevo_nombre.get().strip()
        contrasena = self.entry_nueva_contrasena.get().strip()
        rol = self.combo_rol.get()

        if not usuario or not contrasena:
            messagebox.showwarning("Campos incompletos", "El usuario y la contraseña son obligatorios.", parent=self.ventana_agregar)
            return

        if len(contrasena) < 4:
            messagebox.showwarning("Contraseña débil", "La contraseña debe tener al menos 4 caracteres.", parent=self.ventana_agregar)
            return

        consulta_existe = "SELECT id FROM usuarios WHERE usuario = ?"
        existe = query(consulta_existe, (usuario,))

        if existe and len(existe) > 0:
            messagebox.showerror("Usuario duplicado", f"El usuario '{usuario}' ya existe en el sistema.", parent=self.ventana_agregar)
            return

        consulta_insert = "INSERT INTO usuarios (usuario, contraseña, nombre_completo, rol) VALUES (?, ?, ?, ?)"
        try:
            query(consulta_insert, (usuario, contrasena, nombre_completo, rol))
            messagebox.showinfo("Éxito", f"Usuario '{usuario}' creado correctamente.", parent=self.ventana_agregar)
            self.ventana_agregar.destroy()
            self._cargar_usuarios()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear el usuario.\nError: {str(e)}", parent=self.ventana_agregar)

    # ============================================================
    # SECCIÓN 5: FORMULARIO EDITAR USUARIO (COMPLETAMENTE OPERATIVO)
    # ============================================================

    def _editar_usuario(self):
        if self.usuario_seleccionado is None:
            messagebox.showwarning("Sin selección", "Por favor, seleccione un usuario de la tabla para editar.")
            return

        seleccion = self.tree.selection()
        item = self.tree.item(seleccion[0])
        valores = item["values"]
        usuario_id = valores[0]
        usuario_nombre = valores[1]
        usuario_nombre_completo = valores[2] if valores[2] != "—" else ""
        usuario_rol = valores[3]

        self.ventana_editar = tk.Toplevel(self.parent)
        self.ventana_editar.title("Editar Usuario")
        self.ventana_editar.configure(bg=COLOR_FONDO_INTERNO)
        self.ventana_editar.resizable(False, False)
        self.ventana_editar.grab_set()
        self.ventana_editar.geometry("400x450")
        self.ventana_editar.transient(self.parent)

        tk.Label(
            self.ventana_editar,
            text="Editar Usuario",
            font=("Arial", 18, "bold"),
            fg=COLOR_VERDE_SIDEBAR,
            bg=COLOR_FONDO_INTERNO
        ).pack(pady=(20, 20))

        frame_form = tk.Frame(self.ventana_editar, bg=COLOR_FONDO_INTERNO, padx=30)
        frame_form.pack(fill=tk.X)

        tk.Label(frame_form, text="Usuario:", font=("Arial", 11), fg=COLOR_NEGRO, bg=COLOR_FONDO_INTERNO, anchor="w").pack(fill=tk.X, pady=(10, 2))
        self.entry_edit_usuario = tk.Entry(frame_form, font=("Arial", 12), bg=COLOR_BLANCO, fg=COLOR_NEGRO, relief="flat", bd=1)
        self.entry_edit_usuario.insert(0, usuario_nombre)
        self.entry_edit_usuario.pack(fill=tk.X, ipady=6)

        tk.Label(frame_form, text="Nombre Completo:", font=("Arial", 11), fg=COLOR_NEGRO, bg=COLOR_FONDO_INTERNO, anchor="w").pack(fill=tk.X, pady=(10, 2))
        self.entry_edit_nombre = tk.Entry(frame_form, font=("Arial", 12), bg=COLOR_BLANCO, fg=COLOR_NEGRO, relief="flat", bd=1)
        self.entry_edit_nombre.insert(0, usuario_nombre_completo)
        self.entry_edit_nombre.pack(fill=tk.X, ipady=6)

        tk.Label(frame_form, text="Nueva Contraseña:", font=("Arial", 11), fg=COLOR_NEGRO, bg=COLOR_FONDO_INTERNO, anchor="w").pack(fill=tk.X, pady=(10, 2))
        self.entry_edit_contrasena = tk.Entry(frame_form, font=("Arial", 12), bg=COLOR_BLANCO, fg=COLOR_NEGRO, relief="flat", bd=1, show="*")
        self.entry_edit_contrasena.pack(fill=tk.X, ipady=6)

        tk.Label(
            frame_form,
            text="(Dejar en blanco para mantener la contraseña actual)",
            font=("Arial", 9, "italic"),
            fg="#666666",
            bg=COLOR_FONDO_INTERNO,
            anchor="w"
        ).pack(fill=tk.X, pady=(0, 5))

        tk.Label(frame_form, text="Rol:", font=("Arial", 11), fg=COLOR_NEGRO, bg=COLOR_FONDO_INTERNO, anchor="w").pack(fill=tk.X, pady=(10, 2))
        self.combo_edit_rol = ttk.Combobox(
            frame_form,
            values=["admin", "empleado"],
            font=("Arial", 12),
            state="readonly",
            height=2
        )
        self.combo_edit_rol.set(usuario_rol)
        self.combo_edit_rol.pack(fill=tk.X, ipady=4)

        tk.Frame(self.ventana_editar, bg=COLOR_FONDO_INTERNO, height=20).pack()

        btn_guardar = tk.Button(
            self.ventana_editar,
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
            command=lambda: self._confirmar_editar(usuario_id, usuario_nombre)
        )
        btn_guardar.pack(pady=(0, 20))
        btn_guardar.bind("<Enter>", lambda e: btn_guardar.config(bg="#1a5c1a"))
        btn_guardar.bind("<Leave>", lambda e: btn_guardar.config(bg=COLOR_VERDE_BOTON_ACCION))

    def _confirmar_editar(self, usuario_id, usuario_original):
        usuario = self.entry_edit_usuario.get().strip()
        nombre_completo = self.entry_edit_nombre.get().strip()
        contrasena = self.entry_edit_contrasena.get().strip()
        rol = self.combo_edit_rol.get()

        if not usuario:
            messagebox.showwarning("Campo obligatorio", "El nombre de usuario es obligatorio.", parent=self.ventana_editar)
            return

        if usuario != usuario_original:
            consulta_existe = "SELECT id FROM usuarios WHERE usuario = ? AND id != ?"
            existe = query(consulta_existe, (usuario, usuario_id))
            if existe and len(existe) > 0:
                messagebox.showerror("Usuario duplicado", f"El usuario '{usuario}' ya existe en el sistema.", parent=self.ventana_editar)
                return

        if contrasena and len(contrasena) < 4:
            messagebox.showwarning("Contraseña débil", "La nueva contraseña debe tener al menos 4 caracteres.", parent=self.ventana_editar)
            return

        if contrasena:
            consulta = "UPDATE usuarios SET usuario = ?, contraseña = ?, nombre_completo = ?, rol = ? WHERE id = ?"
            parametros = (usuario, contrasena, nombre_completo, rol, usuario_id)
        else:
            consulta = "UPDATE usuarios SET usuario = ?, nombre_completo = ?, rol = ? WHERE id = ?"
            parametros = (usuario, nombre_completo, rol, usuario_id)

        try:
            query(consulta, parametros)

            if session.usuario == usuario_original:
                session._usuario = usuario
                session._nombre = nombre_completo
                session._rol = rol.lower().strip()

            messagebox.showinfo("Éxito", f"Usuario '{usuario}' actualizado correctamente.", parent=self.ventana_editar)
            self.ventana_editar.destroy()
            self._cargar_usuarios()
            self._resetear_panel_lateral()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo actualizar el usuario.\nError: {str(e)}", parent=self.ventana_editar)

    # ============================================================
    # SECCIÓN 6: OPERACIONES CRUD
    # ============================================================

    def _cargar_usuarios(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        consulta = "SELECT id, usuario, nombre_completo, rol FROM usuarios ORDER BY id"
        resultado = query(consulta)

        if resultado:
            for fila in resultado:
                nombre = fila[2] if fila[2] else "—"
                self.tree.insert("", tk.END, values=(fila[0], fila[1], nombre, fila[3]))

    def _on_seleccionar_usuario(self, event):
        seleccion = self.tree.selection()
        if not seleccion:
            return

        item = self.tree.item(seleccion[0])
        valores = item["values"]
        self.usuario_seleccionado = valores[0]

        self.lbl_info_id.config(text=f"ID: {valores[0]}")
        self.lbl_info_usuario.config(text=f"Usuario: {valores[1]}")
        self.lbl_info_nombre.config(text=f"Nombre: {valores[2]}")
        self.lbl_info_rol.config(text=f"Rol: {valores[3]}")
        self.lbl_nota.config(text="Usuario seleccionado.\nUse los botones de abajo para editar o eliminar.")

    def _eliminar_usuario(self):
        if self.usuario_seleccionado is None:
            messagebox.showwarning("Sin selección", "Por favor, seleccione un usuario de la tabla para eliminar.")
            return

        seleccion = self.tree.selection()
        item = self.tree.item(seleccion[0])
        valores = item["values"]
        usuario_nombre = valores[1]
        usuario_id = valores[0]

        if session.usuario == usuario_nombre:
            messagebox.showerror("Operación no permitida", "No puede eliminar su propio usuario mientras está logueado.")
            return

        respuesta = messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Está seguro de que desea eliminar al usuario '{usuario_nombre}'?\n\nEsta acción no se puede deshacer."
        )

        if respuesta:
            consulta = "DELETE FROM usuarios WHERE id = ?"
            try:
                query(consulta, (usuario_id,))
                messagebox.showinfo("Éxito", f"Usuario '{usuario_nombre}' eliminado correctamente.")
                self.usuario_seleccionado = None
                self._resetear_panel_lateral()
                self._cargar_usuarios()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo eliminar el usuario.\nError: {str(e)}")

    def _resetear_panel_lateral(self):
        self.lbl_info_id.config(text="ID: —")
        self.lbl_info_usuario.config(text="Usuario: —")
        self.lbl_info_nombre.config(text="Nombre: —")
        self.lbl_info_rol.config(text="Rol: —")
        self.lbl_nota.config(text="Seleccione un usuario de la tabla\npara ver sus detalles.")