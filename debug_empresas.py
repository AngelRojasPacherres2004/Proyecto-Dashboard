
"""Script de diagnóstico para admin_empresas"""

import sys
sys.path.insert(0, '.')

from config.db import get_connection

print("=" * 60)
print("DIAGNÓSTICO: admin_empresas.py")
print("=" * 60)

try:
    # 1. Intentar conexión
    print("\n1️⃣ Probando conexión a BD...")
    conn = get_connection()
    print("   ✅ Conexión exitosa")
    
    # 2. Ver tablas disponibles
    print("\n2️⃣ Tablas disponibles:")
    cur = conn.cursor()
    cur.execute("SHOW TABLES")
    tablas = cur.fetchall()
    for tabla in tablas:
        print(f"   - {tabla}")
    
    # 3. Verificar tabla empresas
    print("\n3️⃣ Verificando tabla 'empresas':")
    try:
        cur.execute("SELECT COUNT(*) as total FROM empresas")
        resultado = cur.fetchone()
        total = resultado.get('total') if isinstance(resultado, dict) else resultado[0]
        print(f"   ✅ Tabla existe - Total de empresas: {total}")
        
        if total == 0:
            print("   ⚠️  La tabla está VACÍA. Necesitas insertar datos de prueba.")
        else:
            # Ver estructura
            cur.execute("DESCRIBE empresas")
            columnas = cur.fetchall()
            print(f"\n   Columnas de la tabla:")
            for col in columnas:
                print(f"     - {col}")
            
            # Ver datos de prueba
            print(f"\n   Primeros registros:")
            cur.execute("SELECT id, alias, razon_social, ruc FROM empresas LIMIT 3")
            datos = cur.fetchall()
            for dato in datos:
                print(f"     {dato}")
    
    except Exception as e:
        print(f"   ❌ Tabla no existe: {e}")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {e}")
    print("\nPosibles causas:")
    print("- BD no está corriendo")
    print("- Credenciales incorrectas en .env")
    print("- BD no existe")

print("\n" + "=" * 60)
