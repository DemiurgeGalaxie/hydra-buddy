import pytest
import os
import shutil
from pathlib import Path

@pytest.fixture(autouse=True)
def clean_environment():
    """Nettoie l'environnement avant chaque test"""
    # Sauvegarde les variables d'environnement existantes
    env_backup = {}
    for key in os.environ:
        if key.startswith(('DB_', 'API_', 'REDIS_', 'RABBITMQ_')):
            env_backup[key] = os.environ[key]
            del os.environ[key]
    
    yield
    
    # Restaure les variables d'environnement
    for key, value in env_backup.items():
        os.environ[key] = value 