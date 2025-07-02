from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from collections import defaultdict
from datetime import datetime
import os

app = Flask(__name__)

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
    escolaridade = db.Column(db.String(100))
    curso_teologia = db.Column(db.String(100))
    curso_lider = db.Column(db.String(100))
    batizado = db.Column(db.String(100))
    profissao = db.Column(db.String(100))


class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(150), unique=True, nullable=False)
    senha_hash = db.Column(db.String(256), nullable=False)

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
            profissao = dados.get('profissao_outro') or dados.get('profissao')

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


@app.route('/relatorio_alunos_por_profissao')
@login_required
def relatorio_alunos_por_profissao():
    profissao_filtro = request.args.get('profissao')

    # Lista distinta de profissões no banco (para o filtro)
    profissoes = db.session.query(Pessoa.profissao).distinct().all()
    profissoes = [p[0] for p in profissoes if p[0]]  # converte de tupla para lista

    if profissao_filtro:
        alunos_filtrados = Pessoa.query.filter_by(profissao=profissao_filtro).order_by(Pessoa.nome).all()
    else:
        alunos_filtrados = Pessoa.query.order_by(Pessoa.nome).all()

    return render_template(
        'relatorio_alunos_por_profissao.html',
        alunos_filtrados=alunos_filtrados,
        profissoes=profissoes
    )


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
    tipo = request.args.get('tipo')
    classe = request.args.get('classe')
    query = Pessoa.query
    tipos_validos = ['Aluno', 'Professor', 'Secretario']
    if tipo and tipo in tipos_validos:
        query = query.filter_by(tipo=tipo)
    if classe:
        query = query.filter_by(classe=classe)
    pessoas = query.order_by(Pessoa.classe, Pessoa.nome).all()
    dados_por_classe = defaultdict(list)
    for p in pessoas:
        chave_classe = p.classe if p.classe else 'Sem Classe'
        dados_por_classe[chave_classe].append(p)
    return render_template('relatorio_todos_alunos.html', pessoas=pessoas, dados_por_classe=dados_por_classe, filtro_tipo=tipo, filtro_classe=classe)

@app.route('/relatorio-aniversariantes')
@login_required
def relatorio_aniversariantes():
    hoje = datetime.now()
    pessoas = Pessoa.query.all()
    aniversariantes_por_semana = {"1": [], "2": [], "3": [], "4": []}
    for p in pessoas:
        nascimento = p.nascimento
        if not nascimento:
            continue
        try:
            if isinstance(nascimento, str):
                data = datetime.strptime(nascimento, '%Y-%m-%d')
            else:
                data = nascimento
            if data.month == hoje.month:
                dia = data.day
                if dia <= 7:
                    aniversariantes_por_semana["1"].append(p)
                elif dia <= 14:
                    aniversariantes_por_semana["2"].append(p)
                elif dia <= 21:
                    aniversariantes_por_semana["3"].append(p)
                else:
                    aniversariantes_por_semana["4"].append(p)
        except Exception as e:
            print(f"Erro ao processar nascimento de {p.nome}: {e}")
            continue
    return render_template('relatorio_aniversariantes.html', agora=hoje, aniversariantes_por_semana=aniversariantes_por_semana)

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
    dados = db.session.query(Pessoa.classe, db.func.count(Pessoa.id)).group_by(Pessoa.classe).all()
    labels = [d[0] for d in dados]
    valores = [d[1] for d in dados]
    pessoas = Pessoa.query.all()
    contagem_genero = {"Masculino": 0, "Feminino": 0, "Outros": 0}
    for pessoa in pessoas:
        sexo_raw = (pessoa.sexo or "").strip().lower()
        if sexo_raw in ['masculino', 'm', 'masc']:
            contagem_genero["Masculino"] += 1
        elif sexo_raw in ['feminino', 'f', 'fem']:
            contagem_genero["Feminino"] += 1
        else:
            contagem_genero["Outros"] += 1
    genero_labels = list(contagem_genero.keys())
    genero_valores = list(contagem_genero.values())
    usuario_logado = Usuario.query.get(session['usuario_id']).login
    return render_template('graficos.html', labels=labels, valores=valores, genero_labels=genero_labels, genero_valores=genero_valores, usuario=usuario_logado)

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
        db.create_all()
    app.run(debug=True)
