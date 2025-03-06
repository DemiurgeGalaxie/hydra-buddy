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

### Installation et configuration

1. Installation via pip :
```bash
pip install hydra-buddies
```

2. Configuration minimale requise :
```yaml
# .hydra-conf/config.yaml
key: value
nested:
  key: value
```

### Initialisation et configuration

```python
from hydra_buddies import TheReader

# Initialisation basique
reader = TheReader("config")

# Avec chemin de configuration personnalisé
reader = TheReader("config")
reader.update_path("chemin/vers/config")
```

### Patterns d'utilisation

1. **Pattern Contextuel**
```python
with reader:
    reader.walk("database")
    host = reader.host
    port = reader.port
# Le contexte est automatiquement réinitialisé ici
```

2. **Pattern Chaîné**
```python
# Navigation directe
result = reader.walk("database", "credentials").username

# Avec context manager
with reader.walk("database", "credentials") as r:
    username = r.username
    password = r.password
```

3. **Pattern Dictionnaire**
```python
# Lecture
value = reader["key"]
nested_value = reader["parent"]["child"]

# Écriture
reader["key"] = "nouvelle_valeur"
```

### Gestion des erreurs

```python
try:
    reader.walk("chemin", "inexistant")
except AttributeError as e:
    print("Chemin non trouvé:", e)

try:
    reader.update_path("/mauvais/chemin")
except ValueError as e:
    print("Erreur de mise à jour du chemin:", e)
```

### Bonnes pratiques

1. **Gestion du contexte**
```python
# Recommandé
with reader:
    reader.walk("section")
    # travail dans le contexte

# À éviter
reader.walk("section")
# travail sans context manager
```

2. **Mise à jour des chemins**
```python
# Recommandé - avant toute navigation
reader.update_path("nouveau/chemin")
reader.walk("section")

# À éviter - mise à jour pendant la navigation
reader.walk("section")
reader.update_path("nouveau/chemin")  # Lève une ValueError
```

3. **Utilisation des préfixes**
```python
# Décorateur de préfixe
@reader.add_prefix("dev")
def configure_dev():
    return reader.database.host

# Les clés seront accessibles via dev.database.host
```

### Exemples avancés

1. **Configuration multi-environnement**
```python
# config.yaml
dev:
  database:
    host: localhost
prod:
  database:
    host: production.server

# Usage
with reader:
    # Développement
    reader.walk("dev")
    dev_host = reader.database.host
    
    # Production
    reader.walk("prod")
    prod_host = reader.database.host
```

2. **Manipulation dynamique**
```python
def configure_environment(env: str):
    with reader:
        reader.walk(env)
        return {
            "host": reader.database.host,
            "port": reader.database.port,
            "credentials": {
                "user": reader.database.credentials.username,
                "pass": reader.database.credentials.password
            }
        }
```

## Points forts

1. **Simplicité d'utilisation**
   - API intuitive
   - Réduction de la verbosité
   - Documentation claire

2. **Flexibilité**
   - Multiples styles d'accès
   - Support des configurations complexes
   - Extension facile

3. **Robustesse**
   - Gestion des erreurs
   - Validation des entrées
   - Compatibilité Hydra

## Améliorations futures

1. **Performance**
   - Optimisation de la navigation
   - Cache intelligent
   - Lazy loading

2. **Fonctionnalités**
   - Validation de schéma
   - Support async
   - Plugins système

3. **Documentation**
   - Plus d'exemples
   - Tutoriels vidéo
   - Documentation API complète

## Utilisation de TheReader

La classe `TheReader` est le cœur de Hydra-Buddies. Voici comment l'utiliser :

### Initialisation

Pour initialiser un objet `TheReader`, vous devez fournir le nom de la configuration que vous souhaitez lire. Par exemple :
```python
reader = TheReader("ma_config")
```
Cela créera un objet `TheReader` prêt à lire et à manipuler votre configuration.

### Navigation contextuelle

Pour naviguer dans la hiérarchie de votre configuration, utilisez la méthode `walk()`. Par exemple, pour accéder à une sous-clé `database` puis à une sous-clé `host`, vous pouvez faire :
```python
reader.walk("database", "host")
```
Cela positionnera le curseur sur la clé `host` dans le contexte `database`.

### Accès aux valeurs

Une fois que vous avez navigué jusqu'à une clé, vous pouvez accéder à sa valeur en utilisant le style attribut ou le style dictionnaire. Par exemple :
```python
print(reader.key)  # Style attribut
print(reader["key"])  # Style dictionnaire
```
### Modification des valeurs

Vous pouvez modifier les valeurs de votre configuration en utilisant le style attribut ou le style dictionnaire. Par exemple :
```python
reader.key = "nouvelle_valeur"  # Style attribut
reader["key"] = "nouvelle_valeur"  # Style dictionnaire
```
### Ajout de préfixes

