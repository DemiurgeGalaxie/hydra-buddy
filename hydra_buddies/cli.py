import click
from .buddies import TheReader
import os
import shutil
from cookiecutter.main import cookiecutter
import yaml

@click.group()
def cli():
    """Hydra-Buddies CLI - Gestionnaire de configuration"""
    pass

@cli.command()
@click.argument('config_name')
@click.option('--path', '-p', help='Chemin vers la configuration')
@click.option('--resolve', '-r', is_flag=True, help='Afficher la configuration complètement résolue')
def read(config_name, path, resolve):
    """Lire une configuration"""
    # Normaliser le nom de configuration
    config_name = normalize_config_name(config_name)
    
    if resolve:
        # Utiliser l'API Hydra directement
        import os
        import hydra
        from hydra.core.global_hydra import GlobalHydra
        from omegaconf import OmegaConf
        import yaml
        
        # Déterminer le chemin de configuration
        config_dir = path if path else os.path.join(os.getcwd(), 'hydra_buddies', '.hydra-conf')
        if not os.path.isdir(config_dir):
            config_dir = path if path else os.path.join(os.getcwd(), '.hydra-conf')
        
        if debug:
            click.echo(f"Chemin de configuration utilisé: {config_dir}")
        
        # Réinitialiser Hydra si nécessaire
        if GlobalHydra().is_initialized():
            GlobalHydra.instance().clear()
        
        # Transformer le nom pour Hydra:
        # - Pour config.yaml → utiliser "config"
        # - Pour config_dev.yaml → utiliser "dev"
        hydra_config_name = config_name
        if config_name.startswith("config_"):
            hydra_config_name = config_name[7:]  # Enlever "config_"
        elif config_name == "config":
            hydra_config_name = "config"
        
        if debug:
            click.echo(f"Nom de configuration pour Hydra: {hydra_config_name}")
        
        try:
            # Sauvegarder le répertoire de travail actuel
            original_cwd = os.getcwd()
            
            # Changer temporairement le répertoire de travail
            os.chdir(os.path.dirname(config_dir))
            
            # Utiliser le nom du répertoire comme chemin relatif
            rel_config_dir = os.path.basename(config_dir)
            
            # Initialiser Hydra avec le chemin relatif
            hydra.initialize(config_path=rel_config_dir, version_base=None)
            
            # Composer la configuration complète avec le nom transformé
            cfg = hydra.compose(config_name=hydra_config_name)
            
            # Convertir en dictionnaire simple et résoudre les interpolations
            config_dict = OmegaConf.to_container(cfg, resolve=True)
            
            # Afficher la configuration résolue
            click.echo(yaml.dump(config_dict, default_flow_style=False, sort_keys=False))
        
        finally:
            # Revenir au répertoire de travail original, même en cas d'erreur
            os.chdir(original_cwd)
    else:
        # Pour la version non résolue, utiliser TheReader
        reader = TheReader(config_name)
        if path:
            reader.update_path(path)
        click.echo(reader)

@cli.command()
@click.argument('config_name')
@click.argument('key')
@click.option('--path', '-p', help='Chemin vers la configuration')
def get(config_name, key, path):
    """Obtenir une valeur spécifique de la configuration"""
    # Normaliser le nom de configuration
    config_name = normalize_config_name(config_name)
    
    reader = TheReader(config_name)
    if path:
        reader.update_path(path)
    
    keys = key.split('.')
    with reader:
        reader.walk(*keys[:-1])
        try:
            value = getattr(reader, keys[-1])
            click.echo(value)
        except AttributeError:
            click.echo(f"Clé '{key}' non trouvée", err=True)

