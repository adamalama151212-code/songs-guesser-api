# (No code changes needed, just commit and push the current version)
from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import os
from pathlib import Path
from http import HTTPStatus 


app = Flask(__name__)
CORS(app)

# Ta zmienna będzie zawierala dostep do bazy data.db '
MASTER_DB_PATH = Path(os.getenv("DB_PATH", "data/data.db"))


def get_db_connection(db_path: Path = MASTER_DB_PATH):
    db_path.parent.mkdir(parents=True, exist_ok=True) 
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn

def create_initial_schema(db_path: Path, schema_sql: str):
    conn = None
    try:
        conn = get_db_connection(db_path)
        conn.execute(schema_sql)
        conn.commit()
    except Exception as e:
        pass  # Silent error handling
    finally:
        if conn:
            conn.close()


@app.route("/")
def home():
    return jsonify({
        "message": "Flask Audio API",
        "version": "2.0",
        "timestamp": "2025-11-11"
    })

@app.route("/artists", methods=["GET"])
def get_list_of_artists():
    conn = None
    try:
        conn = get_db_connection()
        rows = conn.execute("SELECT name FROM artist ORDER BY name").fetchall()
        artists = [row["name"] for row in rows]
        return jsonify(artists)
    except sqlite3.OperationalError as e:
        return jsonify({"error": f"Błąd bazy danych: {e}"}), HTTPStatus.NOT_FOUND
    except Exception as e:
        return jsonify({"error": f"Błąd serwera: {e}"}), HTTPStatus.INTERNAL_SERVER_ERROR
    finally:
        if conn:
            conn.close()

# --- Endpoint for songs (z MASTER_DB) ---

@app.route("/songs", methods=["GET"])
def get_list_of_songs():
    conn = None
    try:
        conn = get_db_connection()
        rows = conn.execute("SELECT * FROM songs").fetchall()
        return jsonify([dict(row) for row in rows])
    except sqlite3.OperationalError as e:
        return jsonify({"error": f"Błąd bazy danych: Tabela 'songs' nie istnieje. {e}"}), HTTPStatus.NOT_FOUND
    except Exception as e:
        return jsonify({"error": f"Błąd serwera: {e}"}), HTTPStatus.INTERNAL_SERVER_ERROR
    finally:
        if conn:
            conn.close()


# --- ENDPOINT: Pobierz piosenkę dla artysty (jedna) ---
@app.route("/songs/by-artist", methods=["POST"])
def get_song_by_artist():
    conn = None
    try:
        data = request.get_json()
        if not data or 'artist_name' not in data:
            return jsonify({"error": "Brak 'artist_name' w żądaniu"}), HTTPStatus.BAD_REQUEST
        
        artist_name = data['artist_name']
        
        conn = get_db_connection()
        
        # SQL JOIN - znajdź piosenkę dla artysty
        query = """
            SELECT s.name as song_name 
            FROM songs s 
            JOIN artist a ON s.artist_id = a.id 
            WHERE a.name = ?
            ORDER BY RANDOM() 
            LIMIT 1
        """
        
        row = conn.execute(query, (artist_name,)).fetchone()
        
        if row:
            return jsonify({"song_name": row["song_name"]})
        else:
            return jsonify({"error": f"Nie znaleziono piosenki dla artysty: {artist_name}"}), HTTPStatus.NOT_FOUND
            
    except Exception as e:
        return jsonify({"error": f"Błąd serwera: {e}"}), HTTPStatus.INTERNAL_SERVER_ERROR
    finally:
        if conn:
            conn.close()


# --- NOWY ENDPOINT: Pobierz WSZYSTKIE piosenki dla artysty ---
@app.route("/songs/all-by-artist", methods=["POST"])
def get_all_songs_by_artist():
    conn = None
    try:
        # Pobierz nazwę artysty z requestu
        data = request.get_json()
        if not data or 'artist_name' not in data:
            return jsonify({"error": "Brak 'artist_name' w żądaniu"}), HTTPStatus.BAD_REQUEST
        
        artist_name = data['artist_name']
        
        conn = get_db_connection()
        
        # SQL JOIN - znajdź WSZYSTKIE piosenki dla artysty
        query = """
            SELECT s.name as song_name 
            FROM songs s 
            JOIN artist a ON s.artist_id = a.id 
            WHERE a.name = ?
            ORDER BY s.id
        """
        
        rows = conn.execute(query, (artist_name,)).fetchall()
        
        if rows:
            songs = [row["song_name"] for row in rows]
            return jsonify({"songs": songs})
        else:
            return jsonify({"error": f"Nie znaleziono piosenek dla artysty: {artist_name}"}), HTTPStatus.NOT_FOUND
            
    except Exception as e:
        return jsonify({"error": f"Błąd serwera: {e}"}), HTTPStatus.INTERNAL_SERVER_ERROR
    finally:
        if conn:
            conn.close()


# --- ENDPOINT: Pobierz izolowane ścieżki dla piosenki ---
@app.route("/songs/isolated-tracks", methods=["POST"])
def get_isolated_tracks_for_song():
    conn = None
    try:
        data = request.get_json()
        if not data or 'song_name' not in data or 'artist_name' not in data:
            return jsonify({"error": "Brak 'song_name' i 'artist_name' w żądaniu"}), HTTPStatus.BAD_REQUEST
        
        song_name = data['song_name']
        artist_name = data['artist_name']
        
        conn = get_db_connection()
        
        # SQL JOIN - znajdź izolowane ścieżki dla konkretnej piosenki artysty
        query = """
            SELECT it.track_type, it.filename 
            FROM isolated_tracks it
            JOIN songs s ON it.song_id = s.id
            JOIN artist a ON s.artist_id = a.id 
            WHERE s.name = ? AND a.name = ?
            ORDER BY it.track_type
        """
        
        rows = conn.execute(query, (song_name, artist_name)).fetchall()
        
        if rows:
            tracks = {}
            for row in rows:
                tracks[row["track_type"]] = row["filename"]
            return jsonify({"tracks": tracks})
        else:
            return jsonify({"error": f"Nie znaleziono ścieżek dla piosenki '{song_name}' artysty '{artist_name}'"}), HTTPStatus.NOT_FOUND
            
    except Exception as e:
        return jsonify({"error": f"Błąd serwera: {e}"}), HTTPStatus.INTERNAL_SERVER_ERROR
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    ARTIST_SCHEMA = """
        CREATE TABLE IF NOT EXISTS artist(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    """
    create_initial_schema(MASTER_DB_PATH, ARTIST_SCHEMA)

    SONGS_SCHEMA = """
        CREATE TABLE IF NOT EXISTS songs(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            artist_id INTEGER,
            FOREIGN KEY (artist_id) REFERENCES artist(id)
        )
    """
    create_initial_schema(MASTER_DB_PATH, SONGS_SCHEMA)

    # Tabela dla izolowanych ścieżek audio
    ISOLATED_TRACKS_SCHEMA = """
        CREATE TABLE IF NOT EXISTS isolated_tracks(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            track_type TEXT NOT NULL,
            filename TEXT NOT NULL,
            song_id INTEGER,
            FOREIGN KEY (song_id) REFERENCES songs(id)
        )
    """
    create_initial_schema(MASTER_DB_PATH, ISOLATED_TRACKS_SCHEMA)
    
    app.run(host='0.0.0.0', debug=True)