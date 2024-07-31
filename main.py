# importacion de fastapi
from fastapi import FastAPI, Form, Request
from fastapi import Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import date
import psycopg2
from psycopg2 import sql
import pandas as pd
from config import Config

# importacion para dash 
from dash import Dash, html, dcc, Input, Output
from starlette.middleware.wsgi import WSGIMiddleware
from starlette.responses import RedirectResponse
from map import create_dash_app

# impotaciones de sqlalchemy 

from sqlalchemy import create_engine, Column, Integer, String, Float, Date, Sequence
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from clave import DATABASE
from sqlarchemy_prueba import DatosFormulario

# creasion del engine de sqlalchemy
engine = create_engine(DATABASE)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


#Instanciar la FasAPI
app = FastAPI()

# Configura la aplicación Dash
dash_app = create_dash_app(requests_pathname_prefix="/dash/")
app.mount("/dash", WSGIMiddleware(dash_app.server))

# Montar el directorio de archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configuracion de las plantillas Jinja2
templates = Jinja2Templates(directory="templates")


# esquema del formulario
class Formulario(BaseModel):
    nombre_completo: str
    correo_electronico: str
    sexo: int
    fecha_nacimiento: date
    provincia: str
    ubicacion_especifica: str
    tipo_recurso: str
    cantidad: int
    unidad: str
    fecha_extraccion: date


# ruta de inicio 
@app.get('/')
async def bienvenido(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# ruta del formulario 
@app.get("/formulario")
async def mostrar_formulario(request: Request):
    return templates.TemplateResponse("formulario.html", {"request": request})


# Función de conversión a kilogramos de pendiendo el material o mineral
def convertir_a_kilogramos(cantidad, unidad):
    conversiones = {
        'toneladas': 1000,  # 1 tonelada = 1000 kilogramos
        'kilogramos': 1,    # 1 kilogramo = 1 kilogramo
        'litros': 1,        # Asumiendo que 1 litro = 1 kilogramo (esto puede variar según el tipo de mineral)
        'onzas': 0.0283495, # 1 onza = 0.0283495 kilogramos
        'libras': 0.453592  # 1 libra = 0.453592 kilogramos
    }
    
    factor_conversion = conversiones.get(unidad.lower(), 1)
    return cantidad * factor_conversion

# funcion para calcular la edad 
def calcular_edad(fecha_nacimiento):
    hoy = date.today()
    edad = hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
    return edad

def database(): 
    db = SessionLocal()
    try:
        yield db
    finally: 
        db.close()

# los datos del formulario se enviaran a la base de datos 
@app.post("/enviar/")
async def submit_formulario(
    request: Request,
    nombre_completo: str = Form(...),
    correo_electronico: str = Form(...),
    sexo: int = Form(...),
    fecha_nacimiento: date = Form(...),
    provincia: str = Form(...),
    ubicacion_especifica: str = Form(...),
    tipo_recurso: str = Form(...),
    cantidad: int = Form(...),
    unidad: str = Form(...),
    fecha_extraccion: date = Form(...),
    db: Session = Depends(database)
):
    # Convertir cantidad a kilogramos
    cantidad_kilogramos = convertir_a_kilogramos(cantidad, unidad)
    edad_calculada = calcular_edad(fecha_nacimiento)
    
    Usuario = DatosFormulario(
        nombre_completo=nombre_completo,
        correo_electronico=correo_electronico,
        sexo=sexo,
        fecha_nacimiento=fecha_nacimiento,
        edad=edad_calculada,
        provincia=provincia,
        ubicacion_especifica=ubicacion_especifica,
        tipo_recurso=tipo_recurso,
        cantidad=cantidad,
        cantidad_calculada=cantidad_kilogramos,
        unidad=unidad,
        fecha_extraccion=fecha_extraccion
    )
    db.add(Usuario)
    db.commit()
    db.refresh(Usuario)
    db.close()

    return templates.TemplateResponse("validacion.html", {"request": request})


@app.get("/dashboar")
async def dashboar():
    return RedirectResponse(url="/dash/")




# ver la data 
'''@app.get('/obtener_data')
def verDatos(request: Request):

    diccionario = []
    conn = s.connect("formulario.db")
    cursor = conn.cursor()

    query = """SELECT * FROM datos_formulario"""
    df = pd.read_sql(query, conn)
    diccionario.append(df.to_dict())
    print(diccionario)
    return diccionario''' 

