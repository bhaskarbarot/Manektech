"""initial ontology store schema

Revision ID: 0001
Revises: 
Create Date: 2026-10-15
"""
from alembic import op
import sqlalchemy as sa
import pgvector.sqlalchemy
from sqlalchemy.dialects import postgresql

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.create_table('datasets',
    sa.Column('id', sa.String(length=200), nullable=False),
    sa.Column('name', sa.String(length=120), nullable=False),
    sa.Column('version', sa.String(length=40), nullable=False),
    sa.Column('source', sa.Text(), nullable=True),
    sa.Column('manifest', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('entity_count', sa.Integer(), nullable=False),
    sa.Column('relationship_count', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_datasets')),
    sa.UniqueConstraint('name', 'version', name='uq_datasets_name_version')
    )
    op.create_table('entities',
    sa.Column('uri', sa.Text(), nullable=False),
    sa.Column('entity_id', sa.Text(), nullable=True),
    sa.Column('entity_class', sa.String(length=64), nullable=False),
    sa.Column('framework', sa.String(length=64), nullable=True),
    sa.Column('label', sa.Text(), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('language', sa.String(length=16), nullable=True),
    sa.Column('group_name', sa.Text(), nullable=True),
    sa.Column('subgroup_name', sa.Text(), nullable=True),
    sa.Column('attributes', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
    sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
    sa.Column('dataset_id', sa.String(length=200), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], name=op.f('fk_entities_dataset_id_datasets'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('uri', name=op.f('pk_entities')),
    sa.UniqueConstraint('entity_id', name=op.f('uq_entities_entity_id'))
    )
    op.create_index('ix_entities_class_framework', 'entities', ['entity_class', 'framework'], unique=False)
    op.create_index('ix_entities_dataset_id', 'entities', ['dataset_id'], unique=False)
    op.create_index('ix_entities_description_trgm', 'entities', ['description'], unique=False, postgresql_using='gin', postgresql_ops={'description': 'gin_trgm_ops'})
    op.create_index('ix_entities_label_lower', 'entities', [sa.literal_column('lower(label)')], unique=False)
    op.create_index('ix_entities_label_trgm', 'entities', ['label'], unique=False, postgresql_using='gin', postgresql_ops={'label': 'gin_trgm_ops'})
    op.create_index('ix_entities_language', 'entities', ['language'], unique=False)
    op.create_index('ix_entities_metadata', 'entities', ['metadata'], unique=False, postgresql_using='gin', postgresql_ops={'metadata': 'jsonb_path_ops'})
    op.create_table('relationships',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('subject_uri', sa.Text(), nullable=False),
    sa.Column('predicate_uri', sa.Text(), nullable=False),
    sa.Column('object_uri', sa.Text(), nullable=False),
    sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
    sa.Column('dataset_id', sa.String(length=200), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], name=op.f('fk_relationships_dataset_id_datasets'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_relationships')),
    sa.UniqueConstraint('subject_uri', 'predicate_uri', 'object_uri', name='uq_relationships_triple')
    )
    op.create_index('ix_relationships_dataset_id', 'relationships', ['dataset_id'], unique=False)
    op.create_index('ix_relationships_metadata', 'relationships', ['metadata'], unique=False, postgresql_using='gin', postgresql_ops={'metadata': 'jsonb_path_ops'})
    op.create_index('ix_relationships_object_predicate', 'relationships', ['object_uri', 'predicate_uri'], unique=False)
    op.create_index('ix_relationships_predicate', 'relationships', ['predicate_uri'], unique=False)
    op.create_table('embeddings',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('entity_uri', sa.Text(), nullable=False),
    sa.Column('model_name', sa.String(length=200), nullable=False),
    sa.Column('model_version', sa.String(length=80), nullable=False),
    sa.Column('text_fields', sa.String(length=200), nullable=False),
    sa.Column('dim', sa.Integer(), nullable=False),
    sa.Column('source_text', sa.Text(), nullable=False),
    sa.Column('text_hash', sa.String(length=64), nullable=False),
    sa.Column('vector', pgvector.sqlalchemy.vector.VECTOR(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['entity_uri'], ['entities.uri'], name=op.f('fk_embeddings_entity_uri_entities'), onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_embeddings')),
    sa.UniqueConstraint('entity_uri', 'model_name', 'model_version', 'text_fields', name='uq_embeddings_entity_model_fields')
    )
    op.create_index('ix_embeddings_model', 'embeddings', ['model_name', 'model_version', 'text_fields'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_embeddings_model', table_name='embeddings')
    op.drop_table('embeddings')
    op.drop_index('ix_relationships_predicate', table_name='relationships')
    op.drop_index('ix_relationships_object_predicate', table_name='relationships')
    op.drop_index('ix_relationships_metadata', table_name='relationships', postgresql_using='gin', postgresql_ops={'metadata': 'jsonb_path_ops'})
    op.drop_index('ix_relationships_dataset_id', table_name='relationships')
    op.drop_table('relationships')
    op.drop_index('ix_entities_metadata', table_name='entities', postgresql_using='gin', postgresql_ops={'metadata': 'jsonb_path_ops'})
    op.drop_index('ix_entities_language', table_name='entities')
    op.drop_index('ix_entities_label_trgm', table_name='entities', postgresql_using='gin', postgresql_ops={'label': 'gin_trgm_ops'})
    op.drop_index('ix_entities_label_lower', table_name='entities')
    op.drop_index('ix_entities_description_trgm', table_name='entities', postgresql_using='gin', postgresql_ops={'description': 'gin_trgm_ops'})
    op.drop_index('ix_entities_dataset_id', table_name='entities')
    op.drop_index('ix_entities_class_framework', table_name='entities')
    op.drop_table('entities')
    op.drop_table('datasets')
