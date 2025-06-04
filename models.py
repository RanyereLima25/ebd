from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date

db = SQLAlchemy()

class Pessoa(db.Model):
    class Pessoa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(14), nullable=False, unique=True)
    #nascimento = db.Column(db.String(10), nullable=False)
    nascimento = db.Column(db.Date)
    email = db.Column(db.String(100))
    telefone = db.Column(db.String(20))
    tipo = db.Column(db.String(20), nullable=False)
    matricula = db.Column(db.String(20))
    classe = db.Column(db.String(100))
    sala = db.Column(db.String(20))
    ano_ingresso = db.Column(db.String(4)) 
    cep = db.Column(db.String(10))
    rua = db.Column(db.String(100))
    numero = db.Column(db.String(10))
    complemento = db.Column(db.String(50))
    bairro = db.Column(db.String(100)) 
    cidade = db.Column(db.String(100))
    estado = db.Column(db.String(50)) 
    classe = db.Column(db.String(50))

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(150), unique=True, nullable=False)
    senha_hash = db.Column(db.String(256), nullable=False)

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def checar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)
