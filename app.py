from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from collections import defaultdict
from datetime import datetime
import os

app = Flask(__name__)

# 🔧 Configurações
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL',
    'postgresql://ebd_db_k5jg_user:gr5VUsZ4cS03LAp6jSuYUBDXMWZyxoUh@dpg-d0u8c1c44c73aghr0g-a.oregon-postgres.render.com/ebd_db_k5jg'
)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'ebd')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 📦 MODELOS
class Pessoa(db.Model):
    __tablename__ = 'pessoas'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(20), nullable=False, unique=True)
    nascimento = db.Column(db.String(50))
    email = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)
    tipo = db.Column(db.String(20))
    matricula = db.Column(db.String(20))
    classe = db.Column(db.String(100), nullable=False)
    sala = db.Column(db.String(20))
    ano_ingresso = db.Column(db.String(4))
    cep = db.Column(db.String(10))
    rua = db.Column(db.String(100))
    numero = db.Column(db.String(10))
    complemento = db.Column(db.String(100))
    bairro = db.Column(db.String(100))
    cidade = db.Column(db.String(100))
    estado = db.Column(db.String(100))


class Usuario(db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(150), unique=True, nullable=False)
    senha_hash = db.Column(db.String(256), nullable=False)

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def checar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)


# 🔒 DECORADOR LOGIN
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Você precisa estar logado para acessar esta página.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# 📅 FILTRO JINJA PARA FORMATAR DATAS
@app.template_filter('formatadata')
def formatadata(value):
    if not value:
        return "-"
    try:
        if isinstance(value, datetime):
            return value.strftime('%d/%m/%Y')
        elif isinstance(value, str):
            for fmt in ('%Y-%m-%d', '%d/%m/%Y'):
                try:
                    return datetime.strptime(value, fmt).strftime('%d/%m/%Y')
                except ValueError:
                    continue
            return value
        return str(value)
    except Exception:
        return value


# 🚪 ROTAS DE LOGIN
@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_form = request.form['login']
        senha_form = request.form['senha']
        usuario = db.session.execute(
            db.select(Usuario).filter_by(login=login_form)
        ).scalar_one_or_none()

        if usuario and usuario.checar_senha(senha_form):
            session['usuario_id'] = usuario.id
            return redirect(url_for('visualizar'))
        else:
            flash('Login ou senha inválidos')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('usuario_id', None)
    return redirect(url_for('login'))


@app.route('/registrar', methods=['GET', 'POST'])
def registrar():
    if request.method == 'POST':
        login_form = request.form['login']
        senha_form = request.form['senha']
        existente = db.session.execute(
            db.select(Usuario).filter_by(login=login_form)
        ).scalar_one_or_none()

        if existente:
            flash('Usuário já existe.')
            return redirect(url_for('registrar'))

        novo_usuario = Usuario(login=login_form)
        novo_usuario.set_senha(senha_form)
        db.session.add(novo_usuario)
        db.session.commit()
        flash('Usuário registrado com sucesso.')
        return redirect(url_for('login'))
    return render_template('registrar.html')


# 👥 ROTAS DE PESSOA
@app.route('/cadastro', methods=['GET', 'POST'])
@login_required
def cadastro():
    if request.method == 'POST':
        nascimento = request.form.get('nascimento') or None

        nova_pessoa = Pessoa(
            nome=request.form['nome'],
            cpf=request.form['cpf'],
            nascimento=nascimento,
            email=request.form['email'],
            telefone=request.form['telefone'],
            tipo=request.form.get('tipo'),
            matricula=request.form['matricula'],
            classe=request.form['classe'],
            sala=request.form['sala'],
            ano_ingresso=request.form['ano_ingresso'],
            cep=request.form['cep'],
            rua=request.form['rua'],
            numero=request.form['numero'],
            complemento=request.form['complemento'],
            bairro=request.form['bairro'],
            cidade=request.form['cidade'],
            estado=request.form['estado']
        )
        db.session.add(nova_pessoa)
        db.session.commit()

        flash('Cadastro realizado com sucesso.')
        return redirect(url_for('visualizar'))

    usuario_logado = db.session.get(Usuario, session['usuario_id']).login
    return render_template('cadastro.html', usuario=usuario_logado)


