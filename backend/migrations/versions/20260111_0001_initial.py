"""Initial migration

Revision ID: 0001
Revises: 
Create Date: 2026-01-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    # 初始迁移，暂无操作
    # 后续添加模型后，使用 alembic revision --autogenerate 生成迁移
    pass


def downgrade() -> None:
    """Downgrade database schema."""
    pass