@cli.command()
@click.argument('config_name')
@click.option('--path', '-p', help='Chemin vers la configuration')
@click.option('--full', '-f', is_flag=True, help='Afficher toutes les clés à tous les niveaux')
@click.option('--values', '-v', is_flag=True, help='Afficher les valeurs primitives')
@click.option('--resolve', '-r', is_flag=True, help='Résoudre les références dans defaults')
@click.option('--debug', '-d', is_flag=True, help='Afficher des informations de débogage')
def list_keys(config_name, path, full, values, resolve, debug):
    """Lister toutes les clés disponibles"""
    # Normaliser le nom de configuration
    original_name = config_name  # Garder le nom d'origine pour l'affichage
    config_name = normalize_config_name(config_name)
    
    # Extraire le nom de configuration réel sans le préfixe "config_"
    if config_name == "config":
        display_name = "config"
    elif config_name.startswith("config_"):
        display_name = config_name[7:]  # Enlever "config_"
    else:
        display_name = original_name
    
    if debug:
        click.echo(f"Nom d'affichage de la configuration: {display_name}")
    
    # Structure pour stocker les clés avec leur origine
    # Format: { "source1.source2": ["key1.key2", "key3.key4"] }
    structured_keys = {}
    
    if resolve:
        # Résolution manuelle sans dépendre de Hydra
        import os
        import yaml
        from omegaconf import OmegaConf
        
        # Déterminer le chemin de configuration
        config_dir = path if path else os.path.join(os.getcwd(), 'hydra_buddies', '.hydra-conf')
        if not os.path.isdir(config_dir):
            config_dir = path if path else os.path.join(os.getcwd(), '.hydra-conf')
        
        if debug:
            click.echo(f"Chemin de configuration: {config_dir}")
        
        # Charger le fichier de configuration principal
        config_file = os.path.join(config_dir, f"{config_name}.yaml")
        if not os.path.exists(config_file):
            click.echo(f"Erreur: Fichier de configuration introuvable: {config_file}", err=True)
            return 1
        
        # Charger la configuration
        with open(config_file, 'r') as f:
            config_data = yaml.safe_load(f)
        
        # Afficher le dictionnaire complet si debug est activé
        if debug:
            click.echo("Configuration chargée:")
            import pprint
            pprint.pprint(config_data)
            click.echo("---")
        
        # Fonction pour collecter les clés avec leur source
        def collect_keys(data, key_prefix='', source=''):
            """Collecte uniquement les clés qui mènent à des valeurs primitives."""
            if not isinstance(data, dict):
                return
            
            # Initialiser l'entrée pour cette source si elle n'existe pas
            if source not in structured_keys:
                structured_keys[source] = []
            
            for key, value in data.items():
                full_key = f"{key_prefix}{key}"
                
                # Ne pas ajouter les clés intermédiaires (dictionnaires et listes)
                if isinstance(value, dict):
                    # Récursion sans ajouter la clé intermédiaire
                    collect_keys(value, f"{full_key}.", source)
                elif isinstance(value, list):
                    # Pour les listes, ajouter la clé
                    structured_keys[source].append(full_key)
                    
                    # Vérifier si c'est une liste d'objets
                    if any(isinstance(item, dict) for item in value):
                        for i, item in enumerate(value):
                            if isinstance(item, dict):
                                collect_keys(item, f"{full_key}[{i}].", source)
                else:
                    # Ajouter seulement les clés qui mènent à des valeurs primitives
                    structured_keys[source].append(full_key)
        
        # Collecter les clés du fichier principal
        collect_keys(config_data, source=display_name)
        
        # Charger un fichier référencé
        def load_referenced_config(ref_name, group=None):
            """Charge un fichier de configuration référencé et retourne son contenu."""
            # Déterminer le chemin
            if group:
                ref_path = os.path.join(config_dir, group, f"{ref_name}.yaml")
            else:
                ref_path = os.path.join(config_dir, f"{ref_name}.yaml")
            
            if debug:
                click.echo(f"Tentative de chargement de la référence: {ref_path}")
            
            if os.path.exists(ref_path):
                with open(ref_path, 'r') as f:
                    content = yaml.safe_load(f)
                    if debug:
                        click.echo(f"Fichier chargé avec succès: {ref_path}")
                    return content, ref_path
            
            if debug:
                click.echo(f"Référence non trouvée: {ref_path}")
            return None, None
        
        # Suivre les références dans defaults
        if "defaults" in config_data and isinstance(config_data["defaults"], list):
            for i, item in enumerate(config_data["defaults"]):
                if debug:
                    click.echo(f"Traitement de la référence {i}: {item}")
                
                # Cas 1: Référence simple comme "config"
                if isinstance(item, str):
                    referenced_config, ref_path = load_referenced_config(item)
                    if referenced_config:
                        source = f"{display_name}.{item}"
                        collect_keys(referenced_config, source=source)
                        
                        # Résoudre récursivement si besoin
                        if "defaults" in referenced_config and isinstance(referenced_config["defaults"], list):
                            for sub_item in referenced_config["defaults"]:
                                if isinstance(sub_item, str):
                                    sub_config, sub_path = load_referenced_config(sub_item)
                                    if sub_config:
                                        sub_name = os.path.splitext(os.path.basename(sub_path))[0]
                                        sub_source = f"{source}.{sub_name}"
                                        collect_keys(sub_config, source=sub_source)
                                elif isinstance(sub_item, dict) and len(sub_item) == 1:
                                    for group, name in sub_item.items():
                                        sub_config, sub_path = load_referenced_config(name, group)
                                        if sub_config:
                                            sub_source = f"{source}.{group}"
                                            collect_keys(sub_config, source=sub_source)
                
                # Cas 2: Référence avec groupe
                elif isinstance(item, dict):
                    for group, option in item.items():
                        if debug:
                            click.echo(f"Traitement du groupe {group} avec option: {option} (type: {type(option).__name__})")
                        
                        # Cas 2.1: Option simple (chaîne)
                        if isinstance(option, str):
                            referenced_config, ref_path = load_referenced_config(option, group)
                            if referenced_config:
                                source = f"{display_name}.{group}"
                                
                                # Collecter les clés en ajoutant le préfixe du groupe
                                def collect_with_group_prefix(data, key_prefix=''):
                                    """Collecte les clés en ajoutant le nom du groupe comme préfixe"""
                                    if not isinstance(data, dict):
                                        return
                                    
                                    if source not in structured_keys:
                                        structured_keys[source] = []
                                    
                                    for key, value in data.items():
                                        # Ajouter le préfixe du groupe pour toutes les clés
                                        full_key = f"{group}.{key_prefix}{key}"
                                        
                                        if isinstance(value, dict):
                                            collect_with_group_prefix(value, f"{key_prefix}{key}.")
                                        elif isinstance(value, list):
                                            if any(isinstance(item, dict) for item in value):
                                                for i, item in enumerate(value):
                                                    if isinstance(item, dict):
                                                        collect_with_group_prefix(item, f"{key_prefix}{key}[{i}].")
                                            else:
                                                structured_keys[source].append(full_key)
                                        else:
                                            structured_keys[source].append(full_key)
                                
                                # Utiliser cette fonction pour les références de groupe standard
                                collect_with_group_prefix(referenced_config)
                        
                        # Cas 2.2: Option avec liste explicite (comme {"secrets": ["keys", "login"]})
                        elif isinstance(option, list):
                            if debug:
                                click.echo(f"Option de type liste trouvée pour {group}: {option}")
                            
                            # Traiter chaque élément de la liste séparément
                            for sub_option in option:
                                if debug:
                                    click.echo(f"  Traitement de l'élément de liste: {sub_option}")
                                
                                # Charger le fichier correspondant dans le sous-répertoire
                                ref_file = os.path.join(config_dir, group, f"{sub_option}.yaml")
                                
                                if os.path.exists(ref_file):
                                    if debug:
                                        click.echo(f"  Fichier trouvé: {ref_file}")
                                    with open(ref_file, 'r') as f:
                                        referenced_config = yaml.safe_load(f)
                                        if referenced_config:
                                            # Utiliser un nom de source qui inclut le groupe et le sous-option
                                            source = f"{display_name}.{group}.{sub_option}"
                                            if debug:
                                                click.echo(f"  Collecte des clés pour: {source}")
                                            collect_keys(referenced_config, source=source)
        
        # Récupérer le contenu du fichier config.yaml pour l'examiner et l'analyser directement
        if debug:
            click.echo("Récupération manuelle des fichiers secrets:")
            secrets_dir = os.path.join(config_dir, 'secrets')
            if os.path.isdir(secrets_dir):
                for secret_file in os.listdir(secrets_dir):
                    if secret_file.endswith('.yaml'):
                        secret_name = os.path.splitext(secret_file)[0]
                        secret_path = os.path.join(secrets_dir, secret_file)
                        click.echo(f"  Trouvé fichier secret: {secret_path}")
                        
                        # Charger le fichier secret
                        with open(secret_path, 'r') as f:
                            secret_data = yaml.safe_load(f)
                            
                        # Collecter les clés avec la source correcte
                        source = f"{display_name}.secrets.{secret_name}"
                        if debug:
                            click.echo(f"  Collecte des clés pour: {source}")
                        collect_keys(secret_data, source=source)
        
        # Afficher les clés de manière structurée
        for source, keys in sorted(structured_keys.items()):
            keys.sort()
            for key in keys:
                click.echo(f"{source} -> {key}")
                
    else:
        # Pour la version non résolue, utiliser TheReader comme avant
        reader = TheReader(config_name)
        if path:
            reader.update_path(path)
        
        config = reader.get_cfg()
        
        if full:
            from omegaconf import OmegaConf
            
            # Collecte des clés depuis l'objet OmegaConf
            config_dict = OmegaConf.to_container(config, resolve=False)
            
            # Définir la fonction collect_keys si elle n'existe pas déjà
            def collect_keys(data, key_prefix='', source=''):
                """Collecte uniquement les clés qui mènent à des valeurs primitives."""
                if not isinstance(data, dict):
                    return
                
                # Initialiser l'entrée pour cette source si elle n'existe pas
                if source not in structured_keys:
                    structured_keys[source] = []
                
                for key, value in data.items():
                    full_key = f"{key_prefix}{key}"
                    
                    # Ne pas ajouter les clés intermédiaires (dictionnaires et listes)
                    if isinstance(value, dict):
                        # Récursion sans ajouter la clé intermédiaire
                        collect_keys(value, f"{full_key}.", source)
                    elif isinstance(value, list):
                        # Pour les listes, ajouter la clé
                        structured_keys[source].append(full_key)
                        
                        # Vérifier si c'est une liste d'objets
                        if any(isinstance(item, dict) for item in value):
                            for i, item in enumerate(value):
                                if isinstance(item, dict):
                                    collect_keys(item, f"{full_key}[{i}].", source)
                    else:
                        # Ajouter seulement les clés qui mènent à des valeurs primitives
                        structured_keys[source].append(full_key)
            
            collect_keys(config_dict, source=display_name)
            
            # Afficher les clés de manière structurée
            for source, keys in sorted(structured_keys.items()):
                keys.sort()
                for key in keys:
                    click.echo(f"{source} -> {key}")
        else:
            # Affichage des clés de premier niveau sans modification
            from omegaconf import OmegaConf
            
            if OmegaConf.is_config(config):
                for key in OmegaConf.to_container(config, resolve=False).keys():
                    click.echo(key)
            else:
                for key in config.keys():
                    click.echo(key)

