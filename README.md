# mcpSuunto

MCP Suunto personnel qui donne accès aux activités enregistrées par la montre.

## Importer les activités

Les fichiers `.fit` déposés dans `data/inbox` sont importés dans
`data/database/suunto.duckdb` avec :

```text
uv run mcpSuunto
```

Par défaut, la commande lit le dossier OneDrive synchronisé
`C:\Users\Louis\OneDrive\suunto\fit`, copie les fichiers `.fit` dans
`data/inbox`, puis les supprime du dossier source uniquement après une copie
réussie. Pour conserver les fichiers dans OneDrive :

```powershell
uv run mcpSuunto --keep-onedrive
```

Les erreurs sont affichées dans la console et enregistrées dans
`data/logs/ingestion.log`, avec le fichier concerné et l'étape en échec.
Les chemins variables sont configurés dans `config/config.toml`. Crée ce
fichier à partir de `config/config.example.toml` et adapte notamment
`onedrive_dir`. Le fichier local n'est pas versionné.

Pour une surcharge ponctuelle, les options CLI restent disponibles :

```powershell
uv run mcpSuunto --onedrive "D:\Suunto\fit"
```

Les variables d'environnement `SUUNTO_ONEDRIVE_DIR`,
`SUUNTO_INBOX_DIR`, `SUUNTO_PROCESSED_DIR`, `SUUNTO_DATABASE_PATH` et
`SUUNTO_LOG_FILE` peuvent aussi remplacer les valeurs du fichier de
configuration.

Le pipeline parse, valide avec Pydantic, commit la transaction DuckDB, puis
déplace seulement les fichiers réussis vers `data/processed`. Un fichier en
erreur reste dans `data/inbox` et l'erreur est journalisée. L'import est
rejouable : une activité déjà importée est remplacée à partir de son empreinte
de fichier.

Le flux est séparé en responsabilités :

- `src/mcpSuunto/ingestion` découvre les nouveaux fichiers et évite les doublons ;
- `src/mcpSuunto/parsing` décode les messages FIT ;
- `src/mcpSuunto/duckdb` initialise le schéma SQL et persiste les données.

### OneDrive

Le projet fournit le contrat `OneDriveClient` dans
`src/mcpSuunto/ingestion/ingest.py`, mais aucun connecteur ni secret OneDrive
n'est inventé. Un connecteur externe doit fournir `list_fit_files`,
`download` et `delete`. Les téléchargements sont écrits dans un fichier
`.partial`, renommés atomiquement après vérification, puis seulement supprimés
à distance. Tant qu'aucun connecteur authentifié n'est fourni, le pipeline
local fonctionne avec `data/inbox`.

Pour utiliser d'autres dossiers :

```text
uv run mcpSuunto --inbox chemin/vers/inbox --processed chemin/vers/processed
```

## Serveur MCP

Le serveur MCP expose les données DuckDB sans modifier le parsing ou
l'ingestion :

```powershell
uv run mcpSuunto-server
```

Le transport par défaut est `stdio`, compatible avec Claude Desktop et MCP
Inspector. Pour lancer Inspector avec le serveur :

```powershell
npx @modelcontextprotocol/inspector uv run mcpSuunto-server
```

Les tools disponibles sont :

- `list_activities`
- `get_activity`
- `search_activities`
- `get_training_history`
- `get_training_load`
- `get_performance_trends`
- `get_intervals`
- `query_activity_records`
- `compare_activities`
- `compare_intervals`
- `get_similar_activities`
- `get_personal_bests`
- `get_recent_training_context`

Exemple de configuration Claude Desktop :

```json
{
  "mcpServers": {
    "suunto": {
      "command": "C:\\Users\\Louis\\.local\\bin\\uv.exe",
      "args": [
        "run",
        "--directory",
        "C:\\Users\\Louis\\Code\\projet\\mcpSuunto",
        "mcpSuunto-server"
      ]
    }
  }
}
```
