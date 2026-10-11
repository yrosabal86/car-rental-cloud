# car-rental-cloud
Car Rental Cloud Platform - Proyecto Cloud Computing UGR.
# Car Rental Management System

## 1. Descripción del proyecto
Car Rental Management System es una aplicación web para la gestión del alquiler de vehículos, diseñada siguiendo una arquitectura basada en microservicios y principios Cloud-Native.
El sistema permite a los usuarios registrarse, iniciar sesión, consultar el catálogo de vehículos disponibles y realizar reservas de alquiler.
La aplicación está organizada en componentes independientes que facilitan el mantenimiento, la escalabilidad y la evolución del sistema.

## 2. Arquitectura general
La arquitectura está compuesta por los siguientes elementos tecnológicos:
- **Frontend:** Desarrollado en **React**, encargado de la interfaz de usuario cliente.
- **API Gateway:** Punto de entrada único para las peticiones del cliente.
- **Microservicio de Autenticación:** Desarrollado en **Python** utilizando **FastAPI**.
- **Microservicio de Catálogo de Vehículos:** Desarrollado en **Python** utilizando **FastAPI**.
- **Microservicio de Gestión de Reservas:** Desarrollado en **Python** utilizando **FastAPI**.
- **Base de datos relacional:** Almacenamiento persistente en la nube (PostgreSQL) para usuarios, vehículos y reservas.

## 3. Descripción de los componentes

### 3.1. Frontend: React
El frontend constituye la capa de presentación de la aplicación. Está desarrollado específicamente con **React** y proporciona la interfaz interactiva mediante la que los usuarios y administradores interactúan con el sistema.
Sus principales responsabilidades son:
- Mostrar los formularios de registro e inicio de sesión.
- Presentar el catálogo de vehículos disponibles.
- Permitir la búsqueda y el filtrado de coches.
- Mostrar los detalles de cada vehículo.
- Facilitar la creación y consulta de reservas.
- Comunicar las acciones del usuario con el backend mediante peticiones HTTP desde **React**.

### 3.2. API Gateway
El API Gateway actúa como punto de entrada único para las peticiones procedentes del frontend en **React**.
Sus responsabilidades principales son:
- Enrutar las peticiones al microservicio correspondiente en **Python**.
- Centralizar aspectos comunes de la comunicación, como el registro de peticiones y la gestión de errores.
- Aplicar políticas de seguridad y límites de peticiones cuando estén configurados.
- Verificar o transmitir la información de autenticación según la configuración del sistema.

### 3.3. Microservicio de Autenticación (US01)
Este servicio está desarrollado con **Python** y **FastAPI** y se encarga de gestionar la identidad y el acceso de los usuarios.
Funcionalidades principales:
- Registrar nuevos usuarios.
- Validar las credenciales durante el inicio de sesión.
- Almacenar las contraseñas utilizando mecanismos de hash seguros.
- Emitir tokens de acceso (por ejemplo, JWT).
- Validar la identidad del usuario en las operaciones protegidas.

### 3.4. Microservicio de Catálogo de Vehículos (US02)
Este servicio está desarrollado con **Python** y **FastAPI**, gestionando la información de los coches disponibles para alquiler y permitiendo consultar el catálogo aplicando diferentes criterios de búsqueda.
Funcionalidades principales:
- Consultar los vehículos registrados.
- Buscar vehículos por marca o modelo.
- Filtrar por precio, categoría u otras características.
- Consultar la información detallada de un vehículo.

### 3.5. Microservicio de Gestión de Reservas (US03)
Este servicio está desarrollado con **Python** y **FastAPI**, gestionando el proceso de alquiler y las reservas realizadas por los usuarios.
Funcionalidades principales:
- Crear una reserva de alquiler.
- Consultar las reservas de un usuario.
- Cancelar reservas cuando las reglas del negocio lo permitan.
- Comprobar la disponibilidad del vehículo para el intervalo solicitado, evitando dobles reservas.

## 4. Capa de persistencia
La aplicación utiliza una base de datos relacional alojada en un entorno cloud (PostgreSQL como servicio gestionado), accesible de forma independiente por los microservicios en **Python**.
La persistencia almacena los datos necesarios:
- **Usuarios:** identificador, correo electrónico, hash de contraseña y perfil.
- **Vehículos:** identificador, marca, modelo, categoría, precio y estado.
- **Reservas:** identificador, usuario, vehículo, fechas y estado del alquiler.

## 5. Diagrama de Arquitectura

El siguiente diagrama detalla la arquitectura nativa de la nube (*Cloud-Native*) de la aplicación, mostrando los componentes de **React** en el frontend, la API Gateway, los microservicios en **Python (FastAPI)** y la base de datos persistente:

![Arquitectura Técnica Car Rental Management](Arquitectura.png)

