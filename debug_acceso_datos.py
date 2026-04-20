#!/usr/bin/env python
"""Simular ejecución de admin_empresas para identificar el error"""

import sys
sys.path.insert(0, '.')

from config.db import get_connection

print("Simulando admin_empresas()...\n")

try:
    # Simular _get_empresas()
    print("1️⃣ Obteniendo empresas...")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, alias, razon_social, ruc,
            regimen_tributario, regimen_laboral,
            estado_contrato, correo_principal,
            giro_negocio, fecha_registro
        FROM empresas
        ORDER BY razon_social
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    print(f"   ✅ Obtenidas {len(rows)} empresas")
    print(f"   Tipo de datos: {type(rows[0])}")
    print(f"   Primer registro: {rows[0]}\n")
    
    # Simular acceso a datos como lo hace admin_empresas
    print("2️⃣ Probando acceso a datos...")
    for i, e in enumerate(rows[:2]):
        try:
            print(f"\n   Empresa {i+1}:")
            print(f"     razon_social: {e['razon_social']}")
            print(f"     ruc: {e['ruc']}")
            print(f"     alias: {e['alias']}")
            print(f"     regimen_tributario: {e.get('regimen_tributario')}")
            print(f"     estado_contrato: {e.get('estado_contrato')}")
        except KeyError as ke:
            print(f"   ❌ KeyError: {ke}")
            print(f"      Claves disponibles: {list(e.keys())}")
        except Exception as ex:
            print(f"   ❌ Error: {ex}")
    
    print("\n✅ No hay errores. El problema está en Streamlit o en la interfaz.")
    
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
