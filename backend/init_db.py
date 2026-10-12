"""Script de inicialização do banco SQLite (NF007).

Uso, dentro de backend/ e com a .venv ativa:
    python init_db.py           cria o banco e as tabelas que faltarem
    python init_db.py --reset   APAGA todas as análises e recria as tabelas
"""
import argparse

from app.database import DB_PATH, create_tables, drop_tables, make_engine


def main(argv=None):
    parser = argparse.ArgumentParser(description="Inicializa o banco do AEA.")
    parser.add_argument("--reset", action="store_true",
                        help="apaga todas as tabelas e dados antes de criar")
    args = parser.parse_args(argv)

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    engine = make_engine()

    if args.reset:
        resposta = input("Isso APAGA todo o histórico. Digite 'sim' para "
                         "confirmar: ")
        if resposta.strip().lower() != "sim":
            print("Operação cancelada. Nada foi alterado.")
            return 1
        drop_tables(engine)
        print("Tabelas apagadas.")

    create_tables(engine)
    engine.dispose()
    print(f"Banco pronto em {DB_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
