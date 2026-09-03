"""Store structured three-document indicator comparisons."""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260904_0008"
down_revision: Union[str, None] = "20260903_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("check_results") as batch_op:
        batch_op.add_column(sa.Column("comparison_values", sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("check_results") as batch_op:
        batch_op.drop_column("comparison_values")
