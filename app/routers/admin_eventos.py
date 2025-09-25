from fastapi import APIRouter, Depends, Form, Request, HTTPException, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
from typing import Optional
from PIL import Image
import io

from ..db import get_db
from ..models.evento import Evento
from ..models.categorias_eventos import CategoriaEvento
from ..models.fecha_evento import FechaEvento
from ..models.horario_fecha_evento import HorarioFechaEvento
from ..models.reserva import Reserva
from app.routers.auth import current_superuser

import cloudinary.uploader

def redimensionar_imagen(upload_file: UploadFile, max_width: int = 800, max_height: int = 800, quality: int = 85):
    """
    Redimensiona una imagen manteniendo la proporción y reduce su tamaño.
    
    Args:
        upload_file: Archivo de imagen subido
        max_width: Ancho máximo en píxeles
        max_height: Alto máximo en píxeles  
        quality: Calidad JPEG (1-100, donde 85 es buena calidad/tamaño)
    
    Returns:
        BytesIO: Imagen procesada lista para subir
    """
    # Leer el archivo original
    upload_file.file.seek(0)
    imagen_original = Image.open(upload_file.file)
    
    # Convertir a RGB si es necesario (para JPEG)
    if imagen_original.mode in ('RGBA', 'P'):
        imagen_original = imagen_original.convert('RGB')
    
    # Calcular nuevas dimensiones manteniendo proporción
    width, height = imagen_original.size
    ratio = min(max_width/width, max_height/height)
    
    # Solo redimensionar si la imagen es más grande que los límites
    if ratio < 1:
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        imagen_redimensionada = imagen_original.resize((new_width, new_height), Image.Resampling.LANCZOS)
    else:
        imagen_redimensionada = imagen_original
    
    # Guardar en memoria como JPEG con compresión
    output = io.BytesIO()
    imagen_redimensionada.save(output, format='JPEG', quality=quality, optimize=True)
    output.seek(0)
    
    return output

router = APIRouter()
templates = Jinja2Templates(directory="frontend/templates")

# Panel de eventos
@router.get("/admin/eventos-panel", dependencies=[Depends(current_superuser)])
def admin_eventos_panel(request: Request):
    return templates.TemplateResponse("admin_panel_eventos.html", {"request": request})

# Listar eventos
@router.get("/admin/eventos", dependencies=[Depends(current_superuser)])
def listar_eventos_admin(request: Request, db: Session = Depends(get_db)):
    from datetime import datetime
    
    # Obtener todos los eventos
    eventos = db.query(Evento).options(
        joinedload(Evento.fechas_evento).joinedload(FechaEvento.horarios)
    ).all()
    
    # Filtrar fechas futuras para cada evento
    hoy = datetime.now().date()
    for evento in eventos:
        # Filtrar solo fechas >= hoy
        fechas_futuras = [fecha for fecha in evento.fechas_evento if fecha.fecha >= hoy]
        evento.fechas_evento = fechas_futuras
    
    return templates.TemplateResponse("admin_eventos.html", {
        "request": request,
        "eventos": eventos
    })

# Mostrar formulario crear evento
@router.get("/admin/eventos/crear", dependencies=[Depends(current_superuser)])
def mostrar_formulario_crear_evento(request: Request, db: Session = Depends(get_db)):
    categorias = db.query(CategoriaEvento).all()
    return templates.TemplateResponse("admin_evento_form.html", {
        "request": request,
        "categorias": categorias,
        "modo": "crear"
    })