@cli.command()
def init():
    """Initialiser un répertoire de configuration"""
    if os.path.exists(os.path.join(os.getcwd(), '.hydra-conf')):
        click.echo("Un répertoire de configuration existe déjà", err=True)
        return
    
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'hydra_conf')
    output_path = os.getcwd()
    
    # Copier les templates avec cookiecutter
    cookiecutter(
        template_path,
        output_dir=output_path,
        no_input=True,
        extra_context={
            'project_name': os.path.basename(output_path)
        }
    )
    
    # Déplacer les fichiers au bon endroit
    temp_dir = os.path.join(output_path, os.path.basename(output_path))
    if os.path.exists(temp_dir):
        shutil.move(os.path.join(temp_dir, '.hydra-conf'), output_path)
        shutil.rmtree(temp_dir)
    
    # Vérifier si le répertoire secret est dans le fichier .gitignore
    gitignore_path = os.path.join(output_path, '.gitignore')
    secret_line = '.hydra-conf/secrets/*\n'
    
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r') as file:
            lines = file.readlines()
            if secret_line not in lines:
                with open(gitignore_path, 'a') as file:
                    file.write(secret_line)
    else:
        with open(gitignore_path, 'w') as file:
            file.write(secret_line)
    
    click.echo("Répertoire de configuration initialisé avec succès")
    