### Comunicación entre componentes
La comunicación entre el frontend (**React**) y el backend (**Python / FastAPI**) se realiza mediante **HTTPS y una API REST** en formato JSON.
*Ejemplo de flujo de reserva:*
1. El usuario realiza una acción desde la interfaz de **React**.
2. El frontend envía una petición HTTPS al API Gateway.
3. El Gateway reenvía la petición al microservicio de reservas en **Python**.
4. El servicio valida los datos, la autenticación y comprueba la disponibilidad del vehículo.
5. Se registra la reserva en la base de datos y se devuelve la respuesta al frontend.

## 6. Seguridad y Consideraciones Cloud-Native
- **Seguridad:** Uso de HTTPS, autenticación basada en tokens, contraseñas cifradas con hash y validación de datos en los servicios de **Python**.
- **Cloud-Native:** Preparado para contenerización mediante Docker, configuración externa y escalado independiente de los servicios backend y frontend.
## 7. Justificación bajo los Marcos Teóricos del NIST

### 7.1. NIST SP 800-145 (Características del Cloud Computing)
La arquitectura del sistema de alquiler de coches justifica su diseño *Cloud-Native* cumpliendo con las 5 características esenciales:
- **Autoservicio bajo demanda:** Los usuarios pueden registrarse, buscar vehículos y realizar reservas de forma autónoma a través de la interfaz web sin intervención humana.
- **Acceso amplio a la red:** La aplicación es accesible mediante HTTPS desde cualquier dispositivo con navegador web.
- **Agrupación de recursos (Resource Pooling):** Los microservicios y bases de datos comparten recursos de infraestructura en la nube de forma eficiente.
- **Rápida elasticidad:** Los servicios están diseñados para escalar horizontalmente según la demanda de alquileres.
- **Servicio medido:** La infraestructura supervisa y optimiza el consumo de recursos de cómputo y almacenamiento.

### 7.2. NIST SP 500-292 (Mapeo de Actores Cloud e Impacto Económico)
Siguiendo el marco de referencia del NIST para arquitecturas en la nube, se identifican los siguientes actores en el ecosistema del sistema de alquiler de coches:
- **Consumidor del Servicio:** El cliente o usuario final que navega por el catálogo en React, gestiona su perfil y realiza las reservas de vehículos.
- **Proveedor del Servicio (*Cloud Provider*):** La plataforma cloud (ej. AWS/GCP) que provee la infraestructura subyacente, el servidor de base de datos gestionado (PostgreSQL) y el entorno de red.
- **Intermediario del Servicio:** El API Gateway y los mecanismos de balanceo de carga que gestionan, enrutan y controlan el flujo de peticiones entre el cliente y los servicios backend.
- **Auditor del Servicio:** Herramientas de monitorización y logs encargadas de verificar el cumplimiento de seguridad, control de accesos (JWT) y el registro de auditoría de las transacciones.
- **Operador del Servicio:** El equipo de desarrollo e infraestructura (DevOps) responsable del despliegue mediante contenedores, mantenimiento y escalado de los microservicios en Python.
- **Análisis del Impacto Económico:** El modelo Cloud-Native elimina la necesidad de comprar servidores físicos locales (*CapEx*), transformando los costos en un modelo de pago por uso (*OpEx*), lo que optimiza drásticamente los costos operativos iniciales del negocio de alquiler.

## 8. Especificación de Endpoints de la API REST

A continuación se detallan las rutas principales, verbos HTTP y la estructura de los payloads JSON soportados por el API Gateway:

### Autenticación (US01)
- **`POST /auth/register`** (Registro de usuario)
  - *Payload de entrada (JSON):* `{"email": "user@email.com", "password": "securepassword123"}`
  - *Respuesta:* `{"status": "success", "message": "Usuario registrado correctamente"}`
- **`POST /auth/login`** (Inicio de sesión)
  - *Payload de entrada (JSON):* `{"email": "user@email.com", "password": "securepassword123"}`
  - *Respuesta:* `{"access_token": "eyJhbGciOi...", "token_type": "bearer"}`

### Catálogo de Vehículos (US02)
- **`GET /vehicles`** (Listar vehículos disponibles)
  - *Parámetros opcionales:* `?category=suv&date_start=2026-06-01`
  - *Respuesta:* `[{"id": 1, "brand": "Toyota", "model": "RAV4", "price_per_day": 45.00, "available": true}]`
- **`GET /vehicles/{id}`** (Detalle de un coche)
  - *Respuesta:* `{"id": 1, "brand": "Toyota", "model": "RAV4", "category": "SUV", "specs": {...}}`

### Gestión de Reservas (US03)
- **`POST /reservations`** (Crear reserva)
  - *Payload de entrada (JSON):* `{"user_id": 12, "vehicle_id": 1, "start_date": "2026-06-10", "end_date": "2026-06-15"}`
  - *Respuesta:* `{"reservation_id": 105, "status": "confirmed", "total_price": 225.00}`
- **`GET /reservations`** (Consultar reservas del usuario)
  - *Respuesta:* `[{"reservation_id": 105, "vehicle": "Toyota RAV4", "status": "confirmed"}]`
- **`DELETE /reservations/{id}`** (Cancelar reserva)
  - *Respuesta:* `{"status": "cancelled", "message": "La reserva ha sido anulada con éxito"}`

