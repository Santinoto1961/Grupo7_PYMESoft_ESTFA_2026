#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================
main.py - Punto de Entrada de la Aplicación
============================================================
Este es el archivo principal que debe ejecutarse para iniciar
la aplicación. Arranca el bucle de eventos de Tkinter e
inicializa la ventana de Login importando la clase `VentanaLogin`
del módulo `login.py`.

Estructura del proyecto:
    - database.py     → Función central de base de datos
    - login.py        → Ventana de inicio de sesión
    - main_window.py  → Ventana principal de gestión
    - main.py         → Punto de entrada (este archivo)

Autor: Estudiante
Fecha: 2026-06-04
============================================================
"""

# ============================================================
# 1. IMPORTACIONES
# ============================================================
import tkinter as tk  # Librería estándar para interfaces gráficas

# Importar la clase de login desde el módulo login.py
from login import VentanaLogin


# ============================================================
# 2. FUNCIÓN MAIN (Punto de entrada de la aplicación)
# ============================================================
# Esta función se ejecuta cuando se corre el archivo .py directamente.
# ============================================================

def main():
    """
    Punto de entrada principal de la aplicación.
    Crea la ventana de login y inicia el loop de tkinter.
    """
    # Crear la ventana raíz de tkinter
    root = tk.Tk()

    # Instanciar la clase de login
    app = VentanaLogin(root)

    # Iniciar el bucle principal de eventos de tkinter
    # (mantiene la ventana abierta y responde a clics, teclado, etc.)
    root.mainloop()


# ============================================================
# EJECUCIÓN DIRECTA DEL ARCHIVO
# ============================================================
# Si este archivo se ejecuta directamente (no se importa como módulo),
# se llama a la función main().
# ============================================================

if __name__ == "__main__":
    main()