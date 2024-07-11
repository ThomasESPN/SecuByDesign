from flask import request, jsonify, render_template, redirect, url_for, current_app, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from markupsafe import escape
from app import db
from app.models import User, Book, Borrow

# Variables pour les modes
SAFE_MODE = True
MAX_LOGIN_ATTEMPTS = 5

# Routes pour changer de mode
@current_app.route('/set_mode/<mode>')
def set_mode(mode):
    global SAFE_MODE
    SAFE_MODE = (mode == 'safe')
    return redirect(url_for('index'))

@current_app.route('/')
def index():
    return render_template('index.html', safe_mode=SAFE_MODE)

@current_app.route('/register_login')
def register_login():
    return render_template('register_login.html', safe_mode=SAFE_MODE)

@current_app.route('/books', methods=['GET', 'POST'])
def books():
    search_query = request.form.get('search') if request.method == 'POST' else None
    if SAFE_MODE and search_query:
        search_query = escape(search_query)  # Protection XSS
        all_books = Book.query.filter(Book.title.like(f"%{search_query}%")).all()
    elif search_query:
        all_books = db.session.execute(f"SELECT * FROM book WHERE title LIKE '%{search_query}%'").fetchall()
    else:
        all_books = Book.query.all()
    return render_template('books.html', safe_mode=SAFE_MODE, books=all_books)

@current_app.route('/borrow')
def borrow():
    if SAFE_MODE and 'user_id' not in session:
        return redirect(url_for('register_login'))
    
    if SAFE_MODE:
        user_id = session['user_id']
        borrowed_books = db.session.query(Borrow, Book).join(Book).filter(Borrow.user_id == user_id).all()
    else:
        borrowed_books = db.session.query(Borrow, User, Book).join(User).join(Book).all()
    
    return render_template('borrow.html', safe_mode=SAFE_MODE, borrowed_books=borrowed_books)


# Enregistrement de compte utilisateur
@current_app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if SAFE_MODE:
        username = escape(username)  # Protection XSS
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    else:
        hashed_password = password
    
    new_user = User(username=username, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': 'Utilisateur inscrit avec succès'})

# Connexion utilisateur
login_attempts = {}

@current_app.route('/login', methods=['POST'])
def login():
    global login_attempts
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'message': 'Utilisateur non trouvé'}), 404
    
    if SAFE_MODE:
        if not check_password_hash(user.password, password):
            return jsonify({'message': 'Mot de passe incorrect'}), 401
    else:
        try:
            # Essayez de vérifier le mot de passe haché, si possible
            if check_password_hash(user.password, password):
                # Mot de passe correct
                pass
            else:
                if username in login_attempts and login_attempts[username] >= MAX_LOGIN_ATTEMPTS:
                    return jsonify({'message': 'Trop de tentatives'}), 403
                if user.password != password:
                    login_attempts[username] = login_attempts.get(username, 0) + 1
                    return jsonify({'message': 'Mot de passe incorrect'}), 401
        except ValueError:
            # Comparer directement en clair si le mot de passe n'est pas haché
            if username in login_attempts and login_attempts[username] >= MAX_LOGIN_ATTEMPTS:
                return jsonify({'message': 'Trop de tentatives'}), 403
            if user.password != password:
                login_attempts[username] = login_attempts.get(username, 0) + 1
                return jsonify({'message': 'Mot de passe incorrect'}), 401
    
    login_attempts[username] = 0
    session['user_id'] = user.id
    return jsonify({'message': 'Connecté avec succès', 'redirect': url_for('borrow')})

# Déconnexion utilisateur
@current_app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Vous avez été déconnecté.')
    return redirect(url_for('register_login'))

# Emprunt de livres
@current_app.route('/borrow_book', methods=['POST'])
def borrow_book():
    if SAFE_MODE and 'user_id' not in session:
        return jsonify({'message': 'Non autorisé'}), 401

    data = request.get_json()
    user_id = data.get('user_id')
    book_id = data.get('book_id')
    
    if SAFE_MODE:
        existing_borrow = Borrow.query.filter_by(book_id=book_id).first()
        if existing_borrow:
            return jsonify({'message': 'Livre déjà emprunté'}), 400
    
    new_borrow = Borrow(user_id=user_id, book_id=book_id)
    db.session.add(new_borrow)
    db.session.commit()
    
    return jsonify({'message': 'Livre emprunté avec succès'})
