#!/usr/bin/env python3
"""
Script pour gérer les versions du package hydra-buddies.
"""

import os
import re
import click
import tomlkit
from enum import Enum, auto

class VersionComponent(str, Enum):
    """Énumération des composants de version"""
    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"
    
    def __str__(self):
        return self.value

def get_current_version():
    """Récupère la version actuelle depuis le pyproject.toml à la racine du projet"""
    # Déterminer le chemin du projet
    project_root = find_project_root()
    pyproject_path = os.path.join(project_root, "pyproject.toml")
    
    if not os.path.exists(pyproject_path):
        raise FileNotFoundError(f"Le fichier pyproject.toml n'a pas été trouvé à la racine du projet: {project_root}")
    
    with open(pyproject_path, "r") as f:
        content = f.read()
    
    # Utiliser tomlkit pour parser le fichier
    pyproject = tomlkit.parse(content)
    current_version = pyproject["tool"]["poetry"]["version"]
    return current_version

def find_project_root():
    """Trouve la racine du projet en cherchant le fichier pyproject.toml"""
    current_dir = os.path.abspath(os.getcwd())
    
    # Remonter les répertoires pour trouver pyproject.toml
    while current_dir != "/":
        if os.path.exists(os.path.join(current_dir, "pyproject.toml")):
            return current_dir
        
        # Aller au répertoire parent
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:  # Éviter une boucle infinie
            break
        current_dir = parent_dir
    
    # Fallback: utiliser le répertoire courant
    return os.getcwd()

def increment_version(current_version, component):
    """Incrémente la version selon le composant spécifié (MAJOR.MINOR.PATCH)"""
    major, minor, patch = map(int, current_version.split('.'))
    
    # Si component est déjà une instance de VersionComponent, pas besoin de conversion
    if isinstance(component, str):
        try:
            component = VersionComponent(component.lower())
        except ValueError:
            raise ValueError(f"Composant non reconnu: {component}. Utilisez {', '.join([c.value for c in VersionComponent])}")
    
    if component == VersionComponent.MAJOR:
        major += 1
        minor = 0
        patch = 0
    elif component == VersionComponent.MINOR:
        minor += 1
        patch = 0
    elif component == VersionComponent.PATCH:
        patch += 1
    
    return f"{major}.{minor}.{patch}"

def update_version_in_files(new_version, dry_run=False):
    """Met à jour la version dans pyproject.toml et __init__.py"""
    if dry_run:
        click.echo(f"Mode simulation: La version serait mise à jour vers {new_version}")
        return True
    
    # Déterminer le chemin du projet
    project_root = find_project_root()
    pyproject_path = os.path.join(project_root, "pyproject.toml")
    init_file = os.path.join(project_root, "hydra_buddies/__init__.py")
    
    # Mettre à jour pyproject.toml
    with open(pyproject_path, "r") as f:
        content = f.read()
    
    pyproject = tomlkit.parse(content)
    pyproject["tool"]["poetry"]["version"] = new_version
    
    with open(pyproject_path, "w") as f:
        f.write(tomlkit.dumps(pyproject))
    
    # Mettre à jour __init__.py
    with open(init_file, "r") as f:
        content = f.read()
    
    # Remplacer la ligne de version
    updated_content = re.sub(
        r'__version__\s*=\s*["\'][^"\']*["\']',
        f'__version__ = "{new_version}"',
        content
    )
    
    with open(init_file, "w") as f:
        f.write(updated_content)
    
    return True

def perform_version_update(component, dry_run=False, yes=False):
    """Fonction commune pour mettre à jour la version.
    
    Args:
        component: Composant de version à incrémenter (instance de VersionComponent ou chaîne)
        dry_run: Si True, simule l'opération sans modifier les fichiers
        yes: Si True, confirme automatiquement sans demander
        
    Returns:
        Tuple (success, message): Indique si l'opération a réussi et un message explicatif
    """
    try:
        current_version = get_current_version()
        new_version = increment_version(current_version, component)
        
        if not dry_run and not yes:
            if not click.confirm(f"Mettre à jour la version de {current_version} -> {new_version} ?"):
                return True, "Opération annulée."
        
        if update_version_in_files(new_version, dry_run):
            return True, f"Version mise à jour: {current_version} -> {new_version}"
        return False, "Échec de la mise à jour des fichiers."
    except Exception as e:
        return False, f"Erreur lors de la mise à jour de la version: {e}"

