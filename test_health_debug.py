#!/usr/bin/env python3
"""
Script para probar y debuggear el health check endpoint
"""

import requests
import json
import time

def test_health_check():
    """Prueba el endpoint /api/health con debugging"""
    
    # Probar localmente
    url = 'http://localhost:5000/api/health'
    
    print(f" Probando health check en: {url}")
    print(f" Timestamp: {int(time.time())}")
    print()
    
    try:
        print(" Enviando petición GET...")
        response = requests.get(url, timeout=10)
        
        print(f" Status Code: {response.status_code}")
        print(f" Headers: {dict(response.headers)}")
        print()
        
        try:
            data = response.json()
            print(" Response JSON:")
            print(json.dumps(data, indent=2))
        except json.JSONDecodeError:
            print(" Response (no JSON):")
            print(response.text)
        
        print()
        
        if response.status_code == 200:
            print(" Health check funcionando correctamente")
            
            # Verificar campos esperados
            if isinstance(data, dict):
                if data.get('status') == 'healthy':
                    print(" Status: healthy")
                else:
                    print(f" Status inesperado: {data.get('status')}")
                
                if 'timestamp' in data:
                    print(f" Timestamp: {data['timestamp']}")
                
                if 'service' in data:
                    print(f" Service: {data['service']}")
                
                if 'environment' in data:
                    print(f" Environment: {data['environment']}")
        else:
            print(f" Error en health check: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print(" Error: No se puede conectar al servidor local")
        print(" Asegúrate de que la app esté corriendo en http://localhost:5000")
        print(" Ejecuta: python app.py")
    except requests.exceptions.Timeout:
        print(" Error: Timeout de la petición")
    except Exception as e:
        print(f" Error inesperado: {str(e)}")

def test_with_curl():
    """Prueba usando curl para debugging"""
    import subprocess
    
    print("\n" + "="*50)
    print(" Prueba con curl:")
    print("="*50)
    
    try:
        result = subprocess.run([
            'curl', '-v', 'http://localhost:5000/api/health'
        ], capture_output=True, text=True, timeout=10)
        
        print(" STDOUT:")
        print(result.stdout)
        print("\n STDERR:")
        print(result.stderr)
        print(f"\n Return code: {result.returncode}")
        
    except subprocess.TimeoutExpired:
        print(" Timeout con curl")
    except FileNotFoundError:
        print(" curl no encontrado")
    except Exception as e:
        print(f" Error con curl: {e}")

if __name__ == '__main__':
    print(" Test Health Check Debug")
    print("="*50)
    
    test_health_check()
    test_with_curl()
    
    print("\n" + "="*50)
    print(" Para iniciar la app localmente:")
    print(" python app.py")
    print("="*50)
