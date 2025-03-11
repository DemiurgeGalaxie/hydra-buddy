# Hydra-Buddies

Un wrapper élégant et intuitif pour Hydra qui simplifie la gestion de configuration dans vos projets Python.

## Vue d'ensemble

Hydra-Buddies facilite l'accès et la manipulation des configurations Hydra grâce à une navigation contextuelle fluide, une résolution intelligente des interpolations et une prise en charge des configurations imbriquées. Il est idéal pour les applications complexes nécessitant des configurations structurées.


# Rapport de développement - Hydra-Buddies

## Vue d'ensemble

Hydra-Buddies est un wrapper autour de Hydra qui simplifie la gestion de configuration en Python. Il fournit une interface intuitive pour accéder et manipuler les configurations de manière contextuelle.

## Fonctionnalités clés

### 1. Navigation contextuelle
- Utilisation de `walk()` pour naviguer dans la hiérarchie
- Support du context manager (`with`)
- Accès aux attributs imbriqués

### 2. Flexibilité d'accès
- Style attribut: `reader.key`
- Style dictionnaire: `reader["key"]`
- Navigation chainée: `reader.database.host`

### 3. Gestion des chemins
- Ajout dynamique de chemins de configuration
- Support multi-configuration
- Résolution automatique des configurations

### 4. Préfixage
- Décorateur pour ajouter des préfixes
- Préservation des clés originales
- Utile pour les environnements multiples

## Architecture

### Structure du projet
```
hydra-buddies/
├── hydra_buddies/
│   ├── __init__.py
│   └── reader.py
├── pyproject.toml
├── README.md
└── LICENSE
```

### Diagramme de classe
```
TheReader
├── Attributs
│   ├── config_paths: List[str]
│   ├── cfg: DictConfig
│   ├── context: List[str]
│   └── cursor: DictConfig
└── Méthodes
    ├── __init__(cfg_name: str)
    ├── update_path(path: str)
    ├── walk(*args: list[str])
    ├── get_context()
    └── add_prefix(prefix: str)
```

## Guide technique détaillé

## Installation

```bash
pip install hydra-buddies
```


## Fonctionnalités clés

### 1. Navigation contextuelle

Parcourez votre configuration de manière intuitive :

```python
from hydra_buddies import TheReader

reader = TheReader("config")

# Navigation simple et directe
project_name = reader.project.name

# Navigation contextuelle avec walk()
with reader.walk('database'):
    host = reader.host
    port = reader.port
    
    # Imbrication des contextes
    with reader.walk('credentials'):
        username = reader.username
        password = reader.password

# Le contexte se restaure automatiquement à la sortie du bloc
```


### 2. Flexibilité d'accès

Plusieurs façons d'accéder aux données :

```python
# Style attribut (recommandé)
api_url = reader.api.url

# Style dictionnaire
timeout = reader["api"]["timeout"]

# Navigation chainée
max_retries = reader.api.retry.max_attempts
```


### 3. Gestion avancée des chemins multiples

Nouveauté ! Chargez des configurations depuis plusieurs sources :

```python
# Initialiser avec le chemin par défaut
reader = TheReader("config")

# Définir le chemin principal
reader.update_path("/path/to/main/config")

# Ajouter des chemins supplémentaires pour les imports imbriqués
reader.add_config_path("/path/to/services/config")
reader.add_config_path("/path/to/environments/config")

# Les configurations seront fusionnées intelligemment
```


### 4. Résolution fiable des interpolations

Nouveauté ! Solution robuste pour la résolution des références entre fichiers :

```python
# Obtenir une configuration entièrement résolue
resolved_config = reader.get_resolved_config()

# Accéder aux valeurs résolues (incluant les références croisées)
db_password = resolved_config["database"]["credentials"]["password"]

# La configuration résolue est également stockée dans reader.resolved
```


### 5. Préfixage

Utilisation de décorateurs pour ajouter des préfixes aux clés :

```python
@reader.add_prefix('dev')
def setup_environment():
    # Toutes les clés sont disponibles avec le préfixe 'dev.'
    # mais aussi avec leur nom original
    setup_database(reader.dev.database.host)
```


