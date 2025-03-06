import click
from .reader import TheReader

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