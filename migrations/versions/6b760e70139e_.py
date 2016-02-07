"""empty message

Revision ID: 6b760e70139e
Revises: None
Create Date: 2016-02-06 14:57:10.232453

"""

# revision identifiers, used by Alembic.
revision = '6b760e70139e'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_foreign_key('fk_category_categoryparent', 'category', 'category', ['category_id'], ['id'])
    op.create_foreign_key('fk_category_recenttopic', 'category', 'topic', ['recent_topic_id'], ['id'])
    op.create_foreign_key('fk_pm_r_pm', 'private_message_reply', 'private_message', ['pm_id'], ['id'])
    op.add_column('status_update', sa.Column('attached_to_user_id', sa.Integer(), nullable=True))
    op.add_column('status_update', sa.Column('created', sa.DateTime(), nullable=True))
    op.create_foreign_key('fk_status_update_attachedtouser', 'status_update', 'user', ['attached_to_user_id'], ['id'])
    op.create_foreign_key('fk_status_user_status', 'status_update_user', 'status_update', ['status_id'], ['id'])
    op.create_foreign_key('fk_topicwatchers_topic', 'topic_watchers', 'topic', ['topic_id'], ['id'])
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('fk_topicwatchers_topic', 'topic_watchers', type_='foreignkey')
    op.drop_constraint('fk_status_user_status', 'status_update_user', type_='foreignkey')
    op.drop_constraint('fk_status_update_attachedtouser', 'status_update', type_='foreignkey')
    op.drop_column('status_update', 'created')
    op.drop_column('status_update', 'attached_to_user_id')
    op.drop_constraint('fk_pm_r_pm', 'private_message_reply', type_='foreignkey')
    op.drop_constraint('fk_category_recenttopic', 'category', type_='foreignkey')
    op.drop_constraint('fk_category_categoryparent', 'category', type_='foreignkey')
    ### end Alembic commands ###