Pour ajouter un préfixe à vos clés de configuration, utilisez le décorateur `add_prefix()`. Par exemple :
```python
reader.add_prefix("mon_prefix")
```
Cela ajoutera le préfixe `mon_prefix.` à toutes les clés de votre configuration qui ne le possèdent pas déjà.

### Context manager

`TheReader` supporte le context manager (`with`). Cela signifie que vous pouvez utiliser un objet `TheReader` dans un bloc `with` pour gérer automatiquement le contexte. Par exemple :
```python
with TheReader("ma_config") as reader:
    # Votre code ici
    reader.walk("database", "host")
    print(reader.key)
```
Lorsque vous sortez du bloc `with`, le contexte est automatiquement réinitialisé. Cela vous permet de gérer votre configuration dans un contexte spécifique sans avoir à vous soucier de la gestion du contexte.

### Navigation directe avec context manager

Vous pouvez également utiliser le context manager avec la méthode `walk()` pour naviguer directement dans le contexte. Par exemple :
```python
with TheReader("ma_config").walk("database", "host") as reader:
    # Votre code ici
    print(reader.key)
```
Cela vous permet de naviguer directement dans le contexte sans avoir à appeler la méthode `walk()` séparément.

### Réinitialisation du contexte

Si vous souhaitez réinitialiser le contexte manuellement, vous pouvez utiliser la méthode `start()`. Par exemple :
```python
reader.start()
```
Cela réinitialisera le contexte et vous permettra de recommencer à naviguer dans la hiérarchie de votre configuration.

## Conclusion

Hydra-Buddies offre une solution élégante pour la gestion de configuration en Python, combinant simplicité d'utilisation et puissance fonctionnelle.

# Hydra-Buddies Documentation

## Commandes CLI

Hydra-Buddies fournit plusieurs commandes en ligne de commande via l'utilitaire `buddy`. Voici le détail de chaque commande :

### Initialisation du projet

```bash
buddy init
```

Cette commande initialise un nouveau projet avec une structure de configuration Hydra. Elle :
- Crée un répertoire `.hydra-conf` avec une structure complète
- Configure les environnements dev et prod
- Met en place la gestion des secrets
- Ajoute automatiquement le répertoire des secrets au .gitignore
- Crée les configurations pour la base de données, l'API et les logs

### Lecture de configuration

```bash
# Lire toute la configuration
buddy read config_name

# Lire avec un chemin spécifique
buddy read config_name --path /chemin/vers/config
```

Cette commande affiche le contenu complet d'une configuration. Options :
- `config_name` : Nom de la configuration à lire
- `--path, -p` : Chemin optionnel vers le répertoire de configuration

### Obtention d'une valeur spécifique

```bash
# Obtenir une valeur simple
buddy get config_name database.host

# Avec un chemin personnalisé
buddy get config_name api.url --path /chemin/vers/config
```

Cette commande permet d'extraire une valeur spécifique de la configuration. Arguments :
- `config_name` : Nom de la configuration
- `key` : Chemin de la clé (utilise la notation point)
- `--path, -p` : Chemin optionnel vers le répertoire de configuration

### Liste des clés disponibles

```bash
# Lister toutes les clés
buddy list-keys config_name

# Avec un chemin personnalisé
buddy list-keys config_name --path /chemin/vers/config
```

Cette commande affiche toutes les clés disponibles dans la configuration de manière récursive. Options :
- `config_name` : Nom de la configuration à explorer
- `--path, -p` : Chemin optionnel vers le répertoire de configuration

## Structure de configuration générée

L'initialisation (`buddy init`) crée la structure suivante :

```
.hydra-conf/
├── api/
│   ├── default.yaml
│   ├── dev.yaml
│   └── prod.yaml
├── database/
│   ├── default.yaml
│   ├── dev.yaml
│   └── prod.yaml
├── logging/
│   ├── default.yaml
│   ├── dev.yaml
│   └── prod.yaml
├── secrets/
│   ├── keys.yaml
│   └── login.yaml
├── config.yaml
├── config_dev.yaml
└── config_prod.yaml
```

### Sécurité

La commande `init` configure automatiquement la sécurité :
- Ajoute `.hydra-conf/secret/*` au .gitignore
- Met en place des variables d'environnement pour les secrets
- Sépare les configurations sensibles dans le répertoire `secrets/`

### Exemples d'utilisation

1. Initialiser un nouveau projet :
```bash
buddy init
```

2. Lire la configuration de développement :
```bash
buddy read config_dev
```

3. Obtenir l'URL de l'API en production :
```bash
buddy get config_prod api.url
```

4. Explorer toutes les clés disponibles :
```bash
buddy list-keys config
```

### Bonnes pratiques

1. Toujours initialiser le projet avec `buddy init`
2. Vérifier que les secrets sont bien dans .gitignore
3. Utiliser des variables d'environnement pour les valeurs sensibles
4. Séparer les configurations par environnement