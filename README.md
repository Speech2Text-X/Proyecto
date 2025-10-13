# 🎙️ Speech2Text X  
Transcripción de audios con inteligencia artificial

---

## 👥 Equipo 1  
**Integrantes:** Luciano · Tomás · Nicolás  
**Herramienta de testing:** Pytest  
**Tecnologías:** TypeScript (Frontend) · Python (Backend) · PostgreSQL · AWS  

---

## 💡 Descripción general
Speech2Text X busca ofrecer una forma simple y accesible de convertir audios en texto.  
En esta primera etapa, el proyecto se centra en el flujo **CRUD principal**, validaciones y pruebas básicas.

---

## ⚙️ Funcionalidades implementadas
- Crear proyectos para agrupar audios y transcripciones.  
- Subir archivos de audio y crear su transcripción.  
- Listar y visualizar transcripciones existentes.  
- Editar o eliminar registros desde el panel.  
- Validaciones de formato y tamaño de archivo.  
- Mensajes claros ante errores y operaciones exitosas.

---

## 🧱 Arquitectura actual
- **Frontend:** TypeScript (React).  
- **Backend:** Python (FastAPI) + PostgreSQL.  
- **Infraestructura:** AWS S3 (almacenamiento de audios).  
- **Testing:** Pytest para pruebas unitarias e integración simple.

---

## 🧪 Pruebas
**Herramienta:** Pytest  

Tipos de pruebas aplicadas:
- Unitarias → funciones internas (validaciones, parsers).  
- Integración → endpoints CRUD con base de datos.  
- Validaciones → errores por formato o tamaño.  

## Base de datos
[Link](https://dbdocs.io/Luciano%20Yevenes/Base-de-datos-Speech2Text-X)