@app.route('/visualizar')
@login_required
def visualizar():
    busca = request.args.get('busca', '')
    ordem = request.args.get('ordem', '')

    query = db.select(Pessoa)

    if busca:
        query = query.filter(Pessoa.nome.ilike(f'%{busca}%'))
    if ordem == 'classe':
        query = query.order_by(Pessoa.classe)

    pessoas = db.session.execute(query).scalars().all()
    usuario_logado = db.session.get(Usuario, session['usuario_id']).login

    return render_template('visualizar.html', pessoas=pessoas, total=len(pessoas), usuario=usuario_logado)


@app.route('/editar/<int:pessoa_id>', methods=['GET', 'POST'])
@login_required
def editar(pessoa_id):
    pessoa = db.session.get(Pessoa, pessoa_id)
    if not pessoa:
        flash('Pessoa não encontrada.')
        return redirect(url_for('visualizar'))

    if request.method == 'POST':
        for campo in request.form:
            if hasattr(pessoa, campo):
                setattr(pessoa, campo, request.form[campo])

        db.session.commit()
        flash('Cadastro atualizado com sucesso.')
        return redirect(url_for('visualizar'))

    return render_template('editar.html', pessoa=pessoa)


@app.route('/excluir/<int:pessoa_id>')
@login_required
def excluir(pessoa_id):
    pessoa = db.session.get(Pessoa, pessoa_id)
    if not pessoa:
        flash('Pessoa não encontrada.')
        return redirect(url_for('visualizar'))

    db.session.delete(pessoa)
    db.session.commit()
    flash('Cadastro excluído com sucesso.')
    return redirect(url_for('visualizar'))


# 📊 RELATÓRIOS
@app.route('/relatorios')
@login_required
def relatorios():
    usuario_logado = db.session.get(Usuario, session['usuario_id']).login
    return render_template('relatorios.html', usuario=usuario_logado)


@app.route('/relatorio-por-classe')
@login_required
def relatorio_por_classe():
    alunos = db.session.execute(
        db.select(Pessoa).order_by(Pessoa.classe, Pessoa.nome)
    ).scalars().all()

    dados_por_classe = defaultdict(list)
    for aluno in alunos:
        dados_por_classe[aluno.classe].append(aluno)

    return render_template('relatorio_por_classe.html', dados_por_classe=dados_por_classe)


@app.route('/relatorio-todos-alunos')
@login_required
def relatorio_todos_alunos():
    alunos = db.session.execute(
        db.select(Pessoa).order_by(Pessoa.nome)
    ).scalars().all()

    return render_template('relatorio_todos_alunos.html', alunos=alunos)


@app.route('/relatorio-aniversariantes')
@login_required
def relatorio_aniversariantes_mes():
    hoje = datetime.now()

    aniversariantes = db.session.execute(
        db.select(Pessoa).filter(
            db.extract('month', Pessoa.nascimento) == hoje.month
        ).order_by(db.extract('day', Pessoa.nascimento))
    ).scalars().all()

    return render_template('relatorio_aniversariantes.html', aniversariantes=aniversariantes, agora=hoje)


@app.route('/relatorio-por-tempo')
@login_required
def relatorio_por_tempo():
    tempo = request.args.get('tempo')
    ano_atual = datetime.now().year

    alunos = db.session.execute(
        db.select(Pessoa).order_by(Pessoa.classe, Pessoa.nome)
    ).scalars().all()

    alunos_filtrados = []

    if tempo and tempo.isdigit():
        tempo = int(tempo)
        for aluno in alunos:
            if aluno.ano_ingresso and aluno.ano_ingresso.isdigit():
                anos_no_sistema = ano_atual - int(aluno.ano_ingresso)
                if anos_no_sistema == tempo:
                    alunos_filtrados.append(aluno)
    else:
        alunos_filtrados = alunos

    return render_template('relatorio_por_tempo.html', alunos_filtrados=alunos_filtrados)


