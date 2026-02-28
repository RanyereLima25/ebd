from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, date
from sqlalchemy import func,extract
from models import Aula, Classe, Pessoa, Presenca
from app import app, db
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
    # matricula = db.Column(db.String(20))
    matricula = db.Column(db.String(20), unique=True)
    @staticmethod
    def gerar_matricula():
        ano_atual = datetime.now().year

        # Buscar última matrícula do ano atual
        ultima = Pessoa.query.filter(
            Pessoa.matricula.like(f"EBD-{ano_atual}-%")
        ).order_by(Pessoa.id.desc()).first()

        if ultima:
            ultimo_numero = int(ultima.matricula.split("-")[-1])
            novo_numero = ultimo_numero + 1
        else:
            novo_numero = 1

        return f"EBD-{ano_atual}-{novo_numero:04d}"
        
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

#-----------------------------------------------------------

class Aula(db.Model):
    __tablename__ = 'aula_ebd'

    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, nullable=False)
    trimestre = db.Column(db.Integer)
    tema = db.Column(db.String(200))
    classe = db.Column(db.String(100))  # <-- AGORA É TEXTO


class Frequencia(db.Model):
    __tablename__ = 'frequencia'

    id = db.Column(db.Integer, primary_key=True)

    pessoa_id = db.Column(db.Integer, db.ForeignKey('pessoa.id'), nullable=False)
    aula_id = db.Column(db.Integer, db.ForeignKey('aula_ebd.id'), nullable=False)

    presente = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    pessoa = db.relationship('Pessoa')
    aula = db.relationship('Aula')

    __table_args__ = (
        db.UniqueConstraint('pessoa_id', 'aula_id', name='unique_presenca'),
    )

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

# ================= LOGIN =================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_form = request.form.get('login')
        senha_form = request.form.get('senha')

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


# ================= LOGOUT =================
@app.route('/logout')
@login_required
def logout():
    session.pop('usuario_id', None)
    flash('Você saiu do sistema.')
    return redirect(url_for('login'))


# ================= REGISTRAR USUÁRIO =================
@app.route('/registrar', methods=['GET', 'POST'])
def registrar():
    if request.method == 'POST':
        login_form = request.form.get('login')
        senha_form = request.form.get('senha')

        if Usuario.query.filter_by(login=login_form).first():
            flash('Usuário já existe.')
        else:
            novo_usuario = Usuario(login=login_form)
            novo_usuario.set_senha(senha_form)
            db.session.add(novo_usuario)
            db.session.commit()
            flash('Usuário registrado com sucesso.')

    return render_template('registrar.html')


# ================= CADASTRO DE PESSOA =================
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
            #matricula=Usuario.gerar_matricula(),
            matricula=Pessoa.gerar_matricula(),
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


# ROTA LISTA DE AULAS

@app.route("/aulas")
def listar_aulas():
    classe_id = request.args.get("classe_id")

    classes = Classe.query.all()

    aulas = []
    if classe_id:
        aulas = Aula.query.filter_by(classe_id=classe_id).all()

        for aula in aulas:
            total_alunos = Pessoa.query.filter_by(classe_id=classe_id, tipo="aluno").count()
            total_presentes = Presenca.query.filter_by(aula_id=aula.id, presente=True).count()

            aula.total_alunos = total_alunos
            aula.total_presentes = total_presentes

    return render_template("aulas.html",
                           classes=classes,
                           aulas=aulas,
                           classe_id=int(classe_id) if classe_id else None)
    

#ROTA REGISTRAR FREQUÊNCIA
@app.route("/frequencia/<int:aula_id>", methods=["GET", "POST"])
def frequencia_aula(aula_id):
    aula = Aula.query.get_or_404(aula_id)

    classe_id = aula.classe_id

    professor = Pessoa.query.filter_by(classe_id=classe_id, tipo="professor").first()
    alunos = Pessoa.query.filter_by(classe_id=classe_id, tipo="aluno").all()

    if request.method == "POST":
        Presenca.query.filter_by(aula_id=aula_id).delete()

        marcados = request.form.getlist("presenca")

        # Professor
        if professor:
            presente = f"prof_{professor.id}" in marcados
            db.session.add(Presenca(
                aula_id=aula_id,
                pessoa_id=professor.id,
                presente=presente
            ))

        # Alunos
        for aluno in alunos:
            presente = f"aluno_{aluno.id}" in marcados
            db.session.add(Presenca(
                aula_id=aula_id,
                pessoa_id=aluno.id,
                presente=presente
            ))

        db.session.commit()
        return redirect(url_for("listar_aulas", classe_id=classe_id))

    # GET
    presencas = Presenca.query.filter_by(aula_id=aula_id, presente=True).all()
    alunos_presentes = [p.pessoa_id for p in presencas]

    professor_presente = False
    if professor:
        professor_presente = professor.id in alunos_presentes

    return render_template("frequencia.html",
                           aula=aula,
                           professor=professor,
                           alunos=alunos,
                           alunos_presentes=alunos_presentes,
                           professor_presente=professor_presente)



