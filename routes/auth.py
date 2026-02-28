from flask import Blueprint, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user
from sqlalchemy.exc import IntegrityError
from models import db, User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    hashed_password = generate_password_hash(password)

    new_user = User(username=username, email=request.form['email'], password=hashed_password)
    
    try:
        db.session.add(new_user)
        db.session.commit()
        flash('Aramıza hoş geldin! Şimdi giriş yapabilirsin. ✨', 'success')
    except IntegrityError:
        db.session.rollback()
        flash('Bu kullanıcı adı veya e-posta zaten alınmış.', 'error')
        
    return redirect(url_for('main.index'))
@auth_bp.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password, password):
        login_user(user)
        flash(f'Hoş geldiniz, {user.username}! 👋', 'success')
    else:
        flash('Kullanıcı adı veya şifre hatalı.', 'error')
    
    return redirect(url_for('main.index'))
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Görüşmek üzere! 👋', 'info')
    return redirect(url_for('main.index'))