import click
from .buddies import TheReader
import os
import shutil
from cookiecutter.main import cookiecutter

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
    

