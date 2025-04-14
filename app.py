from flask import Flask, session, request, redirect, url_for, render_template, jsonify, flash
import data_model as model
from functools import wraps
from datetime import datetime
import os

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False # pour les caractères spéciaux
app.secret_key = b'84652b407b532f2c44cdcc113c822865e417699fbe3ce327daa33e9e1d8463f5'

# Middleware d'authentification
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Routes d'authentification
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = model.authenticate_user(username, password)
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            
            next_page = request.args.get('next')
            if not next_page:
                next_page = url_for('home')
            
            return redirect(next_page)
        else:
            flash('Nom d\'utilisateur ou mot de passe incorrect.')
    
    return render_template('auth.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        
        user_id = model.create_user(username, password, email)
        if user_id:
            flash('Inscription réussie! Vous pouvez maintenant vous connecter.')
            return redirect(url_for('login'))
        else:
            flash('Nom d\'utilisateur ou email déjà utilisé.')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

# Routes de profil utilisateur
@app.route('/profile', methods=['GET'])
@login_required
def profile():
    user = model.get_user(session['user_id'])
    user_sports = model.get_user_sports(session['user_id'])
    sports = model.get_all_sports()
    skill_levels = model.get_all_skill_levels()
    
    return render_template('profile.html', 
                          user=user, 
                          user_sports=user_sports, 
                          sports=sports, 
                          skill_levels=skill_levels)

@app.route('/profile/sports', methods=['POST'])
@login_required
def add_user_sport():
    sport_id = int(request.form['sport_id'])
    skill_level_id = int(request.form['skill_level_id'])
    
    model.add_user_sport(session['user_id'], sport_id, skill_level_id)
    flash('Sport ajouté à votre profil!')
    
    return redirect(url_for('profile'))

@app.route('/profile/sports/<int:sport_id>', methods=['DELETE'])
@login_required
def remove_user_sport(sport_id):
    # Implémentation à faire - Suppression d'un sport
    return jsonify({'success': True})

# Routes de gestion des sessions
@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Récupérer les filtres de la requête
    filters = {}
    if request.args.get('sport_id'):
        filters['sport_id'] = int(request.args.get('sport_id'))
    if request.args.get('skill_level_id'):
        filters['skill_level_id'] = int(request.args.get('skill_level_id'))
    if request.args.get('date_from'):
        filters['date_from'] = request.args.get('date_from')
    if request.args.get('status'):
        filters['status'] = request.args.get('status')
    
    sessions = model.get_sessions(filters)
    sports = model.get_all_sports()
    skill_levels = model.get_all_skill_levels()
    
    return render_template('home.html', 
                          sessions=sessions, 
                          sports=sports, 
                          skill_levels=skill_levels,
                          filters=filters)

@app.route('/sessions/new', methods=['GET'])
@login_required
def new_session():
    sports = model.get_all_sports()
    skill_levels = model.get_all_skill_levels()
    
    return render_template('create_session.html', 
                          sports=sports, 
                          skill_levels=skill_levels,
                          datetime=datetime)


@app.route('/create_session', methods=['GET', 'POST'])
@login_required
def create_session():
    sports = model.get_all_sports()
    skill_levels = model.get_all_skill_levels()
    
    if request.method == 'POST':
        try:
            # Récupération des données du formulaire
            sport_id = int(request.form['sport_id'])
            location = request.form['location']
            datetime_str = request.form['datetime']  
            min_players = int(request.form['min_players'])
            max_players = int(request.form['max_players'])
            skill_level_id = int(request.form['skill_level_id'])
            description = request.form['description']

            # Conversion du format datetime
            # Le format reçu du formulaire HTML est '%Y-%m-%dT%H:%M'
            datetime_obj = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M')
            # Convertir en chaîne au format que la base de données attend
            datetime_db_format = datetime_obj.strftime('%Y-%m-%d %H:%M:%S')

            # Création de la session dans la base de données
            session_id = model.create_session(
                sport_id=sport_id,
                creator_id=session['user_id'],
                location=location,
                datetime_str=datetime_db_format,  # Passer la chaîne formatée
                min_players=min_players,
                max_players=max_players,
                skill_level_id=skill_level_id,
                description=description
            )

            if not session_id:
                flash("Erreur lors de la création de la session")
                return render_template('create_session.html',
                                      sports=sports,
                                      skill_levels=skill_levels,
                                      form_data=request.form)

            flash('Session créée avec succès!')
            return redirect(url_for('session_details', session_id=session_id))

        except ValueError as e:
            flash(f'Erreur de format: {str(e)}')
            return render_template('create_session.html',
                                  sports=sports,
                                  skill_levels=skill_levels,
                                  form_data=request.form)
        except Exception as e:
            import traceback
            print(traceback.format_exc())  # Pour le débogage
            flash(f'Une erreur est survenue: {str(e)}')
            return render_template('create_session.html',
                                  sports=sports,
                                  skill_levels=skill_levels,
                                  form_data=request.form)
    
    # GET request - afficher le formulaire
    return render_template('create_session.html',
                         sports=sports,
                         skill_levels=skill_levels)
    
@app.route('/sessions/<int:session_id>', methods=['GET'])
@login_required
def session_details(session_id):
    sport_session = model.get_session(session_id)
    if not sport_session:
        flash('Session introuvable.')
        return redirect(url_for('home'))
    
    participants = model.get_session_participants(session_id)
    
    # Vérifier si l'utilisateur participe à cette session
    is_participant = False
    for p in participants:
        if p['user_id'] == session['user_id']:
            is_participant = True
            break
    
    # Vérifier si l'utilisateur est le créateur
    is_creator = sport_session['creator_id'] == session['user_id']
    
    return render_template('session_details.html', 
                          session=sport_session, 
                          participants=participants,
                          is_participant=is_participant,
                          is_creator=is_creator)

@app.route('/sessions/<int:session_id>/join', methods=['POST'])
@login_required
def join_session(session_id):
    model.join_session(session_id, session['user_id'])
    flash('Vous avez rejoint la session!')
    return redirect(url_for('session_details', session_id=session_id))

@app.route('/sessions/<int:session_id>/update-status', methods=['POST'])
@login_required
def update_session_status(session_id):
    sport_session = model.get_session(session_id)
    if not sport_session:
        flash('Session introuvable.')
        return redirect(url_for('home'))
    # Vérifie que l'utilisateur est bien le créateur
    if sport_session['creator_id'] != session['user_id']:
        flash('Action non autorisée :Seul le créateur peut modifier le statut de la session.')
        return redirect(url_for('session_details', session_id=session_id))
     # Récupère le nouveau statut depuis le formulaire
    new_status = request.form.get('status')
   
    # Valide le statut (protection contre les valeurs incorrectes)
    valid_statuses = ['ouvert', 'complet', 'annulé']
    if new_status not in valid_statuses:
        flash('Statut invalide.')
        return redirect(url_for('session_details', session_id=session_id))
    
    # Met à jour le statut en base de données
    model.update_session_status(session_id, new_status)
    
    flash(f'Statut de la session mis à jour : {new_status}')
    return redirect(url_for('session_details', session_id=session_id))

@app.route('/sessions/<int:session_id>/leave', methods=['POST'])
@login_required
def leave_session(session_id):
    model.leave_session(session_id, session['user_id'])
    flash('Vous avez quitté la session.')
    return redirect(url_for('session_details', session_id=session_id))


@app.route('/my-sessions', methods=['GET'])
@login_required
def my_sessions():
    created_sessions = model.get_user_created_sessions(session['user_id'])
    participating_sessions = model.get_user_participating_sessions(session['user_id'])
    
    # Convertir les objets Row en dictionnaires pour pouvoir les modifier
    created_sessions_list = [dict(s) for s in created_sessions]
    participating_sessions_list = [dict(s) for s in participating_sessions]
    
    # Formater les dates et calculer les différences
    now = datetime.now()
    for s in created_sessions_list:
        s['time_remaining'] = calculate_time_remaining(s['datetime'], now)
    
    for s in participating_sessions_list:
        s['time_remaining'] = calculate_time_remaining(s['datetime'], now)
    
    return render_template('my_sessions.html', 
                         created_sessions=created_sessions_list,
                         participating_sessions=participating_sessions_list,
                         now=now)
def calculate_time_remaining(session_datetime, current_datetime):
    """Calcule la différence entre deux dates et retourne un string formaté"""
    if isinstance(session_datetime, str):
        try:
            session_datetime = datetime.strptime(session_datetime, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            session_datetime = datetime.strptime(session_datetime, '%Y-%m-%d %H:%M:%S.%f')
    
    delta = session_datetime - current_datetime
    total_seconds = delta.total_seconds()
    
    if total_seconds < 0:
        return "session terminée"
    days = int(total_seconds // 86400)
    hours = int((total_seconds % 86400) // 3600)
    minutes = int((total_seconds % 3600) // 60)
    
    return f"{days}j {hours}h {minutes}m"
# Routes API pour les interactions dynamiques
@app.route('/api/sessions', methods=['GET'])
@login_required
def api_sessions():
    # Récupérer les filtres de la requête
    filters = {}
    if request.args.get('sport_id'):
        filters['sport_id'] = int(request.args.get('sport_id'))
    if request.args.get('skill_level_id'):
        filters['skill_level_id'] = int(request.args.get('skill_level_id'))
    if request.args.get('date_from'):
        filters['date_from'] = request.args.get('date_from')
    if request.args.get('status'):
        filters['status'] = request.args.get('status')
    
    sessions = model.get_sessions(filters)
    
    # Convertir les objets Row en dictionnaires pour la sérialisation JSON
    sessions_list = []
    for session in sessions:
        session_dict = dict(session)
        # Convertir la date en chaîne pour la sérialisation JSON
        if 'datetime' in session_dict:
            session_dict['datetime'] = str(session_dict['datetime'])
        sessions_list.append(session_dict)
    
    return jsonify(sessions_list)

@app.route('/api/sports', methods=['GET'])
@login_required
def api_sports():
    sports = model.get_all_sports()
    sports_list = [dict(sport) for sport in sports]
    return jsonify(sports_list)

if __name__ == '__main__':
    app.run(debug=True)