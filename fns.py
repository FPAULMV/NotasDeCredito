import os
import zipfile
import xml.etree.ElementTree as ET
import sys
import re
import pandas as pd
import sqlalchemy
import pyodbc
from decouple import config
from urllib.parse import quote_plus 


class SqlResources():
    """
    ----------------------------------------------------------------
    Alojamiento de recursos para Sql y sus funciones.
    """

    def __init__(self):
        self.registred_nc = self.query_sql("SELECT DISTINCT([CreditNoteNumber]) FROM [Sinergia_Aux].[dbo].[CreditNoteVendor]")


    def query_sql(self, query):
      """
      Realiza consultas a SQL.
      """
      engine = None
      try:
          conn_str = f"mssql+pymssql://{config('user_name')}:{quote_plus(config('password'))}@{config('server')}/{config('database')}"
          engine = sqlalchemy.create_engine(conn_str)
          resultado = pd.read_sql(query, engine)
      except Exception as e:
          print("Error en la conexión o en la ejecución del query:\n", e)
          if engine:
              engine.dispose()
      else:
          return resultado
    

    def insert_sql(self, query):
        """
        Inserta datos en SQL. 
        """
        try:
            conn_str = (
                f"DRIVER={config('driver')};"
                f"SERVER={config('server')};"
                f"DATABASE={config('database')};"
                f"UID={config('user_name')};"
                f"PWD={config('password')}"
            )
            with pyodbc.connect(conn_str) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query)
                    conn.commit()
        except pyodbc.Error as e:
            print("Error en la conexión o en la ejecución del query:", e)
        except Exception as e:
            print("Ocurrió un error inesperado:", e)
        else:
            conn.close()