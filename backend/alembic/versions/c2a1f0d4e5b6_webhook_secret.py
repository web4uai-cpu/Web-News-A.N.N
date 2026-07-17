"""Add client_api_keys.webhook_secret for HMAC-signed outbound webhooks

Revision ID: c2a1f0d4e5b6
Revises: b76641343311
Create Date: 2026-07-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'c2a1f0d4e5b6'
down_revision: Union[str, Sequence[str], None] = 'b76641343311'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('client_api_keys', sa.Column('webhook_secret', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('client_api_keys', 'webhook_secret')
