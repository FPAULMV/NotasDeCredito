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
from typing import Dict
import json


class Systempath():
    """
    ----------------------------------------------------------------
    Alojamiento de recursos relacionados al systema.
    """
    def __init__(self):
        """
        ----------------------------------------------------------------
        Con 'self.path_base' Define la ruta desde donde iniciara la busqueda
        recursiva de los documentos. 
        Con 'self.files' se obtiene las rutas de todos los archivos que se deben
        leer.
        """
        self.path_base = r"C:\Users\AdminTI\Sinergia\PETRODIESEL - 2025\ENERO 2"
        self.files = self.path_files(self.path_base)

    def path_files(self, ruta_base: str) -> list:
        """
        Lee recursivamente todos los directorios y subdirectorios a partir de una ruta base,
        y guarda las rutas completas de los archivos encontrados en una lista.
        
        Args:
            ruta_base (str): La ruta base desde donde iniciar la búsqueda.
        
        Returns:
            list: Lista de rutas completas de los archivos encontrados.
        """
        _files = []
        for root, _, files in os.walk(ruta_base):
            for file in files:
                _files.append(os.path.join(root, file))
        return _files
    
    def filter_extension(self, path_list: list, ext: str) -> bool:
        """
        Filra segun la extencion proporcionada una lista de archivos y devuelve
        una lista con los archivos que coincidan con la extencion. 
        Args:
            files (list): Lista de archivos a filtrar.
            ext (str): Extencion, como parametro para el filtro.
        Return: 
            Lista de rutas que coinciden con la extencion proporcionada.
        """
        returned_path = []
        for path in path_list:
            if str(path).lower().endswith(ext) == True:
                returned_path.append(path)
            
        return returned_path
        