#ROTA RANKING 75%

@app.route('/ranking')
@login_required
def ranking():

    ano = date.today().year

    resultado = db.session.query(
        Pessoa.nome,
        Pessoa.tipo,
        func.count(Frequencia.id).filter(Frequencia.presente == True).label('presencas'),
        func.count(Aula.id).label('total')
    ).join(Frequencia, Pessoa.id == Frequencia.pessoa_id)\
     .join(Aula, Aula.id == Frequencia.aula_id)\
     .filter(extract('year', Aula.data) == ano)\
     .group_by(Pessoa.id)\
     .all()

    ranking_lista = []

    for r in resultado:
        if r.total > 0:
            percentual = round((r.presencas / r.total) * 100, 2)
            if percentual >= 75:
                ranking_lista.append({
                    'nome': r.nome,
                    'tipo': r.tipo,
                    'percentual': percentual
                })

    ranking_lista.sort(key=lambda x: x['percentual'], reverse=True)

    return render_template('ranking.html', ranking=ranking_lista)


# =====================================================
# EDITAR PESSOA
# =====================================================

@app.route('/editar/<int:pessoa_id>', methods=['GET', 'POST'])
@login_required
def editar(pessoa_id):
    pessoa = Pessoa.query.get_or_404(pessoa_id)

    if request.method == 'POST':
        dados = request.form.to_dict()

        pessoa.nome = dados.get('nome')
        pessoa.cpf = dados.get('cpf')
        pessoa.nascimento = dados.get('nascimento') or None
        pessoa.email = dados.get('email')
        pessoa.telefone = dados.get('telefone')
        pessoa.tipo = dados.get('tipo')
        pessoa.classe = dados.get('classe')
        pessoa.sala = dados.get('sala')
        pessoa.ano_ingresso = dados.get('ano_ingresso')
        pessoa.cep = dados.get('cep')
        pessoa.rua = dados.get('rua')
        pessoa.numero = dados.get('numero')
        pessoa.complemento = dados.get('complemento')
        pessoa.bairro = dados.get('bairro')
        pessoa.cidade = dados.get('cidade')
        pessoa.estado = dados.get('estado')
        pessoa.sexo = dados.get('sexo')
        pessoa.escolaridade = dados.get('escolaridade')
        pessoa.curso_teologia = dados.get('curso_teologia')
        pessoa.curso_lider = dados.get('curso_lider')
        pessoa.batizado = dados.get('batizado')
        pessoa.profissao = dados.get('profissao_outro') or dados.get('profissao')

        db.session.commit()
        flash('Cadastro atualizado com sucesso.')
        return redirect(url_for('visualizar'))

    usuario_logado = Usuario.query.get(session['usuario_id']).login

    return render_template(
        'cadastro.html',  # reutiliza o mesmo formulário
        pessoa=pessoa,
        usuario=usuario_logado,
        modo_edicao=True
    )

# ================= EXCLUIR =================

@app.route('/excluir/<int:pessoa_id>', methods=['POST'])
@login_required
def excluir(pessoa_id):
    pessoa = Pessoa.query.get_or_404(pessoa_id)

    db.session.delete(pessoa)
    db.session.commit()

    flash('Cadastro excluído com sucesso!', 'success')
    return redirect(url_for('visualizar'))

# ================= VISUALIZAR =================
@app.route('/visualizar')
@login_required
def visualizar():
    pessoas = Pessoa.query.order_by(Pessoa.classe, Pessoa.nome).all()
    usuario_logado = Usuario.query.get(session['usuario_id']).login
    return render_template(
        'visualizar.html',
        pessoas=pessoas,
        total=len(pessoas),
        usuario=usuario_logado
    )


# =====================================================
# RELATÓRIOS
# =====================================================

@app.route('/relatorios')
@login_required
def relatorios():
    usuario_logado = Usuario.query.get(session['usuario_id']).login
    total = Pessoa.query.count()
    return render_template('relatorios.html', total=total, usuario=usuario_logado)


