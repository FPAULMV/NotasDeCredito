from fns import SqlResources, Systempath, Processing
import zipfile


if __name__ == '__main__':

    creditnotes = SqlResources()
    path = Systempath()
    print(f"Las notas de credito registradas son:\n{creditnotes.registred_nc}")
    zip_files = path.filter_extension(path.files, ".zip")
    xml_files = path.filter_extension(path.files, ".xml") 

    xml_to_sql = []

    for zip in zip_files:
        print(f"Trabajando con el archivo zip: \n{zip}")
        with zipfile.ZipFile(zip, "r") as zip:
            for file in zip.namelist():
                if file.lower().endswith(".xml"):
                    print(f"Trabajando con el archivo: \n{file}")
                    with zip.open(file, "r") as xml_file:
                        xml = xml_file.read().decode("utf-8")
                        datos_xml = Processing.parse_xml(xml, creditnotes.registred_nc)
                        
                        if isinstance(datos_xml, dict):
                            xml_to_sql.append(datos_xml)
                        else:
                            #print(f"Warning: El archivo {file} no generó datos válidos.")
                            pass

    print(f"\nLos datos encontrados fueron:\n{xml_to_sql}")

    print("Insertando datos en la tabla.")
    SqlResources.insert_sql(xml_to_sql)
    print("Listo, datos insertados.")
    print("Ejecutando EXEC.")
    SqlResources.insert_sql_exec(xml_to_sql)
    print("Listo, EXEC ejecutado.")
    
    print(f"Script Finalizado.")



