from flask import Flask
from flask_login import LoginManager
from models import db, init_db, User
from dotenv import load_dotenv
import os

# Blueprint Importları
from routes.main import main_bp
from routes.auth import auth_bp
from routes.movie import movie_bp

load_dotenv()

app = Flask(__name__, template_folder='templates')
app.secret_key = 'cok_gizli_bir_anahtar'

# Veritabanı Ayarları
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'main.index'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Blueprint'leri Kaydet
app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(movie_bp)

# Veritabanını Başlat
init_db(app)

if __name__ == '__main__':
    app.run(debug=True)
