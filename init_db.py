from app import db, Usuario
import os

# cria a pasta do banco persistente se não existir
os.makedirs("/opt/render/project/data", exist_ok=True)

# cria todas as tabelas
with db.app.app_context():
    db.create_all()

    # cria usuário admin inicial se não existir
    if not Usuario.query.filter_by(login='admin').first():
        admin = Usuario(login='admin')
        admin.set_senha('admin123')  # ALTERE a senha depois!
        db.session.add(admin)
        db.session.commit()
        print("Usuário admin criado: login=admin, senha=admin123")
    else:
        print("Usuário admin já existe")
