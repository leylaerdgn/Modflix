from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    
    # İlişkiler (One-to-Many)
    # lazy=True: Veriler sadece ihtiyaç duyulduğunda yüklenir (performans için)
    # cascade="all, delete-orphan": Kullanıcı silinirse, ilişkili verileri de silinir
    favorites = db.relationship('Favorite', backref='user', lazy=True, cascade="all, delete-orphan")
    watched = db.relationship('Watched', backref='user', lazy=True, cascade="all, delete-orphan")
    watchlist = db.relationship('Watchlist', backref='user', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<User {self.username}>'

# Ortak alanlar için soyut sınıf (Tekrarı önlemek için)
class BaseMovie(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    movie_id = db.Column(db.Integer, nullable=False) # TMDB Movie ID
    title = db.Column(db.String(255), nullable=False)
    poster_path = db.Column(db.String(255))

class Favorite(BaseMovie):
    __tablename__ = 'favorites'
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Favorite {self.title}>'

class Watched(BaseMovie):
    __tablename__ = 'watched'
    rating = db.Column(db.Float, nullable=True) # Kullanıcının filme verdiği puan (opsiyonel)
    watched_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Watched {self.title}>'

class Watchlist(BaseMovie):
    __tablename__ = 'watchlist'
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Watchlist {self.title}>'

# Veritabanını oluşturmak için yardımcı fonksiyon (app.py içinde çağrılacak)
def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()