#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================
main_window.py - Ventana Principal (Menú)
============================================================
Clase `VentanaPrincipal` que implementa la interfaz de la
ventana principal con sidebar de navegación.

Diseño fiel al mockup adjunto:
  - Sidebar verde oscuro a la izquierda (~220px)
  - Logo "PYME soft" en la parte superior del sidebar
  - Botones de navegación: FACTURACION, STOCK, PRECIOS,
    CLIENTES, PROVEEDORES, BALANCE, USUARIOS
  - Enlace "soporte tecnico" y botón "Cerrar Sesion" abajo
  - Área de contenido gris a la derecha

Paleta de colores (según imagen adjunta):
  - Verde sidebar:   #1B4D1B
  - Verde botón:     #a6a6a6
  - Verde hover:     #FFFFFF
  - Gris fondo:      #A8A8A8
  - Blanco texto:    #FFFFFF
  - Negro texto:     #000000
  - Rojo cerrar:     #8B0000
  - Rojo hover:      #A52A2A

Autor: Estudiante
Fecha: 2026-07-02
============================================================
"""

import tkinter as tk
from tkinter import messagebox

from session import session
from usuarios import VistaUsuarios


# ============================================================
# PALETA DE COLORES
# ============================================================
COLOR_VERDE_SIDEBAR = "#1B4D1B"
COLOR_VERDE_BOTON   = "#a6a6a6"
COLOR_VERDE_HOVER   = "#FFFFFF"
COLOR_GRIS_FONDO    = "#A8A8A8"
COLOR_BLANCO        = "#FFFFFF"
COLOR_NEGRO         = "#000000"
COLOR_ROJO_CERRAR   = "#8B0000"
COLOR_ROJO_HOVER    = "#A52A2A"


class VentanaPrincipal:
    """
    Ventana principal de la aplicación PYMEsoft.
    Contiene un sidebar de navegación y un área de contenido.
    """

    def __init__(self, root):
        self.root = root
        self.root.title("PYMEsoft - Panel Principal")
        self.root.configure(bg=COLOR_GRIS_FONDO)

        # Maximizar ventana
        try:
            self.root.state("zoomed")
        except Exception:
            self.root.attributes("-zoomed", True)

        self.root.resizable(True, True)

        # ============================================================
        # FRAME CONTENEDOR PRINCIPAL (ocupa toda la ventana)
        # ============================================================
        self.frame_contenedor = tk.Frame(self.root, bg=COLOR_GRIS_FONDO)
        self.frame_contenedor.pack(fill=tk.BOTH, expand=True)

        # ============================================================
        # SIDEBAR IZQUIERDO (verde oscuro)
        # ============================================================
        self.sidebar = tk.Frame(
            self.frame_contenedor,
            bg=COLOR_VERDE_SIDEBAR,
            width=220
        )
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)  # Fijar ancho

        # ── Logo / Título en el sidebar ─────────────────────────
        self._crear_logo_sidebar()

        # ── Botones de navegación ───────────────────────────────
        self._crear_botones_navegacion()

        # ── Separador flexible ──────────────────────────────────
        tk.Frame(self.sidebar, bg=COLOR_VERDE_SIDEBAR, height=20).pack()

        # ── Enlace "soporte tecnico" ────────────────────────────
        self._crear_soporte_tecnico()

        # ── Botón "Cerrar Sesion" ───────────────────────────────
        self._crear_boton_cerrar_sesion()

        # ============================================================
        # ÁREA DE CONTENIDO PRINCIPAL (gris)
        # ============================================================
        self.area_contenido = tk.Frame(
            self.frame_contenedor,
            bg=COLOR_GRIS_FONDO
        )
        self.area_contenido.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # ── Título de bienvenida ────────────────────────────────
        self._mostrar_bienvenida()

    # ============================================================
    # MÉTODOS PRIVADOS: Construcción de la UI
    # ============================================================

    def _crear_logo_sidebar(self):
        """
        Crea el logo/título "PYME soft" en la parte superior del sidebar.
        """
        frame_logo = tk.Frame(self.sidebar, bg=COLOR_VERDE_SIDEBAR, pady=25)
        frame_logo.pack(fill=tk.X)

        # Canvas para el logo con la rana (o texto si no hay imagen)
        self.canvas_logo = tk.Canvas(
            frame_logo,
            width=180,
            height=80,
            bg=COLOR_VERDE_SIDEBAR,
            highlightthickness=0
        )
        self.canvas_logo.pack()

        # Intentar cargar imagen del logo
        try:
            self.img_logo = tk.PhotoImage(file="assets/logo_sidebar.png")
            self.canvas_logo.create_image(90, 40, image=self.img_logo)
        except Exception:
            # Dibujar texto "PYME soft" como fallback
            self.canvas_logo.create_text(
                90, 30,
                text="PYME",
                font=("Arial", 22, "bold"),
                fill=COLOR_BLANCO,
                anchor="center"
            )
            self.canvas_logo.create_text(
                90, 55,
                text="soft",
                font=("Arial", 16),
                fill="#cccccc",
                anchor="center"
            )

    def _crear_botones_navegacion(self):
        """
        Crea los botones del menú lateral según el rol del usuario.
        Admin ve todos. Empleado ve solo los permitidos.
        """
        # Todos los botones disponibles
        botones_todos = [
            {"texto": "FACTURACION", "comando": self._abrir_facturacion},
            {"texto": "STOCK",       "comando": self._abrir_stock},
            {"texto": "PRECIOS",     "comando": self._abrir_precios},
            {"texto": "CLIENTES",    "comando": self._abrir_clientes},
            {"texto": "PROVEEDORES", "comando": self._abrir_proveedores},
            {"texto": "BALANCE",     "comando": self._abrir_balance},
            {"texto": "USUARIOS",    "comando": self._abrir_usuarios},
        ]

        # Botones que el empleado PUEDE ver
        botones_empleado = ["FACTURACION", "STOCK", "PRECIOS", "CLIENTES", "PROVEEDORES", "BALANCE"]

        # Filtrar según rol
        if session.is_admin():
            botones_a_mostrar = botones_todos
        else:
            botones_a_mostrar = [
                b for b in botones_todos if b["texto"] in botones_empleado
            ]

        self.botones_menu = []

        for boton_data in botones_a_mostrar:
            btn = tk.Button(
                self.sidebar,
                text=boton_data["texto"],
                font=("Arial", 12, "bold"),
                bg=COLOR_VERDE_BOTON,
                fg=COLOR_NEGRO,
                activebackground=COLOR_VERDE_HOVER,
                activeforeground=COLOR_NEGRO,
                relief="flat",
                bd=0,
                cursor="hand2",
                height=2,
                command=boton_data["comando"]
            )
            btn.pack(fill=tk.X, padx=15, pady=8)
            self.botones_menu.append(btn)

            # Efecto hover
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=COLOR_VERDE_HOVER))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=COLOR_VERDE_BOTON))

    def _crear_soporte_tecnico(self):
        """
        Crea el enlace de texto "soporte tecnico" en la parte inferior.
        """
        frame_soporte = tk.Frame(self.sidebar, bg=COLOR_VERDE_SIDEBAR, pady=10)
        frame_soporte.pack(fill=tk.X, side=tk.BOTTOM)

        self.lbl_soporte = tk.Label(
            frame_soporte,
            text="soporte tecnico",
            font=("Arial", 10, "underline"),
            fg=COLOR_BLANCO,
            bg=COLOR_VERDE_SIDEBAR,
            cursor="hand2"
        )
        self.lbl_soporte.pack()
        self.lbl_soporte.bind("<Button-1>", lambda e: self._abrir_soporte())

    def _crear_boton_cerrar_sesion(self):
        """
        Crea el botón rojo "Cerrar Sesion" al final del sidebar.
        """
        frame_cerrar = tk.Frame(self.sidebar, bg=COLOR_VERDE_SIDEBAR, pady=15, padx=15)
        frame_cerrar.pack(fill=tk.X, side=tk.BOTTOM)

        self.btn_cerrar = tk.Button(
            frame_cerrar,
            text="Cerrar Sesion",
            font=("Arial", 11, "bold"),
            bg=COLOR_ROJO_CERRAR,
            fg=COLOR_BLANCO,
            activebackground=COLOR_ROJO_HOVER,
            activeforeground=COLOR_BLANCO,
            relief="flat",
            bd=0,
            cursor="hand2",
            height=2,
            command=self._cerrar_sesion
        )
        self.btn_cerrar.pack(fill=tk.X)

        # Efecto hover
        self.btn_cerrar.bind("<Enter>", lambda e: self.btn_cerrar.config(bg=COLOR_ROJO_HOVER))
        self.btn_cerrar.bind("<Leave>", lambda e: self.btn_cerrar.config(bg=COLOR_ROJO_CERRAR))

    def _mostrar_bienvenida(self):
        """
        Muestra un mensaje de bienvenida en el área de contenido.
        """
        for widget in self.area_contenido.winfo_children():
            widget.destroy()

        frame_bienvenida = tk.Frame(self.area_contenido, bg=COLOR_GRIS_FONDO)
        frame_bienvenida.place(relx=0.5, rely=0.5, anchor="center")

        # Nombre del usuario
        nombre = session.nombre or session.usuario or "Usuario"
        rol_texto = "Administrador" if session.is_admin() else "Empleado"

        tk.Label(
            frame_bienvenida,
            text=f"¡Bienvenido, {nombre}!",
            font=("Arial", 28, "bold"),
            fg=COLOR_VERDE_SIDEBAR,
            bg=COLOR_GRIS_FONDO
        ).pack(pady=(0, 10))

        tk.Label(
            frame_bienvenida,
            text=f"Rol: {rol_texto}",
            font=("Arial", 14),
            fg="#555555",
            bg=COLOR_GRIS_FONDO
        ).pack()

        tk.Label(
            frame_bienvenida,
            text="Seleccione una opción del menú lateral para comenzar.",
            font=("Arial", 12),
            fg="#666666",
            bg=COLOR_GRIS_FONDO
        ).pack(pady=(20, 0))

    # ============================================================
    # COMANDOS DE LOS BOTONES DEL MENÚ
    # ============================================================

    def _abrir_facturacion(self):
        self._cambiar_vista("FACTURACIÓN", "Módulo de facturación")

    def _abrir_stock(self):
        self._cambiar_vista("STOCK", "Módulo de gestión de inventario")

    def _abrir_precios(self):
        self._cambiar_vista("PRECIOS", "Módulo de gestión de precios")

    def _abrir_clientes(self):
        self._cambiar_vista("CLIENTES", "Módulo de gestión de clientes")

    def _abrir_proveedores(self):
        self._cambiar_vista("PROVEEDORES", "Módulo de gestión de proveedores")

    def _abrir_balance(self):
        self._cambiar_vista("BALANCE", "Módulo de balances y reportes")

    def _abrir_usuarios(self):
        """
        Abre la pantalla de gestión de usuarios (solo admin).
        """
        # Limpiar área de contenido
        for widget in self.area_contenido.winfo_children():
            widget.destroy()

        # Instanciar la vista de usuarios
        VistaUsuarios(self.area_contenido)

    def _abrir_soporte(self):
        messagebox.showinfo(
            "Soporte Técnico",
            "Contacte al soporte técnico:\n\n"
            "Email: soporte@pymesoft.com\n"
            "Teléfono: +54 11 1234-5678"
        )

    def _cambiar_vista(self, titulo, subtitulo):
        """
        Cambia el contenido del área principal mostrando el título del módulo.
        """
        for widget in self.area_contenido.winfo_children():
            widget.destroy()

        frame_modulo = tk.Frame(self.area_contenido, bg=COLOR_GRIS_FONDO)
        frame_modulo.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(
            frame_modulo,
            text=titulo,
            font=("Arial", 32, "bold"),
            fg=COLOR_VERDE_SIDEBAR,
            bg=COLOR_GRIS_FONDO
        ).pack(pady=(0, 10))

        tk.Label(
            frame_modulo,
            text=subtitulo,
            font=("Arial", 14),
            fg="#555555",
            bg=COLOR_GRIS_FONDO
        ).pack()

        tk.Label(
            frame_modulo,
            text="(Contenido del módulo en desarrollo...)",
            font=("Arial", 11, "italic"),
            fg="#777777",
            bg=COLOR_GRIS_FONDO
        ).pack(pady=(30, 0))

    # ============================================================
    # CERRAR SESIÓN
    # ============================================================

    def _cerrar_sesion(self):
        """
        Cierra la sesión actual, limpia el estado global y vuelve al login.
        """
        respuesta = messagebox.askyesno(
            "Cerrar Sesión",
            "¿Está seguro de que desea cerrar la sesión?"
        )
        if respuesta:
            # Limpiar sesión global
            session.cerrar_sesion()

            # Destruir ventana principal
            self.root.destroy()

            # Importación LOCAL (lazy) para evitar circular import
            from login import VentanaLogin

            # Volver a abrir login
            ventana_login = tk.Tk()
            app = VentanaLogin(ventana_login)
            ventana_login.mainloop()