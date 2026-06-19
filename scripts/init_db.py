from app.db.session import init_db
from app.core.config import get_settings


def main() -> None:
    settings = get_settings()
    init_db()
    print(f"[OK] database initialized: {settings.sqlite_path}")
    print("[OK] tables ensured: documents, chunks, notes")
    print("[OK] sample notes inserted with INSERT OR IGNORE")


if __name__ == "__main__":
    main()