class SqlResources():
    """
    ----------------------------------------------------------------
    Alojamiento de recursos para Sql y sus funciones.
    """

    def __init__(self):
        self.query_nc = f"SELECT DISTINCT([CreditNoteNumber]) FROM [Sinergia_Aux].[dbo].[CreditNoteVendor]"
        self.registred_nc = SqlResources.query_sql(self.query_nc)


    def query_sql(query):
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
                
            print(f"Script Finalizado.")
            exit()
      else:
          return resultado
    

    def insert_sql(data: list[Dict[str, any]]):
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
                    batch_size = 1000  # Máximo permitido por SQL Server
                    for i in range(0, len(data), batch_size):
                        batch =data[i:i + batch_size]
                        values = ", ".join([
                            f"({d['vendorid']}, {d['stationid']}, '{d['fecha']}', '{d['description']}', '{d['invoice']}', '{d['rel']}', "
                            f"'{d['creditnotenumber']}', '{d['tad']}', {float(d['importe'])}, {float(d['total'])}, {d['destinationid']}, '{d['uuid']}')"
                            for d in batch
                        ])

                        query = f"""
                        INSERT INTO SINERGIA_AUX.DBO.CreditNoteVendor 
                        (VendorId, StationId, Date, ProductName, Remision, Invoice, CreditNoteNumber, TarTad, Tax, Total, DestinationName, FiscalFolio)
                        VALUES {values}"""

                    cursor.execute(query)
                    conn.commit()
                    msg = "Datos ingresados correctamente."
                    print(msg)
                    return msg
                
        except pyodbc.Error as e:
            print("Error en la conexión o en la ejecución del query:", e)
        except Exception as e:
            print("Ocurrió un error inesperado:", e)

    def insert_sql_exec(data: list[Dict[str, any]]):
        """
        Inserta datos en SQL ejecutando un procedimiento almacenado.
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
                    for d in data:
                        query = f"""
                        EXEC NexusFuel_PetroDiesel.Operation.StpCreditNoteVendorSave
                            @vendorId = '{d['vendorid']}',
                            @stationId = '{d['stationid']}',
                            @date = '{d['fecha']}',
                            @productName = '{d['description']}',
                            @remision = '{d['rel']}',
                            @invoice = '{d['invoice']}',
                            @creditNoteNumber = '{d['creditnotenumber']}',
                            @tarTad = '{d['tad']}',
                            @tax = {float(d['importe'])},
                            @total = {float(d['total'])},
                            @destinationName = '{d['destinationid']}',
                            @FiscalFolio = '{d['uuid']}'
                        """
                        cursor.execute(query)
                        conn.commit()

                    msg = "Datos ingresados correctamente."
                    print(msg)
                    return msg
                    
        except pyodbc.Error as e:
            print("Error en la conexión o en la ejecución del query:", e)
        except Exception as e:
            print("Ocurrió un error inesperado al ejecutar el EXEC:", e)



class Processing():
    """
    ----------------------------------------------------------------
    Alojamiento de funciones realcionadas a el procesamiento de documentos
    """

    def parse_xml(xmlstring: str, df: pd.DataFrame) -> Dict[str, any]:
        """
        ----------------------------------------------------------------
        Valida la informacion de un .XML y devuelve un diccionario con
        ciertos valores.
        """

        try:
            root = ET.fromstring(xmlstring)

            # Definir namespace
            namespaces = {
                "cfdi": "http://www.sat.gob.mx/cfd/4",
                "tfd": "http://www.sat.gob.mx/TimbreFiscalDigital",
                "pm": "http://pemex.com/facturaelectronica/addenda/v2"
            }

            # Valores
            tipodecomprobante = root.attrib.get("TipoDeComprobante")
            fecha = root.attrib.get("Fecha")[:10]
            total = root.attrib.get("Total")
            creditnotenumber = root.attrib.get("Serie") + "-" + root.attrib.get("Folio")


            if tipodecomprobante != "E":
                #print("El 'TipoDeComprobante' es diferente de 'E'")
                return None
            
            if creditnotenumber in df['CreditNoteNumber'].values:
                print(f"El creditnotenumber '{creditnotenumber}' ya existe en el DataFrame.")
                return None
            else:
                print(f"El NC: {creditnotenumber} NO SE HA REGISTRADO.")

            print(creditnotenumber)
            
            conceptos = root.find("cfdi:Conceptos", namespaces)
            if conceptos is not None:
                for concepto in conceptos.findall("cfdi:Concepto", namespaces):
                    description = concepto.get("Descripcion")
            else:
                print("No se encontró el nodo cfdi:Conceptos")
                return
            
            remision = root.find(".//pm:NREMISION", namespaces)
            if remision is not None:
                #rem = re.search(r"(\d+)$", remision.text.replace("  ", "")).group(1)
                tad = re.search(r"RC-(\d+)", remision.text.replace("  ", "")).group(1)
            else:
                print("No se encontró el nodo pm:NREMISION")
                return

            relacion = root.find(".//pm:A_RELACION", namespaces)
            if relacion is not None:
                rel = re.search(r"(\d+)$", relacion.text.replace("  ", "")).group(1)
            else:
                print("No se encontró el nodo pm:A_RELACION")
                return

            traslado = root.find(".//cfdi:Traslado", namespaces)
            if traslado is not None:
                importe = traslado.attrib.get("Importe")
            else:
                print("No se encontró el nodo .//cfdi:Traslado")
                return

            timbre = root.find(".//tfd:TimbreFiscalDigital", namespaces)
            if timbre is not None:
                uuid = timbre.attrib.get("UUID")
            else:
                print("No se encontró el nodo .//tfd:TimbreFiscalDigital")
                return

            _query = f"""SELECT invoice AS [Invoice], DestinationId AS [ID] 
                        FROM NexusFuel_PetroDiesel.dbo.opr_fuelpurchase 
                        WHERE remision = '{rel}' and tar_tad = '{tad}'"""
            

            df = SqlResources.query_sql(_query)
            if df.empty:
                print(f"La Remisión: {rel} no devolvió un 'DestinationId' válido.")
                return
            
            destinationid = df['ID'].values[0]
            invoice = df['Invoice'].values[0]

            dc = {
                "vendorid": 1,  # Reemplaza con el valor correspondiente si aplica
                "stationid": 44,  # Reemplaza con el valor correspondiente si aplica
                "fecha": fecha,
                "description": description,
                "rel": rel,
                "invoice": invoice,
                "creditnotenumber": creditnotenumber,
                "tad": tad,
                "importe": importe,
                "total": total,
                "destinationid": destinationid,  # Reemplaza con el valor correspondiente si aplica
                "uuid": uuid
            }
        
            print(f"Los siguientes datos fueron encontrados en el xml:")
            print(f'''"fecha": {fecha},
            "description": {description},
            "rel": {rel},
            "invoice": {invoice}, 
            "creditnotenumber": {creditnotenumber},
            "tad": {tad},
            "importe": {importe},
            "total": {total},
            "destinationid": {destinationid},
            "uuid": {uuid}.
            ''')

            return(dc)

        except ET.ParseError:
            print("Error al analizar el XML. Verifica el formato del archivo.")
            return





"""
EXEC Operation.StpCreditNoteVendorSave
    @vendorId = 6432,
    @stationId = 4, 
    @date = '2024-04-30', 
    @productName = 'RECUPERACION DE FLETE', 
	@remision = '74708',
    @invoice = 'NCP-1377', 
    @creditNoteNumber = 'NCP-1377', 
    @tarTad = '629', 
    @tax = 1240.97, 
    @total = 8997.06,
    @destinationName = 'Destino-206 E04055', 
    @FiscalFolio = '4B7B75EA-E368-49FD-9D5A-C9A3673D3814'
GO
"""