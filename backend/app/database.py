import json
from contextlib import contextmanager
from datetime import datetime, timezone
from sqlalchemy import create_engine, String, Text, DateTime, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from .config import DATABASE_URL

class Base(DeclarativeBase):
    pass

class Record(Base):
    __tablename__ = 'records'
    key: Mapped[str] = mapped_column(String(160), primary_key=True)
    kind: Mapped[str] = mapped_column(String(32), index=True)
    payload: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False} if DATABASE_URL.startswith('sqlite') else {}, pool_pre_ping=True)
Session = sessionmaker(engine)
with engine.begin() as connection:
    if engine.dialect.name == 'postgresql':
        connection.execute(text('SELECT pg_advisory_xact_lock(78142001)'))
    Base.metadata.create_all(connection)

@contextmanager
def exclusive():
    """Serialize index-sensitive operations across serverless instances."""
    if engine.dialect.name != 'postgresql':
        yield
        return
    with engine.connect() as connection:
        connection.execute(text('SELECT pg_advisory_lock(78142002)'))
        try:
            yield
        finally:
            connection.execute(text('SELECT pg_advisory_unlock(78142002)'))
            connection.commit()

def put_many(rows):
    """Atomic seeding with batched upserts; avoids a network round trip per field."""
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    from sqlalchemy.dialects.sqlite import insert as sqlite_insert
    insert = pg_insert if engine.dialect.name == 'postgresql' else sqlite_insert
    values=[{'key':f'{kind}:{id}','kind':kind,'payload':json.dumps(value)} for kind,id,value in rows]
    with Session.begin() as session:
        for start in range(0,len(values),200):
            statement=insert(Record).values(values[start:start+200])
            session.execute(statement.on_conflict_do_update(index_elements=['key'],set_={'payload':statement.excluded.payload}))

def put(kind, id, value):
    with Session.begin() as s:
        key = f'{kind}:{id}'
        row = s.get(Record, key)
        if row:
            row.payload = json.dumps(value)
        else:
            s.add(Record(key=key, kind=kind, payload=json.dumps(value)))
    return value

def get(kind, id):
    with Session() as s:
        r = s.get(Record, f'{kind}:{id}')
        return json.loads(r.payload) if r else None

def all_records(kind):
    with Session() as s:
        return [json.loads(r.payload) for r in s.query(Record).filter_by(kind=kind).order_by(Record.created_at).all()]

def delete(kind, id):
    with Session.begin() as s:
        r = s.get(Record, f'{kind}:{id}')
        if r:
            s.delete(r)
