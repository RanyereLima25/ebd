from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from collections import defaultdict
from datetime import datetime
import os
import pytz

# =============================
# CONFIGURAÇÃO DO APP
# =============================
app = Flask(__name__)

# =============================
# FILTROS DE TEMPLATE
# =============================
@app.template_filter('mes_em_portugues')
def mes_em_portugues(mes_ingles):
    meses = {
        'January': 'Janeiro',
        'February': 'Fevereiro',
        'March': 'Março',
        'April': 'Abril',
        'May': 'Maio',
        'June': 'Junho',
        'July': 'Julho',
        'August': 'Agosto',
        'September': 'Setembro',
        'October': 'Outubro',
        'November': 'Novembro',
        'December': 'Dezembro'
    }
    return meses.get(mes_ingles, mes_ingles)

@app.template_filter('formatadata')
def formatadata(value):
    if not value:
        return "-"
    try:
        return datetime.strptime(value, '%Y-%m-%d').strftime('%d/%m/%Y')
    except Exception:
        return value

# =============================
# CONFIGURAÇÃO DO BANCO
# =============================
# Use pasta persistente no Render para o SQLite
db_path = '/opt/render/project/data/cadastro_ebd.db'
os.makedirs(os.path.dirname(db_path), exist_ok=True)

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "ebd-secret-key")

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
    escolaridade = db.Column(db.String(100))
    curso_teologia = db.Column(db.String(100))
    curso_lider = db.Column(db.String(100))
    batizado = db.Column(db.String(100))
    profissao = db.Column(db.String(100))

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(150), unique=True, nullable=False)
    senha_hash = db.Column(db.String(256), nullable=False)
    ultimo_login = db.Column(db.DateTime, nullable=True)

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def checar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    @staticmethod
    def gerar_matricula():
        agora = datetime.now()
        ano = agora.year
        mes = f'{agora.month:02d}'
        prefixo = f"{ano}.{mes}"
        ultimo = Pessoa.query.filter(Pessoa.matricula.like(f"{prefixo}.%")).count() + 1
        numero = f"{ultimo:04d}"
        return f"{prefixo}.{numero}"

# =============================
# DECORADORES
# =============================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Você precisa estar logado para acessar esta página.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# =============================
# ROTAS
# =============================
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_form = request.form['login']
        senha_form = request.form['senha']
        usuario = Usuario.query.filter_by(login=login_form).first()
        if usuario and usuario.checar_senha(senha_form):
            tz = pytz.timezone("America/Sao_Paulo")
            usuario.ultimo_login = datetime.now(tz)
            db.session.commit()
            session['usuario_id'] = usuario.id
            flash('Login realizado com sucesso.')
            return redirect(url_for('visualizar'))
        else:
            flash('Login ou senha inválidos.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('usuario_id', None)
    flash('Você saiu do sistema.')
    return redirect(url_for('login'))

@app.route('/registrar', methods=['GET', 'POST'])
def registrar():
    if request.method == 'POST':
        login_form = request.form['login']
        senha_form = request.form['senha']
        if Usuario.query.filter_by(login=login_form).first():
            flash('Usuário já existe.')
        else:
            novo_usuario = Usuario(login=login_form)
            novo_usuario.set_senha(senha_form)
            db.session.add(novo_usuario)
            db.session.commit()
            flash('Usuário registrado com sucesso.')
            return redirect(url_for('login'))
    return render_template('registrar.html')

# ... (adicione aqui as outras rotas seguindo o mesmo padrão)

# =============================
# EXECUÇÃO
# =============================
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
