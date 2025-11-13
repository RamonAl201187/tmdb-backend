import os
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient

# Carga las variables del archivo .env
load_dotenv()

# --- 1. Inicialización de Flask y CORS ---
app = Flask(__name__)

# CORS configurado para permitir peticiones desde cualquier origen
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# --- 2. Conexión a MongoDB Atlas ---
MONGO_URI = os.getenv('MONGO_URI')

if not MONGO_URI:
    print("ERROR: MONGO_URI no se ha cargado. Revisa tu archivo .env o las variables de entorno de Render.")
    exit()

try:
    client = MongoClient(MONGO_URI)
    db = client.tmdb_nosql
    collection = db.movies
    print("Conexión a MongoDB Atlas exitosa.")
except Exception as e:
    print(f"Error al conectar a MongoDB: {e}")


# Endpoint de prueba
@app.route('/', methods=['GET'])
def index():
    return jsonify({"status": "API corriendo", "db_conectada": True})


@app.route('/api/reportes/top_generos', methods=['GET'])
def get_top_genres():
    """
    Calcula el conteo de películas por género.
    Parámetros opcionales:
    - limit: número de géneros a retornar (default: 10)
    - sort: 'asc' o 'desc' (default: 'desc')
    """
    try:
        # Obtener parámetros de query
        limit = request.args.get('limit', default=10, type=int)
        sort_order = request.args.get('sort', default='desc', type=str)
        
        # Validar límite
        limit = max(1, min(limit, 50))  # Entre 1 y 50
        
        # Determinar orden
        sort_direction = -1 if sort_order == 'desc' else 1
        
        pipeline = [
            {'$unwind': '$genres'},
            {'$group': {'_id': '$genres.name', 'conteo': {'$sum': 1}}},
            {'$sort': {'conteo': sort_direction}},
            {'$limit': limit}
        ]
        
        data = list(collection.aggregate(pipeline))
        formatted_data = [{'nombre': item['_id'], 'conteo': item['conteo']} for item in data]
        
        return jsonify(formatted_data)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/reportes/top_directores_ingresos', methods=['GET'])
def get_top_directors_revenue():
    """
    Calcula la suma total de ingresos por director.
    Parámetros opcionales:
    - limit: número de directores a retornar (default: 5)
    - sort: 'asc' o 'desc' (default: 'desc')
    """
    try:
        # Obtener parámetros de query
        limit = request.args.get('limit', default=5, type=int)
        sort_order = request.args.get('sort', default='desc', type=str)
        
        # Validar límite
        limit = max(1, min(limit, 30))  # Entre 1 y 30
        
        # Determinar orden
        sort_direction = -1 if sort_order == 'desc' else 1
        
        pipeline = [
            {'$unwind': '$crew'},
            {'$match': {'crew.job': 'Director'}},
            {'$group': {
                '_id': '$crew.name', 
                'ingresos_totales': {'$sum': '$revenue'}
            }},
            {'$sort': {'ingresos_totales': sort_direction}},
            {'$limit': limit}
        ]
        
        data = list(collection.aggregate(pipeline))
        formatted_data = [
            {'director': item['_id'], 'ingresos_totales': item['ingresos_totales']} 
            for item in data
        ]
        
        return jsonify(formatted_data)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/reportes/search', methods=['GET'])
def search():
    """
    Busca en géneros y directores.
    Parámetro requerido:
    - q: término de búsqueda
    """
    try:
        query = request.args.get('q', default='', type=str)
        
        if not query:
            return jsonify({"error": "Parámetro 'q' requerido"}), 400
        
        # Buscar en géneros
        genre_pipeline = [
            {'$unwind': '$genres'},
            {'$match': {'genres.name': {'$regex': query, '$options': 'i'}}},
            {'$group': {'_id': '$genres.name', 'conteo': {'$sum': 1}}},
            {'$sort': {'conteo': -1}},
            {'$limit': 10}
        ]
        
        genres = list(collection.aggregate(genre_pipeline))
        
        # Buscar en directores
        director_pipeline = [
            {'$unwind': '$crew'},
            {'$match': {
                'crew.job': 'Director',
                'crew.name': {'$regex': query, '$options': 'i'}
            }},
            {'$group': {
                '_id': '$crew.name',
                'ingresos_totales': {'$sum': '$revenue'}
            }},
            {'$sort': {'ingresos_totales': -1}},
            {'$limit': 10}
        ]
        
        directors = list(collection.aggregate(director_pipeline))
        
        return jsonify({
            'genres': [{'nombre': g['_id'], 'conteo': g['conteo']} for g in genres],
            'directors': [{'director': d['_id'], 'ingresos_totales': d['ingresos_totales']} for d in directors]
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/reportes/stats', methods=['GET'])
def get_stats():
    """
    Retorna estadísticas generales.
    """
    try:
        total_movies = collection.count_documents({})
        
        # Total de géneros únicos
        genre_pipeline = [
            {'$unwind': '$genres'},
            {'$group': {'_id': '$genres.name'}},
            {'$count': 'total'}
        ]
        genre_result = list(collection.aggregate(genre_pipeline))
        total_genres = genre_result[0]['total'] if genre_result else 0
        
        # Director con más ingresos
        director_pipeline = [
            {'$unwind': '$crew'},
            {'$match': {'crew.job': 'Director'}},
            {'$group': {
                '_id': '$crew.name',
                'ingresos_totales': {'$sum': '$revenue'}
            }},
            {'$sort': {'ingresos_totales': -1}},
            {'$limit': 1}
        ]
        top_director = list(collection.aggregate(director_pipeline))
        
        return jsonify({
            'total_movies': total_movies,
            'total_genres': total_genres,
            'top_director': top_director[0] if top_director else None
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)