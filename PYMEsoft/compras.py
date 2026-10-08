#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================
compras.py - Historial de Compras / Importaciones a Proveedores
============================================================
Módulo SIN interfaz gráfica. Toda la persistencia de compras
pasa por aquí y, a su vez, TODO acceso a SQLite pasa por
`database.query()` (la única función que toca la base).

Modelo de datos
---------------
compras            1 fila por cada Excel importado (cabecera)
detalle_compras    1 fila por cada producto de ese Excel

    proveedores 1 ──< compras 1 ──< detalle_compras >── 1 productos

Regla de oro del Balance
------------------------
GASTO EN MERCADERÍA = SUM(compras.monto_total)   (lo que SALIÓ
de la caja al comprar), NO el costo de lo vendido.

Notas de diseño
---------------
* `proveedor_nombre` y `nombre_producto` se guardan como
  "foto" (snapshot): si después se renombra o borra el
  proveedor/producto, el historial contable no se rompe.
* SQLite no aplica claves foráneas salvo PRAGMA foreign_keys=ON
  (database.query no lo activa), por eso el snapshot es necesario.
* `lote` es un identificador único por importación; se usa para
  recuperar el id de la cabecera recién insertada, ya que
  query() no devuelve lastrowid.
============================================================
"""

import uuid
from datetime import datetime

from database import query


# ============================================================
# CREACIÓN DE TABLAS (idempotente)
# ============================================================

def crear_tablas_compras():
    """Crea las tablas del historial de compras si todavía no existen."""
    query("""
        CREATE TABLE IF NOT EXISTS compras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_proveedor INTEGER,
            proveedor_nombre TEXT,
            fecha TEXT NOT NULL,
            archivo TEXT,
            lote TEXT NOT NULL UNIQUE,
            cantidad_items INTEGER NOT NULL DEFAULT 0,
            cantidad_unidades INTEGER NOT NULL DEFAULT 0,
            monto_total REAL NOT NULL DEFAULT 0,
            FOREIGN KEY (id_proveedor)
                REFERENCES proveedores(id)
                ON UPDATE CASCADE
                ON DELETE SET NULL
        )
    """)
    query("""
        CREATE TABLE IF NOT EXISTS detalle_compras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_compra INTEGER NOT NULL,
            id_producto INTEGER,
            nombre_producto TEXT NOT NULL,
            cantidad INTEGER NOT NULL,
            precio_unitario REAL NOT NULL,
            subtotal REAL NOT NULL,
            FOREIGN KEY (id_compra)
                REFERENCES compras(id)
                ON UPDATE CASCADE
                ON DELETE CASCADE
        )
    """)
    query("CREATE INDEX IF NOT EXISTS idx_compras_fecha ON compras(fecha)")
    query("CREATE INDEX IF NOT EXISTS idx_compras_prov ON compras(id_proveedor)")
    query("CREATE INDEX IF NOT EXISTS idx_detalle_compra ON detalle_compras(id_compra)")


# ============================================================
# ESCRITURA
# ============================================================

def calcular_monto_compra(productos):
    """
    Monto total de una compra = SUM(cantidad * precio_compra).
    `productos` es la lista de dicts que devuelve stock._procesar_excel().
    """
    return round(sum(p["cantidad"] * p["precio_compra"] for p in productos), 2)


def existe_compra_similar(id_proveedor, archivo, monto_total):
    """
    True si ya se importó el mismo archivo, del mismo proveedor y con el
    mismo monto (posible importación duplicada). Sirve solo para avisar.
    """
    res = query(
        "SELECT COUNT(*) FROM compras "
        "WHERE id_proveedor = ? AND archivo = ? AND ABS(monto_total - ?) < 0.005",
        (id_proveedor, archivo, monto_total),
    )
    return bool(res and res[0][0] > 0)


def registrar_compra(id_proveedor, archivo, productos):
    """
    Guarda la cabecera + el detalle de una importación.

    productos: lista de dicts con claves
        nombre, cantidad, precio_compra y (opcional) id_producto.

    Retorna (id_compra, monto_total).
    """
    crear_tablas_compras()

    prov = query("SELECT nombre FROM proveedores WHERE id = ?", (id_proveedor,))
    proveedor_nombre = prov[0][0] if prov else None

    monto_total = calcular_monto_compra(productos)
    unidades = sum(int(p["cantidad"]) for p in productos)
    lote = uuid.uuid4().hex[:12]
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    query(
        """INSERT INTO compras
           (id_proveedor, proveedor_nombre, fecha, archivo, lote,
            cantidad_items, cantidad_unidades, monto_total)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (id_proveedor, proveedor_nombre, fecha, archivo, lote,
         len(productos), unidades, monto_total),
    )
    id_compra = query("SELECT id FROM compras WHERE lote = ?", (lote,))[0][0]

    for p in productos:
        subtotal = round(p["cantidad"] * p["precio_compra"], 2)
        query(
            """INSERT INTO detalle_compras
               (id_compra, id_producto, nombre_producto, cantidad,
                precio_unitario, subtotal)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (id_compra, p.get("id_producto"), p["nombre"],
             int(p["cantidad"]), float(p["precio_compra"]), subtotal),
        )

    return id_compra, monto_total


# ============================================================
# LECTURA
# ============================================================

def obtener_compras_proveedor(id_proveedor):
    """Lista de (id, fecha, archivo, items, unidades, monto), la más nueva primero."""
    return query(
        """SELECT id, fecha, archivo, cantidad_items, cantidad_unidades, monto_total
           FROM compras
           WHERE id_proveedor = ?
           ORDER BY fecha DESC, id DESC""",
        (id_proveedor,),
    ) or []


def obtener_detalle_compra(id_compra):
    """Lista de (producto, cantidad, precio_unitario, subtotal)."""
    return query(
        """SELECT nombre_producto, cantidad, precio_unitario, subtotal
           FROM detalle_compras
           WHERE id_compra = ?
           ORDER BY id""",
        (id_compra,),
    ) or []


def obtener_compras_por_proveedor(inicio, fin):
    """
    Compras del período [inicio, fin) agrupadas por proveedor.
    Retorna lista de (proveedor, cantidad_de_compras, monto_total).
    """
    return query(
        """SELECT COALESCE(pr.nombre, c.proveedor_nombre, 'Sin proveedor'),
                  COUNT(c.id),
                  COALESCE(SUM(c.monto_total), 0)
           FROM compras c
           LEFT JOIN proveedores pr ON pr.id = c.id_proveedor
           WHERE c.fecha >= ? AND c.fecha < ?
           GROUP BY c.id_proveedor, c.proveedor_nombre
           ORDER BY 3 DESC""",
        (inicio, fin),
    ) or []
