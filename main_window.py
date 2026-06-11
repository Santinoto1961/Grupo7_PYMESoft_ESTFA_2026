#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================
main_window.py - Módulo de Ventana Principal
============================================================
Clase `VentanaPrincipal` que maneja la interfaz gráfica principal
de la aplicación de gestión de PYMEs.

Aquí irá toda la lógica de gestión de la PYME (productos, clientes,
ventas, etc.) en futuras expansiones del proyecto.

Autor: Estudiante
Fecha: 2026-06-04
============================================================
"""

# ============================================================
# 1. IMPORTACIONES
# ============================================================
import tkinter as tk  # Librería estándar para interfaces gráficas


# ============================================================
# 2. CLASE DE VENTANA PRINCIPAL (Gestión de PYME)
# ============================================================
# Ventana que se muestra después del login exitoso.
# Actualmente simula una ventana con estructura preparada para
# futuras funcionalidades.
# ============================================================

class VentanaPrincipal:
    """
    Clase que maneja la interfaz gráfica principal de la aplicación.
    Aquí irá toda la lógica de gestión de la PYME.
    """

    def __init__(self, root):
        """
        Constructor: recibe la ventana raíz de tkinter.
        """
        self.root = root
        self.root.title("Sistema de Gestión de PYMEs")
        self.root.geometry("900x600")           # Tamaño de la ventana: 900px ancho x 600px alto
        self.root.resizable(True, True)       # Permite redimensionar la ventana
        self.root.configure(bg="#ecf0f1")       # Color de fondo de la ventana (gris muy claro)

        # --------------------------------------------------------
        # FRAME SUPERIOR: BARRA DE TÍTULO / MENÚ
        # --------------------------------------------------------
        # Este frame simula una barra de navegación superior
        self.frame_superior = tk.Frame(
            self.root,
            bg="#34495e",                      # Color de fondo: gris azulado oscuro
            height=60                           # Altura fija: 60px
        )
        self.frame_superior.pack(fill="x")      # Ocupa todo el ancho horizontal
        self.frame_superior.pack_propagate(False)  # Mantiene la altura fija

        # Label del título en la barra superior
        self.label_titulo_barra = tk.Label(
            self.frame_superior,
            text="Panel de Gestión de PYME",
            font=("Arial", 16, "bold"),        # Fuente: Arial, 16px, negrita
            fg="#ffffff",                      # Color del texto: blanco
            bg="#34495e"                       # Fondo: gris azulado oscuro
        )
        self.label_titulo_barra.pack(side="left", padx=20, pady=10)

        # --------------------------------------------------------
        # FRAME CENTRAL: ÁREA DE TRABAJO PRINCIPAL
        # --------------------------------------------------------
        # Este frame ocupa el resto de la ventana y es donde irá el contenido
        self.frame_central = tk.Frame(
            self.root,
            bg="#ecf0f1"                       # Color de fondo: gris muy claro
        )
        self.frame_central.pack(expand=True, fill="both")  # Ocupa todo el espacio disponible

        # --------------------------------------------------------
        # LABEL CENTRAL: TEXTO INDICATIVO
        # --------------------------------------------------------
        # Este label indica que aquí se debe insertar el código futuro
        self.label_insertar = tk.Label(
            self.frame_central,
            text="insertar codigo",
            font=("Arial", 24, "italic"),      # Fuente: Arial, 24px, cursiva
            fg="#bdc3c7",                      # Color del texto: gris claro
            bg="#ecf0f1"                       # Fondo: gris muy claro
        )
        self.label_insertar.place(relx=0.5, rely=0.5, anchor="center")  # Perfectamente centrado

        # --------------------------------------------------------
        # FRAME INFERIOR: BARRA DE ESTADO
        # --------------------------------------------------------
        # Barra inferior con información del sistema
        self.frame_inferior = tk.Frame(
            self.root,
            bg="#95a5a6",                      # Color de fondo: gris medio
            height=30                           # Altura fija: 30px
        )
        self.frame_inferior.pack(fill="x", side="bottom")  # Pegado al fondo
        self.frame_inferior.pack_propagate(False)  # Mantiene la altura fija

        # Label de estado en la barra inferior
        self.label_estado = tk.Label(
            self.frame_inferior,
            text="Conectado a: archivo.db  |  Usuario: admin",
            font=("Arial", 10),                # Fuente: Arial, 10px
            fg="#ffffff",                      # Color del texto: blanco
            bg="#95a5a6"                       # Fondo: gris medio
        )
        self.label_estado.pack(side="right", padx=10, pady=5)