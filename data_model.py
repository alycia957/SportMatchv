import sqlite3
import math
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# Fonction pour se connecter à la base de données
def get_db_connection():
    conn = sqlite3.connect('sportmatch.db')
    conn.row_factory = sqlite3.Row
    return conn

# Fonctions de gestion des utilisateurs
def create_user(username, password, email):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Vérifier si l'utilisateur existe déjà
    cursor.execute('SELECT * FROM users WHERE username = ? OR email = ?', (username, email))
    if cursor.fetchone():
        conn.close()
        return None
    
    # Créer le nouvel utilisateur
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    password_hash = generate_password_hash(password)
    cursor.execute(
        'INSERT INTO users (username, password_hash, email, created_at) VALUES (?, ?, ?, ?)',
        (username, password_hash, email, created_at)
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return user_id

def get_user(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    return user

def get_user_by_username(username):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    return user

def authenticate_user(username, password):
    user = get_user_by_username(username)
    if user and check_password_hash(user['password_hash'], password):
        return user
    return None

# Fonctions de gestion des sports
def get_all_sports():
    conn = get_db_connection()
    sports = conn.execute('SELECT * FROM sports').fetchall()
    conn.close()
    return sports

def get_user_sports(user_id):
    conn = get_db_connection()
    query = '''
    SELECT us.id, us.user_id, us.sport_id, us.skill_level_id, 
           s.name as sport_name, sl.level as skill_level
    FROM user_sports us
    JOIN sports s ON us.sport_id = s.id
    JOIN skill_levels sl ON us.skill_level_id = sl.id
    WHERE us.user_id = ?
    '''
    user_sports = conn.execute(query, (user_id,)).fetchall()
    conn.close()
    return user_sports

def add_user_sport(user_id, sport_id, skill_level_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Vérifier si l'association existe déjà
    cursor.execute(
        'SELECT id FROM user_sports WHERE user_id = ? AND sport_id = ?',
        (user_id, sport_id)
    )
    existing = cursor.fetchone()
    
    if existing:
        # Mettre à jour le niveau
        cursor.execute(
            'UPDATE user_sports SET skill_level_id = ? WHERE id = ?',
            (skill_level_id, existing['id'])
        )
    else:
        # Créer la nouvelle association
        cursor.execute(
            'INSERT INTO user_sports (user_id, sport_id, skill_level_id) VALUES (?, ?, ?)',
            (user_id, sport_id, skill_level_id)
        )
    
    conn.commit()
    conn.close()
    return True

# Fonctions de gestion des sessions
def create_session(sport_id, creator_id, location, datetime_str, min_players, max_players, skill_level_id, description):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        '''INSERT INTO sessions 
           (sport_id, creator_id, location, datetime, min_players, max_players, 
            skill_level_id, description, status) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (sport_id, creator_id, location, datetime_str, min_players, max_players, 
         skill_level_id, description, 'ouvert')
    )
    
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return session_id

def get_sessions(filters=None):
    conn = get_db_connection()
    query = '''
     SELECT s.*, sp.name as sport_name, sl.level as skill_level, 
           u.username as creator_name,
           datetime(s.datetime) as formatted_datetime,
           (SELECT COUNT(*) FROM participants p WHERE p.session_id = s.id AND p.status = 'confirmé') as participant_count
    FROM sessions s
    JOIN sports sp ON s.sport_id = sp.id
    JOIN skill_levels sl ON s.skill_level_id = sl.id
    JOIN users u ON s.creator_id = u.id
    '''
    
    conditions = []
    params = []
    
    if filters:
        if 'sport_id' in filters and filters['sport_id']:
            conditions.append('s.sport_id = ?')
            params.append(filters['sport_id'])
        
        if 'skill_level_id' in filters and filters['skill_level_id']:
            conditions.append('s.skill_level_id = ?')
            params.append(filters['skill_level_id'])
        
        if 'date_from' in filters and filters['date_from']:
            conditions.append('s.datetime >= ?')
            params.append(filters['date_from'])
        
        if 'date_to' in filters and filters['date_to']:
            conditions.append('s.datetime <= ?')
            params.append(filters['date_to'])
        
        if 'status' in filters and filters['status']:
            conditions.append('s.status = ?')
            params.append(filters['status'])
    
    if conditions:
        query += ' WHERE ' + ' AND '.join(conditions)
    
    query += ' ORDER BY s.datetime'
    
    sessions = conn.execute(query, params).fetchall()
    conn.close()
    return sessions

def get_session(session_id):
    conn = get_db_connection()
    query = '''
    SELECT s.*, sp.name as sport_name, sl.level as skill_level, 
           u.username as creator_name
    FROM sessions s
    JOIN sports sp ON s.sport_id = sp.id
    JOIN skill_levels sl ON s.skill_level_id = sl.id
    JOIN users u ON s.creator_id = u.id
    WHERE s.id = ?
    '''
    session = conn.execute(query, (session_id,)).fetchone()
    conn.close()
    return session

def update_session_status(session_id, status):
    conn = get_db_connection()
    conn.execute('UPDATE sessions SET status = ? WHERE id = ?', (status, session_id))
    conn.commit()
    conn.close()
    return True

# Fonctions de gestion des participants
def join_session(session_id, user_id, status='confirmé'):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Vérifier si l'utilisateur est déjà inscrit
    cursor.execute(
        'SELECT id FROM participants WHERE session_id = ? AND user_id = ?',
        (session_id, user_id)
    )
    existing = cursor.fetchone()
    
    if existing:
        # Mettre à jour le statut
        cursor.execute(
            'UPDATE participants SET status = ? WHERE id = ?',
            (status, existing['id'])
        )
    else:
        # Ajouter le participant
        cursor.execute(
            'INSERT INTO participants (session_id, user_id, status) VALUES (?, ?, ?)',
            (session_id, user_id, status)
        )
    
    conn.commit()
    conn.close()
    return True

def leave_session(session_id, user_id):
    conn = get_db_connection()
    conn.execute(
        'DELETE FROM participants WHERE session_id = ? AND user_id = ?',
        (session_id, user_id)
    )
    conn.commit()
    conn.close()
    return True

def get_session_participants(session_id):
    conn = get_db_connection()
    query = '''
    SELECT p.*, u.username
    FROM participants p
    JOIN users u ON p.user_id = u.id
    WHERE p.session_id = ?
    '''
    participants = conn.execute(query, (session_id,)).fetchall()
    conn.close()
    return participants

def get_user_created_sessions(user_id):
    conn = get_db_connection()
    query = '''
    SELECT s.*, sp.name as sport_name, sl.level as skill_level,
           (SELECT COUNT(*) FROM participants p WHERE p.session_id = s.id AND p.status = 'confirmé') as participant_count
           
    FROM sessions s
    JOIN sports sp ON s.sport_id = sp.id
    JOIN skill_levels sl ON s.skill_level_id = sl.id
    WHERE s.creator_id = ?
    ORDER BY s.datetime
    '''
    sessions = conn.execute(query, (user_id,)).fetchall()
    conn.close()
    return sessions

def get_user_participating_sessions(user_id):
    conn = get_db_connection()
    query = '''
    SELECT s.*, sp.name as sport_name, sl.level as skill_level, 
           u.username as creator_name, p.status as participation_status,
           (SELECT COUNT(*) FROM participants p2 WHERE p2.session_id = s.id AND p2.status = 'confirmé') as participant_count
    FROM participants p
    JOIN sessions s ON p.session_id = s.id
    JOIN sports sp ON s.sport_id = sp.id
    JOIN skill_levels sl ON s.skill_level_id = sl.id
    JOIN users u ON s.creator_id = u.id
    WHERE p.user_id = ?
    ORDER BY s.datetime
    '''
    sessions = conn.execute(query, (user_id,)).fetchall()
    conn.close()
    return sessions

def get_all_skill_levels():
    conn = get_db_connection()
    skill_levels = conn.execute('SELECT * FROM skill_levels').fetchall()
    conn.close()
    return skill_levels