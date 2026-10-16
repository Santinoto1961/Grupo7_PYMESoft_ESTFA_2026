#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
database.py - Módulo de Persistencia de Datos
ÚNICA función que interactúa con SQLite3: query().
"""

import sqlite3


def query(consulta, parametros=()):
    """
    Ejecuta una consulta SQL.
    - SELECT: devuelve lista de tuplas.
    - INSERT/UPDATE/DELETE: hace commit y devuelve None.
    La conexión SIEMPRE se cierra (aunque falle la consulta),
    así no queda la base bloqueada ("database is locked").
    """
    con = sqlite3.connect("database.db", timeout=10)
    try:
        cursor = con.cursor()
        cursor.execute(consulta, parametros)

        if consulta.strip().upper().startswith("SELECT"):
            return cursor.fetchall()

        con.commit()
        return None
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()