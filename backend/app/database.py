"""Conexão com o banco SQLite via SQLAlchemy (NF010).

O arquivo do banco fica em backend/instance/aea.db, pasta que o
.gitignore já ignora: cada pessoa tem o próprio histórico local.
"""
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

BACKEND_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BACKEND_DIR / "instance" / "aea.db"
DEFAULT_DB_URL = f"sqlite:///{DB_PATH.as_posix()}"


class Base(DeclarativeBase):
    """Classe-mãe de todos os modelos (tabelas) do sistema."""


@event.listens_for(Engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
    """Liga a checagem de chave estrangeira, que o SQLite deixa DESLIGADA.

    Sem isso, o SQLite aceitaria uma análise apontando para um áudio que
    não existe, e o ON DELETE CASCADE não funcionaria.
    """
    if dbapi_connection.__class__.__module__.startswith("sqlite3"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def make_engine(url=DEFAULT_DB_URL):
    """Cria o 'motor' de conexão. Os testes passam uma URL em memória."""
    return create_engine(url)


def make_session_factory(engine):
    """Fábrica de sessões: cada sessão é uma 'conversa' com o banco."""
    return sessionmaker(bind=engine, expire_on_commit=False)


def create_tables(engine):
    """Cria as tabelas que ainda não existem (não apaga dados)."""
    from . import models  # noqa: F401  registra os modelos na Base

    Base.metadata.create_all(engine)


def drop_tables(engine):
    """Apaga TODAS as tabelas e os dados. Usado só pelo --reset."""
    from . import models  # noqa: F401

    Base.metadata.drop_all(engine)
