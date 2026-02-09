import os
from flask import Flask
from models import *
from flask_migrate import Migrate
from routes import routes
from flask_login import LoginManager

# -----------------------
# DIRETÓRIO BASE E VOLUME
# -----------------------
base_dir = os.path.dirname(os.path.abspath(__file__))

if os.environ.get("RENDER"):
    # Ambiente Render
    volume_path = "/data"  # volume configurado no Render
    db_dir = os.path.join(volume_path, "sqlite")  # subpasta para gravar DB
    os.makedirs(db_dir, exist_ok=True)
    db_path = os.path.join(db_dir, "producao.db")
else:
    # Desenvolvimento local
    instance_path = os.path.join(base_dir, "instance")
    os.makedirs(instance_path, exist_ok=True)
    db_path = os.path.join(instance_path, "producao.db")

db_uri = f"sqlite:///{db_path}"

# -----------------------
# CONFIGURAÇÃO DO APP
# -----------------------
app = Flask(__name__, template_folder=os.path.join(base_dir, "templates"))
app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "123"  # em produção use variável de ambiente segura

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