@cli.command()
@click.argument('name')
def add_config(name):
    """Créer une nouvelle configuration basée sur default"""
    config_dir = os.path.join(os.getcwd(), '.hydra-conf')
    
    try:
        default_config = validate_add_config(name, config_dir)
    except ConfigError as e:
        click.echo(str(e), err=True)
        return 1
    
    # Charger le contenu de config_default.yaml
    with open(default_config, 'r') as f:
        config_content = yaml.safe_load(f) or {}
    
    # Modifier la variable env si elle existe
    if 'env' in config_content:
        config_content['env'] = name
    else:
        # Ajouter la variable env si elle n'existe pas
        config_content['env'] = name
    
    # Créer le fichier config_<name>.yaml
    new_config_file = os.path.join(config_dir, f"config_{name}.yaml")
    with open(new_config_file, 'w') as f:
        yaml.dump(config_content, f, default_flow_style=False)
    
    # Parcourir tous les sous-répertoires pour copier default.yaml
    subdirs_copied = 0
    for root, dirs, files in os.walk(config_dir):
        for dir_name in dirs:
            subdir = os.path.join(root, dir_name)
            default_yaml = os.path.join(subdir, "default.yaml")
            
            if os.path.exists(default_yaml):
                new_yaml = os.path.join(subdir, f"{name}.yaml")
                shutil.copy2(default_yaml, new_yaml)
                subdirs_copied += 1
    
    click.echo(f"Configuration '{name}' créée avec succès.")
    click.echo(f"- Fichier principal: {new_config_file}")
    click.echo(f"- {subdirs_copied} fichiers de configuration copiés dans les sous-répertoires.")
    return 0

