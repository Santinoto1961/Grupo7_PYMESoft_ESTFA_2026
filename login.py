#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================
login.py - Módulo de Login
============================================================
Clase `VentanaLogin` que maneja la interfaz gráfica del login.
Valida las credenciales contra la tabla `usuarios` de la base
de datos real (`archivo.db`) usando la función `query()` del
módulo `database.py`.

Tras un login exitoso, destruye la ventana de login y abre la
ventana principal importando `VentanaPrincipal` de `main_window.py`.

Autor: Estudiante
Fecha: 2026-06-04
============================================================
"""

# ============================================================
# 1. IMPORTACIONES
# ============================================================
import tkinter as tk              # Librería estándar para interfaces gráficas
from tkinter import messagebox    # Ventanas emergentes de alerta/error

# Importar la función central de base de datos desde el módulo database.py
from database import query

# Importar la clase de la ventana principal desde el módulo main_window.py
from main_window import VentanaPrincipal


# ============================================================
# 2. CLASE DE LOGIN
# ============================================================
class VentanaLogin:
    """
    Clase que maneja la interfaz gráfica del login.
    Separada completamente de la lógica de negocio.
    """

    def __init__(self, root):
        """
        Constructor: recibe la ventana raíz de tkinter.
        """
        self.root = root
        self.root.title("Login - Gestión de PYMEs")
        self.root.resizable(True, True)

        # ── Pantalla completa (maximizada) ──────────────────────
        # Maximiza la ventana en Windows, Linux y macOS
        try:
            self.root.state("zoomed")          # Windows / algunos Linux
        except Exception:
            self.root.attributes("-zoomed", True)  # Linux fallback

        self.root.configure(bg="#a6a6a6")      # Fondo gris general

        # --------------------------------------------------------
        # VARIABLES DE CONTROL
        # --------------------------------------------------------
        self.usuario_var = tk.StringVar()
        self.contrasena_var = tk.StringVar()

        # --------------------------------------------------------
        # FRAME PRINCIPAL: centra el contenido en la pantalla
        # --------------------------------------------------------
        self.frame_principal = tk.Frame(self.root, bg="#a6a6a6")
        self.frame_principal.place(relx=0.5, rely=0.5, anchor="center")

        # --------------------------------------------------------
        # TÍTULO "PYMEsoft" — fuera del card, arriba
        # "PYME" en verde oscuro, "soft" en blanco
        # --------------------------------------------------------
        self.canvas_titulo = tk.Canvas(
            self.frame_principal,
            width=460, height=90,
            bg="#a6a6a6", highlightthickness=0
        )
        self.canvas_titulo.pack(pady=(0, 22))

        # "PYME" en verde oscuro
        self.canvas_titulo.create_text(
            228, 48,
            text="PYME",
            font=("Arial", 52, "bold"),
            fill="#06370b",
            anchor="e"
        )
        # "soft" en blanco (mismo baseline, fuente regular)
        self.canvas_titulo.create_text(
            232, 52,
            text="soft",
            font=("Arial", 46),
            fill="#ffffff",
            anchor="w"
        )

        # --------------------------------------------------------
        # CARD VERDE exterior
        # Contiene: título "inicie sesion" + sub-frame gris con inputs/botón
        # --------------------------------------------------------
        self.frame_card_verde = tk.Frame(
            self.frame_principal,
            bg="#06370b",
            padx=22,
            pady=22
        )
        self.frame_card_verde.pack()

        # Título "inicie sesion" — zona verde del card
        self.label_titulo = tk.Label(
            self.frame_card_verde,
            text="inicie sesion",
            font=("Arial", 20),
            fg="#ffffff",
            bg="#06370b"
        )
        self.label_titulo.pack(anchor="w", pady=(0, 16))

        # --------------------------------------------------------
        # SUB-FRAME GRIS — contiene los inputs y el botón
        # Este es el panel gris interno visible en el mockup
        # --------------------------------------------------------
        self.frame_gris = tk.Frame(
            self.frame_card_verde,
            bg="#a6a6a6",
            padx=18,
            pady=18
        )
        self.frame_gris.pack()

        # ── ENTRY: USUARIO ──────────────────────────────────────
        self.entry_usuario = tk.Entry(
            self.frame_gris,
            textvariable=self.usuario_var,
            font=("Arial", 14),
            width=34,
            bg="#f5f5f5",
            fg="#a6a6a6",
            relief="flat",
            bd=0,
            insertbackground="#06370b"
        )
        self.entry_usuario.insert(0, "usuario....")
        self.entry_usuario.pack(ipady=12, pady=(0, 10))

        # ── ENTRY: CONTRASEÑA ───────────────────────────────────
        self.entry_contrasena = tk.Entry(
            self.frame_gris,
            textvariable=self.contrasena_var,
            font=("Arial", 14),
            width=34,
            bg="#f5f5f5",
            fg="#a6a6a6",
            relief="flat",
            bd=0,
            insertbackground="#06370b"
        )
        self.entry_contrasena.insert(0, "contraseña....")
        self.entry_contrasena.pack(ipady=12, pady=(0, 16))

        # ── BOTÓN: ACEPTAR ──────────────────────────────────────
        self.boton_login = tk.Button(
            self.frame_gris,
            text="aceptar",
            font=("Arial", 14),
            bg="#06370b",
            fg="#ffffff",
            activebackground="#0a5212",
            activeforeground="#ffffff",
            width=30,
            cursor="hand2",
            relief="flat",
            bd=0,
            command=self.verificar_login
        )
        self.boton_login.pack(ipady=10)

        # --------------------------------------------------------
        # LOGO (debajo del card)
        # TAMAÑO RECOMENDADO DEL LOGO: 130x130 px — adaptá assets/logo.png a este tamaño
        # --------------------------------------------------------
        try:
            self.logo_img = tk.PhotoImage(file="assets/logo.png")
            self.label_logo = tk.Label(
                self.frame_principal,
                image=self.logo_img,
                bg="#a6a6a6"
            )
            self.label_logo.pack(pady=(22, 0))
        except Exception:
            # Espacio reservado si no existe el archivo
            # TAMAÑO: 130x130 px
            self.label_logo = tk.Label(
                self.frame_principal,
                text="[ logo 130×130 px\nassets/logo.png ]",
                font=("Arial", 9),
                fg="#555555",
                bg="#a6a6a6",
                width=18,
                height=6
            )
            self.label_logo.pack(pady=(22, 0))

        # --------------------------------------------------------
        # PLACEHOLDER: limpiar al hacer foco, restaurar si queda vacío
        # --------------------------------------------------------
        self.entry_usuario.bind("<FocusIn>", self._limpiar_placeholder_usuario)
        self.entry_usuario.bind("<FocusOut>", self._restaurar_placeholder_usuario)
        self.entry_contrasena.bind("<FocusIn>", self._limpiar_placeholder_contrasena)
        self.entry_contrasena.bind("<FocusOut>", self._restaurar_placeholder_contrasena)

        # Foco automático al abrir
        self.entry_usuario.focus()

        # Enter dispara el login
        self.root.bind("<Return>", lambda event: self.verificar_login())

    # --------------------------------------------------------
    # MÉTODOS DE PLACEHOLDER
    # --------------------------------------------------------
    def _limpiar_placeholder_usuario(self, event):
        if self.entry_usuario.get() == "usuario....":
            self.entry_usuario.delete(0, tk.END)
            self.entry_usuario.config(fg="#2c2c2c")

    def _restaurar_placeholder_usuario(self, event):
        if not self.entry_usuario.get():
            self.entry_usuario.insert(0, "usuario....")
            self.entry_usuario.config(fg="#a6a6a6")

    def _limpiar_placeholder_contrasena(self, event):
        if self.entry_contrasena.get() == "contraseña....":
            self.entry_contrasena.delete(0, tk.END)
            self.entry_contrasena.config(fg="#2c2c2c", show="*")

    def _restaurar_placeholder_contrasena(self, event):
        if not self.entry_contrasena.get():
            self.entry_contrasena.config(show="")
            self.entry_contrasena.insert(0, "contraseña....")
            self.entry_contrasena.config(fg="#a6a6a6")

    # --------------------------------------------------------
    # MÉTODO: VERIFICAR CREDENCIALES
    # --------------------------------------------------------
    def verificar_login(self):
        """
        Comprueba usuario y contraseña consultando la base de datos.
        Busca en la tabla 'usuarios' de archivo.db si existe una fila
        donde el usuario y la contraseña coincidan con los ingresados.
        """
        # --------------------------------------------------------
        # PASO 1: Obtener los datos ingresados por el usuario en los Entrys
        # --------------------------------------------------------
        usuario = self.usuario_var.get().strip()
        contrasena = self.contrasena_var.get().strip()

        # --------------------------------------------------------
        # PASO 2: Validar que los campos no estén vacíos
        # --------------------------------------------------------
        if not usuario or not contrasena or usuario == "usuario...." or contrasena == "contraseña....":
            messagebox.showwarning(
                "Campos vacíos",
                "Por favor, ingrese tanto el usuario como la contraseña."
            )
            return

        # --------------------------------------------------------
        # PASO 3: Consultar la base de datos usando la función query()
        # --------------------------------------------------------
        # Buscamos una fila en la tabla 'usuarios' donde usuario y contraseña coincidan
        # Usamos parámetros (?, ?) para evitar inyección SQL
        consulta_sql = "SELECT * FROM usuarios WHERE usuario = ? AND contraseña = ?"
        parametros = (usuario, contrasena)

        resultado = query(consulta_sql, parametros)

        # --------------------------------------------------------
        # PASO 4: Verificar si se encontró el usuario
        # --------------------------------------------------------
        # Si resultado tiene al menos una fila, el login es exitoso
        if resultado and len(resultado) > 0:
            # Login exitoso: destruir ventana de login y abrir la principal
            self.root.destroy()
            self.abrir_ventana_principal()
        else:
            # Login fallido: mostrar mensaje de error
            messagebox.showerror(
                "Error de autenticación",
                "Usuario o contraseña incorrectos.\n\nPor favor, verifique sus credenciales."
            )

    # --------------------------------------------------------
    # MÉTODO: ABRIR VENTANA PRINCIPAL
    # --------------------------------------------------------
    def abrir_ventana_principal(self):
        """
        Crea una nueva ventana raíz para la aplicación principal.
        """
        ventana_principal = tk.Tk()
        app = VentanaPrincipal(ventana_principal)
        ventana_principal.mainloop()