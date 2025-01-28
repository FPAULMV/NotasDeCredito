from urllib.parse import quote_plus 
import sqlalchemy
import pandas as pd
from decouple import config
import sys
# ----------------------------------------------------------------
# CREA UNA CONEXION PARA SOLICITAR CONSULTAS A SQL
# DEVUELVE EL RESULTADO DE LA CONSULTA
def enviar_solicitud(query):
    engine = None
    try:
        conn_str = f"mssql+pymssql://{config('user_name')}:{quote_plus(config('password'))}@{config('server')}/{config('database')}"
        engine = sqlalchemy.create_engine(conn_str)
        resultado = pd.read_sql(query, engine)
    except Exception as e:
        print("Error en la conexión o en la ejecución del query:\n", e)
        if engine:
            engine.dispose()
        sys.exit()
    else:
        return resultado


# ----------------------------------------------------------------
# REALIZA UNA CONSULTA A SQL Y DEVUELVE UNA LISTA DE TODAS LAS FECHAS QUE SE HAN REGISTRADO.
# DEVUELVE UNA LISTA CON TODAS LAS FECHAS REGISTRADAS 
def obtener_fechas_sql():
    msg = f"Obteniendo las fechas existentes"
    print(msg)
    query = "select distinct(Fecha) as Fecha from Sinergia_Aux.dbo.Lista_Precios_Pemex order by fecha desc"
    resultado = enviar_solicitud(query)
    if resultado is not None and not resultado.empty:
        resultado['Fecha'] = pd.to_datetime(resultado['Fecha'])
        return resultado['Fecha'].dt.strftime('%Y-%m-%d').tolist()
    else:
        return []
    

def obtener_destinos_activos():
    query = """select T1.Id AS [ID Portal], T0.client_id, T0.commercial_name, T0.number from NexusFuel.dbo.sale_client AS T0
                INNER JOIN nexusfuel.Portal.ClientUser AS T1 ON  T0.client_id = T1.ClientId 
                ORDER BY T1.Id asc"""
    resultado = enviar_solicitud(query)
    return resultado