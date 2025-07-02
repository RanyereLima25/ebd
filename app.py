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
# DECORADORES E FILTROS
# =============================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Você precisa estar logado para acessar esta página.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.template_filter('formatadata')
def formatadata(value):
    if not value:
        return "-"
    try:
        return datetime.strptime(value, '%Y-%m-%d').strftime('%d/%m/%Y')
    except Exception:
        return value

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
        nascimento = dados.get('nascimento') or None

        nova_pessoa = Pessoa(
            nome=dados.get('nome'),
            cpf=dados.get('cpf'),
            nascimento=nascimento,
            email=dados.get('email'),
            telefone=dados.get('telefone'),
            tipo=dados.get('tipo'),
            matricula=dados.get('matricula'),
            classe=dados.get('classe'),
            sala=dados.get('sala'),
            ano_ingresso=dados.get('ano_ingresso'),
            cep=dados.get('cep'),
            rua=dados.get('rua'),
            numero=dados.get('numero'),
            complemento=dados.get('complemento'),
            bairro=dados.get('bairro'),
            cidade=dados.get('cidade'),
            estado=dados.get('estado')
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
    busca = request.args.get('busca', '').strip()
    ordem = request.args.get('ordem', '')

    query = Pessoa.query
    if busca:
        query = query.filter(Pessoa.nome.ilike(f'%{busca}%'))
    if ordem == 'classe':
        query = query.order_by(Pessoa.classe)

    pessoas = query.all()
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
    tipo = request.args.get('tipo')      # filtro tipo: Aluno, Professor, Secretario, ou None para todos
    classe = request.args.get('classe')  # filtro classe: nome da classe ou None para todas

    query = Pessoa.query

    # Filtrar pelo tipo se for um valor válido
    tipos_validos = ['Aluno', 'Professor', 'Secretario']
    if tipo and tipo in tipos_validos:
        query = query.filter_by(tipo=tipo)

    # Filtrar pela classe se selecionada
    if classe:
        query = query.filter_by(classe=classe)

    # Ordenar por classe e nome
    pessoas = query.order_by(Pessoa.classe, Pessoa.nome).all()

    # Agrupar por classe para o template
    dados_por_classe = {}
    for p in pessoas:
        chave_classe = p.classe if p.classe else 'Sem Classe'
        dados_por_classe.setdefault(chave_classe, []).append(p)

    return render_template(
        'relatorio_todos_alunos.html',
        pessoas=pessoas,
        dados_por_classe=dados_por_classe,
        filtro_tipo=tipo,
        filtro_classe=classe
    )



@app.route('/relatorio-aniversariantes')
@login_required
def relatorio_aniversariantes():
    hoje = datetime.now()
    pessoas = Pessoa.query.all()

    aniversariantes = []
    for p in pessoas:
        try:
            data = datetime.strptime(p.nascimento, '%Y-%m-%d')
            if data.month == hoje.month:
                aniversariantes.append((p, data.day))
        except:
            continue

    # Ordenar pelo dia do mês
    aniversariantes.sort(key=lambda x: x[1])
    aniversariantes = [p[0] for p in aniversariantes]

    return render_template('relatorio_aniversariantes.html', aniversariantes=aniversariantes, agora=hoje)


@app.route('/relatorio-por-tempo')
@login_required
def relatorio_por_tempo():
    tempo = request.args.get('tempo')
    ano_atual = datetime.now().year

    alunos = Pessoa.query.order_by(Pessoa.classe, Pessoa.nome).all()
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
    # Gráfico 1: Alunos por Classe
    dados = db.session.query(Pessoa.classe, db.func.count(Pessoa.id)).group_by(Pessoa.classe).all()
    labels = [d[0] for d in dados]
    valores = [d[1] for d in dados]

    # Gráfico 2: Matrículas por Gênero - com tratamento de caixa e acento
    pessoas = Pessoa.query.all()
    contagem_genero = {"Masculino": 0, "Feminino": 0, "Outros": 0}

    for pessoa in pessoas:
        sexo_raw = (pessoa.sexo or "").strip().lower()

        # Padronizando para aceitar várias formas
        if sexo_raw in ['masculino', 'm', 'masc']:
            contagem_genero["Masculino"] += 1
        elif sexo_raw in ['feminino', 'f', 'fem']:
            contagem_genero["Feminino"] += 1
        else:
            contagem_genero["Outros"] += 1

    genero_labels = list(contagem_genero.keys())
    genero_valores = list(contagem_genero.values())

    # Usuário logado
    usuario_logado = Usuario.query.get(session['usuario_id']).login

    return render_template(
        'graficos.html',
        labels=labels,
        valores=valores,
        genero_labels=genero_labels,
        genero_valores=genero_valores,
        usuario=usuario_logado
    )



@app.route('/editar/<int:pessoa_id>', methods=['GET', 'POST'])
@login_required
def editar(pessoa_id):
    pessoa = Pessoa.query.get_or_404(pessoa_id)
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
    pessoa = Pessoa.query.get_or_404(pessoa_id)
    db.session.delete(pessoa)
    db.session.commit()
    flash('Cadastro excluído com sucesso.')
    return redirect(url_for('visualizar'))

# =============================
# EXECUÇÃO
# =============================
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Cria as tabelas se não existirem
    app.run(debug=True)
