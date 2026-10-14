"""
Auditor de Migración de Bases de Datos (ETL Reconciliator)

Este script escanea dinámicamente las estructuras de dos bases de datos MySQL (Origen y Destino),
extrae los registros iterativamente para optimizar el uso de memoria RAM, y cruza la información
para detectar anomalías, modificaciones o pérdida de datos. 

Genera dos entregables: un reporte operativo en formato Excel con el detalle de las discrepancias 
y un reporte ejecutivo en formato PDF.

Autor: Jesús Jafet Fernández Hernández
"""
import os 
from dotenv import load_dotenv
import pandas as pd
from fpdf import FPDF


load_dotenv()

host_origen = os.getenv('DB_HOST_ORIGEN')
bd_origen = os.getenv('DB_NAME_ORIGEN')

host_destino = os.getenv('DB_HOST_DESTINO')
bd_destino = os.getenv('DB_NAME_DESTINO')

print(f"Conexión a BD Origen: {bd_origen} en Host: {host_origen}")
print(f"Conexión a BD Destino: {bd_destino} en Host: {host_destino}")

usuario_origen = os.getenv('DB_USER_ORIGEN')
pass_origen = os.getenv('DB_PASS_ORIGEN')
port_origen = os.getenv('DB_PORT_ORIGEN')

usuario_destino = os.getenv('DB_USER_DESTINO')
pass_destino = os.getenv('DB_PASS_DESTINO')
port_destino = os.getenv('DB_PORT_DESTINO')

print("DATOS DE BD ORIGEN")
print(f"Usuario: {usuario_origen}")
print(f"Puerto: {port_origen}")
print("DATOS DE BD DESTINO")
print(f"Usuario: {usuario_destino}")
print(f"Puerto: {port_destino}")

from sqlalchemy import create_engine, inspect

url_origen = f"mysql+pymysql://{usuario_origen}:{pass_origen}@{host_origen}:{port_origen}/{bd_origen}"
motor_origen = create_engine(url_origen)
try:
    with motor_origen.connect() as conexion:
        print("Base ORIGEN conectado correctamente")
except Exception as e:
    print(f"Error al conectar a la base ORIGEN: {e}")

url_destino = f"mysql+pymysql://{usuario_destino}:{pass_destino}@{host_destino}:{port_destino}/{bd_destino}"
motor_destino = create_engine(url_destino)
try:
    with motor_destino.connect() as conexion:
        print("Base DESTINO conectada correctamente")
except Exception as e:
    print(f"Error al conectarse a la base DESTINO: {e}")

inspector = inspect(motor_origen)
tablas = inspector.get_table_names()

writer = pd.ExcelWriter('Reporte_migracion.xlsx', engine='openpyxl')
resumen = []

for tabla in tablas:
    llave = inspector.get_pk_constraint(tabla)['constrained_columns'][0]
    print(f"Tabla: {tabla} (Llave primaria: {llave})")

    query = f"SELECT * FROM {tabla} ORDER BY {llave}"

    try:
        # Procesamiento en bloques (chunks) para evitar la saturación de la memoria
        iterador_origen = pd.read_sql(query, motor_origen, chunksize=1000)
        iterador_destino = pd.read_sql(query, motor_destino, chunksize=1000)

        bloque = 1
        diferencias_totales=0
        df_diferencias_tabla = pd.DataFrame()

        for chunk_origen, chunk_destino in zip(iterador_origen, iterador_destino):
                chunk_origen['_servidor'] = 'ORIGEN' 
                chunk_destino['_servidor'] = 'DESTINO'
                
                df_unido = pd.concat([chunk_origen, chunk_destino])
            
                columnas_reales = list(chunk_origen.columns)
                columnas_reales.remove('_servidor')
                
                diferencias = df_unido.drop_duplicates(subset=columnas_reales, keep=False)

                if diferencias.empty:
                    print(f"Bloque {bloque}: No hay diferencias encontradas")
                else:
                    print(f"Bloque{bloque}: Se encontraron diferencias en {len(diferencias)} resgistros:")
                    print(diferencias.sort_values(by=llave))
                    diferencias_totales += len(diferencias)
                    df_diferencias_tabla = pd.concat([df_diferencias_tabla, diferencias])
                bloque += 1

        resumen.append({'Tabla': tabla, 'Diferencias': len(diferencias)})

        if diferencias_totales > 0:
            nombre_pestana = tabla[:31]
            df_diferencias_tabla.sort_values(by=llave).to_excel(writer, sheet_name=nombre_pestana, index=False)
              
    except Exception as e:
        print(f"ERROR: No se pudo comprar la tabla '{tabla}'")
        print(f"La Tabla no existe en el destino o hay un problema de estructura")
        resumen.append({'Tabla': tabla, 'Diferencias': 'Error/No existe'})
df_resumen = pd.DataFrame(resumen)
df_resumen.to_excel(writer, sheet_name='Resumen_general', index=False)
writer.close()
print("Reporte en excell generado")

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0,10, 'Reporte de migracion de datos', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')
pdf = PDF()
pdf.add_page()

pdf.set_font("Arial", size=10)
pdf.cell(0, 6, f"Base de Datos Origen: {bd_origen} (Host: {host_origen})", 0, 1)
pdf.cell(0, 6, f"Base de Datos Destino: {bd_destino} (Host: {host_destino})", 0, 1)
pdf.ln(5)

pdf.set_font("Arial", 'B', 10)
pdf.cell(90, 10, 'Tabla destino', 1)
pdf.cell(40, 10, 'Diferencias', 1)
pdf.ln()

pdf.set_font("Arial", size=10)
for fila in resumen:
    tabla_nombre = str(fila['Tabla'])
    diferencias = str(fila['Diferencias'])
    
    pdf.cell(90, 10, tabla_nombre, 1)
    pdf.cell(40, 10, diferencias, 1, align='C')
    pdf.ln()

pdf.output("Reporte_Migracion.pdf")

print("Reporte pdf generado")

        