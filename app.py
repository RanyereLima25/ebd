from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, date
from sqlalchemy import func, extract
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
    matricula = db.Column(db.String(20), unique=True)

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

    @staticmethod
    def gerar_matricula():
        ano_atual = datetime.now().year
        ultima = Pessoa.query.filter(
            Pessoa.matricula.like(f"EBD-{ano_atual}-%")
        ).order_by(Pessoa.id.desc()).first()

        if ultima:
            ultimo_numero = int(ultima.matricula.split("-")[-1])
            novo_numero = ultimo_numero + 1
        else:
            novo_numero = 1

        return f"EBD-{ano_atual}-{novo_numero:04d}"


class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(150), unique=True, nullable=False)
    senha_hash = db.Column(db.String(256), nullable=False)
    ultimo_login = db.Column(db.DateTime)

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def checar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)


class Aula(db.Model):
    __tablename__ = 'aula_ebd'

    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, nullable=False)
    trimestre = db.Column(db.Integer)
    tema = db.Column(db.String(200))
    classe = db.Column(db.String(100))


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
# LOGIN REQUIRED
# =====================================================
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'usuario_id' not in session:
            flash("Você precisa estar logado.")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# =====================================================
# LOGIN
# =====================================================
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = Usuario.query.filter_by(
            login=request.form.get('login')
        ).first()

        if usuario and usuario.checar_senha(request.form.get('senha')):
            tz = pytz.timezone("America/Sao_Paulo")
            usuario.ultimo_login = datetime.now(tz)
            db.session.commit()

            session['usuario_id'] = usuario.id
            return redirect(url_for('visualizar'))

        flash('Login inválido.')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    session.clear()
    return redirect(url_for('login'))

# =====================================================
# AULAS
# =====================================================
@app.route("/aulas")
@login_required
def listar_aulas():
    classe = request.args.get("classe")

    todas_classes = db.session.query(Pessoa.classe)\
        .distinct().order_by(Pessoa.classe).all()

    lista_classes = [c[0] for c in todas_classes if c[0]]

    aulas = []

    if classe:
        aulas = Aula.query.filter_by(classe=classe)\
            .order_by(Aula.data.desc()).all()

        for aula in aulas:
            total_alunos = Pessoa.query.filter(
                func.lower(Pessoa.tipo) == "aluno",
                Pessoa.classe == classe
            ).count()

            total_presentes = Frequencia.query.filter_by(
                aula_id=aula.id,
                presente=True
            ).count()

            aula.total_alunos = total_alunos
            aula.total_presentes = total_presentes

    return render_template(
        "aulas.html",
        aulas=aulas,
        lista_classes=lista_classes,
        classe=classe
    )

@app.route("/frequencia/<int:aula_id>", methods=["GET", "POST"])
@login_required
def frequencia_aula(aula_id):

    aula = Aula.query.get_or_404(aula_id)
    classe = aula.classe

    professor = Pessoa.query.filter(
        func.lower(Pessoa.tipo) == "professor",
        Pessoa.classe == classe
    ).first()

    alunos = Pessoa.query.filter(
        func.lower(Pessoa.tipo) == "aluno",
        Pessoa.classe == classe
    ).order_by(Pessoa.nome).all()

    if request.method == "POST":
        Frequencia.query.filter_by(aula_id=aula_id).delete()
        marcados = request.form.getlist("presenca")

        if professor:
            db.session.add(Frequencia(
                aula_id=aula_id,
                pessoa_id=professor.id,
                presente=str(professor.id) in marcados
            ))

        for aluno in alunos:
            db.session.add(Frequencia(
                aula_id=aula_id,
                pessoa_id=aluno.id,
                presente=str(aluno.id) in marcados
            ))

        db.session.commit()
        return redirect(url_for("listar_aulas", classe=classe))

    presencas = Frequencia.query.filter_by(
        aula_id=aula_id,
        presente=True
    ).all()

    presentes_ids = [p.pessoa_id for p in presencas]

    return render_template(
        "frequencia.html",
        aula=aula,
        professor=professor,
        alunos=alunos,
        presentes_ids=presentes_ids
    )

# =====================================================
# INICIALIZAÇÃO
# =====================================================
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
