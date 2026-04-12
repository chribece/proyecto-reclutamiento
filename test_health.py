#!/usr/bin/env python3
"""
Script para probar el health check endpoint
"""

import requests
import json

def test_health_check():
    """Prueba el endpoint /api/health"""
    
    # Probar localmente
    try:
        response = requests.get('http://localhost:5000/api/health', timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print(" Health check funcionando correctamente")
        else:
            print(" Error en health check")
            
    except requests.exceptions.ConnectionError:
        print(" Error: No se puede conectar al servidor local")
        print(" Asegúrate de que la app esté corriendo en http://localhost:5000")
    except Exception as e:
        print(f" Error inesperado: {str(e)}")

if __name__ == "__main__":
    test_health_check()
