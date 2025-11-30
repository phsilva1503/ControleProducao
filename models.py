# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import date

db = SQLAlchemy()

class Componente(db.Model):
    __tablename__ = "componente"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    ativo = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<Componente {self.nome}>"


class Producao(db.Model):
    __tablename__ = "producao"

    id = db.Column(db.Integer, primary_key=True)
    producao_id = db.Column(db.String(50), unique=True, nullable=False)
    data_producao = db.Column(db.Date, default=date.today, nullable=False)
    tipo_espuma = db.Column(db.String(50), nullable=False)
    cor = db.Column(db.String(30), nullable=False)
    conformidade = db.Column(db.String(20), nullable=False)
    observacoes = db.Column(db.Text)
    altura = db.Column(db.Float, nullable=True, default=0.0)

    componentes = db.relationship('ComponenteProducao',back_populates='producao',cascade='all, delete-orphan')
    def __repr__(self):
        return f"<Producao {self.producao_id}>"


class ComponenteProducao(db.Model):
    __tablename__ = "componenteproducao"  # ou manter maiúsculo, mas deve bater com FK
    id = db.Column(db.Integer, primary_key=True)
    producao_id = db.Column(db.Integer, db.ForeignKey("producao.id"), nullable=False)
    componente_id = db.Column(db.Integer, db.ForeignKey("componente.id"), nullable=False)
    quantidade_usada = db.Column(db.Float, nullable=False)

    componente = db.relationship("Componente")
    producao = db.relationship("Producao", back_populates="componentes")
    def __repr__(self):
        return f"<ComponenteProducao Produção:{self.producao_id} Componente:{self.componente_id} Qtd:{self.quantidade_usada}>"

class Movimentacao(db.Model):
    __tablename__ = "movimentacao"
    id = db.Column(db.Integer, primary_key=True)
    componente_id = db.Column(db.Integer, db.ForeignKey("componente.id"), nullable=False)
    tipo = db.Column(db.String(10), nullable=False)  # 'entrada' ou 'saida'
    quantidade = db.Column(db.Float, nullable=False)
    data = db.Column(db.Date, default=date.today, nullable=False)
    producao_id = db.Column(db.Integer, db.ForeignKey("producao.id"), nullable=True)

    componente = db.relationship("Componente", backref="movimentacoes")
    producao = db.relationship("Producao", backref="movimentacoes")

    def __repr__(self):
        return f"<Movimentacao Componente={self.componente_id}, Tipo={self.tipo}, Qtd={self.quantidade}, Data={self.data}>"

class Estoque(db.Model):
    __tablename__ = "estoque"
    id = db.Column(db.Integer, primary_key=True)
    componente_id = db.Column(db.Integer, db.ForeignKey("componente.id"), nullable=False)
    quantidade = db.Column(db.Float, default=0.0, nullable=False)

    componente = db.relationship("Componente", backref="estoque")

    def __repr__(self):
        return f"<Estoque Componente={self.componente_id}, Qtd={self.quantidade}>"
    
class FichaTecnica(db.Model):
    __tablename__ = "ficha_tecnica"

    id = db.Column(db.Integer, primary_key=True)
    tipo_espuma_id = db.Column(db.Integer, db.ForeignKey('tipo_espuma.id'), nullable=False)
    descricao = db.Column(db.Text, nullable=True)

    tipo_espuma = db.relationship("TipoEspuma", back_populates="fichas_tecnicas")

    componentes = db.relationship("FichaTecnicaComponente",back_populates="ficha_tecnica",cascade="all, delete-orphan")

    def __repr__(self):
        return f"<FichaTecnica {self.tipo_espuma}>"
    

class TipoEspuma(db.Model):
    __tablename__ = "tipo_espuma"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), unique=True, nullable=False)

    fichas_tecnicas = db.relationship("FichaTecnica", back_populates="tipo_espuma")

    def __repr__(self):
        return f"<TipoEspuma {self.nome}>"



class FichaTecnicaComponente(db.Model):
    __tablename__ = 'ficha_tecnica_componente'
    id = db.Column(db.Integer, primary_key=True)
    ficha_tecnica_id = db.Column(db.Integer, db.ForeignKey('ficha_tecnica.id'), nullable=False)
    componente_id = db.Column(db.Integer, db.ForeignKey('componente.id'), nullable=False)

    ficha_tecnica = db.relationship("FichaTecnica", back_populates="componentes")
    componente = db.relationship("Componente", backref="fichas_tecnicas")

    def __repr__(self):
        return f"<FichaTecnicaComponente FichaTecnicaID={self.ficha_tecnica_id}, ComponenteID={self.componente_id}>"


__all__ = ["db", "Componente", "Producao", "ComponenteProducao", "Movimentacao", "Estoque", "FichaTecnica", "FichaTecnicaComponente", "TipoEspuma"]

