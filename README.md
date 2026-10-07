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
Le chemin source peut être changé avec `--onedrive`.

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