## Structure recommandée des configurations

Pour une résolution correcte des interpolations, structurez vos fichiers YAML comme suit :

```yaml
# config.yaml
defaults:
  - secrets/login      # Charger les secrets en PREMIER
  - secrets/keys       # Puis les clés sensibles
  - secrets/env        # Puis les variables d'environnement
  - _self_             # Contenu de ce fichier
  - database: default  # Configurations de composants
  - api: default
  - logging: default

project:
  name: "mon-projet"
  version: "1.0.0"
```


## Interface en ligne de commande

### Lire une configuration

```bash
buddy read CONFIG_NAME [OPTIONS]
```


Options:
- `--path, -p TEXT` : Chemin vers le répertoire de configuration
- `--resolve, -r` : Résoudre les interpolations
- `--debug, -d` : Afficher des informations de débogage

Exemples:
```bash
buddy read dev                      # Afficher dev.yaml
buddy read config --resolve         # Afficher avec interpolations résolues
```


### Obtenir une valeur spécifique

```bash
buddy get CONFIG_NAME KEY [OPTIONS]
```


Options:
- `--path, -p TEXT` : Chemin vers le répertoire de configuration

Exemples:
```bash
buddy get dev database.host         # Récupérer l'hôte de la base de données
```


### Lister les clés d'une configuration

```bash
buddy list-keys CONFIG_NAME [OPTIONS]
```


Options:
- `--path, -p TEXT` : Chemin vers le répertoire de configuration
- `--full, -f` : Afficher toutes les clés à tous les niveaux
- `--values, -v` : Afficher les valeurs primitives
- `--resolve, -r` : Résoudre les références 
- `--debug, -d` : Afficher des informations de débogage
- `--ref` : Afficher les références des sources
- `--raw` : Inclure les clés defaults dans le résultat

## Architecture

```
TheReader
├── Attributs
│   ├── primary_path: str              # Chemin principal
│   ├── config_paths: List[str]        # Chemins supplémentaires
│   ├── cfg_name: str                  # Nom de la configuration
│   ├── cfg: DictConfig                # Configuration chargée
│   ├── resolved: dict                 # Configuration résolue
│   ├── context: List[str]             # Contexte de navigation
│   └── cursor: DictConfig             # Curseur de navigation
└── Méthodes
    ├── __init__(cfg_name: str)
    ├── update_path(path: str)
    ├── add_config_path(path: str)
    ├── _promote_secrets()
    ├── get_resolved_config()
    ├── walk(*args: list[str])
    ├── get_context()
    └── add_prefix(prefix: str)
```


## Exemples d'intégration

### Avec Flask

```python
from flask import Flask
from hydra_buddies import TheReader

env = os.environ.get("FLASK_ENV", "dev")
config_reader = TheReader(env)

app = Flask(__name__)
app.config.update(config_reader.get_resolved_config())
```


### Dans un script de traitement de données

```python
from hydra_buddies import TheReader

reader = TheReader("etl")
config = reader.get_resolved_config()

db_connection = create_connection(
    host=config["database"]["host"],
    port=config["database"]["port"],
    user=config["database"]["credentials"]["username"],
    password=config["database"]["credentials"]["password"]
)
```


## Bonnes pratiques

1. **Secrets en premier** : Placez toujours les imports de secrets au début de la liste `defaults`
2. **Structure claire** : Organisez vos configurations par domaine fonctionnel
3. **Chemins multiples** : Utilisez `add_config_path()` pour les grandes applications avec plusieurs modules
4. **Valeurs par défaut** : Fournissez des valeurs par défaut pour les variables d'environnement
5. **Isolation** : Séparez les configurations spécifiques à l'environnement dans des fichiers distincts (dev, prod, etc.)

## Références

- [Documentation Hydra](https://hydra.cc/docs/intro)
- [Tutoriel sur OmegaConf](https://omegaconf.readthedocs.io/)

---

Contribuez à Hydra-Buddies ou signalez des problèmes sur [GitHub](https://github.com/votre-repo/hydra-buddies).