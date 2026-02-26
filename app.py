from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
import os
import pytz

app = Flask(__name__)

# =============================
# CONTEXT PROCESSOR (RESOLVE AGORA NO BASE.HTML)
# =============================
@app.context_processor
def inject_now():
    return {'agora': datetime.now()}

# =============================
# FILTROS
# =============================
@app.template_filter('mes_em_portugues')
def mes_em_portugues(mes_ingles):
    meses = {
        'January': 'Janeiro', 'February': 'Fevereiro', 'March': 'Março',
        'April': 'Abril', 'May': 'Maio', 'June': 'Junho',
        'July': 'Julho', 'August': 'Agosto', 'September': 'Setembro',
        'October': 'Outubro', 'November': 'Novembro', 'December': 'Dezembro'
    }
    return meses.get(mes_ingles, mes_ingles)

@app.template_filter('formatadata')
def formatadata(value):
    if not value:
        return "-"
    try:
        return datetime.strptime(value, '%Y-%m-%d').strftime('%d/%m/%Y')
    except:
        return value

# =============================
# BANCO
# =============================
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
else:
    db_path = 'cadastro_ebd.db'
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

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(150), unique=True, nullable=False)
    senha_hash = db.Column(db.String(256), nullable=False)
    ultimo_login = db.Column(db.DateTime)

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def checar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

# =============================
# LOGIN REQUIRED
# =============================
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Você precisa estar logado.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# =============================
# ROTAS
# =============================
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = Usuario.query.filter_by(login=request.form['login']).first()
        if usuario and usuario.checar_senha(request.form['senha']):
            tz = pytz.timezone("America/Sao_Paulo")
            usuario.ultimo_login = datetime.now(tz)
            db.session.commit()
            session['usuario_id'] = usuario.id
            return redirect(url_for('visualizar'))
        flash('Login inválido.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/registrar', methods=['GET', 'POST'])
def registrar():
    if request.method == 'POST':
        if Usuario.query.filter_by(login=request.form['login']).first():
            flash('Usuário já existe.')
        else:
            novo = Usuario(login=request.form['login'])
            novo.set_senha(request.form['senha'])
            db.session.add(novo)
            db.session.commit()
            flash('Usuário criado.')
            return redirect(url_for('login'))
    return render_template('registrar.html')

@app.route('/visualizar')
@login_required
def visualizar():
    pessoas = Pessoa.query.order_by(Pessoa.classe, Pessoa.nome).all()
    return render_template('visualizar.html', pessoas=pessoas)

# =============================
# ROTAS QUE ESTAVAM QUEBRANDO
# =============================
@app.route('/relatorios')
@login_required
def relatorios():
    total = Pessoa.query.count()
    return render_template('relatorios.html', total=total)

@app.route('/graficos')
@login_required
def graficos():
    total = Pessoa.query.count()
    return render_template('graficos.html', total=total)

# =============================
# ERRO 404
# =============================
@app.errorhandler(404)
def pagina_nao_encontrada(e):
    return "<h2>Página não encontrada</h2>", 404

# =============================
# EXECUÇÃO
# =============================
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("Banco pronto!")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
