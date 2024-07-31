from sqlalchemy import create_engine, Column, Integer, String, Float, Date, Sequence
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from clave import DATABASE # AQUI ESTA MI CONEXION A POSTGRESQL CON CLAVE Y TODO NO VISIBLE 


engine = create_engine(DATABASE)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Creamos una clase que represente una tabla en la base de datos
class DatosFormulario(Base):
    __tablename__ = 'datos_formulario'
    id = Column(Integer, Sequence('usuario_id'), primary_key=True)
    nombre_completo = Column(String(50),nullable=False)
    correo_electronico = Column(String(50), nullable=False)
    sexo = Column(Integer, nullable=False)
    fecha_nacimiento = Column(Date, nullable=False)
    edad = Column(Integer, nullable=False)
    provincia = Column(String(50), nullable=False)
    ubicacion_especifica = Column(String(100), nullable=False)
    tipo_recurso = Column(String(50), nullable=False)
    cantidad = Column(Float, nullable=False)
    cantidad_calculada = Column(Float, nullable=False)
    unidad = Column(String(20), nullable=False)
    fecha_extraccion = Column(Date, nullable=False)


# Crear las tablas en la base de datos
#Base.metadata.create_all(engine) # solo debe ser ejecuctado una sola vez nada mas porque si esta activo sobreescribira la base de datos


"""
# Crear una sesión
Session = sessionmaker(bind=engine)
session = Session()

persona1 = Persona(cedula = "12345678901", nombre = "Elvin", apellido = "Coronado", edad = 24, sexo = 0)
session.add(persona1)
session.commit()"""