# Crear evento (solo información básica)
@router.post("/admin/eventos/crear", dependencies=[Depends(current_superuser)])
def crear_evento(
    titulo: str = Form(...),
    descripcion: str = Form(...),
    categoria_id: Optional[str] = Form(None),
    ubicacion: str = Form(None),
    direccion: str = Form(None),
    costo: float = Form(...),
    prioridad: Optional[str] = Form(None),
    imagen: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    # Si vino vacío, lo convierto a None
    categoria_id_int = int(categoria_id) if categoria_id else None
    prioridad_int = int(prioridad) if prioridad and prioridad.strip() else None
    
    # Subir imagen a Cloudinary si se proporciona
    imagen_url = None
    imagen_public_id = None
    if imagen and imagen.filename:
        try:
            # Redimensionar imagen localmente antes de subir
            imagen_procesada = redimensionar_imagen(imagen)
            
            # Subir imagen ya procesada a Cloudinary
            result = cloudinary.uploader.upload(
                imagen_procesada,
                folder="eventos", 
                transformation=[
                    {"quality": "auto"},
                    {"fetch_format": "auto"}
                ]
            )
            imagen_url = result["secure_url"]
            imagen_public_id = result["public_id"]
        except Exception as e:
            print(f"Error subiendo imagen: {e}")

    nuevo_evento = Evento(
        titulo=titulo,
        descripcion=descripcion,
        categoria_id=categoria_id_int,
        ubicacion=ubicacion,
        direccion=direccion,
        costo=costo,
        prioridad=prioridad_int,
        imagen=imagen_url,
        imagen_public_id=imagen_public_id
    )
    db.add(nuevo_evento)
    db.commit()
    return RedirectResponse(url="/admin/eventos", status_code=303)

# Mostrar formulario editar evento
@router.get("/admin/eventos/{evento_id}/editar", dependencies=[Depends(current_superuser)])
def mostrar_formulario_editar_evento(evento_id: int, request: Request, db: Session = Depends(get_db)):
    from datetime import datetime
    
    evento = db.query(Evento).options(
        joinedload(Evento.fechas_evento).joinedload(FechaEvento.horarios)
    ).get(evento_id)
    categorias = db.query(CategoriaEvento).all()
    if not evento:
        return templates.TemplateResponse("404.html", {"request": request})
    
    # Filtrar fechas futuras para el evento
    hoy = datetime.now().date()
    fechas_futuras = [fecha for fecha in evento.fechas_evento if fecha.fecha >= hoy]
    evento.fechas_evento = fechas_futuras
    
    return templates.TemplateResponse("admin_evento_form.html", {
        "request": request,
        "evento": evento,
        "categorias": categorias,
        "modo": "editar"
    })

# Actualizar evento (solo información básica)
@router.post("/admin/eventos/{evento_id}/editar", dependencies=[Depends(current_superuser)])
def actualizar_evento(
    evento_id: int,
    titulo: str = Form(...),
    descripcion: str = Form(...),
    categoria_id: Optional[str] = Form(None),
    ubicacion: str = Form(None),
    direccion: str = Form(None),
    costo: float = Form(...),
    prioridad: Optional[str] = Form(None),
    imagen: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    # Si vino vacío, lo convierto a None
    categoria_id_int = int(categoria_id) if categoria_id else None
    prioridad_int = int(prioridad) if prioridad and prioridad.strip() else None

    evento = db.query(Evento).get(evento_id)
    if not evento:
        return RedirectResponse(url="/admin/eventos", status_code=303)

    # Subir nueva imagen a Cloudinary si se proporciona
    if imagen and imagen.filename:
        try:
            # Eliminar imagen anterior de Cloudinary si existe
            if evento.imagen:
                try:
                    # Extraer public_id del URL anterior
                    old_public_id = evento.imagen_public_id
                    cloudinary.uploader.destroy(old_public_id)
                except Exception as e:
                    print(f"Error eliminando imagen anterior: {e}")
            
            # Redimensionar imagen localmente antes de subir
            imagen_procesada = redimensionar_imagen(imagen)
            
            # Subir imagen ya procesada a Cloudinary
            result = cloudinary.uploader.upload(
                imagen_procesada,
                folder="eventos",
                transformation=[
                    {"quality": "auto"},
                    {"fetch_format": "auto"}
                ]
            )
            evento.imagen = result["secure_url"]
            evento.imagen_public_id = result["public_id"]
        except Exception as e:
            print(f"Error subiendo imagen: {e}")

    evento.titulo = titulo
    evento.descripcion = descripcion
    evento.categoria_id = categoria_id_int
    evento.ubicacion = ubicacion
    evento.direccion = direccion
    evento.costo = costo
    evento.prioridad = prioridad_int

    db.commit()
    return RedirectResponse(url="/admin/eventos", status_code=303)


# Eliminar evento
@router.post("/admin/eventos/{evento_id}/eliminar", dependencies=[Depends(current_superuser)])
def eliminar_evento(evento_id: int, db: Session = Depends(get_db)):
    evento = db.query(Evento).get(evento_id)
    if evento:
        # Verificar si tiene reservas a través de sus horarios
        reservas_count = db.query(Reserva).join(HorarioFechaEvento).join(FechaEvento).filter(
            FechaEvento.evento_id == evento_id
        ).count()
        
        if reservas_count > 0:
            return templates.TemplateResponse("error_admin.html", {
                "request": {},
                "mensaje": "No se puede eliminar el evento porque tiene reservas registradas.",
                "url_volver": "/admin/eventos"
            })
        
        # Guardar información de la imagen antes de eliminar el evento
        imagen_url = evento.imagen
        imagen_public_id = evento.imagen_public_id
        titulo_evento = evento.titulo
        
        # Eliminar el evento de la base de datos
        db.delete(evento)
        db.commit()
        
        # Si la eliminación fue exitosa y había una imagen, eliminarla de Cloudinary
        if imagen_url:
            try:
                # Public id
                public_id = imagen_public_id
                cloudinary.uploader.destroy(public_id)
            except Exception as e:
                print(f"Error eliminando imagen de Cloudinary: {e}")
                # No fallar la operación si no se puede eliminar la imagen
        
    return RedirectResponse(url="/admin/eventos", status_code=303)

# Gestionar fechas y horarios del evento
@router.get("/admin/eventos/{evento_id}/fechas", dependencies=[Depends(current_superuser)])
def gestionar_fechas_evento(evento_id: int, request: Request, db: Session = Depends(get_db)):
    from datetime import datetime
    
    evento = db.query(Evento).options(
        joinedload(Evento.fechas_evento).joinedload(FechaEvento.horarios)
    ).get(evento_id)
    
    if not evento:
        return RedirectResponse(url="/admin/eventos", status_code=303)
    
    # Filtrar fechas futuras para el evento
    hoy = datetime.now().date()
    fechas_futuras = [fecha for fecha in evento.fechas_evento if fecha.fecha >= hoy]
    evento.fechas_evento = fechas_futuras
    
    return templates.TemplateResponse("admin_evento_fechas.html", {
        "request": request,
        "evento": evento
    })

# Agregar fecha al evento
@router.post("/admin/eventos/{evento_id}/fechas", dependencies=[Depends(current_superuser)])
def agregar_fecha_evento(
    evento_id: int,
    fecha: str = Form(...),
    db: Session = Depends(get_db)
):
    evento = db.query(Evento).get(evento_id)
    if not evento:
        return RedirectResponse(url="/admin/eventos", status_code=303)
    
    fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
    
    # Verificar si la fecha ya existe para este evento
    fecha_existente = db.query(FechaEvento).filter(
        FechaEvento.evento_id == evento_id,
        FechaEvento.fecha == fecha_obj
    ).first()
    
    if fecha_existente:
        return JSONResponse(
            status_code=400,
            content={"error": "La fecha ya existe"}
        )
    
    nueva_fecha = FechaEvento(
        evento_id=evento_id,
        fecha=fecha_obj
    )
    db.add(nueva_fecha)
    db.commit()
    
    return RedirectResponse(url=f"/admin/eventos/{evento_id}/fechas", status_code=303)

# Agregar horario a una fecha
@router.post("/admin/fechas/{fecha_id}/horarios", dependencies=[Depends(current_superuser)])
def agregar_horario_fecha(
    fecha_id: int,
    hora_inicio: str = Form(...),
    duracion_minutos: int = Form(...),
    cupos: int = Form(...),
    db: Session = Depends(get_db)
):
    fecha_evento = db.query(FechaEvento).get(fecha_id)
    if not fecha_evento:
        raise HTTPException(status_code=404, detail="Fecha no encontrada")
    
    nuevo_horario = HorarioFechaEvento(
        fecha_evento_id=fecha_id,
        hora_inicio=datetime.strptime(hora_inicio[:5], '%H:%M').time(),
        duracion_minutos=duracion_minutos,
        cupos=cupos
    )
    db.add(nuevo_horario)
    db.commit()
    db.refresh(nuevo_horario)
    
    # Devolver JSON con los datos del nuevo horario para actualización dinámica
    return JSONResponse({
        "id": nuevo_horario.id,
        "hora_inicio": nuevo_horario.hora_inicio.strftime('%H:%M'),
        "duracion_minutos": nuevo_horario.duracion_minutos,
        "cupos": nuevo_horario.cupos
    })

# Eliminar fecha
@router.delete("/admin/fechas/{fecha_id}", dependencies=[Depends(current_superuser)])
def eliminar_fecha(fecha_id: int, db: Session = Depends(get_db)):
    fecha = db.query(FechaEvento).get(fecha_id)
    if fecha:
        # Verificar si tiene reservas
        reservas_count = db.query(Reserva).join(HorarioFechaEvento).filter(
            HorarioFechaEvento.fecha_evento_id == fecha_id
        ).count()
        
        if reservas_count > 0:
            raise HTTPException(status_code=400, detail="No se puede eliminar la fecha porque tiene reservas")
        
        db.delete(fecha)
        db.commit()
    
    return {"success": True}

# Eliminar horario
@router.delete("/admin/horarios/{horario_id}", dependencies=[Depends(current_superuser)])
def eliminar_horario(horario_id: int, db: Session = Depends(get_db)):
    horario = db.query(HorarioFechaEvento).get(horario_id)
    if horario:
        # Verificar si tiene reservas
        reservas_count = db.query(Reserva).filter(Reserva.horario_id == horario_id).count()
        
        if reservas_count > 0:
            raise HTTPException(status_code=400, detail="No se puede eliminar el horario porque tiene reservas")
        
        db.delete(horario)
        db.commit()
    
    return {"success": True}

# Ver reservas del evento (actualizado para nueva estructura)
@router.get("/admin/eventos/{evento_id}/reservas", dependencies=[Depends(current_superuser)])
def ver_reservas_evento(
    evento_id: int, 
    request: Request, 
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    db: Session = Depends(get_db)
):
    from datetime import datetime
    
    evento = db.query(Evento).get(evento_id)
    if not evento:
        return RedirectResponse(url="/admin/eventos", status_code=303)
    
    # Construir query base
    query = db.query(Evento).filter(Evento.id == evento_id).options(
        joinedload(Evento.fechas_evento).joinedload(FechaEvento.horarios).joinedload(HorarioFechaEvento.reservas).joinedload(Reserva.usuario)
    )
    
    # Si no se proporcionan filtros, usar fecha de hoy como fecha_inicio por defecto
    hoy = datetime.now().date()
    if not fecha_inicio and not fecha_fin:
        fecha_inicio = hoy.strftime("%Y-%m-%d")
    
    # Aplicar filtros de fecha
    if fecha_inicio or fecha_fin:
        # Filtrar las fechas del evento
        fecha_filter = db.query(FechaEvento).filter(FechaEvento.evento_id == evento_id)
        
        if fecha_inicio:
            try:
                fecha_inicio_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
                fecha_filter = fecha_filter.filter(FechaEvento.fecha >= fecha_inicio_dt)
            except ValueError:
                pass  # Ignorar fecha inválida
        
        if fecha_fin:
            try:
                fecha_fin_dt = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
                fecha_filter = fecha_filter.filter(FechaEvento.fecha <= fecha_fin_dt)
            except ValueError:
                pass  # Ignorar fecha inválida
        
        # Obtener IDs de fechas filtradas
        fechas_filtradas_ids = [f.id for f in fecha_filter.all()]
        
        # Filtrar el evento para incluir solo las fechas que cumplen el criterio
        if fechas_filtradas_ids:
            query = query.filter(
                Evento.fechas_evento.any(FechaEvento.id.in_(fechas_filtradas_ids))
            )
        else:
            # Si no hay fechas que cumplan el criterio, crear evento vacío
            evento.fechas_evento = []
    
    evento = query.first()
    if not evento:
        return RedirectResponse(url="/admin/eventos", status_code=303)
    
    # Si hay filtros aplicados, filtrar las fechas del evento cargado
    if fecha_inicio or fecha_fin:
        fechas_filtradas = []
        for fecha_evento in evento.fechas_evento:
            incluir_fecha = True
            
            if fecha_inicio:
                try:
                    fecha_inicio_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
                    if fecha_evento.fecha < fecha_inicio_dt:
                        incluir_fecha = False
                except ValueError:
                    pass
            
            if fecha_fin and incluir_fecha:
                try:
                    fecha_fin_dt = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
                    if fecha_evento.fecha > fecha_fin_dt:
                        incluir_fecha = False
                except ValueError:
                    pass
            
            if incluir_fecha:
                fechas_filtradas.append(fecha_evento)
        
        evento.fechas_evento = fechas_filtradas
    
    return templates.TemplateResponse("admin_reservas_evento.html", {
        "request": request,
        "evento": evento
    })

# Eliminar reserva (actualizado para nueva estructura)
@router.post("/admin/reservas/{reserva_id}/eliminar", dependencies=[Depends(current_superuser)])
def eliminar_reserva(reserva_id: int, db: Session = Depends(get_db)):
    reserva = db.query(Reserva).options(
        joinedload(Reserva.horario).joinedload(HorarioFechaEvento.fecha_evento)
    ).get(reserva_id)
    
    if reserva:
        evento_id = reserva.horario.fecha_evento.evento_id
        db.delete(reserva)
        db.commit()
        return RedirectResponse(f"/admin/eventos/{evento_id}/reservas", status_code=303)
    
    return RedirectResponse("/admin/eventos", status_code=303)

#############################
# Categorias Eventos

# Listar categorías de eventos
@router.get("/admin/categorias_eventos", dependencies=[Depends(current_superuser)])
def listar_categorias_eventos(request: Request, db: Session = Depends(get_db)):
    categorias = db.query(CategoriaEvento).options(
        joinedload(CategoriaEvento.categoria_padre),
        joinedload(CategoriaEvento.subcategorias),
        joinedload(CategoriaEvento.eventos)
    ).all()
    return templates.TemplateResponse("admin_categorias_eventos.html", {
        "request": request,
        "categorias": categorias
    })

@router.get("/admin/categorias_eventos/padres", dependencies=[Depends(current_superuser)])
def listar_categorias_eventos_padres(request: Request, db: Session = Depends(get_db)):
    # Filtramos solo las categorías que no tienen padre
    categorias_padres = db.query(CategoriaEvento).filter(
        CategoriaEvento.id_categoria_padre == None
    ).options(
        joinedload(CategoriaEvento.subcategorias),
        joinedload(CategoriaEvento.eventos)
    ).all()

    return templates.TemplateResponse("admin_categorias_eventos.html", {
        "request": request,
        "categorias": categorias_padres,
        "titulo": "Categorías principales de eventos"
    })

@router.get("/admin/categorias_eventos/{categoria_id}/hijos", dependencies=[Depends(current_superuser)])
def listar_hijos_categoria_evento(categoria_id: int, request: Request, db: Session = Depends(get_db)):
    # Buscamos la categoría padre
    categoria_padre = db.query(CategoriaEvento).options(
        joinedload(CategoriaEvento.subcategorias)
    ).get(categoria_id)
    if not categoria_padre:
        return templates.TemplateResponse("404.html", {"request": request})

    # Tomamos solo las subcategorías
    subcategorias = categoria_padre.subcategorias

    return templates.TemplateResponse("admin_categorias_eventos.html", {
        "request": request,
        "categorias": subcategorias,
        "categoria_padre": categoria_padre
    })

# Mostrar formulario crear categoría de evento
@router.get("/admin/categorias_eventos/crear", dependencies=[Depends(current_superuser)])
def mostrar_formulario_crear_categoria_evento(request: Request, db: Session = Depends(get_db)):
    categorias = db.query(CategoriaEvento).options(
        joinedload(CategoriaEvento.subcategorias)
    ).all()  # para seleccionar padre opcional
    return templates.TemplateResponse("admin_categoria_evento_form.html", {
        "request": request,
        "categorias": categorias,
        "modo": "crear"
    })

# Crear categoría de evento
@router.post("/admin/categorias_eventos/crear", dependencies=[Depends(current_superuser)])
def crear_categoria_evento(
    nombre: str = Form(...), 
    id_categoria_padre: Optional[str] = Form(None), 
    db: Session = Depends(get_db)
):
    # Si vino vacío, lo convierto a None
    id_categoria_padre = int(id_categoria_padre) if id_categoria_padre else None

    if id_categoria_padre is not None:
        padre = db.query(CategoriaEvento).get(id_categoria_padre)
        if not padre:
            return templates.TemplateResponse("error_admin.html", {
                "request": {},
                "mensaje": "La categoría padre seleccionada no existe.",
                "url_volver": "/admin/categorias_eventos"
            })
    
    nueva_categoria = CategoriaEvento(
        nombre=nombre,
        id_categoria_padre=id_categoria_padre
    )
    db.add(nueva_categoria)
    db.commit()
    return RedirectResponse(url="/admin/categorias_eventos", status_code=303)

# Mostrar formulario editar categoría de evento
@router.get("/admin/categorias_eventos/{categoria_id}/editar", dependencies=[Depends(current_superuser)])
def mostrar_formulario_editar_categoria_evento(categoria_id: int, request: Request, db: Session = Depends(get_db)):
    categoria = db.query(CategoriaEvento).get(categoria_id)
    if not categoria:
        return templates.TemplateResponse("404.html", {"request": request})
    categorias = db.query(CategoriaEvento).filter(
        CategoriaEvento.id != categoria_id
    ).options(joinedload(CategoriaEvento.subcategorias)).all()
    return templates.TemplateResponse("admin_categoria_evento_form.html", {
        "request": request,
        "categoria": categoria,
        "categorias": categorias,
        "modo": "editar"
    })

# Actualizar categoría de evento
@router.post("/admin/categorias_eventos/{categoria_id}/editar", dependencies=[Depends(current_superuser)])
def actualizar_categoria_evento(
    categoria_id: int, 
    nombre: str = Form(...), 
    id_categoria_padre: Optional[str] = Form(None), 
    db: Session = Depends(get_db)
):
    # Si vino vacío, lo convierto a None
    id_categoria_padre = int(id_categoria_padre) if id_categoria_padre else None

    categoria = db.query(CategoriaEvento).get(categoria_id)
    if not categoria:
        return RedirectResponse(url="/admin/categorias_eventos", status_code=303)

    if id_categoria_padre == categoria.id:
        return templates.TemplateResponse("error_admin.html", {
            "request": {},
            "mensaje": "Una categoría no puede ser padre de sí misma."
        })

    # Validar que no haya ciclo en ancestros
    ancestro_id = id_categoria_padre
    while ancestro_id:
        if ancestro_id == categoria.id:
            return templates.TemplateResponse("error_admin.html", {
                "request": {},
                "mensaje": "No se puede crear un ciclo en la jerarquía de categorías.",
                "url_volver": "/admin/categorias_eventos"
            })
        ancestro = db.query(CategoriaEvento).get(ancestro_id)
        ancestro_id = ancestro.id_categoria_padre if ancestro else None

    categoria.nombre = nombre
    categoria.id_categoria_padre = id_categoria_padre
    db.commit()
    return RedirectResponse(url="/admin/categorias_eventos", status_code=303)

@router.post("/admin/categorias_eventos/{categoria_id}/eliminar", dependencies=[Depends(current_superuser)])
def eliminar_categoria_evento(categoria_id: int, db: Session = Depends(get_db)):
    categoria = db.query(CategoriaEvento).get(categoria_id)
    if categoria:
        # Verificar si tiene subcategorías
        hijos = db.query(CategoriaEvento).filter(CategoriaEvento.id_categoria_padre == categoria_id).all()
        if hijos:
            return templates.TemplateResponse("error_admin.html", {
                "request": {},
                "mensaje": "No se puede eliminar la categoría porque tiene subcategorías asociadas.",
                "url_volver": "/admin/categorias_eventos"
            })

        # Verificar si tiene eventos asociados
        eventos = db.query(Evento).filter(Evento.categoria_id == categoria_id).all()
        if eventos:
            return templates.TemplateResponse("error_admin.html", {
                "request": {},
                "mensaje": "No se puede eliminar la categoría porque tiene eventos asociados.",
                "url_volver": "/admin/categorias_eventos"
            })

        db.delete(categoria)
        db.commit()
    return RedirectResponse(url="/admin/categorias_eventos", status_code=303)

# Editar horario - GET (mostrar formulario)
@router.get("/admin/horarios/{horario_id}/editar", dependencies=[Depends(current_superuser)])
def mostrar_formulario_editar_horario(horario_id: int, request: Request, evento_id: int = None, db: Session = Depends(get_db)):
    horario = db.query(HorarioFechaEvento).options(
        joinedload(HorarioFechaEvento.fecha_evento).joinedload(FechaEvento.evento)
    ).get(horario_id)
    
    if not horario:
        return templates.TemplateResponse("404.html", {"request": request})
    
    # Si no se proporciona evento_id, obtenerlo del horario
    if not evento_id:
        evento_id = horario.fecha_evento.evento.id
    
    evento = horario.fecha_evento.evento
    
    return templates.TemplateResponse("admin_horario_form.html", {
        "request": request,
        "horario": horario,
        "evento": evento
    })

# Editar horario - POST (procesar formulario)
@router.post("/admin/horarios/{horario_id}/editar", dependencies=[Depends(current_superuser)])
def actualizar_horario(
    horario_id: int,
    request: Request,
    hora_inicio: str = Form(...),
    duracion_minutos: int = Form(...),
    cupos: int = Form(...),
    evento_id: int = Form(...),
    db: Session = Depends(get_db)
):
    horario = db.query(HorarioFechaEvento).get(horario_id)
    if not horario:
        return RedirectResponse(url="/admin/eventos", status_code=303)
    
    try:
        # Validaciones
        if duracion_minutos < 15:
            raise HTTPException(status_code=400, detail="La duración mínima es 15 minutos")
        
        if cupos < 1:
            raise HTTPException(status_code=400, detail="Debe haber al menos 1 cupo")
        
        # Verificar que no haya más reservas que cupos
        reservas_count = db.query(Reserva).filter(Reserva.horario_id == horario_id).count()
        if cupos < reservas_count:
            raise HTTPException(
                status_code=400, 
                detail=f"No se pueden reducir los cupos a {cupos}. Ya hay {reservas_count} reservas confirmadas."
            )
        
        # Convertir hora_inicio a objeto time
        hora_obj = datetime.strptime(hora_inicio[:5], "%H:%M").time()
        
        # Actualizar horario
        horario.hora_inicio = hora_obj
        horario.duracion_minutos = duracion_minutos
        horario.cupos = cupos
        
        db.commit()
        
        # Redirigir de vuelta al evento
        return RedirectResponse(url=f"/admin/eventos/{evento_id}/fechas", status_code=303)
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de hora inválido")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
