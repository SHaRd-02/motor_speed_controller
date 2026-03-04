

# ⚙️ Motor Speed Controller – Mechatronic System

Sistema de control de velocidad para un motor DC con encoder, utilizando Arduino para el control en lazo cerrado y una aplicación en Python para monitoreo, almacenamiento en la nube y visualización de datos.

---

## 📌 Descripción General

Este proyecto implementa:

- 🔁 Control de velocidad en lazo cerrado (PI/PID) en Arduino  
- 📈 Lectura de RPM mediante encoder  
- 🖥 Aplicación de escritorio (Textual) para:
  - Enviar setpoint de velocidad
  - Detener el motor
  - Leer RPM en tiempo real
- ☁️ Almacenamiento de datos en Supabase (cada 30 segundos)
- 📊 Dashboard en Streamlit que visualiza los datos desde Supabase

---

## 🧠 Arquitectura del Sistema

```
Usuario → App Python (Textual)
        → Serial
        → Arduino (Control PI/PID)
        → Motor DC + Encoder
        → Lecturas RPM
        → App Python
        → Supabase
        → Dashboard Streamlit
```

---

## 🔌 Hardware Utilizado

- Arduino Uno
- Motor DC con encoder (ej. JGA25-371)
- Shield HW-130 (L293D)
- Fuente externa para motor

---

## 🖥 Aplicación Principal (app.py)

Funcionalidades:

- Conexión serial seleccionable (puerto y baudrate)
- Envío de velocidad en tiempo real
- Botón Start / Stop
- Lectura y promedio de RPM
- Guardado en Supabase cada 30 segundos
- Log de:
  - `[TX]` comandos enviados
  - `[DB]` datos guardados

---

## ☁️ Base de Datos (Supabase)

Tabla utilizada:

`speed_data`

Campos mínimos:

- `id` (auto generado)
- `speed` (float)
- `created_at` (timestamp default now())

Los datos almacenados son el promedio de RPM cada 30 segundos para evitar saturar la base de datos.

---

## 📊 Dashboard (Streamlit)

Archivo: `dashboard.py`

Funcionalidades:

- Conexión a Supabase
- Lectura de datos históricos
- Visualización con gráfica de línea
- Actualización en tiempo real al recargar

Ejecutar con:

```
streamlit run app/dashboard.py
```

---

## 🚀 Instalación

1. Clonar repositorio
2. Crear entorno virtual
3. Instalar dependencias:

```
pip install -r requirements.txt
```

4. Crear archivo `.env` con:

```
SUPABASE_URL=your_url
SUPABASE_KEY=your_public_key
```

5. Ejecutar aplicación principal:

```
python app/app.py
```

---

## 📈 Flujo de Datos

- Arduino calcula RPM cada 200 ms
- Python promedia lecturas cada 0.5 s
- Se guarda promedio global cada 2 s en Supabase
- Streamlit consulta Supabase para visualización

---

## 🎯 Propósito Académico

Proyecto desarrollado como práctica de control mecatrónico:

- Control de velocidad con retroalimentación
- Integración hardware-software
- Comunicación serial
- Backend en la nube
- Visualización de datos

---

## 👨‍💻 Autor

Ricardo Hernández  
Proyecto académico – Control de velocidad de motor DC