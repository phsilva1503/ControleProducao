import os
from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate

from models import db, Usuario
from routes import routes

# -----------------------
# BASE DIR
# -----------------------
base_dir = os.path.dirname(os.path.abspath(__file__))

# -----------------------
# CONFIGURAÇÃO DO APP
# -----------------------
app = Flask(__name__, template_folder=os.path.join(base_dir, "templates"))

# -----------------------
# CONFIGURAÇÃO DO AMBIENTE
# -----------------------
IS_RENDER = os.environ.get("RENDER") is not None

# -----------------------
# BANCO DE DADOS
# -----------------------
if IS_RENDER:
    # Render já monta o volume persistente em /data
    db_path = "/data/producao.db"  # use diretamente, não faça makedirs
else:
    # Ambiente local
    instance_path = os.path.join(base_dir, "instance")
    os.makedirs(instance_path, exist_ok=True)
    db_path = os.path.join(instance_path, "producao.db")

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# -----------------------
# SEGURANÇA
# -----------------------
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")

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
# ROTAS
# -----------------------
routes(app)

# -----------------------
# START
# -----------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=not IS_RENDER)