@app.route('/graficos')
@login_required
def graficos():
    dados = db.session.execute(
        db.select(Pessoa.classe, db.func.count(Pessoa.id)).group_by(Pessoa.classe)
    ).all()

    labels = [d[0] for d in dados]
    valores = [d[1] for d in dados]

    usuario_logado = db.session.get(Usuario, session['usuario_id']).login

    return render_template('graficos.html', labels=labels, valores=valores, usuario=usuario_logado)


# 🏗️ CRIA O BANCO SE NÃO EXISTIR
with app.app_context():
    db.create_all()




======================
from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from collections import defaultdict
from datetime import datetime
import os

app = Flask(__name__)

# Configurações
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cadastro.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://ebd_db_k5jg_user:gr5VUsZ4cS03LAp6jSuYUBDXMWZyxoUh@dpg-d0u8c1c9c44c73aghr0g-a.oregon-postgres.render.com/ebd_db_k5jg'
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'ebd')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# MODELOS
class Pessoa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(20), nullable=False, unique=True)
    nascimento = db.Column(db.String(50))
    email = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)
    tipo = db.Column(db.String(20))
    matricula = db.Column(db.String(20))
    classe = db.Column(db.String(100), nullable=False)
    sala = db.Column(db.String(20))
    ano_ingresso = db.Column(db.String(4))
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


# DECORADOR LOGIN
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Você precisa estar logado para acessar esta página.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# FILTRO DE DATA
@app.template_filter('formatadata')
def formatadata(value):
    if value is None:
        return "-"
    if isinstance(value, datetime):
        return value.strftime('%d/%m/%Y')
    try:
        return datetime.strptime(value, '%Y-%m-%d').strftime('%d/%m/%Y')
    except Exception:
        return value


# ROTAS
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
            session['usuario_id'] = usuario.id
            return redirect(url_for('visualizar'))
        else:
            flash('Login ou senha inválidos')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('usuario_id', None)
    return redirect(url_for('login'))


