import argparse
from pathlib import Path

from mcpSuunto.config import AppConfig
from mcpSuunto.ingestion.ingest import (
    LocalOneDriveClient,
    download_onedrive_files,
    ingest_directory,
)
from mcpSuunto.observability import configure_logging


def main() -> None:
    config = AppConfig.load()
    parser = argparse.ArgumentParser(description="Importe les activités FIT Suunto dans DuckDB.")
    parser.add_argument(
        "--onedrive",
        type=Path,
        default=None,
        help="Dossier OneDrive synchronisé contenant les nouveaux .fit",
    )
    parser.add_argument(
        "--inbox",
        type=Path,
        default=None,
        help="Dossier contenant les fichiers .fit (défaut: data/inbox)",
    )
    parser.add_argument(
        "--processed",
        type=Path,
        default=None,
        help="Dossier des fichiers traités (défaut: data/processed)",
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        default=None,
        help="Fichier de journalisation (défaut: data/logs/ingestion.log)",
    )
    parser.add_argument(
        "--keep-onedrive",
        action="store_true",
        help="Conserver les fichiers dans OneDrive après copie locale réussie",
    )
    args = parser.parse_args()

    onedrive = args.onedrive or config.onedrive_dir
    inbox = args.inbox or config.inbox_dir
    processed = args.processed or config.processed_dir
    log_file = args.log_file or config.log_file
    configure_logging(log_file)
    if not onedrive.is_dir():
        raise FileNotFoundError(f"OneDrive FIT folder does not exist: {onedrive}")
    client = LocalOneDriveClient(
        onedrive,
        delete_after_download=not args.keep_onedrive,
    )
    download_onedrive_files(client, inbox)
    imported = ingest_directory(inbox, database_path=config.database_path, processed_dir=processed)
    print(f"{len(imported)} activité(s) importée(s).")


if __name__ == "__main__":
    main()