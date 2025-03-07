import os
import pytest
import re
import tomlkit
from click.testing import CliRunner
from scripts.upversion import cli, VersionComponent

@pytest.fixture
def test_project(tmp_path):
    """Crée un projet de test temporaire avec les fichiers nécessaires."""
    # Créer un fichier pyproject.toml
    pyproject_path = tmp_path / "pyproject.toml"
    test_version = "1.2.3"
    
    pyproject_content = {
        "tool": {
            "poetry": {
                "name": "test-project",
                "version": test_version,
                "description": "Projet pour test",
                "authors": ["Test <test@example.com>"]
            }
        }
    }
    
    with open(pyproject_path, "w") as f:
        f.write(tomlkit.dumps(pyproject_content))
    
    # Créer le répertoire et le fichier __init__.py
    init_dir = tmp_path / "test_package"
    os.makedirs(init_dir, exist_ok=True)
    
    init_path = init_dir / "__init__.py"
    with open(init_path, "w") as f:
        f.write(f'__version__ = "{test_version}"\n')
    
    # Retourner le chemin et la version
    return {
        "project_dir": tmp_path,
        "version": test_version,
        "pyproject_path": pyproject_path,
        "init_path": init_path
    }

@pytest.fixture
def runner():
    """Retourne un CLI runner pour tester les commandes Click."""
    return CliRunner()

def test_current_version(runner, test_project, monkeypatch):
    """Teste que la commande 'current' renvoie la bonne version."""
    # Changer le répertoire courant pour le test
    monkeypatch.chdir(test_project["project_dir"])
    
    result = runner.invoke(cli, ["current"])
    assert result.exit_code == 0
    assert f"Version actuelle: {test_project['version']}" in result.output

def test_dry_run_no_changes(runner, test_project, monkeypatch):
    """Teste que l'option --dry-run n'apporte aucune modification."""
    # Changer le répertoire courant pour le test
    monkeypatch.chdir(test_project["project_dir"])
    
    # Sauvegarder le contenu des fichiers avant
    with open(test_project["pyproject_path"], "r") as f:
        pyproject_before = f.read()
    
    with open(test_project["init_path"], "r") as f:
        init_before = f.read()
    
    # Tester chaque composant de version avec --dry-run
    for component in [c.value for c in VersionComponent]:
        result = runner.invoke(cli, ["bump", component, "--dry-run"])
        assert result.exit_code == 0
        assert "Mode simulation" in result.output
    
    # Vérifier également la commande 'set'
    result = runner.invoke(cli, ["set", "2.0.0", "--dry-run"])
    assert result.exit_code == 0
    assert "Mode simulation" in result.output
    
    # Vérifier que les fichiers n'ont pas été modifiés
    with open(test_project["pyproject_path"], "r") as f:
        pyproject_after = f.read()
    
    with open(test_project["init_path"], "r") as f:
        init_after = f.read()
    
    assert pyproject_before == pyproject_after, "Le fichier pyproject.toml a été modifié malgré --dry-run"
    assert init_before == init_after, "Le fichier __init__.py a été modifié malgré --dry-run"

def test_patch_calculation(runner, test_project, monkeypatch):
    """Teste que le calcul de version de patch est correct."""
    monkeypatch.chdir(test_project["project_dir"])
    
    # Version de départ: 1.2.3
    # Version de patch attendue: 1.2.4
    result = runner.invoke(cli, ["patch", "--dry-run"])
    assert result.exit_code == 0
    assert "1.2.4" in result.output

def test_minor_calculation(runner, test_project, monkeypatch):
    """Teste que le calcul de version mineure est correct."""
    monkeypatch.chdir(test_project["project_dir"])
    
    # Version de départ: 1.2.3
    # Version mineure attendue: 1.3.0
    result = runner.invoke(cli, ["minor", "--dry-run"])
    assert result.exit_code == 0
    assert "1.3.0" in result.output

def test_major_calculation(runner, test_project, monkeypatch):
    """Teste que le calcul de version majeure est correct."""
    monkeypatch.chdir(test_project["project_dir"])
    
    # Version de départ: 1.2.3
    # Version majeure attendue: 2.0.0
    result = runner.invoke(cli, ["major", "--dry-run"])
    assert result.exit_code == 0
    assert "2.0.0" in result.output

def test_dry_run_output_format(runner, test_project, monkeypatch):
    """Teste que le format de sortie en mode dry-run est correct."""
    monkeypatch.chdir(test_project["project_dir"])
    
    result = runner.invoke(cli, ["patch", "--dry-run"])
    assert "Mode simulation: La version serait mise à jour vers 1.2.4" in result.output 