# Comparador de Bases de Datos

Este script en Python compara dos bases de datos MySQL (origen y destino) para encontrar diferencias, registros faltantes o errores después de una migración.

## Qué hace el script
* Compara todas las tablas de ambas bases de datos automáticamente.
* Lee los datos por bloques para no saturar la memoria de la computadora.
* Genera un reporte en Excel con los registros exactos que tienen diferencias.
* Genera un resumen en PDF con el estado general de la migración.

## Requisitos
* Python 3 instalado.
* Credenciales de acceso a los servidores MySQL de origen y destino.

## Instalación y Configuración

1. Crea y activa un entorno virtual:
   * En Windows:
     python -m venv venv
     .\venv\Scripts\activate
   * En macOS / Linux:
     python3 -m venv venv
     source venv/bin/activate

2. Instala las librerías necesarias:
   pip install -r requirements.txt

3. Configura tus credenciales:
   * Haz una copia del archivo .env.example y renómbrala a .env
   * Abre tu nuevo archivo .env y escribe las IPs, usuarios y contraseñas de tus bases de datos.

## Uso
Con el entorno virtual activado, ejecuta el script en tu terminal:
python comparador.py

Al finalizar, el programa creará los archivos Reporte_Operativo_Migracion.xlsx y Reporte_Ejecutivo_Migracion.pdf en esa misma carpeta.