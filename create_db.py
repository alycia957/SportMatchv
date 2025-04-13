import sqlite3
import json
from werkzeug.security import generate_password_hash
from datetime import datetime

def init_db():
    # Connexion à la base de données (création si elle n'existe pas)
    conn = sqlite3.connect('sportmatch.db')
    cursor = conn.cursor()
    
    # Création des tables
    cursor.executescript('''
    -- Table des utilisateurs
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        created_at TIMESTAMP NOT NULL
    );
    
    -- Table des sports
    CREATE TABLE IF NOT EXISTS sports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    );
    
    -- Table des niveaux de compétence
    CREATE TABLE IF NOT EXISTS skill_levels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        level TEXT NOT NULL
    );
    
    -- Table des associations utilisateurs-sports
    CREATE TABLE IF NOT EXISTS user_sports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        sport_id INTEGER NOT NULL,
        skill_level_id INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (sport_id) REFERENCES sports (id),
        FOREIGN KEY (skill_level_id) REFERENCES skill_levels (id),
        UNIQUE (user_id, sport_id)
    );
    
    -- Table des sessions
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sport_id INTEGER NOT NULL,
        creator_id INTEGER NOT NULL,
        location TEXT NOT NULL,
        datetime TIMESTAMP NOT NULL,
        min_players INTEGER NOT NULL,
        max_players INTEGER NOT NULL,
        skill_level_id INTEGER NOT NULL,
        description TEXT,
        status TEXT NOT NULL,
        FOREIGN KEY (sport_id) REFERENCES sports (id),
        FOREIGN KEY (creator_id) REFERENCES users (id),
        FOREIGN KEY (skill_level_id) REFERENCES skill_levels (id)
    );
    
    -- Table des participants
    CREATE TABLE IF NOT EXISTS participants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        status TEXT NOT NULL,
        FOREIGN KEY (session_id) REFERENCES sessions (id),
        FOREIGN KEY (user_id) REFERENCES users (id),
        UNIQUE (session_id, user_id)
    );
    ''')
    
    # Charger les données initiales
    with open('data.json', 'r') as f:
        data = json.load(f)
    
    # Insérer les sports
    for sport in data['sports']:
        cursor.execute('INSERT OR IGNORE INTO sports (name) VALUES (?)', (sport,))
    
    # Insérer les niveaux de compétence
    for level in data['skill_levels']:
        cursor.execute('INSERT OR IGNORE INTO skill_levels (level) VALUES (?)', (level,))
    
    # Insérer un utilisateur admin pour tester
    if data.get('admin_user'):
        admin = data['admin_user']
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        password_hash = generate_password_hash(admin['password'])
        
        cursor.execute(
            'INSERT OR IGNORE INTO users (username, password_hash, email, created_at) VALUES (?, ?, ?, ?)',
            (admin['username'], password_hash, admin['email'], created_at)
        )
    
    # Sauvegarder les modifications
    conn.commit()
    conn.close()
    
    print("Base de données initialisée avec succès!")

if __name__ == '__main__':
    init_db()