@app.route('/registrar', methods=['GET', 'POST'])
def registrar():
    if request.method == 'POST':
        login_form = request.form['login']
        senha_form = request.form['senha']
        if Usuario.query.filter_by(login=login_form).first():
            flash('Usuário já existe.')
            return redirect(url_for('registrar'))
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
        nascimento_str = request.form.get('nascimento')
        try:
            nascimento = datetime.strptime(nascimento_str, '%Y-%m-%d') if nascimento_str else None
        except ValueError:
            nascimento = nascimento_str

        nova_pessoa = Pessoa(
            nome=request.form['nome'],
            cpf=request.form['cpf'],
            nascimento=nascimento,
            email=request.form['email'],
            telefone=request.form['telefone'],
            tipo=request.form.get('tipo'),
            matricula=request.form['matricula'],
            classe=request.form['classe'],
            sala=request.form['sala'],
            ano_ingresso=request.form['ano_ingresso'],
            cep=request.form['cep'],
            rua=request.form['rua'],
            numero=request.form['numero'],
            complemento=request.form['complemento'],
            bairro=request.form['bairro'],
            cidade=request.form['cidade'],
            estado=request.form['estado']
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
    busca = request.args.get('busca', '')
    ordem = request.args.get('ordem', '')

    pessoas = Pessoa.query

    if busca:
        pessoas = pessoas.filter(Pessoa.nome.ilike(f'%{busca}%'))
    if ordem == 'classe':
        pessoas = pessoas.order_by(Pessoa.classe)

    pessoas = pessoas.all()

    usuario_logado = Usuario.query.get(session['usuario_id']).login
    return render_template('visualizar.html', pessoas=pessoas, total=len(pessoas), usuario=usuario_logado)


@app.route('/relatorios')
@login_required
def relatorios():
    usuario_logado = Usuario.query.get(session['usuario_id']).login
    return render_template('relatorios.html', usuario=usuario_logado)


@app.route('/relatorio-por-classe')
@login_required
def relatorio_por_classe():
    alunos = Pessoa.query.order_by(Pessoa.classe, Pessoa.nome).all()
    dados_por_classe = defaultdict(list)
    for aluno in alunos:
        dados_por_classe[aluno.classe].append(aluno)
    return render_template('relatorio_por_classe.html', dados_por_classe=dados_por_classe)


@app.route('/relatorio-todos-alunos')
@login_required
def relatorio_todos_alunos():
    alunos = Pessoa.query.order_by(Pessoa.nome).all()
    return render_template('relatorio_todos_alunos.html', alunos=alunos)


@app.route('/relatorio-aniversariantes')
@login_required
def relatorio_aniversariantes_mes():
    hoje = datetime.now()
    aniversariantes = Pessoa.query.filter(
        db.extract('month', Pessoa.nascimento) == hoje.month
    ).order_by(db.extract('day', Pessoa.nascimento)).all()
    return render_template('relatorio_aniversariantes.html', aniversariantes=aniversariantes, agora=hoje)


@app.route('/relatorio-por-tempo')
@login_required
def relatorio_por_tempo():
    tempo = request.args.get('tempo')
    ano_atual = datetime.now().year

    alunos = Pessoa.query.order_by(Pessoa.classe, Pessoa.nome).all()

    alunos_filtrados = []

    if tempo:
        tempo = int(tempo)
        for aluno in alunos:
            if aluno.ano_ingresso and aluno.ano_ingresso.isdigit():
                anos_no_sistema = ano_atual - int(aluno.ano_ingresso)
                if anos_no_sistema == tempo:
                    alunos_filtrados.append(aluno)
    else:
        alunos_filtrados = alunos

    return render_template('relatorio_por_tempo.html', alunos_filtrados=alunos_filtrados)


@app.route('/graficos')
@login_required
def graficos():
    dados = db.session.query(Pessoa.classe, db.func.count(Pessoa.id)).group_by(Pessoa.classe).all()
    labels = [d[0] for d in dados]
    valores = [d[1] for d in dados]

    usuario_logado = Usuario.query.get(session['usuario_id']).login
    return render_template('graficos.html', labels=labels, valores=valores, usuario=usuario_logado)


@app.route('/editar/<int:pessoa_id>', methods=['GET', 'POST'])
@login_required
def editar(pessoa_id):
    pessoa = Pessoa.query.get_or_404(pessoa_id)
    if request.method == 'POST':
        pessoa.nome = request.form.get('nome', pessoa.nome)
        pessoa.cpf = request.form.get('cpf', pessoa.cpf)
        pessoa.nascimento = request.form.get('nascimento', pessoa.nascimento)
        pessoa.email = request.form.get('email', pessoa.email)
        pessoa.telefone = request.form.get('telefone', pessoa.telefone)
        pessoa.tipo = request.form.get('tipo', pessoa.tipo)
        pessoa.matricula = request.form.get('matricula', pessoa.matricula)
        pessoa.classe = request.form.get('classe', pessoa.classe)
        pessoa.sala = request.form.get('sala', pessoa.sala)
        pessoa.ano_ingresso = request.form.get('ano_ingresso', pessoa.ano_ingresso)
        pessoa.cep = request.form.get('cep', pessoa.cep)
        pessoa.rua = request.form.get('rua', pessoa.rua)
        pessoa.numero = request.form.get('numero', pessoa.numero)
        pessoa.complemento = request.form.get('complemento', pessoa.complemento)
        pessoa.bairro = request.form.get('bairro', pessoa.bairro)
        pessoa.cidade = request.form.get('cidade', pessoa.cidade)
        pessoa.estado = request.form.get('estado', pessoa.estado)

        db.session.commit()
        flash('Cadastro atualizado com sucesso.')
        return redirect(url_for('visualizar'))
    return render_template('editar.html', pessoa=pessoa)


@app.route('/excluir/<int:pessoa_id>')
@login_required
def excluir(pessoa_id):
    pessoa = Pessoa.query.get_or_404(pessoa_id)
    db.session.delete(pessoa)
    db.session.commit()
    flash('Cadastro excluído com sucesso.')
    return redirect(url_for('visualizar'))


# CRIA O BANCO DE DADOS SE NÃO EXISTIR
with app.app_context():
    db.create_all()
