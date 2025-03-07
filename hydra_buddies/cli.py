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
def read(config_name, path):
    """Lire une configuration"""
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
def list_keys(config_name, path):
    """Lister toutes les clés disponibles"""
    reader = TheReader(config_name)
    if path:
        reader.update_path(path)
    
    def print_keys(obj, prefix=''):
        for key in obj.keys():
            full_key = f"{prefix}{key}"
            click.echo(full_key)
            if isinstance(obj[key], dict):
                print_keys(obj[key], f"{full_key}.")
    
    print_keys(reader.get_cfg()) 
    
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

