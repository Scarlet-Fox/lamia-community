"""empty message

Revision ID: ae4afba8e2f5
Revises: 74a97255bd9e
Create Date: 2016-03-08 19:26:38.837026

"""

# revision identifiers, used by Alembic.
revision = 'ae4afba8e2f5'
down_revision = '74a97255bd9e'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(u'fk_topic_label', 'topic', type_='foreignkey')
    op.create_foreign_key('fk_topic_label', 'topic', 'label', ['label_id'], ['id'], ondelete='SET NULL')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('fk_topic_label', 'topic', type_='foreignkey')
    op.create_foreign_key(u'fk_topic_label', 'topic', 'label', ['label_id'], ['id'])
    ### end Alembic commands ###
