#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================
session.py - Estado Global de Sesión (Singleton)
============================================================
Módulo que actúa como estado global singleton para almacenar
los datos del usuario autenticado. Cualquier módulo puede
importar `session` y consultar el rol activo.

Uso:
    from session import session
    if session.is_admin():
        # Mostrar funciones de administrador

Autor: yo
Fecha: 2026-07-02
============================================================
"""


class SessionManager:
    """
    Singleton que gestiona el estado de la sesión del usuario.
    Almacena: id, usuario, nombre, rol y estado de autenticación.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SessionManager, cls).__new__(cls)
            cls._instance._reset()
        return cls._instance

    def _reset(self):
        """Reinicia todos los valores de la sesión."""
        self._autenticado = False
        self._id_usuario = None
        self._usuario = None
        self._nombre = None
        self._rol = None  # 'administrador' o 'empleado'

    # ============================================================
    # MÉTODOS PÚBLICOS: Iniciar / Cerrar sesión
    # ============================================================

    def iniciar_sesion(self, id_usuario, usuario, nombre, rol):
        """
        Establece los datos del usuario tras un login exitoso.
        """
        self._autenticado = True
        self._id_usuario = id_usuario
        self._usuario = usuario
        self._nombre = nombre
        self._rol = rol.lower().strip() if rol else None

    def cerrar_sesion(self):
        """
        Limpia todos los datos de la sesión (logout).
        """
        self._reset()

    # ============================================================
    # PROPIEDADES DE LECTURA
    # ============================================================

    @property
    def autenticado(self):
        return self._autenticado

    @property
    def id_usuario(self):
        return self._id_usuario

    @property
    def usuario(self):
        return self._usuario

    @property
    def nombre(self):
        return self._nombre

    @property
    def rol(self):
        return self._rol

    # ============================================================
    # MÉTODOS DE UTILIDAD PARA ROLES
    # ============================================================

    def is_admin(self):
        """Devuelve True si el usuario es administrador."""
        return self._rol == "administrador"

    def is_empleado(self):
        """Devuelve True si el usuario es empleado."""
        return self._rol == "empleado"

    def get_info(self):
        """Devuelve un diccionario con toda la info de la sesión."""
        return {
            "autenticado": self._autenticado,
            "id_usuario": self._id_usuario,
            "usuario": self._usuario,
            "nombre": self._nombre,
            "rol": self._rol,
        }


# ============================================================
# INSTANCIA GLOBAL ÚNICA
# ============================================================
# Importar esta variable en cualquier archivo:
#     from session import session
# ============================================================
session = SessionManager()