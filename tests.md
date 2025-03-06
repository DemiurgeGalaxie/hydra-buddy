# Documentation des Tests Hydra-Buddy

Ce document décrit l'approche de test utilisée pour Hydra-Buddy, les différents tests implémentés, et comment les exécuter.

## Vue d'ensemble

Hydra-Buddy est testé en utilisant pytest. Les tests couvrent :

1. La classe `TheReader` pour la lecture de configuration
2. Les commandes CLI pour interagir avec les configurations
3. L'intégration avec Hydra

## Structure des Tests

Les tests sont organisés en deux fichiers principaux :

- `tests/test_reader.py` : Tests unitaires pour la classe `TheReader`
- `tests/test_cli.py` : Tests d'intégration pour les commandes CLI

## Fixtures communes

### Configuration temporaire

```python
@pytest.fixture
def config_dir(tmp_path):
    """Crée une configuration temporaire pour les tests"""
    config_dir = tmp_path / ".hydra-conf"
    config_dir.mkdir()
    
    # Créer config.yaml
    with open(config_dir / "config.yaml", "w") as f:
        f.write("""
defaults:
  - _self_
  - database: default
  - api: default
  - secrets/keys
  - secrets/login

project:
  name: test-project
  version: "0.1.0"
        """)
    
    # Créer les sous-répertoires et fichiers de configuration...
    # ...
    
    return config_dir
```

### Nettoyage Hydra

Pour éviter les conflits entre les tests, nous nettoyons l'état global de Hydra :

```python
@pytest.fixture(autouse=True)
def cleanup_hydra():
    """Nettoie Hydra avant et après chaque test"""
    import hydra
    from hydra.core.global_hydra import GlobalHydra
    # Nettoyer avant
    GlobalHydra.instance().clear()
    yield
    # Nettoyer après
    GlobalHydra.instance().clear()
```

## Tests de TheReader

### Mock TheReader pour les tests

Pour éviter la dépendance à Hydra dans les tests unitaires, nous utilisons une version mock de `TheReader` :

```python
class MockTheReader(TheReader):
    def __init__(self, cfg_name, config_dir):
        self.cfg_name = cfg_name
        # Charger directement les fichiers YAML...
        # Ajouter des sections pour les références...
        # ...
```

### Tests implémentés

1. **Test de lecture basique** : Vérifie que les valeurs simples sont lues correctement
2. **Test de lecture imbriquée** : Vérifie que les configurations imbriquées sont accessibles
3. **Test d'accès style dictionnaire** : Vérifie l'accès aux valeurs via la syntaxe de dictionnaire
4. **Test du gestionnaire de contexte** : Vérifie le fonctionnement du context manager
5. **Test de gestion des erreurs** : Vérifie que les erreurs sont correctement levées

## Tests CLI

### Environnement d'exécution CLI

Un runner Click est utilisé pour simuler les appels CLI :

```python
@pytest.fixture
def runner():
    """Crée un runner CLI pour les tests"""
    return CliRunner()
```

### Projet temporaire

Pour isoler les tests, un projet temporaire est créé :

```python
@pytest.fixture
def temp_project(tmp_path, runner):
    """Crée un projet temporaire pour les tests"""
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        os.chdir(td)  # Change le répertoire courant
        yield Path(td)
```

### Tests implémentés

1. **Test de la commande init** : Vérifie que l'initialisation crée correctement les répertoires et fichiers
2. **Test de la commande read** : Vérifie que la lecture de configuration fonctionne
3. **Test de la commande get** : Vérifie l'extraction de valeurs spécifiques
4. **Test de la commande list-keys** : Vérifie le listing des clés disponibles

## Astuces et Solutions

### Problèmes courants avec Hydra

1. **Chemin de configuration introuvable** : Hydra exige des chemins relatifs.
   Solution : Changer le répertoire courant avant d'initialiser Hydra.

2. **Erreur "GlobalHydra is already initialized"** : 
   Solution : Utiliser le fixture `cleanup_hydra` pour réinitialiser Hydra entre les tests.

3. **Problème de chargement des configurations imbriquées** :
   Solution : Implémenter un chargement direct des fichiers YAML comme solution de secours.

### Stratégies de test robustes

1. **Tester indépendamment de Hydra** : Utiliser des mocks pour éviter les dépendances.

2. **Utiliser des solutions de secours** : Implémenter des alternatives lorsque Hydra échoue.

3. **Isoler les tests** : Utiliser des répertoires temporaires et des environnements isolés.

## Exécution des tests

Pour exécuter tous les tests :

```bash
poetry run pytest
```

Pour exécuter les tests avec couverture :

```bash
poetry run pytest --cov=hydra_buddies
``` 