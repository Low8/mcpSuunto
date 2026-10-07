import argparse
from pathlib import Path

from mcpSuunto.ingestion.ingest import (
    LocalOneDriveClient,
    download_onedrive_files,
    ingest_directory,
)
from mcpSuunto.observability import configure_logging


def main() -> None:
    parser = argparse.ArgumentParser(description="Importe les activités FIT Suunto dans DuckDB.")
    parser.add_argument(
        "--onedrive",
        type=Path,
        default=Path(r"C:\Users\Louis\OneDrive\suunto\fit"),
        help="Dossier OneDrive synchronisé contenant les nouveaux .fit",
    )
    parser.add_argument(
        "--inbox",
        type=Path,
        default=Path("data/inbox"),
        help="Dossier contenant les fichiers .fit (défaut: data/inbox)",
    )
    parser.add_argument(
        "--processed",
        type=Path,
        default=Path("data/processed"),
        help="Dossier des fichiers traités (défaut: data/processed)",
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        default=Path("data/logs/ingestion.log"),
        help="Fichier de journalisation (défaut: data/logs/ingestion.log)",
    )
    parser.add_argument(
        "--keep-onedrive",
        action="store_true",
        help="Conserver les fichiers dans OneDrive après copie locale réussie",
    )
    args = parser.parse_args()

    configure_logging(args.log_file)
    if not args.onedrive.is_dir():
        raise FileNotFoundError(f"OneDrive FIT folder does not exist: {args.onedrive}")
    client = LocalOneDriveClient(
        args.onedrive,
        delete_after_download=not args.keep_onedrive,
    )
    download_onedrive_files(client, args.inbox)
    imported = ingest_directory(args.inbox, processed_dir=args.processed)
    print(f"{len(imported)} activité(s) importée(s).")


if __name__ == "__main__":
    main()