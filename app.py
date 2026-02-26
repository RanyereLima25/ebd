from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
import os
import pytz

app = Flask(__name__)

# =====================================================
# CONFIGURAÇÕES
# =====================================================
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "ebd-secret-key")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///cadastro_ebd.db"

db = SQLAlchemy(app)

# =====================================================
# CONTEXT PROCESSOR (resolve {{ agora.year }})
# =====================================================
@app.context_processor
def inject_now():
    return {'agora': datetime.now()}

# =====================================================
# FILTROS
# =====================================================
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

# =====================================================
# MODELOS
# =====================================================
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

# =====================================================
# DECORADOR LOGIN REQUIRED
# =====================================================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash("Você precisa estar logado.")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# =====================================================
# ROTAS
# =====================================================

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

@app.route('/cadastro', methods=['GET', 'POST'])
@login_required
def cadastro():
    if request.method == 'POST':
        dados = request.form.to_dict()

        nova_pessoa = Pessoa(
            nome=dados.get('nome'),
            cpf=dados.get('cpf'),
            nascimento=dados.get('nascimento') or None,
            email=dados.get('email'),
            telefone=dados.get('telefone'),
            tipo=dados.get('tipo'),
            matricula=Usuario.gerar_matricula(),
            classe=dados.get('classe'),
            sala=dados.get('sala'),
            ano_ingresso=dados.get('ano_ingresso'),
            cep=dados.get('cep'),
            rua=dados.get('rua'),
            numero=dados.get('numero'),
            complemento=dados.get('complemento'),
            bairro=dados.get('bairro'),
            cidade=dados.get('cidade'),
            estado=dados.get('estado'),
            sexo=dados.get('sexo'),
            escolaridade=dados.get('escolaridade'),
            curso_teologia=dados.get('curso_teologia'),
            curso_lider=dados.get('curso_lider'),
            batizado=dados.get('batizado'),
            profissao=dados.get('profissao_outro') or dados.get('profissao')
        )

        db.session.add(nova_pessoa)
        db.session.commit()
        flash('Cadastro realizado com sucesso.')
        return redirect(url_for('visualizar'))

    usuario_logado = Usuario.query.get(session['usuario_id']).login
    return render_template('cadastro.html', usuario=usuario_logado)

@app.route('/visualizar')
@login_required
def visualizar():
    pessoas = Pessoa.query.order_by(Pessoa.classe, Pessoa.nome).all()
    usuario_logado = Usuario.query.get(session['usuario_id']).login
    return render_template('visualizar.html', pessoas=pessoas, total=len(pessoas), usuario=usuario_logado)


# =====================================================
# ERRO 404
# =====================================================
@app.errorhandler(404)
def pagina_nao_encontrada(e):
    return "<h2>Página não encontrada</h2>", 404

# =====================================================
# INICIALIZAÇÃO
# =====================================================
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("Banco verificado/criado com sucesso!")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
