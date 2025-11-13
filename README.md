\# TMDB Backend API



API Flask para análisis de datos de películas usando MongoDB Atlas.



\## Tecnologías

\- Python 3.x

\- Flask

\- MongoDB Atlas

\- Gunicorn



\## Variables de Entorno

Configura estas variables en Render:

\- `MONGO\_URI`: mongodb+srv://dbUSER:<db_password>@cluster0.kicndvr.mongodb.net/?appName=Cluster0



\## Endpoints

\- `GET /api/reportes/top\_generos?limit=10\&sort=desc`

\- `GET /api/reportes/top\_directores\_ingresos?limit=5\&sort=desc`

\- `GET /api/reportes/search?q=term`

\- `GET /api/reportes/stats`

