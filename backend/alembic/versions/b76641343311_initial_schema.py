"""Initial schema — creates all A.N.N. tables (matches models/b2b_database.py)

Revision ID: b76641343311
Revises:
Create Date: 2026-03-20 16:32:30.025676

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b76641343311'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the core tables."""
    op.create_table(
        'broadcast_scripts',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('headline', sa.String(), nullable=False),
        sa.Column('english_script', sa.String(), nullable=False),
        sa.Column('hindi_script', sa.String(), nullable=False, server_default=''),
        sa.Column('translations_json', sa.String(), nullable=False, server_default='{}'),
        sa.Column('category', sa.String(), nullable=False, server_default='general'),
        sa.Column('source_url', sa.String(), nullable=False, server_default=''),
        sa.Column('word_count_en', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('word_count_hi', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('estimated_duration_seconds', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_table(
        'agent_metrics',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('agent_name', sa.String(), nullable=False, index=True),
        sa.Column('status', sa.String(), nullable=False, server_default='completed'),
        sa.Column('latency_seconds', sa.Float(), nullable=False, server_default='0'),
        sa.Column('tasks_completed', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_table(
        'media_jobs',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('script_id', sa.String(), nullable=False, index=True),
        sa.Column('headline', sa.String(), nullable=False, server_default=''),
        sa.Column('media_type', sa.String(), nullable=False, server_default='audio'),
        sa.Column('language', sa.String(), nullable=False, server_default='en'),
        sa.Column('status', sa.String(), nullable=False, server_default='queued'),
        sa.Column('progress', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('duration', sa.String(), nullable=False, server_default='--'),
        sa.Column('output_url', sa.String(), nullable=False, server_default=''),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_table(
        'client_api_keys',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('client_name', sa.String(), nullable=False, index=True),
        sa.Column('api_key', sa.String(), nullable=False, unique=True, index=True),
        sa.Column('key_prefix', sa.String(), nullable=True, server_default=''),
        sa.Column('plan_tier', sa.String(), nullable=False, server_default='standard'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('monthly_quota', sa.Integer(), nullable=False, server_default='1000'),
        sa.Column('requests_used', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('webhook_url', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    """Drop the core tables."""
    op.drop_table('client_api_keys')
    op.drop_table('media_jobs')
    op.drop_table('agent_metrics')
    op.drop_table('broadcast_scripts')
