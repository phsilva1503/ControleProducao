import os
from flask import Flask
from models import *
from flask_migrate import Migrate
from routes import routes
from flask_login import LoginManager

# -----------------------
# DIRETÓRIO DE TEMPLATES
# -----------------------
base_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(base_dir, "templates")

# -----------------------
# CONFIGURAÇÃO DO APP
# -----------------------
app = Flask(__name__, template_folder=template_dir)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = '123'  # Em produção, use variável de ambiente segura

# -----------------------
# BANCO DE DADOS (LOCAL x RENDER)
# -----------------------
if os.environ.get("RENDER"):
    # Caminho do volume persistente no Render (não criar subpastas!)
    db_path = "/data/producao.db"
else:
    # Banco local para desenvolvimento
    instance_path = os.path.join(base_dir, "instance")
    os.makedirs(instance_path, exist_ok=True)
    db_path = os.path.join(instance_path, "producao.db")

app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"

# -----------------------
# EXTENSÕES
# -----------------------
db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# -----------------------
# CRIAÇÃO DO BANCO (somente se não existir)
# -----------------------
with app.app_context():
    db.create_all()
    print(f"✅ Banco '{db_path}' criado/verificado com sucesso!")

# -----------------------
# ROTAS
# -----------------------
routes(app)

# -----------------------
# START
# -----------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
