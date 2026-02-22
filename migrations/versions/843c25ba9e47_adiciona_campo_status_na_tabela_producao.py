"""Adiciona campo status na tabela Producao

Revision ID: 843c25ba9e47
Revises: 99ac928b9fce
Create Date: 2026-02-22 10:44:56.903211
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '843c25ba9e47'
down_revision = '99ac928b9fce'
branch_labels = None
depends_on = None

def upgrade():
    # 1️⃣ Adiciona a coluna como nullable
    with op.batch_alter_table('producao', schema=None) as batch_op:
        batch_op.add_column(sa.Column('status', sa.String(length=20), nullable=True))
    
    # 2️⃣ Atualiza os registros existentes para 'ativa'
    op.execute("UPDATE producao SET status = 'ativa'")
    
    # 3️⃣ Altera a coluna para NOT NULL
    with op.batch_alter_table('producao', schema=None) as batch_op:
        batch_op.alter_column('status', nullable=False)

def downgrade():
    with op.batch_alter_table('producao', schema=None) as batch_op:
        batch_op.drop_column('status')