"""Criar tabela usuario e adicionar usuario em producao"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# Revisões do Alembic
revision = 'ad3f836fcdf8'
down_revision = '1ced13cedfc1'
branch_labels = None
depends_on = None

def upgrade():
    conn = op.get_bind()
    inspector = inspect(conn)

    # 1️⃣ Criar tabela 'usuario' se não existir
    if 'usuario' not in inspector.get_table_names():
        op.create_table(
            'usuario',
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('username', sa.String(50), nullable=False, unique=True),
            sa.Column('password', sa.String(255), nullable=False)
        )

    # 2️⃣ Alterar tabela 'producao' em batch mode (SQLite safe)
    columns = [c['name'] for c in inspector.get_columns('producao')]
    if 'usuario_id' not in columns:
        with op.batch_alter_table('producao', recreate='always') as batch_op:
            batch_op.add_column(sa.Column('usuario_id', sa.Integer, nullable=True))
            batch_op.create_foreign_key(
                'fk_producao_usuario',
                'usuario',
                ['usuario_id'],
                ['id']
            )

def downgrade():
    with op.batch_alter_table('producao', recreate='always') as batch_op:
        batch_op.drop_constraint('fk_producao_usuario', type_='foreignkey')
        batch_op.drop_column('usuario_id')

    # Remover tabela usuario
    if 'usuario' in inspect(op.get_bind()).get_table_names():
        op.drop_table('usuario')
