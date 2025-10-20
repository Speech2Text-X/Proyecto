# 🎙️ Speech2Text X
**Transcripción de audios con inteligencia artificial**

---

## Integrantes del equipo
- Tomás Castillo
- Nicolas Cortes
- Luciano Yevenes

### **Herramienta de testing:** PyTest  
### **Tecnologías:** TypeScript (Frontend) · Python (Backend) · PostgreSQL · AWS
---

## Resumen del Proyecto
**Speech2Text X** es un software diseñado para ofrecer una solución automatizada de transcripción de audios mediante inteligencia artificial.  
El objetivo es **democratizar el acceso** a herramientas de transcripción de calidad con **costos mínimos** y una **interfaz simple y accesible**.

En esta primera entrega se desarrolló el **backend completo**, incluyendo la base de datos, los endpoints CRUD y el entorno contenerizado.  
En etapas futuras se integrará el modelo **Whisper** de OpenAI para la transcripción automática y las funciones de resumen inteligente.

---

```
Proyecto/
│
├─ backend/
│   ├─ app/
│   ├─ tests/
│   ├─ Dockerfile
│   └─ requirements.txt
│
├─ frontend/
│   └─ tailadmin-react-pro-2.1.1.zip        (Base del front)
│
├─ docs/
│   └─ Base de datos Speech2Text-X.pdf
│
├─ db/
│   └─ scripts para la creacion de la db
│
├─ docker-compose.yml
├─ .gitignore
├─ LICENSE
└─ README.md
```

---

## Instrucciones de instalación
### Requisitos previos
- Docker y Docker Compose instalados.
- Git instalado.
- Archivo `.env` con variables de entorno (ejemplo en `.env.example`).

### Pasos de instalación
1. Clonar el repositorio:
   ```bash
   git clone git@github.com:Speech2Text-X/Proyecto.git
   cd Proyecto
   ```

2. Crear el archivo `.env` con las siguientes variables mínimas:
   ```env
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   POSTGRES_DB=s2x
   DB_URL=postgresql+psycopg://postgres:postgres@db:5432/s2x
   ```

3. Levantar el entorno con Docker Compose:
   ```bash
   docker-compose up --build
   ```

4. Una vez iniciado:
    - API disponible en: `http://localhost:8000/docs`
    - Base de datos disponible en contenedor `s2x-postgres`

---

## Documentación del Proyecto
Toda la documentación detallada se encuentra en la **Wiki del repositorio**, que incluye:
- Resumen y objetivos del proyecto
- Descripción del trabajo realizado
- Tecnologías y relación con las pruebas
- Evidencia del trabajo (capturas, código, endpoints funcionales)
- Estrategia de pruebas
- Supuestos y dependencias del desarrollo

📖 **[Ver Wiki completa →](https://github.com/Speech2Text-X/Proyecto/wiki)**

---

## Principales Funcionalidades Implementadas

- CRUD completo para:
    - Usuarios
    - Proyectos
    - Archivos de audio
    - Transcripciones
- Validaciones de formato y tipo de datos con Pydantic.
- Migraciones automáticas y esquema SQL inicial.
- Entorno contenerizado con Docker Compose.
- Configuración desacoplada mediante `.env`.

---

## Estrategia de Pruebas

Durante esta primera entrega, las pruebas se realizaron **de manera manual**, verificando el correcto funcionamiento de los endpoints y la conexión entre los contenedores.  
Estas pruebas incluyeron:
- Ejecución y respuesta de los endpoints CRUD (`/users`, `/projects`, `/audio_files`, `/transcriptions`).
- Validación de datos incorrectos (errores 422 en FastAPI).
- Conectividad entre la API y la base de datos PostgreSQL a través de Docker.

### Próximas versiones
Para futuras entregas, se implementarán:
- **Pruebas unitarias** de funciones internas con **PyTest**.
- **Pruebas de integración** automatizadas para verificar flujo completo.
- **Cobertura de pruebas** y CI/CD básico para asegurar estabilidad.

---

## Supuestos y Dependencias

- El sistema se ejecuta en entornos contenerizados (Docker).
- La integración del modelo de IA se realiza en la siguiente entrega.
- Las pruebas actuales se concentran en el backend.
- Variables sensibles se manejan mediante `.env`.
- Dependencias externas: PostgreSQL, Docker, FastAPI, psycopg_pool.

---

## Release Notes

### v1.0 — Entrega 1
- Implementación base del backend con FastAPI.
- CRUD completo para usuarios, proyectos, audios y transcripciones.
- Validación de datos con Pydantic.
- Base de datos relacional PostgreSQL.
- Contenedorización completa con Docker Compose.

📌 [Ver releases en GitHub](https://github.com/usuario/speech2textx/releases)

---

## Cápsula de Video Explicativa
🔗 [Video Entrega 1 - YouTube](https://youtu.be/MEkOMKmbDxs)

---

## Licencia

Este proyecto está licenciado bajo la [MIT License](./LICENSE).  
Consulta el archivo `LICENSE` para más detalles.

## Contribución y Contacto

### Cómo contribuir:
1. Crea un **fork** del repositorio.
2. Crea una nueva rama para tus cambios:
   ```bash
   git checkout -b feature/nueva-funcionalidad
   ```
3. Haz commit y push de tus cambios.
4. Crea un **Pull Request** con la descripción de tus aportes.

### Contacto del equipo:
- **Luciano Yévenes** — luciano@correo.com
- **Tomás** — t@correo.com
- **Nicolás** — n@correo.com

---

## .gitignore
El archivo `.gitignore` está configurado para ignorar:
- Archivos de entorno (`.env`)
- Archivos temporales de Python (`__pycache__/`, `.pytest_cache/`)
- Carpetas de dependencias (`node_modules/`, `venv/`)
- Imágenes o salidas temporales (`*.log`, `*.tmp`)
- Archivos de construcción de Docker y frontend

---

## Información adicional

- **Repositorio:** [https://github.com/usuario/speech2textx](https://github.com/usuario/speech2textx)
- **Documentación extendida:** disponible en la Wiki.
- **Diagramas y evidencias:** ubicados en la carpeta `/docs`.
- **Frontend:** en desarrollo (fase 2 del proyecto).