# 📘 Alunos por Classe
@app.route('/relatorios/por-classe')
@login_required
def relatorio_por_classe():
    classe_filtro = request.args.get('classe')
    tipo_filtro = request.args.get('tipo')

    query = Pessoa.query

    # 🔹 Filtro por tipo (case insensitive)
    if tipo_filtro:
        query = query.filter(func.lower(Pessoa.tipo) == tipo_filtro.lower())

    # 🔹 Filtro por classe
    if classe_filtro:
        query = query.filter(Pessoa.classe == classe_filtro)

    pessoas = query.order_by(Pessoa.classe, Pessoa.nome).all()

    # 🔹 Buscar classes distintas
    todas_classes = db.session.query(Pessoa.classe) \
        .distinct() \
        .order_by(Pessoa.classe) \
        .all()

    lista_classes = [c[0] for c in todas_classes if c[0]]

    # 🔹 Buscar tipos distintos (exatamente como estão no banco)
    todos_tipos = db.session.query(Pessoa.tipo) \
        .distinct() \
        .order_by(Pessoa.tipo) \
        .all()

    lista_tipos = [t[0] for t in todos_tipos if t[0]]

    # 🔹 Organizar por classe
    dados = {}
    for pessoa in pessoas:
        classe = pessoa.classe or "Não informada"

        if classe not in dados:
            dados[classe] = []

        dados[classe].append(pessoa)

    return render_template(
        'relatorio_por_classe.html',
        dados_por_classe=dados,
        lista_classes=lista_classes,
        lista_tipos=lista_tipos
    )


# 📋 Todos os Alunos
@app.route('/relatorios/todos-alunos')
@login_required
def relatorio_todos_alunos():
    alunos = Pessoa.query.filter_by(tipo='Aluno') \
        .order_by(Pessoa.nome).all()

    return render_template('relatorio_todos_alunos.html', dados_por_classe=alunos)

# 🎂 Aniversariantes do Mês
@app.route('/relatorios/aniversariantes')
@login_required
def relatorio_aniversariantes():
    mes_atual = datetime.now().month

    aniversariantes = Pessoa.query.filter(
        func.extract('month', Pessoa.nascimento) == mes_atual
    ).order_by(Pessoa.nome).all()

    return render_template(
        'relatorio_aniversariantes.html',
        aniversariantes=aniversariantes
    )


# ⏳ Alunos por Tempo (Ano de Ingresso)
@app.route('/relatorios/por-tempo')
@login_required
def relatorio_por_tempo():
    dados = db.session.query(
        Pessoa.ano_ingresso,
        func.count(Pessoa.id)
    ).filter(Pessoa.tipo == 'Aluno') \
     .group_by(Pessoa.ano_ingresso) \
     .order_by(Pessoa.ano_ingresso).all()

    return render_template('relatorio_por_tempo.html', dados=dados)


# 🧑‍💼 Alunos por Profissão
@app.route('/relatorios/por-profissao')
@login_required
def relatorio_alunos_por_profissao():
    dados = db.session.query(
        Pessoa.profissao,
        func.count(Pessoa.id)
    ).filter(Pessoa.tipo == 'Aluno') \
     .group_by(Pessoa.profissao) \
     .order_by(Pessoa.profissao).all()

    return render_template('relatorio_por_profissao.html', dados=dados)


# 📄 Relatório PECC
@app.route('/relatorios/pecc')
@login_required
def relatorio_pecc():
    alunos = Pessoa.query.filter_by(tipo='Aluno') \
        .order_by(Pessoa.classe, Pessoa.nome).all()

    return render_template('relatorio_pecc.html', alunos=alunos)


# =====================================================
# GRÁFICOS
# =====================================================

@app.route('/graficos')
@login_required
def graficos():
    total = Pessoa.query.count()

    # 📊 1️⃣ Alunos por Classe
    resultado_classe = db.session.query(
        Pessoa.classe,
        func.count(Pessoa.id)
    ).filter(Pessoa.tipo == 'Aluno') \
     .group_by(Pessoa.classe).all()

    labels = [r[0] or "Não informada" for r in resultado_classe]
    valores = [r[1] for r in resultado_classe]

    # 📊 2️⃣ Alunos por Sexo
    resultado_genero = db.session.query(
        Pessoa.sexo,
        func.count(Pessoa.id)
    ).filter(Pessoa.tipo == 'Aluno') \
     .group_by(Pessoa.sexo).all()

    genero_labels = [r[0] or "Não informado" for r in resultado_genero]
    genero_valores = [r[1] for r in resultado_genero]

    return render_template(
        'graficos.html',
        total=total,
        labels=labels,
        valores=valores,
        genero_labels=genero_labels,
        genero_valores=genero_valores
    )

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