@cli.command()
@click.argument('name')
@click.option('--force', '-f', is_flag=True, help='Forcer la suppression sans confirmation')
def remove_config(name, force):
    """Supprimer une configuration existante"""
    try:
        config_info = validate_remove_config(name)
        config_file, subconfig_files = config_info
    except ConfigError as e:
        click.echo(str(e), err=True)
        return 1
    
    # Demander confirmation à moins que --force soit utilisé
    if not force:
        file_count = len(subconfig_files) + 1  # +1 pour le fichier principal
        message = f"Vous êtes sur le point de supprimer {file_count} fichiers de configuration pour '{name}'.\nContinuer? [y/N] "
        if not click.confirm(message, default=False):
            click.echo("Opération annulée.")
            return 0
    
    # Supprimer le fichier principal
    os.remove(config_file)
    
    # Supprimer les fichiers dans les sous-répertoires
    for subfile in subconfig_files:
        try:
            os.remove(subfile)
        except OSError:
            click.echo(f"Impossible de supprimer {subfile}", err=True)
    
    click.echo(f"Configuration '{name}' supprimée avec succès.")
    click.echo(f"- {len(subconfig_files) + 1} fichiers supprimés au total.")
    return 0

class ConfigError(Exception):
    """Exception pour les erreurs de configuration"""
    pass

def validate_add_config(name, config_dir=None):
    """Valide les paramètres pour add_config et lève des exceptions si nécessaire.
    
    Args:
        name: Nom de la configuration à ajouter
        config_dir: Répertoire de configuration (par défaut: .hydra-conf dans le répertoire courant)
        
    Raises:
        ConfigError: Si la validation échoue
    """
    if config_dir is None:
        config_dir = os.path.join(os.getcwd(), '.hydra-conf')
    
    if not os.path.exists(config_dir):
        raise ConfigError("Aucun répertoire de configuration trouvé. Exécutez 'buddy init' d'abord.")
    
    # Vérifier si cette configuration existe déjà
    new_config_file = os.path.join(config_dir, f"config_{name}.yaml")
    if os.path.exists(new_config_file):
        raise ConfigError(f"La configuration '{name}' existe déjà.")
    
    # Vérifier que les fichiers source existent
    default_config = os.path.join(config_dir, "config_default.yaml")
    if not os.path.exists(default_config):
        default_config = os.path.join(config_dir, "config.yaml")
        if not os.path.exists(default_config):
            raise ConfigError("Aucun fichier config_default.yaml ou config.yaml trouvé.")
    
    return default_config

def validate_remove_config(name, config_dir=None):
    """Valide les paramètres pour remove_config et lève des exceptions si nécessaire."""
    if config_dir is None:
        config_dir = os.path.join(os.getcwd(), '.hydra-conf')
    
    if not os.path.exists(config_dir):
        raise ConfigError("Aucun répertoire de configuration trouvé. Exécutez 'buddy init' d'abord.")
    
    # Interdire complètement la suppression de tout ce qui s'appelle "default"
    if name.lower() == "default":  # Rendre insensible à la casse
        raise ConfigError("Impossible de supprimer la configuration par défaut.")
    
    # Vérifier si cette configuration existe
    config_file = os.path.join(config_dir, f"config_{name}.yaml")
    if not os.path.exists(config_file):
        raise ConfigError(f"La configuration '{name}' n'existe pas.")
    
    # Trouver tous les fichiers associés dans les sous-répertoires
    subconfig_files = []
    for root, dirs, files in os.walk(config_dir):
        for dir_name in dirs:
            subdir = os.path.join(root, dir_name)
            subconfig_file = os.path.join(subdir, f"{name}.yaml")
            if os.path.exists(subconfig_file):
                subconfig_files.append(subconfig_file)
    
    return (config_file, subconfig_files)

def normalize_config_name(name):
    """Normalise le nom de configuration en ajoutant le préfixe 'config_' si nécessaire.
    
    Si le nom fourni ne commence pas déjà par 'config_' et n'est pas 'default', 
    alors le préfixe est ajouté.
    """
    if name == "default":
        return "config"  # config.yaml est la configuration par défaut
    
    if not name.startswith("config_"):
        return f"config_{name}"
    
    return name  # Déjà au bon format

