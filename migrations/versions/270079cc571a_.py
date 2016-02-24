"""empty message

Revision ID: 270079cc571a
Revises: d1ed55e64bc8
Create Date: 2016-02-22 18:18:45.118835

"""

# revision identifiers, used by Alembic.
revision = '270079cc571a'
down_revision = 'd1ed55e64bc8'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('post', sa.Column('post_history', postgresql.JSONB(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('post', 'post_history')
    ### end Alembic commands ###