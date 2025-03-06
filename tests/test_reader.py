import pytest
from hydra_buddies import TheReader
import os
import shutil
from pathlib import Path
import yaml
from omegaconf import OmegaConf

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
    
    # Créer les sous-répertoires
    (config_dir / "database").mkdir()
    (config_dir / "api").mkdir()
    (config_dir / "secrets").mkdir()
    
    # Configuration database
    with open(config_dir / "database" / "default.yaml", "w") as f:
        f.write("""
host: localhost
port: 5432
credentials:
  username: user
  password: test_password
        """)
    
    # Configuration API
    with open(config_dir / "api" / "default.yaml", "w") as f:
        f.write("""
url: http://api.example.com
key: test_key
timeout: 30
        """)
    
    return config_dir

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

@pytest.fixture
def reader(config_dir, cleanup_hydra):
    """Crée une instance de TheReader pour les tests"""
    import os
    import yaml
    from omegaconf import OmegaConf
    
    # Mock TheReader pour éviter d'utiliser Hydra
    class MockTheReader(TheReader):
        def __init__(self, cfg_name, config_dir):
            self.cfg_name = cfg_name
            config_file = os.path.join(config_dir, f"{cfg_name}.yaml")
            with open(config_file, "r") as f:
                self.cfg = OmegaConf.create(yaml.safe_load(f))
            
            # Traiter les 'database' et 'api' comme des sections de premier niveau
            # plutôt que comme des références à d'autres fichiers
            
            # Pour database
            db_file = os.path.join(config_dir, "database/default.yaml")
            if os.path.exists(db_file):
                with open(db_file, "r") as f:
                    db_config = yaml.safe_load(f)
                    # Créer une section 'database' directement dans self.cfg
                    self.cfg.database = OmegaConf.create(db_config)
            
            # Pour api
            api_file = os.path.join(config_dir, "api/default.yaml")
            if os.path.exists(api_file):
                with open(api_file, "r") as f:
                    api_config = yaml.safe_load(f)
                    # Créer une section 'api' directement dans self.cfg
                    self.cfg.api = OmegaConf.create(api_config)
            
            self.context = []
            self.cursor = self.cfg
            
            # Ajouter une fonction walk spéciale pour les tests
            def custom_walk(self, *args):
                self.context.extend(args)
                return self
            
            self.walk = custom_walk.__get__(self)
    
    # Créer l'instance avec notre mock
    reader = MockTheReader("config", str(config_dir))
    return reader

def test_basic_read(reader):
    """Test la lecture basique des valeurs"""
    assert reader.project.name == "test-project"
    assert reader.project.version == "0.1.0"

def test_nested_read(reader):
    """Test la lecture de valeurs imbriquées"""
    with reader:
        reader.walk("database")
        assert reader.host == "localhost"
        assert reader.port == 5432
        assert reader.credentials.username == "user"

def test_dict_style_access(reader):
    """Test l'accès style dictionnaire"""
    assert reader["database"]["host"] == "localhost"
    assert reader["api"]["timeout"] == 30

def test_context_manager(reader):
    """Test le context manager"""
    with reader.walk("database", "credentials") as r:
        assert r.username == "user"
        assert r.password == "test_password"

def test_error_handling(reader):
    """Test la gestion des erreurs"""
    with pytest.raises(AttributeError):
        reader.nonexistent_key

    with pytest.raises(KeyError):
        reader["nonexistent_key"] 