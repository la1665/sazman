from sqlalchemy import Table, Column, Integer, ForeignKey

from database.engine import Base


camera_lpr_association = Table(
    'camera_lpr_association',
    Base.metadata,
    Column('camera_id', Integer, ForeignKey('cameras.id', ondelete="CASCADE"), primary_key=True),
    Column('lpr_id', Integer, ForeignKey('lprs.id', ondelete="CASCADE"), primary_key=True)
)
