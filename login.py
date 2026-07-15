#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================
login.py - Módulo de Login
============================================================
"""

import tkinter as tk
from tkinter import messagebox

from database import query
from session import session
from main_window import VentanaPrincipal


class VentanaLogin:
    def __init__(self, root):
        self.root = root
        self.root.title("Login - Gestión de PYMEs")
        self.root.resizable(True, True)

        try:
            self.root.state("zoomed")
        except Exception:
            self.root.attributes("-zoomed", True)

        self.root.configure(bg="#a6a6a6")

        self.usuario_var = tk.StringVar()
        self.contrasena_var = tk.StringVar()

        self.frame_principal = tk.Frame(self.root, bg="#a6a6a6")
        self.frame_principal.place(relx=0.5, rely=0.5, anchor="center")

        # Título PYMEsoft
        self.canvas_titulo = tk.Canvas(
            self.frame_principal,
            width=460, height=90,
            bg="#a6a6a6", highlightthickness=0
        )
        self.canvas_titulo.pack(pady=(0, 22))

        self.canvas_titulo.create_text(
            228, 48, text="PYME",
            font=("Arial", 52, "bold"),
            fill="#06370b", anchor="e"
        )
        self.canvas_titulo.create_text(
            232, 52, text="soft",
            font=("Arial", 46),
            fill="#ffffff", anchor="w"
        )

        # Card verde
        self.frame_card_verde = tk.Frame(
            self.frame_principal,
            bg="#06370b",
            padx=22, pady=22
        )
        self.frame_card_verde.pack()

        self.label_titulo = tk.Label(
            self.frame_card_verde,
            text="inicie sesion",
            font=("Arial", 20),
            fg="#ffffff", bg="#06370b"
        )
        self.label_titulo.pack(anchor="w", pady=(0, 16))

        # Sub-frame gris
        self.frame_gris = tk.Frame(
            self.frame_card_verde,
            bg="#a6a6a6",
            padx=18, pady=18
        )
        self.frame_gris.pack()

        # Entry usuario
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

        # Entry contraseña
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

        # Botón aceptar
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

        # Logo
        try:
            self.logo_img = tk.PhotoImage(file="assets/logo.png")
            self.label_logo = tk.Label(
                self.frame_principal,
                image=self.logo_img,
                bg="#a6a6a6"
            )
            self.label_logo.pack(pady=(22, 0))
        except Exception:
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

        # Placeholders
        self.entry_usuario.bind("<FocusIn>", self._limpiar_placeholder_usuario)
        self.entry_usuario.bind("<FocusOut>", self._restaurar_placeholder_usuario)
        self.entry_contrasena.bind("<FocusIn>", self._limpiar_placeholder_contrasena)
        self.entry_contrasena.bind("<FocusOut>", self._restaurar_placeholder_contrasena)

        self.entry_usuario.focus()
        self.root.bind("<Return>", lambda event: self.verificar_login())

    # Placeholders
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

    # Login
    def verificar_login(self):
        usuario = self.usuario_var.get().strip()
        contrasena = self.contrasena_var.get().strip()

        if not usuario or not contrasena or usuario == "usuario...." or contrasena == "contraseña....":
            messagebox.showwarning("Campos vacíos", "Por favor, ingrese tanto el usuario como la contraseña.")
            return

        # ============================================================
        # CONSULTA CORREGIDA: usa 'nombre_completo' y 'rol'
        # ============================================================
        consulta_sql = """
            SELECT id, usuario, nombre_completo, rol 
            FROM usuarios 
            WHERE usuario = ? AND contraseña = ?
        """
        parametros = (usuario, contrasena)
        resultado = query(consulta_sql, parametros)

        if resultado and len(resultado) > 0:
            fila = resultado[0]
            id_usuario = fila[0]
            nombre_usuario = fila[1]
            nombre_completo = fila[2] if fila[2] else fila[1]
            rol = fila[3] if len(fila) > 3 else "empleado"

            # Normalizar rol: 'admin' → 'administrador'
            if rol and rol.lower() == "admin":
                rol = "administrador"

            session.iniciar_sesion(
                id_usuario=id_usuario,
                usuario=nombre_usuario,
                nombre=nombre_completo,
                rol=rol
            )

            self.root.destroy()
            self.abrir_ventana_principal()

        else:
            messagebox.showerror(
                "Error de autenticación",
                "Usuario o contraseña incorrectos."
            )

    def abrir_ventana_principal(self):
        ventana_principal = tk.Tk()
        app = VentanaPrincipal(ventana_principal)
        ventana_principal.mainloop()