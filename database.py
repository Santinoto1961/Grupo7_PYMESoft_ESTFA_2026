#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================
database.py - Módulo de Persistencia de Datos
============================================================
Módulo exclusivo para la gestión de la base de datos SQLite3.
Contiene la función central `query()` que es la ÚNICA que 
interactúa directamente con SQLite3.

Este módulo puede ser importado por cualquier ventana futura
que necesite acceder a la base de datos, asegurando que
siempre apunte al archivo correcto (`archivo.db`).

Autor: Estudiante
Fecha: 2026-06-04
============================================================
"""

import sqlite3  # Base de datos local SQLite3


# ============================================================
# FUNCIÓN CENTRAL DE BASE DE DATOS
# ============================================================
# Basada en el modelo de la pizarra adjunta.
# Esta es la ÚNICA función que interactúa con SQLite3.
# ============================================================

def query(consulta, parametros=()):
    """
    Función central para ejecutar cualquier consulta SQL.

    Parámetros:
        consulta    (str)  : Sentencia SQL a ejecutar.
        parametros  (tuple): Valores a insertar en la consulta (evita inyección SQL).

    Retorna:
        - Si es SELECT: lista de tuplas con los resultados (.fetchall()).
        - Si es INSERT/UPDATE/DELETE: None (solo confirma cambios con .commit()).
    """
    # --------------------------------------------------------
    # PASO 1: Conectar con el archivo de la base de datos
    # --------------------------------------------------------
    con = sqlite3.connect("archivo.db")

    # --------------------------------------------------------
    # PASO 2: Crear el cursor (se posiciona en la base de datos)
    # --------------------------------------------------------
    cursor = con.cursor()

    # --------------------------------------------------------
    # PASO 3: Ejecutar la consulta con parámetros seguros
    # --------------------------------------------------------
    cursor.execute(consulta, parametros)

    # --------------------------------------------------------
    # PASO 4: Determinar si la consulta devuelve datos o modifica datos
    # --------------------------------------------------------
    # Si la consulta empieza con SELECT, devuelve resultados
    if consulta.strip().upper().startswith("SELECT"):
        resultado = cursor.fetchall()   # Obtiene TODOS los registros
    else:
        # Si es INSERT, UPDATE o DELETE: confirmar cambios en la base de datos
        con.commit()
        resultado = None

    # --------------------------------------------------------
    # PASO 5: Cerrar la conexión de forma segura
    # --------------------------------------------------------
    con.close()

    # --------------------------------------------------------
    # PASO 6: Retornar el resultado (si la base de datos devuelve algo)
    # --------------------------------------------------------
    return resultado