@click.group()
def cli():
    """Outil de gestion de version pour hydra-buddies."""
    pass

@cli.command()
def current():
    """Affiche la version actuelle du package."""
    try:
        version = get_current_version()
        click.echo(f"Version actuelle: {version}")
    except Exception as e:
        click.echo(f"Erreur: {e}", err=True)
        return 1
    return 0

@cli.command()
@click.argument('component', type=click.Choice([c.value for c in VersionComponent], case_sensitive=False))
@click.option('--dry-run', '-d', is_flag=True, help="Simule l'opération sans modifier les fichiers")
@click.option('--yes', '-y', is_flag=True, help="Confirme automatiquement sans demander")
def bump(component, dry_run, yes):
    """Incrémente un composant de la version (MAJOR.MINOR.PATCH)."""
    success, message = perform_version_update(component, dry_run, yes)
    click.echo(message, err=not success)
    return 0 if success else 1

# Commandes individuelles pour chaque composant - évite l'utilisation de sys.argv
@cli.command("major")
@click.option('--dry-run', '-d', is_flag=True, help="Simule l'opération sans modifier les fichiers")
@click.option('--yes', '-y', is_flag=True, help="Confirme automatiquement sans demander")
def bump_major(dry_run, yes):
    """Incrémente la version majeure."""
    success, message = perform_version_update(VersionComponent.MAJOR, dry_run, yes)
    click.echo(message, err=not success)
    return 0 if success else 1

@cli.command("minor")
@click.option('--dry-run', '-d', is_flag=True, help="Simule l'opération sans modifier les fichiers")
@click.option('--yes', '-y', is_flag=True, help="Confirme automatiquement sans demander")
def bump_minor(dry_run, yes):
    """Incrémente la version mineure."""
    success, message = perform_version_update(VersionComponent.MINOR, dry_run, yes)
    click.echo(message, err=not success)
    return 0 if success else 1

@cli.command("patch")
@click.option('--dry-run', '-d', is_flag=True, help="Simule l'opération sans modifier les fichiers")
@click.option('--yes', '-y', is_flag=True, help="Confirme automatiquement sans demander")
def bump_patch(dry_run, yes):
    """Incrémente la version de patch."""
    success, message = perform_version_update(VersionComponent.PATCH, dry_run, yes)
    click.echo(message, err=not success)
    return 0 if success else 1

@cli.command()
@click.argument('version')
@click.option('--dry-run', '-d', is_flag=True, help="Simule l'opération sans modifier les fichiers")
@click.option('--yes', '-y', is_flag=True, help="Confirme automatiquement sans demander")
def set(version, dry_run, yes):
    """Définit directement une version spécifique."""
    # Vérifier que la version est au format correct
    if not re.match(r'^\d+\.\d+\.\d+$', version):
        click.echo("Erreur: Le format de version doit être X.Y.Z (ex: 1.2.3)", err=True)
        return 1
    
    try:
        current_version = get_current_version()
        
        if not dry_run and not yes:
            if not click.confirm(f"Changer la version de {current_version} -> {version} ?"):
                click.echo("Opération annulée.")
                return 0
        
        if update_version_in_files(version, dry_run):
            click.echo(f"Version définie: {current_version} -> {version}")
            return 0
    except Exception as e:
        click.echo(f"Erreur lors de la définition de la version: {e}", err=True)
        return 1

def main():
    """Point d'entrée pour poetry run upversion"""
    return cli()

if __name__ == "__main__":
    cli() 