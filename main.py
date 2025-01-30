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

class GetPath():
  def __init__(self):
    """
    ----------------------------------------------------------------
    Con 'self.path_base' Define la ruta desde donde iniciara la busqueda
    recursiva de los documentos. 
    Con 'self.files' se obtiene las rutas de todos los archivos que se deben
    leer.
    """
    self.path_base = r"C:\Users\AdminTI\Sinergia\PETRODIESEL - 2025"
    self.files = self.path_files(self.path_base)
    self.registred_nc = self.query_sql("SELECT DISTINCT([CreditNoteNumber]) FROM [Sinergia_Aux].[dbo].[CreditNoteVendor]")
    

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
    print(_files)
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
  

  def parse_xml(self, xmlstring: str):
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

        if tipodecomprobante != "E":
            #print("El 'TipoDeComprobante' es diferente de 'E'")
            return  # Salta este archivo y continúa con el siguiente

        conceptos = root.find("cfdi:Conceptos", namespaces)
        if conceptos is not None:
            for concepto in conceptos.findall("cfdi:Concepto", namespaces):
                description = concepto.get("Descripcion")
        else:
            print("No se encontró el nodo cfdi:Conceptos")
            return  # Salta este archivo

        remision = root.find(".//pm:NREMISION", namespaces)
        if remision is not None:
            rem = re.search(r"(\d+)$", remision.text.replace("  ", "")).group(1)
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

        total = root.attrib.get("Total")

        timbre = root.find(".//tfd:TimbreFiscalDigital", namespaces)
        if timbre is not None:
            uuid = timbre.attrib.get("UUID")
        else:
            print("No se encontró el nodo .//tfd:TimbreFiscalDigital")
            return

        query = f"""SELECT invoice AS [Invoice], DestinationId AS [ID] 
                    FROM NexusFuel_PetroDiesel.dbo.opr_fuelpurchase 
                    WHERE remision = '{rel}'"""
        df = self.query_sql(query)
        if df.empty:
            print(f"La Remisión: {rem} no devolvió un 'DestinationId' válido.")
            return

        destinationid = df['ID'].values[0]
        creditnotenumber = root.attrib.get("Serie") + "-" + root.attrib.get("Folio")

        insert = f"""INSERT INTO SINERGIA_AUX.DBO.CreditNoteVendor (
            VendorId, StationId, Date, ProductName, Remision, Invoice, CreditNoteNumber, TarTad, Tax, Total, DestinationName, FiscalFolio )
            VALUES (1,44,'{fecha}','{description}','{rem}','{rel}','{creditnotenumber}','{tad}',{importe},{total},'{destinationid}','{uuid}');"""
        self.insert_sql(insert)
        print(f"Datos Insertados en la tabla.\n")

    except ET.ParseError:
        print("Error al analizar el XML. Verifica el formato del archivo.")
        return
    except Exception as e:
        print(f"Se produjo un error inesperado: {e}")
        return





if __name__ == '__main__':
  path = GetPath()

  path_base = path.files
  zip_files = path.filter_extension(path_base, ".zip")
  xml_files = path.filter_extension(path_base, ".xml")

  for zip in zip_files:
    print(f"Trabajando con el archivo zip: \n{zip}")
    with zipfile.ZipFile(zip, "r") as zip:
      for file in zip.namelist():
        if file.lower().endswith(".xml"):
          #print(f"Trabajando con el archivo: \n{file}")
          with zip.open(file, "r") as xml_file:
            xml = xml_file.read().decode("utf-8")
            path.parse_xml(xml)

  print("--------")

  for xml in xml_files:
    print(xml)



     
     



