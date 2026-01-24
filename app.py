import os
from flask import Flask
from models import *
from flask_migrate import Migrate
from routes import routes  # Importa suas rotas definidas
from flask_login import LoginManager

# -----------------------
# DIRETÓRIO BASE E TEMPLATES
# -----------------------
base_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(base_dir, "templates")

# -----------------------
# CONFIGURAÇÃO DO APP
# -----------------------
app = Flask(__name__, template_folder=template_dir)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///producao.db'  # Banco SQLite
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = '123'  # Para produção, gerar uma chave mais segura

# -----------------------
db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.login_view = "login"  # rota de login
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id)) 

with app.app_context():
    db.create_all()
    print("✅ Banco 'producao.db' criado/verificado com sucesso!")

# Registrando rotas
routes(app) 

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

