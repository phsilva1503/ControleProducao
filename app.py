import os
from flask import Flask
from models import *
from flask_migrate import Migrate
from routes import routes
from flask_login import LoginManager

# -----------------------
# DIRETÓRIO DO VOLUME
# -----------------------
volume_path = "/data"  # caminho do volume no Render
os.makedirs(volume_path, exist_ok=True)  # garante que a pasta exista

# -----------------------
# BANCO DE DADOS
# -----------------------
db_path = os.path.join(volume_path, "producao.db")
db_uri = f"sqlite:///{db_path}"

# -----------------------
# DIRETÓRIO DE TEMPLATES
# -----------------------
base_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(base_dir, "templates")

# -----------------------
# CONFIGURAÇÃO DO APP
# -----------------------
app = Flask(__name__, template_folder=template_dir)
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = '123'  # para produção, use algo seguro

# -----------------------
db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id)) 

with app.app_context():
    db.create_all()
    print(f"✅ Banco '{db_path}' criado/verificado com sucesso!")

# Registrando rotas
routes(app) 

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
##AJUSTEFFFFGFG