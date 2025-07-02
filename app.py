from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from collections import defaultdict
from datetime import datetime
import os

app = Flask(__name__)

# =============================
# CONFIGURAÇÃO DO BANCO
# =============================
DATABASE_URL = "postgresql://postgres.asvombxvhklbqkmprzdy:CADASTRO-EBD@aws-0-sa-east-1.pooler.supabase.com:5432/postgres"

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'ebd'

db = SQLAlchemy(app)

# =============================
# MODELOS
# =============================

class Pessoa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(20), nullable=False, unique=True)
    nascimento = db.Column(db.String(10))
    email = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)
    tipo = db.Column(db.String(20))
    matricula = db.Column(db.String(20))
    classe = db.Column(db.String(100), nullable=False)
    sala = db.Column(db.String(20))
    ano_ingresso = db.Column(db.String(4))
    sexo = db.Column(db.String(20))
    cep = db.Column(db.String(10))
    rua = db.Column(db.String(100))
    numero = db.Column(db.String(10))
    complemento = db.Column(db.String(100))
    bairro = db.Column(db.String(100))
    cidade = db.Column(db.String(100))
    estado = db.Column(db.String(100))

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(150), unique=True, nullable=False)
    senha_hash = db.Column(db.String(256), nullable=False)

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def checar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

# =============================
# FUNÇÃO PARA GERAR MATRÍCULA
# =============================

def gerar_matricula():
    agora = datetime.now()
    ano = agora.year
    mes = f'{agora.month:02d}'
    prefixo = f"{ano}.{mes}"

    # Verificar quantas matrículas já existem no mês
    ultimo = Pessoa.query.filter(Pessoa.matricula.like(f"{prefixo}.%")).count() + 1
    numero = f"{ultimo:04d}"

    return f"{prefixo}.{numero}"

# =============================
# DECORADORES E FILTROS
# =============================

# (continua normalmente com o restante do código)
