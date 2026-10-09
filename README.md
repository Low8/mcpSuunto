# mcpSuunto

Serveur MCP local qui permet à Claude Desktop d'interroger les activités
Suunto stockées dans une base DuckDB.

Le projet est conçu pour fonctionner localement : les fichiers FIT, la base
et les données de santé ou de localisation ne quittent pas l'ordinateur de
l'utilisateur.

> **Important :** ce projet fonctionne avec **Claude Desktop**, installé sur
> l'ordinateur. Il ne fonctionne pas directement avec Claude dans le navigateur
> (Claude Web), car le serveur MCP utilise le transport local `stdio`.

## Ce que fait le projet

Le projet contient deux commandes principales :

```text
OneDrive synchronisé
        ↓
import FIT
        ↓
validation Pydantic
        ↓
DuckDB locale
        ↓
serveur MCP local
        ↓
Claude Desktop
```

### Import des activités

La commande `mcpSuunto` :

1. cherche les fichiers `.fit` dans le dossier OneDrive configuré ;
2. les copie dans `data/inbox/` ;
3. parse les fichiers FIT avec `fitdecode` ;
4. valide les données avec les modèles Pydantic ;
5. insère l'activité et ses données dans DuckDB dans une transaction atomique ;
6. déplace les fichiers réussis dans `data/processed/` ;
7. supprime le fichier du dossier OneDrive après une copie réussie.

Les données suivantes sont conservées lorsque le fichier FIT les contient :

- activités running, trail running, cycling, mountain biking, hiking,
  swimming, walking et autres sports ;
- records détaillés ;
- laps ;
- intervalles structurés de workout ;
- champs développeur Suunto comme NGP et pente ;
- longueurs de natation ;
- événements FIT.

Un fichier en erreur reste dans `data/inbox/`. Les autres fichiers continuent
d'être traités indépendamment. Les erreurs sont enregistrées dans
`data/logs/ingestion.log`.

## Installation pour débutant

### Prérequis

Sur Windows, installer :

1. **Git** : <https://git-scm.com/download/win>
2. **uv** : <https://docs.astral.sh/uv/getting-started/installation/>
3. **Claude Desktop** : <https://claude.ai/download>
4. OneDrive, si les fichiers FIT sont synchronisés localement.

Le projet utilise Python `>= 3.13`, mais `uv` installe et utilise
automatiquement l'environnement Python du projet.

### Cloner le dépôt

Ouvrir PowerShell et exécuter :

```powershell
git clone https://github.com/Low8/mcpSuunto.git
cd mcpSuunto
uv sync
```

Pour vérifier l'installation :

```powershell
uv run pytest
```

## Configurer le dossier OneDrive

### 1. Créer la configuration locale

Copier le modèle :

```powershell
Copy-Item config\config.example.toml config\config.toml
```

Ouvrir le fichier :

```powershell
notepad config\config.toml
```

### 2. Modifier `onedrive_dir`

Exemple Windows :

```toml
[paths]
onedrive_dir = "C:/Users/MonNom/OneDrive/suunto/fit"
inbox_dir = "data/inbox"
processed_dir = "data/processed"
database_path = "data/database/suunto.duckdb"
log_file = "data/logs/ingestion.log"
```

Remplacer `C:/Users/MonNom/OneDrive/suunto/fit` par le dossier réel qui
contient les fichiers `.fit`.

Les autres chemins peuvent rester tels quels. Ils sont relatifs à la racine
du projet.

Le fichier `config/config.toml` est volontairement ignoré par Git. Chaque
utilisateur conserve donc sa propre configuration et son propre chemin
OneDrive.

### 3. Tester l'import

Lancer :

```powershell
uv run mcpSuunto
```

Un fichier FIT traité avec succès finit dans :

```text
data/processed/
```

La base est créée ici :

```text
data/database/suunto.duckdb
```

Pour conserver une copie des fichiers dans OneDrive après l'import :

