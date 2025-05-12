"""add phone column to user table

Revision ID: aac54e78d123
Revises: 9f0c9cd09105
Create Date: 2025-05-07 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision = 'aac54e78d123'
down_revision = '9f0c9cd09105'
branch_labels = None
depends_on = None


def upgrade():
    """Add phone column to user table."""
    # 获取当前连接和检查器
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    
    # 获取'user'表中的所有列
    columns = [col["name"] for col in inspector.get_columns("user")]
    
    # 获取'user'表的所有索引
    indexes = [idx["name"] for idx in inspector.get_indexes("user")]
    
    # 添加手机号字段，如果不存在
    if 'phone' not in columns:
        op.add_column('user', sa.Column('phone', sa.String(), nullable=True))
    
    # 创建手机号唯一索引，如果不存在
    if 'ix_user_phone' not in indexes:
        # 创建手机号唯一索引
        # 注意：在SQLite中无法直接添加UNIQUE约束，但可以创建唯一索引
        op.create_index('ix_user_phone', 'user', ['phone'], unique=True)


def downgrade():
    """Remove phone column from user table."""
    # 获取当前连接和检查器
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    
    # 获取索引，如果存在则删除
    indexes = [idx["name"] for idx in inspector.get_indexes("user")]
    if 'ix_user_phone' in indexes:
        op.drop_index('ix_user_phone', table_name='user')
    
    # 获取列，如果存在则删除
    columns = [col["name"] for col in inspector.get_columns("user")]
    if 'phone' in columns:
        op.drop_column('user', 'phone') 