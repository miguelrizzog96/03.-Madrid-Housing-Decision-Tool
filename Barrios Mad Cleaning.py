# -*- coding: utf-8 -*-
"""
Created on Sat Jan 20 11:01:48 2024

@author: migue
"""
#%%
#Import libraries
import geopandas as gpd
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re

#reading input files
paths=[r"poblacion_1_enero.csv",
       r"Barrios\Barrios.shp",
       r"Distritos\Distritos_20210712.shp",
       r"Ranking barrios - Hoja 1.csv"]

barrios_shp,distritos_shp,rankings,poblacion = gpd.read_file(paths[1]),gpd.read_file(paths[2]),pd.read_csv(paths[3],delimiter=","),pd.read_csv(paths[0],delimiter=";")

poblacion=poblacion.loc[(poblacion['fecha']=="1 de enero de 2023") & (poblacion['barrio']!=poblacion['distrito'])]
# URL of the Wikipedia page
url = "https://es.wikipedia.org/wiki/Anexo:Barrios_administrativos_de_Madrid"

# Send a GET request to the URL
response = requests.get(url)

# Check if the request was successful (status code 200)
if response.status_code == 200:
    # Parse the HTML content of the page
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the table on the page
    table = soup.find('table', {'class': 'wikitable'})

    # Extract data from the table and create a list of dictionaries
    data = []
    headers = []
    for row_idx, row in enumerate(table.find_all('tr')):
        cells = row.find_all(['th', 'td'])
        if row_idx == 0:
            # Header row
            headers = [re.sub(r'\W+', '', cell.text.strip()) for cell in cells ][1:-1]
        else:
            # Data rows
            row_data = [re.sub(r'\W+', ' ', cell.text.replace('\xa0', ' ').strip()) for cell in cells][:-1]
            if len(row_data)==4:
                row_data.pop(0)
            data.append(dict(zip(headers, row_data)))

    # Convert the list of dictionaries to a DataFrame
    areas = pd.DataFrame(data, index=None)

else:
    print(f"Failed to retrieve the page. Status code: {response.status_code}")

#%%
def remove_non_numeric(value):
    return float(''.join(c for c in value if c.isdigit()).strip('²'))/1000

# Apply the function to the 'Nombre' column

areas['Superficiekm²2'] = areas['Superficiekm²2'].apply(remove_non_numeric)
#%%

# Define the function to add space before capitalized letters
def add_spaces_to_series(series):
    result_series = []
    for s in series:
        result_series.append(add_space(s))
    return result_series

def add_space(s):
    result = []
    i = 0
    while i < len(s):
        # Check for "de" or "del" before a capitalized letter
        if i + 2 < len(s) and s[i:i + 2].lower() == 'de' and i + 3 < len(s) and s[i + 2].isupper():
            result.append(' ')
        elif i + 3 < len(s) and s[i:i + 3].lower() == 'del' and i + 4 < len(s) and s[i + 3].isupper():
            result.append(' ')
        
        # Add space before capitalized letters
        if i > 0 and s[i].isupper() and not s[i - 1].isspace():
            result.append(' ')
        
        result.append(s[i])
        i += 1
    
    return ''.join(result)
poblacion['barrio']= add_spaces_to_series(poblacion['barrio'])
barrios_shp.columns.values
rankings.columns.values
distritos_shp.columns.values
poblacion.columns.values
areas.columns.values


def procesar_serie(serie):
    def reemplazar_vocales_con_acento(texto):
        # Definir un diccionario con las vocales con acento y sus correspondientes sin acento
        reemplazos = {'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u'}
        
        # Aplicar los reemplazos en el texto
        for vocal_acentuada, vocal_sin_acento in reemplazos.items():
            texto = texto.lower().replace(vocal_acentuada, vocal_sin_acento)
            # Reemplazar "LOS, EL, ETC."
            texto= re.sub('^(e|l).* ','',texto.lower()).replace('palos de moguer','palos de la frontera').replace('san andres','villaverde alto')
            texto= re.sub('^.+ casco historico de villaverde','villaverde alto',texto.lower()) 
        return texto

    # Aplicar la función de reemplazo y convertir a mayúsculas
    serie_procesada = serie.apply(lambda x: reemplazar_vocales_con_acento(x).upper())
    
    return serie_procesada

barrios_shp["NOMDIS"]= procesar_serie(barrios_shp["NOMDIS"])
rankings['Barrio']=procesar_serie(rankings['Barrio'])
poblacion['barrio']=procesar_serie(poblacion['barrio'])
areas['Nombre']=procesar_serie(areas['Nombre'])
barrios_shp["BARRIO_MAY"]= procesar_serie(barrios_shp["BARRIO_MAY"])

#%%
#renaming columns
rankings=rankings.rename(columns={'Barrio':'barrio'})
barrios_shp=pd.DataFrame(barrios_shp.rename(columns={'BARRIO_MAY':'barrio','NOMDIS':'distrito'}))
areas=areas.rename(columns={'Nombre':'barrio'})
distritos_shp=pd.DataFrame(distritos_shp.rename(columns={'DISTRI_MAY':'distrito'}))


final_output = pd.merge(pd.merge(rankings, areas, on='barrio', how='outer'),
                         pd.merge(barrios_shp, poblacion, on='barrio', how='outer'), on='barrio', how='outer')
final_output.rename(columns={'distrito_x':'distrito'},inplace=True)
final_output=pd.merge(final_output,distritos_shp, on='distrito',how='outer')
distinct_names= []

for i in [areas,rankings,barrios_shp,poblacion]:
    for j in i['barrio']:
        distinct_names.append(j)
distinct_names=pd.Series(pd.Series(distinct_names).unique()).sort_values()

final_output=final_output[final_output['barrio']!="AMBROZ"] # ya no existe
