#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================
main_window.py - Ventana Principal (Menú)
============================================================
Clase `VentanaPrincipal` que implementa la interfaz de la
ventana principal con sidebar de navegación e integración
de todos los módulos del sistema.

Módulos integrados:
  - FACTURACION  → facturacion.py
  - STOCK        → stock.py
  - PRECIOS      → placeholder
  - CLIENTES     → clientes.py
  - PROVEEDORES  → proveedores.py
  - BALANCE      → placeholder
  - USUARIOS     → usuarios.py

Autor: Estudiante
Fecha: 2026-08-30
============================================================
"""

import tkinter as tk
from tkinter import messagebox

from session import session
from clientes import VistaClientes
from proveedores import VistaProveedores
from stock import VistaStock
from facturacion import VistaFacturacion
from usuarios import VistaUsuarios
from balance import VistaBalance


# ============================================================
# PALETA DE COLORES
# ============================================================
COLOR_VERDE_SIDEBAR = "#0F3A10"
COLOR_VERDE_BOTON   = "#a6a6a6"
COLOR_VERDE_HOVER   = "#d9d9d9"
COLOR_GRIS_FONDO    = "#A6A6A6"
COLOR_BLANCO        = "#FFFFFF"
COLOR_NEGRO         = "#000000"
COLOR_ROJO_CERRAR   = "#4A0000"
COLOR_ROJO_HOVER    = "#6B0000"


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
        # FRAME CONTENEDOR PRINCIPAL
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
        self.sidebar.pack_propagate(False)

        self._crear_logo_sidebar()
        self._crear_botones_navegacion()
        tk.Frame(self.sidebar, bg=COLOR_VERDE_SIDEBAR, height=20).pack()
        self._crear_soporte_tecnico()
        self._crear_boton_cerrar_sesion()

        # ============================================================
        # ÁREA DE CONTENIDO PRINCIPAL (gris)
        # ============================================================
        self.area_contenido = tk.Frame(
            self.frame_contenedor,
            bg=COLOR_GRIS_FONDO
        )
        self.area_contenido.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._mostrar_bienvenida()

    # ============================================================
    # MÉTODOS PRIVADOS: Construcción de la UI
    # ============================================================

    def _crear_logo_sidebar(self):
        """Logo: imagen (assets/logo2.png, 90x70 px) + texto PYME / soft al lado."""
        frame_logo = tk.Frame(self.sidebar, bg=COLOR_VERDE_SIDEBAR)
        frame_logo.pack(fill=tk.X, padx=15, pady=(30, 25))

        # Imagen a la izquierda
        try:
            self.img_logo = tk.PhotoImage(file="assets/logo2.png")
            tk.Label(
                frame_logo, image=self.img_logo, bg=COLOR_VERDE_SIDEBAR
            ).pack(side=tk.LEFT)
        except Exception:
            tk.Label(
                frame_logo, text="[logo2]", font=("Arial", 9),
                fg="#cccccc", bg=COLOR_VERDE_SIDEBAR, width=9, height=4
            ).pack(side=tk.LEFT)

        # Texto a la derecha de la imagen
        frame_texto = tk.Frame(frame_logo, bg=COLOR_VERDE_SIDEBAR)
        frame_texto.pack(side=tk.LEFT, padx=(6, 0))

        tk.Label(
            frame_texto, text="PYME",
            font=("Arial", 15, "bold"),
            fg=COLOR_BLANCO, bg=COLOR_VERDE_SIDEBAR
        ).pack(anchor="w")
        tk.Label(
            frame_texto, text="soft",
            font=("Arial", 13, "bold"),
            fg="#9aa89a", bg=COLOR_VERDE_SIDEBAR
        ).pack(anchor="w")

    def _crear_botones_navegacion(self):
        botones_todos = [
            {"texto": "FACTURACION", "comando": self._abrir_facturacion},
            {"texto": "STOCK",       "comando": self._abrir_stock},
            {"texto": "CLIENTES",    "comando": self._abrir_clientes},
            {"texto": "PROVEEDORES", "comando": self._abrir_proveedores},
            {"texto": "BALANCE",     "comando": self._abrir_balance},
            {"texto": "USUARIOS",    "comando": self._abrir_usuarios},
        ]

        botones_empleado = ["FACTURACION", "STOCK", "PRECIOS", "CLIENTES", "PROVEEDORES", "BALANCE"]

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
                font=("Arial", 11, "bold"),
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
            btn.pack(fill=tk.X, padx=27, pady=11)
            self.botones_menu.append(btn)

            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=COLOR_VERDE_HOVER))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=COLOR_VERDE_BOTON))

    def _crear_soporte_tecnico(self):
        frame_soporte = tk.Frame(self.sidebar, bg=COLOR_VERDE_SIDEBAR, pady=6, padx=27)
        frame_soporte.pack(fill=tk.X, side=tk.BOTTOM)

        self.lbl_soporte = tk.Label(
            frame_soporte,
            text="soporte tecnico",
            font=("Arial", 10, "underline"),
            fg=COLOR_BLANCO,
            bg=COLOR_VERDE_SIDEBAR,
            cursor="hand2"
        )
        self.lbl_soporte.pack(anchor="w")
        self.lbl_soporte.bind("<Button-1>", lambda e: self._abrir_soporte())

    def _crear_boton_cerrar_sesion(self):
        frame_cerrar = tk.Frame(self.sidebar, bg=COLOR_VERDE_SIDEBAR, pady=15, padx=27)
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

        self.btn_cerrar.bind("<Enter>", lambda e: self.btn_cerrar.config(bg=COLOR_ROJO_HOVER))
        self.btn_cerrar.bind("<Leave>", lambda e: self.btn_cerrar.config(bg=COLOR_ROJO_CERRAR))

    def _mostrar_bienvenida(self):
        for widget in self.area_contenido.winfo_children():
            widget.destroy()

        frame_bienvenida = tk.Frame(self.area_contenido, bg=COLOR_GRIS_FONDO)
        frame_bienvenida.place(relx=0.5, rely=0.5, anchor="center")

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
    # NAVEGACIÓN A MÓDULOS
    # ============================================================

    def _abrir_facturacion(self):
        for widget in self.area_contenido.winfo_children():
            widget.destroy()
        VistaFacturacion(self.area_contenido)

    def _abrir_stock(self):
        for widget in self.area_contenido.winfo_children():
            widget.destroy()
        VistaStock(self.area_contenido)

    def _abrir_clientes(self):
        for widget in self.area_contenido.winfo_children():
            widget.destroy()
        VistaClientes(self.area_contenido)

    def _abrir_proveedores(self):
        for widget in self.area_contenido.winfo_children():
            widget.destroy()
        VistaProveedores(self.area_contenido)

    def _abrir_balance(self):
        for widget in self.area_contenido.winfo_children():
            widget.destroy()
        VistaBalance(self.area_contenido)

    def _abrir_usuarios(self):
        for widget in self.area_contenido.winfo_children():
            widget.destroy()
        VistaUsuarios(self.area_contenido)

    def _abrir_soporte(self):
        messagebox.showinfo(
            "Soporte Técnico",
            "Contacte al soporte técnico:\n\n"
            "Email: soporte@pymesoft.com\n"
            "Teléfono: +54 11 1234-5678"
        )

    def _cambiar_vista(self, titulo, subtitulo):
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
        respuesta = messagebox.askyesno(
            "Cerrar Sesión",
            "¿Está seguro de que desea cerrar la sesión?"
        )
        if respuesta:
            session.cerrar_sesion()
            self.root.destroy()

            from login import VentanaLogin
            ventana_login = tk.Tk()
            app = VentanaLogin(ventana_login)
            ventana_login.mainloop()