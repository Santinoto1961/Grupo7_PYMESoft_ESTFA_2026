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
  - Eliminar usuarios seleccionados de la base de datos

Todas las operaciones de BD usan la función query() del
módulo database.py.

Diseño fiel al mockup de referencia:
  - Título grande en negro
  - Panel verde oscuro con título blanco
  - Tabla con columnas
  - Panel lateral con info adicional
  - Botones de acción abajo

Autor: Estudiante
Fecha: 2026-07-04
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
COLOR_VERDE_BOTON_ACCION = "#0D2E0D"  # Verde oscuro para botones de acción


class VistaUsuarios:
    """
    Clase que construye y gestiona la pantalla de usuarios
    dentro del área de contenido de la ventana principal.
    """

    def __init__(self, parent_frame):
        """
        Constructor: recibe el frame padre (area_contenido) donde
        se renderizará toda la interfaz de usuarios.
        """
        self.parent = parent_frame
        self.usuario_seleccionado = None  # ID del usuario seleccionado en la tabla

        # Limpiar el área de contenido antes de renderizar
        for widget in self.parent.winfo_children():
            widget.destroy()

        # ============================================================
        # 1. TÍTULO PRINCIPAL
        # ============================================================
        self._crear_titulo()

        # ============================================================
        # 2. PANEL PRINCIPAL VERDE (contiene tabla + panel lateral)
        # ============================================================
        self._crear_panel_principal()

        # ============================================================
        # 3. BOTONES DE ACCIÓN (abajo del panel)
        # ============================================================
        self._crear_botones_accion()

        # ============================================================
        # 4. CARGAR DATOS INICIALES
        # ============================================================
        self._cargar_usuarios()

    # ============================================================
    # SECCIÓN 1: TÍTULO PRINCIPAL
    # ============================================================

    def _crear_titulo(self):
        """
        Crea el título grande 'USUARIOS:' en la parte superior
        del área de contenido, alineado a la izquierda.
        """
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
        """
        Crea el panel verde oscuro que contiene:
          - Título 'Lista de usuarios:' en blanco
          - Tabla Treeview con los usuarios
          - Panel lateral derecho con info del usuario seleccionado
        """
        # Frame verde exterior (con padding para el borde verde)
        self.frame_panel = tk.Frame(
            self.parent,
            bg=COLOR_VERDE_SIDEBAR,
            padx=8,
            pady=8
        )
        self.frame_panel.pack(fill=tk.BOTH, expand=True, padx=40, pady=(0, 20))

        # Título dentro del panel verde
        self.lbl_subtitulo = tk.Label(
            self.frame_panel,
            text="Lista de usuarios:",
            font=("Arial", 16, "bold"),
            fg=COLOR_BLANCO,
            bg=COLOR_VERDE_SIDEBAR
        )
        self.lbl_subtitulo.pack(anchor="w", pady=(0, 8))

        # Frame interno gris (contiene tabla + panel lateral)
        self.frame_interno = tk.Frame(
            self.frame_panel,
            bg=COLOR_GRIS_FONDO
        )
        self.frame_interno.pack(fill=tk.BOTH, expand=True)

        # ── Sub-sección 2A: Tabla de usuarios ─────────────────
        self._crear_tabla_usuarios()

        # ── Sub-sección 2B: Panel lateral (info del seleccionado) ─
        self._crear_panel_lateral()

    def _crear_tabla_usuarios(self):
        """
        Crea el Treeview con las columnas:
        ID | Usuario | Nombre Completo | Rol
        """
        # Frame contenedor de la tabla (izquierda)
        self.frame_tabla = tk.Frame(
            self.frame_interno,
            bg=COLOR_GRIS_FONDO
        )
        self.frame_tabla.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 2))

        # Definir columnas
        columnas = ("id", "usuario", "nombre_completo", "rol")
        self.tree = ttk.Treeview(
            self.frame_tabla,
            columns=columnas,
            show="headings",
            height=12
        )

        # Configurar encabezados
        self.tree.heading("id", text="ID")
        self.tree.heading("usuario", text="Usuario")
        self.tree.heading("nombre_completo", text="Nombre Completo")
        self.tree.heading("rol", text="Rol")

        # Configurar anchos de columna
        self.tree.column("id", width=50, anchor="center")
        self.tree.column("usuario", width=120, anchor="w")
        self.tree.column("nombre_completo", width=200, anchor="w")
        self.tree.column("rol", width=100, anchor="center")

        # Scrollbar vertical
        scrollbar = ttk.Scrollbar(
            self.frame_tabla,
            orient=tk.VERTICAL,
            command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Empaquetar tabla y scrollbar
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)

        # Evento: al hacer clic en una fila, mostrar info en panel lateral
        self.tree.bind("<<TreeviewSelect>>", self._on_seleccionar_usuario)

    def _crear_panel_lateral(self):
        """
        Crea el panel derecho que muestra información del usuario
        seleccionado en la tabla. Similar al panel 'Última actualización'
        del mockup de precios.
        """
        # Frame del panel lateral (derecha, con borde izquierdo)
        self.frame_lateral = tk.Frame(
            self.frame_interno,
            bg=COLOR_GRIS_FONDO,
            width=280
        )
        self.frame_lateral.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)
        self.frame_lateral.pack_propagate(False)

        # Título del panel lateral
        self.lbl_info_titulo = tk.Label(
            self.frame_lateral,
            text="Información del usuario:",
            font=("Arial", 12, "bold"),
            fg=COLOR_NEGRO,
            bg=COLOR_GRIS_FONDO
        )
        self.lbl_info_titulo.pack(anchor="w", pady=(0, 15))

        # Campos de info (se actualizan al seleccionar)
        self.lbl_info_id = tk.Label(
            self.frame_lateral,
            text="ID: —",
            font=("Arial", 11),
            fg=COLOR_NEGRO,
            bg=COLOR_GRIS_FONDO,
            anchor="w"
        )
        self.lbl_info_id.pack(fill=tk.X, pady=5)

        self.lbl_info_usuario = tk.Label(
            self.frame_lateral,
            text="Usuario: —",
            font=("Arial", 11),
            fg=COLOR_NEGRO,
            bg=COLOR_GRIS_FONDO,
            anchor="w"
        )
        self.lbl_info_usuario.pack(fill=tk.X, pady=5)

        self.lbl_info_nombre = tk.Label(
            self.frame_lateral,
            text="Nombre: —",
            font=("Arial", 11),
            fg=COLOR_NEGRO,
            bg=COLOR_GRIS_FONDO,
            anchor="w"
        )
        self.lbl_info_nombre.pack(fill=tk.X, pady=5)

        self.lbl_info_rol = tk.Label(
            self.frame_lateral,
            text="Rol: —",
            font=("Arial", 11),
            fg=COLOR_NEGRO,
            bg=COLOR_GRIS_FONDO,
            anchor="w"
        )
        self.lbl_info_rol.pack(fill=tk.X, pady=5)

        # Separador visual
        tk.Frame(self.frame_lateral, bg="#888888", height=1).pack(fill=tk.X, pady=15)

        # Nota informativa
        self.lbl_nota = tk.Label(
            self.frame_lateral,
            text="Seleccione un usuario de la tabla\npara ver sus detalles.",
            font=("Arial", 9, "italic"),
            fg="#666666",
            bg=COLOR_GRIS_FONDO,
            justify=tk.LEFT
        )
        self.lbl_nota.pack(anchor="w")

    # ============================================================
    # SECCIÓN 3: BOTONES DE ACCIÓN
    # ============================================================

    def _crear_botones_accion(self):
        """
        Crea los botones de acción en la parte inferior:
          - Editar usuario (izquierda)
          - Agregar usuario (centro-derecha)
          - Eliminar usuario (derecha, verde oscuro)
          - Botón ancho verde: 'VER LOG DE ACTIVIDAD'
        """
        # Frame contenedor de botones
        self.frame_botones = tk.Frame(
            self.parent,
            bg=COLOR_GRIS_FONDO
        )
        self.frame_botones.pack(fill=tk.X, padx=40, pady=(0, 10))

        # ── Fila superior de botones ────────────────────────────
        self.frame_fila_botones = tk.Frame(
            self.frame_botones,
            bg=COLOR_GRIS_FONDO
        )
        self.frame_fila_botones.pack(fill=tk.X)

        # Botón "Editar usuario" (izquierda)
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

        # Espaciador
        tk.Frame(self.frame_fila_botones, bg=COLOR_GRIS_FONDO).pack(side=tk.LEFT, expand=True)

        # Botón "Agregar usuario" (centro-derecha)
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

        # Botón "Eliminar usuario" (derecha, verde oscuro)
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

        # Efectos hover para botones
        self.btn_editar.bind("<Enter>", lambda e: self.btn_editar.config(bg=COLOR_VERDE_HOVER))
        self.btn_editar.bind("<Leave>", lambda e: self.btn_editar.config(bg=COLOR_VERDE_BOTON))
        self.btn_agregar.bind("<Enter>", lambda e: self.btn_agregar.config(bg=COLOR_VERDE_HOVER))
        self.btn_agregar.bind("<Leave>", lambda e: self.btn_agregar.config(bg=COLOR_VERDE_BOTON))
        self.btn_eliminar.bind("<Enter>", lambda e: self.btn_eliminar.config(bg="#1a5c1a"))
        self.btn_eliminar.bind("<Leave>", lambda e: self.btn_eliminar.config(bg=COLOR_VERDE_BOTON_ACCION))

     
    def _mostrar_formulario_agregar(self):
        """
        Abre una ventana emergente (Toplevel) con un formulario
        para crear un nuevo usuario en la base de datos.
        """
        # Crear ventana modal
        self.ventana_agregar = tk.Toplevel(self.parent)
        self.ventana_agregar.title("Agregar Nuevo Usuario")
        self.ventana_agregar.configure(bg=COLOR_GRIS_FONDO)
        self.ventana_agregar.resizable(False, False)
        self.ventana_agregar.grab_set()  # Modal: bloquea interacción con ventana principal

        # Centrar la ventana
        self.ventana_agregar.geometry("400x400")
        self.ventana_agregar.transient(self.parent)

        # ── Título del formulario ───────────────────────────────
        tk.Label(
            self.ventana_agregar,
            text="Nuevo Usuario",
            font=("Arial", 18, "bold"),
            fg=COLOR_VERDE_SIDEBAR,
            bg=COLOR_GRIS_FONDO
        ).pack(pady=(20, 20))

        # ── Frame del formulario ──────────────────────────────
        frame_form = tk.Frame(self.ventana_agregar, bg=COLOR_GRIS_FONDO, padx=30)
        frame_form.pack(fill=tk.X)

        # Campo: Usuario
        tk.Label(
            frame_form,
            text="Usuario:",
            font=("Arial", 11),
            fg=COLOR_NEGRO,
            bg=COLOR_GRIS_FONDO,
            anchor="w"
        ).pack(fill=tk.X, pady=(10, 2))

        self.entry_nuevo_usuario = tk.Entry(
            frame_form,
            font=("Arial", 12),
            bg=COLOR_BLANCO,
            fg=COLOR_NEGRO,
            relief="flat",
            bd=1
        )
        self.entry_nuevo_usuario.pack(fill=tk.X, ipady=6)

        # Campo: Nombre Completo
        tk.Label(
            frame_form,
            text="Nombre Completo:",
            font=("Arial", 11),
            fg=COLOR_NEGRO,
            bg=COLOR_GRIS_FONDO,
            anchor="w"
        ).pack(fill=tk.X, pady=(10, 2))

        self.entry_nuevo_nombre = tk.Entry(
            frame_form,
            font=("Arial", 12),
            bg=COLOR_BLANCO,
            fg=COLOR_NEGRO,
            relief="flat",
            bd=1
        )
        self.entry_nuevo_nombre.pack(fill=tk.X, ipady=6)

        # Campo: Contraseña
        tk.Label(
            frame_form,
            text="Contraseña:",
            font=("Arial", 11),
            fg=COLOR_NEGRO,
            bg=COLOR_GRIS_FONDO,
            anchor="w"
        ).pack(fill=tk.X, pady=(10, 2))

        self.entry_nueva_contrasena = tk.Entry(
            frame_form,
            font=("Arial", 12),
            bg=COLOR_BLANCO,
            fg=COLOR_NEGRO,
            relief="flat",
            bd=1,
            show="*"
        )
        self.entry_nueva_contrasena.pack(fill=tk.X, ipady=6)

        # Campo: Rol (Combobox)
        tk.Label(
            frame_form,
            text="Rol:",
            font=("Arial", 11),
            fg=COLOR_NEGRO,
            bg=COLOR_GRIS_FONDO,
            anchor="w"
        ).pack(fill=tk.X, pady=(10, 2))

        self.combo_rol = ttk.Combobox(
            frame_form,
            values=["admin", "empleado"],
            font=("Arial", 12),
            state="readonly",
            height=2
        )
        self.combo_rol.set("empleado")  # Valor por defecto
        self.combo_rol.pack(fill=tk.X, ipady=4)

        # ── Botón Confirmar ─────────────────────────────────────
        tk.Frame(self.ventana_agregar, bg=COLOR_GRIS_FONDO, height=20).pack()

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
        """
        Valida los campos del formulario e inserta el nuevo usuario
        en la base de datos mediante la función query().
        """
        usuario = self.entry_nuevo_usuario.get().strip()
        nombre_completo = self.entry_nuevo_nombre.get().strip()
        contrasena = self.entry_nueva_contrasena.get().strip()
        rol = self.combo_rol.get()

        # Validaciones
        if not usuario or not contrasena:
            messagebox.showwarning(
                "Campos incompletos",
                "El usuario y la contraseña son obligatorios.",
                parent=self.ventana_agregar
            )
            return

        if len(contrasena) < 4:
            messagebox.showwarning(
                "Contraseña débil",
                "La contraseña debe tener al menos 4 caracteres.",
                parent=self.ventana_agregar
            )
            return

        # Verificar que el usuario no exista ya
        consulta_existe = "SELECT id FROM usuarios WHERE usuario = ?"
        existe = query(consulta_existe, (usuario,))

        if existe and len(existe) > 0:
            messagebox.showerror(
                "Usuario duplicado",
                f"El usuario '{usuario}' ya existe en el sistema.",
                parent=self.ventana_agregar
            )
            return

        # Insertar en base de datos
        consulta_insert = """
            INSERT INTO usuarios (usuario, contraseña, nombre_completo, rol)
            VALUES (?, ?, ?, ?)
        """
        try:
            query(consulta_insert, (usuario, contrasena, nombre_completo, rol))
            messagebox.showinfo(
                "Éxito",
                f"Usuario '{usuario}' creado correctamente.",
                parent=self.ventana_agregar
            )
            self.ventana_agregar.destroy()
            self._cargar_usuarios()  # Recargar tabla
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"No se pudo crear el usuario.\nError: {str(e)}",
                parent=self.ventana_agregar
            )

    # ============================================================
    # SECCIÓN 5: OPERACIONES CRUD
    # ============================================================

    def _cargar_usuarios(self):
        """
        Consulta todos los usuarios de la base de datos y los
        carga en el Treeview. Usa la función query() del módulo database.
        """
        # Limpiar tabla actual
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Consultar usuarios
        consulta = "SELECT id, usuario, nombre_completo, rol FROM usuarios ORDER BY id"
        resultado = query(consulta)

        if resultado:
            for fila in resultado:
                # Formatear nombre_completo si es None
                nombre = fila[2] if fila[2] else "—"
                self.tree.insert("", tk.END, values=(fila[0], fila[1], nombre, fila[3]))

    def _on_seleccionar_usuario(self, event):
        """
        Evento que se dispara al hacer clic en una fila de la tabla.
        Actualiza el panel lateral con la información del usuario seleccionado.
        """
        seleccion = self.tree.selection()
        if not seleccion:
            return

        # Obtener valores de la fila seleccionada
        item = self.tree.item(seleccion[0])
        valores = item["values"]

        self.usuario_seleccionado = valores[0]  # ID

        # Actualizar panel lateral
        self.lbl_info_id.config(text=f"ID: {valores[0]}")
        self.lbl_info_usuario.config(text=f"Usuario: {valores[1]}")
        self.lbl_info_nombre.config(text=f"Nombre: {valores[2]}")
        self.lbl_info_rol.config(text=f"Rol: {valores[3]}")

        self.lbl_nota.config(
            text="Usuario seleccionado.\nUse los botones de abajo para editar o eliminar."
        )

    def _eliminar_usuario(self):
        """
        Elimina el usuario seleccionado de la base de datos.
        No permite eliminar al usuario actualmente logueado.
        """
        if self.usuario_seleccionado is None:
            messagebox.showwarning(
                "Sin selección",
                "Por favor, seleccione un usuario de la tabla para eliminar."
            )
            return

        # Obtener datos del usuario seleccionado
        seleccion = self.tree.selection()
        item = self.tree.item(seleccion[0])
        valores = item["values"]
        usuario_nombre = valores[1]
        usuario_id = valores[0]

        # No permitir eliminar al usuario logueado
        if session.usuario == usuario_nombre:
            messagebox.showerror(
                "Operación no permitida",
                "No puede eliminar su propio usuario mientras está logueado."
            )
            return

        # Confirmar eliminación
        respuesta = messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Está seguro de que desea eliminar al usuario '{usuario_nombre}'?\n\n"
            "Esta acción no se puede deshacer."
        )

        if respuesta:
            consulta = "DELETE FROM usuarios WHERE id = ?"
            try:
                query(consulta, (usuario_id,))
                messagebox.showinfo(
                    "Éxito",
                    f"Usuario '{usuario_nombre}' eliminado correctamente."
                )
                self.usuario_seleccionado = None
                self._resetear_panel_lateral()
                self._cargar_usuarios()
            except Exception as e:
                messagebox.showerror(
                    "Error",
                    f"No se pudo eliminar el usuario.\nError: {str(e)}"
                )

    def _editar_usuario(self):
        """
        Placeholder para la funcionalidad de edición.
        Se puede implementar en una futura versión.
        """
        if self.usuario_seleccionado is None:
            messagebox.showwarning(
                "Sin selección",
                "Por favor, seleccione un usuario de la tabla para editar."
            )
            return

        messagebox.showinfo(
            "En desarrollo",
            "La función de edición de usuarios estará disponible próximamente."
        )

    def _ver_log(self):
        """
        Placeholder para la funcionalidad de log de actividad.
        """
        messagebox.showinfo(
            "En desarrollo",
            "El log de actividad de usuarios estará disponible próximamente."
        )

    def _resetear_panel_lateral(self):
        """
        Limpia la información del panel lateral cuando no hay
        usuario seleccionado.
        """
        self.lbl_info_id.config(text="ID: —")
        self.lbl_info_usuario.config(text="Usuario: —")
        self.lbl_info_nombre.config(text="Nombre: —")
        self.lbl_info_rol.config(text="Rol: —")
        self.lbl_nota.config(
            text="Seleccione un usuario de la tabla\npara ver sus detalles."
        )