```powershell
uv run mcpSuunto --keep-onedrive
```

Sans cette option, les fichiers sont supprimés du dossier OneDrive après
traitement réussi. Ils restent disponibles dans `data/processed/`.

### Importer de nouvelles activités plus tard

Déposer ou synchroniser les nouveaux fichiers FIT dans le dossier OneDrive,
puis relancer :

```powershell
uv run mcpSuunto
```

L'import est rejouable. Une activité déjà connue est remplacée
atomiquement, sans créer de copie partielle dans la base.

### Actualiser la base quand Claude Desktop utilise le MCP

Si Claude Desktop utilise actuellement le serveur MCP, il peut verrouiller
son exécutable et empêcher `uv` de le mettre à jour. Le script fourni arrête
uniquement les processus `mcpSuunto-server`, lance l'import, puis se termine.
Il ne ferme pas Claude Desktop et ne touche pas aux autres processus.

Depuis la racine du projet, lancer :

```powershell
.\scripts\refresh-suunto.ps1
```

Pour conserver également les fichiers dans OneDrive :

```powershell
.\scripts\refresh-suunto.ps1 --keep-onedrive
```

Claude Desktop pourra relancer automatiquement le serveur MCP lors de sa
prochaine utilisation. Si PowerShell bloque l'exécution des scripts, autoriser
uniquement cette session puis relancer la commande :

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\refresh-suunto.ps1
```

## Connecter Claude Desktop

### Important : Desktop, pas Claude Web

Il faut utiliser **Claude Desktop**, pas `claude.ai dans le navigateur`.

Le serveur actuel est un processus local lancé par Claude Desktop. Claude Web
ne peut pas exécuter un programme présent sur l'ordinateur et ne peut donc pas
accéder directement à ce serveur local.

### 1. Trouver le chemin de `uv`

Dans PowerShell :

```powershell
(Get-Command uv).Source
```

Copier le chemin retourné. Il ressemble à l'un des exemples suivants :

```text
C:\Users\MonNom\AppData\Local\Microsoft\WinGet\Packages\...\uv.exe
C:\Users\MonNom\.local\bin\uv.exe
```

### 2. Ouvrir la configuration MCP de Claude Desktop

Dans Claude Desktop :

1. ouvrir **Settings** ;
2. ouvrir **Developer** ;
3. cliquer sur **Edit Config** ou **Modifier la configuration** ;
4. ouvrir le fichier de configuration affiché.

Si le bouton n'est pas disponible, le fichier peut généralement être ouvert
depuis PowerShell avec :

```powershell
explorer "$env:APPDATA\Claude"
```

Avec la version Microsoft Store, le fichier peut se trouver sous un chemin
similaire à :

```text
C:\Users\MonNom\AppData\Local\Packages\Claude_...\LocalCache\Roaming\Claude\
```

Il faut modifier le fichier de configuration MCP affiché par Claude Desktop,
pas un fichier situé dans le dossier `logs`.

### 3. Ajouter le serveur Suunto

Ajouter une propriété `mcpServers` au niveau racine du JSON :

```json
{
  "mcpServers": {
    "suunto": {
      "command": "<chemin-absolu-vers-uv.exe>",
      "args": [
        "run",
        "--directory",
        "<chemin-absolu-vers-le-projet-mcpSuunto>",
        "mcpSuunto-server"
      ]
    }
  }
}
```

Exemple fictif complet sous Windows :

```json
{
  "mcpServers": {
    "suunto": {
      "command": "C:\\Users\\MonNom\\AppData\\Local\\uv\\uv.exe",
      "args": [
        "run",
        "--directory",
        "C:\\Projets\\mcpSuunto",
        "mcpSuunto-server"
      ]
    }
  }
}
```

Si le fichier contient déjà d'autres propriétés, ne pas les supprimer.
Ajouter seulement `mcpServers` au niveau racine. Dans un fichier JSON, les
antislashs Windows doivent être doublés :

```json
"C:\\Projets\\mcpSuunto"
```

et non :

```text
C:\Projets\mcpSuunto
```

### 4. Redémarrer Claude Desktop

Fermer complètement Claude Desktop, y compris depuis la zone de notification
Windows, puis le relancer.

Dans une nouvelle conversation, demander :

```text
Quels outils MCP Suunto sont disponibles ?
```

Puis tester :

```text
Liste mes 5 dernières activités Suunto.
```

Claude Desktop lance automatiquement `mcpSuunto-server` lorsque la connexion
MCP est configurée. Il n'est pas nécessaire de lancer le serveur à la main.

## Outils disponibles dans Claude

Le serveur expose notamment :

- `list_activities` : activités récentes ;
- `get_activity` : détail d'une activité ;
- `search_activities` : recherche par date, sport, distance, durée ou D+ ;
- `get_training_history` : historique groupé par jour, semaine ou mois ;
- `get_training_load` : charge sur une période ;
- `get_performance_trends` : données pour analyser les tendances ;
- `get_intervals` : intervalles structurés et métadonnées FIT ;
- `query_activity_records` : records détaillés avec sélection de champs et
  échantillonnage ;
- `compare_activities` : comparaison de plusieurs activités ;
- `compare_intervals` : comparaison d'intervalles ;
- `get_similar_activities` : activités similaires ;
- `get_personal_bests` : meilleurs résultats calculables avec les données
  disponibles ;
- `get_recent_training_context` : contexte des 7 et 28 derniers jours.

Le serveur fournit les données structurées. Claude interprète ensuite les
résultats et peut produire une analyse ou une recommandation. Le serveur ne
génère pas lui-même de programme d'entraînement.

## Tester avec MCP Inspector

MCP Inspector est optionnel. Pour l'utiliser :

```powershell
uv run mcp dev src/mcpSuunto/mcp/server.py
```

Inspector permet de vérifier que les tools sont enregistrés et d'appeler
manuellement `list_activities`, `get_activity`, etc.

Pour tester directement le serveur :

```powershell
uv run mcpSuunto-server
```

Il est normal de ne voir aucun écran : le serveur attend une connexion MCP
sur l'entrée/sortie standard. Arrêter avec `Ctrl+C`.

## Gestion des erreurs

Les erreurs sont visibles dans la console et enregistrées dans :

```text
data/logs/ingestion.log
```

Pour consulter les dernières erreurs :

```powershell
Get-Content data\logs\ingestion.log -Tail 50
```

Si une activité échoue :

- elle reste dans `data/inbox/` ;
- elle n'est pas déplacée vers `data/processed/` ;
- la transaction DuckDB est annulée ;
- les autres activités continuent d'être traitées.

## Structure du projet

```text
src/mcpSuunto/
├── config.py              # Configuration locale des chemins
├── ingestion/             # OneDrive local et orchestration des imports
├── parsing/               # Parsing FIT vers modèles Pydantic
├── models/                # Modèles métier indépendants de DuckDB
├── duckdb/                # Schéma et persistance transactionnelle
├── observability/         # Logs et diagnostic des erreurs
└── mcp/                   # Repository de lecture et tools MCP
```

Les données personnelles ne sont pas nécessaires pour cloner le projet :

- `data/database/` est ignoré ;
- `data/inbox/` est ignoré ;
- `data/processed/` est ignoré ;
- `data/inspection/` est ignoré ;
- les fichiers `*.fit` sont ignorés ;
- `data/logs/` est ignoré ;
- `config/config.toml` est ignoré.

## Développement et vérifications

Depuis la racine du projet :

```powershell
uv run pytest
uv run ruff check .
uv run mypy src
```

Les tests utilisent une base DuckDB temporaire et ne nécessitent pas les
données Suunto personnelles d'un utilisateur.
