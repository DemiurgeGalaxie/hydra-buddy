from hydra import initialize, compose
from typing import Any, List, Optional
import os
from omegaconf import OmegaConf, DictConfig
import copy
import asyncio  
import hydra
from hydra.core.global_hydra import GlobalHydra

config_paths = [
    ".hydra-conf",

]

initialize(config_path=config_paths[0], version_base="1.1")

class TheReader:
    def __init__(self, cfg_name: str):
        """Initialise un lecteur de configuration.
        
        Args:
            cfg_name: Nom de la configuration à charger
        """
        self.config_paths = ["."]
        self.cfg_name = cfg_name
        self._initialize_hydra()
        
        try:
            self.cfg = self._load_config(cfg_name)
        except:
            # En cas d'erreur, essayer de charger directement le fichier yaml
            import yaml
            import os
            
            # Rechercher le fichier dans les répertoires courants
            for path in [".hydra-conf", os.getcwd()]:
                config_file = os.path.join(path, f"{cfg_name}.yaml")
                if os.path.exists(config_file):
                    with open(config_file, 'r') as f:
                        self.cfg = OmegaConf.create(yaml.safe_load(f))
                    break
            else:
                raise ValueError(f"Configuration '{cfg_name}' introuvable")
        
        self.context = []
        self.cursor = self.cfg

    def _initialize_hydra(self):
        """Initialise Hydra s'il ne l'est pas déjà."""
        if GlobalHydra().is_initialized():
            GlobalHydra.instance().clear()
        hydra.initialize(config_path=None, version_base=None)

    def _load_config(self, cfg_name: str) -> DictConfig:
        """Charge la configuration depuis le fichier.
        
        Args:
            cfg_name: Nom de la configuration
            
        Returns:
            Configuration chargée
        """
        return hydra.compose(config_name=cfg_name)

    def update_path(self, path: str):
        """Met à jour le chemin de recherche des configurations.
        
        Args:
            path: Nouveau chemin à ajouter
        """
        try:
            # Réinitialiser Hydra avec le nouveau chemin
            if GlobalHydra().is_initialized():
                GlobalHydra.instance().clear()
            
            # S'assurer que le chemin est relatif comme l'exige Hydra
            if os.path.isabs(path):
                prev_dir = os.getcwd()
                os.chdir(os.path.dirname(path))
                path = os.path.basename(path)
            
            # Essayer d'initialiser Hydra
            hydra.initialize(config_path=path, version_base=None)
            self.cfg = self._load_config(self.cfg_name)
            
            # Revenir au répertoire précédent si nécessaire
            if prev_dir:
                os.chdir(prev_dir)
            
        except Exception as e:
            # Solution de secours: charger directement les fichiers YAML
            import yaml
            
            config_file = os.path.join(path, f"{self.cfg_name}.yaml")
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    self.cfg = OmegaConf.create(yaml.safe_load(f))
                    
                # Charger les fichiers référencés dans defaults si possible
                if "defaults" in self.cfg:
                    for default in self.cfg.defaults:
                        if isinstance(default, dict):
                            for group, name in default.items():
                                subconfig_file = os.path.join(path, group, f"{name}.yaml")
                                if os.path.exists(subconfig_file):
                                    with open(subconfig_file, 'r') as f:
                                        self.cfg[group] = OmegaConf.create(yaml.safe_load(f))
            else:
                raise ValueError(f"Configuration '{self.cfg_name}' introuvable dans {path}")
        
        self.cursor = self.cfg
        self.context = []
        return self

    def __call__(self, *args: Any, **kwds: Any) -> DictConfig:
        if self.context:
            return self.cursor
        else:
            return self.cfg
    
    def get_context(self):
        cursor = self.cursor
        for key in self.context:
            try:
                cursor = getattr(cursor, key)
            except Exception as e:
                raise e
        return cursor

    def start(self) -> None:
        self.context = []

    def walk(self,*args:list[str])->None:
        self.context.extend(args)
        self.cursor = self.get_context()
        return self

    def __setitem__(self, key:str, value:DictConfig ) -> None:
        if self.context:
            self.cursor[key] = value
        else:
            self.cfg[key] = value

    def __getitem__(self, key:str) -> DictConfig:
        if self.context:
            return self.cursor[key]
        else:
            return self.cfg[key]
    def get(self, key:str)->DictConfig:
        return self.cursor[key]

    def __getattribute__(self, key: str) -> DictConfig:
        try:
            test = object.__getattribute__(self, key)
            if asyncio.iscoroutinefunction(test):
                return test 
            return test
        except AttributeError:
            cursor = object.__getattribute__(self, 'cursor')
            context = object.__getattribute__(self, 'context')
            
            if context:
                for ctx_key in context:
                    cursor = getattr(cursor, ctx_key)
            
            if key in cursor:
                return getattr(cursor, key)
            else:
                raise AttributeError(f"L'attribut '{key}' n'existe pas")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cursor = self.cfg
        self.context = []

    def add_prefix(self, prefix:str):
        """
        Decorator that adds a prefix to all configuration keys that do not already start with this prefix.

        Args:
            prefix (str): The prefix to add to the configuration keys.

        Returns:
            function: The decorator that wraps the original function.

        The decorator modifies the configuration by adding new prefixed keys 
        while preserving the original keys. The new prefixed keys are added 
        to the `self.prefixes` list.
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                new_keys = []
                for key, value in self.cfg.items():
                    if not key.startswith(prefix):
                        new_key = f"{prefix}.{key}"
                        self.cfg[new_key] = value
                        new_keys.append(new_key)
                self.prefixes.extend(new_keys)
                return func(*args, **kwargs)
            return wrapper
        return decorator

    

    def get_cfg(self):
        return self.cfg
    
    def __repr__(self):
        return OmegaConf.to_yaml(self.cfg)
    
    def __str__(self):
        return OmegaConf.to_yaml(self.cfg)
    
    def __bool__(self):
        return bool(self.cfg)