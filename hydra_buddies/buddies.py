from hydra import initialize, compose
from typing import Any, List, Optional
import os
from omegaconf import OmegaConf, DictConfig
import copy
import asyncio  
import hydra
from hydra.core.global_hydra import GlobalHydra

class TheReader:
    def __init__(self, cfg_name: str = "config"):
        """Initialise un lecteur de configuration.
        
        Args:
            cfg_name: Nom de la configuration à charger
        """
        # Liste des chemins de recherche supplémentaires (après le chemin principal)
        self.config_paths = []
        
        # Chemin principal (utilisé pour initialize)
        self.primary_path = ".hydra-conf"
        
        self.cfg_name = cfg_name
        
        # Initialiser Hydra et charger la configuration
        self._initialize_hydra()
        
        try:
            self.cfg = self._load_config(cfg_name)
            
            # Promouvoir les secrets au niveau racine
            self._promote_secrets()
            
        except Exception as e:
            # En cas d'erreur, essayer de charger directement le fichier yaml
            import yaml
            
            # Rechercher le fichier dans les répertoires courants
            search_paths = [self.primary_path] + self.config_paths + [os.getcwd()]
            for path in search_paths:
                config_file = os.path.join(path, f"{cfg_name}.yaml")
                if os.path.exists(config_file):
                    with open(config_file, 'r') as f:
                        self.cfg = OmegaConf.create(yaml.safe_load(f))
                    # Promouvoir les secrets ici aussi
                    self._promote_secrets()
                    break
            else:
                raise ValueError(f"Configuration '{cfg_name}' introuvable dans {search_paths}")
        
        self.context = []
        self.cursor = self.cfg

    def _initialize_hydra(self):
        """Initialise Hydra avec le chemin principal."""
        if GlobalHydra().is_initialized():
            GlobalHydra.instance().clear()
        
        # Initialiser avec le chemin principal
        hydra.initialize(config_path=self.primary_path, version_base=None)

    def _load_config(self, cfg_name: str) -> DictConfig:
        """Charge la configuration depuis le fichier avec chemins supplémentaires.
        
        Args:
            cfg_name: Nom de la configuration
            
        Returns:
            Configuration chargée
        """
        # Construire les overrides pour les chemins supplémentaires
        path_overrides = [f"+config_path={path}" for path in self.config_paths]
        
        # Composer la configuration avec les overrides
        return hydra.compose(config_name=cfg_name, overrides=path_overrides)
    
    def _promote_secrets(self):
        """Promeut les valeurs des secrets au niveau racine."""
        if 'secrets' in self.cfg:
            # Convertir en dictionnaire standard
            config_dict = OmegaConf.to_container(self.cfg, resolve=False)
            
            # Parcourir toutes les sections de secrets
            if 'secrets' in config_dict and isinstance(config_dict['secrets'], dict):
                for section, values in config_dict['secrets'].items():
                    if section not in config_dict:
                        # Ajouter la section à la racine si elle n'existe pas déjà
                        config_dict[section] = values
                    elif isinstance(values, dict) and isinstance(config_dict[section], dict):
                        # Fusion si les deux sont des dictionnaires
                        for k, v in values.items():
                            if k not in config_dict[section]:
                                config_dict[section][k] = v
            
            # Reconvertir en OmegaConf
            self.cfg = OmegaConf.create(config_dict)

    def update_path(self, path: str):
        """Met à jour le chemin principal de recherche des configurations.
        
        Args:
            path: Nouveau chemin principal
        """
        prev_dir = None
        self.primary_path = path
        
        try:
            # Réinitialiser Hydra avec le nouveau chemin
            if GlobalHydra().is_initialized():
                GlobalHydra.instance().clear()
            
            # S'assurer que le chemin est relatif comme l'exige Hydra
            if os.path.isabs(path):
                prev_dir = os.getcwd()
                os.chdir(os.path.dirname(path))
                self.primary_path = os.path.basename(path)
            
            # Essayer d'initialiser Hydra
            hydra.initialize(config_path=self.primary_path, version_base=None)
            self.cfg = self._load_config(self.cfg_name)
            
            # Promouvoir les secrets
            self._promote_secrets()
            
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
                
                # Promouvoir les secrets
                self._promote_secrets()
                    
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
            
            # Revenir au répertoire précédent si nécessaire
            if prev_dir:
                os.chdir(prev_dir)
        
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

    def get_config_dir(self):
        """Retourne le chemin vers le répertoire de configuration."""
        return self.primary_path if hasattr(self, 'primary_path') else '.hydra-conf'

    def get_resolved_config(self):
        """Retourne la configuration avec toutes les références résolues.
        
        Returns:
            dict: Configuration complètement résolue
        """
        # Sauvegarder le répertoire courant si nécessaire
        original_dir = None
        if hasattr(self, 'primary_path') and os.path.isabs(self.primary_path):
            original_dir = os.getcwd()
            os.chdir(os.path.dirname(self.primary_path))
        
        try:
            # Promouvoir à nouveau les secrets pour s'assurer que tout est à jour
            self._promote_secrets()
            
            # Résoudre toutes les interpolations
            resolved = OmegaConf.to_container(self.cfg, resolve=True)
            self.resolved = resolved
            return resolved
        
        except Exception as e:
            # En cas d'erreur, afficher des informations de débogage
            print(f"Erreur lors de la résolution complète: {e}")
            # Renvoyer la version non résolue
            return OmegaConf.to_container(self.cfg, resolve=False)
        
        finally:
            # Restaurer le répertoire si nécessaire
            if original_dir:
                os.chdir(original_dir)

    def add_config_path(self, path: str):
        """Ajoute un chemin de recherche supplémentaire.
        
        Args:
            path: Chemin supplémentaire à ajouter
            
        Returns:
            self: Pour le chaînage de méthodes
        """
        # S'assurer que le chemin n'est pas déjà dans la liste
        if path != self.primary_path and path not in self.config_paths:
            self.config_paths.append(path)
            
            # Recharger la configuration avec le nouveau chemin
            try:
                self.cfg = self._load_config(self.cfg_name)
                self._promote_secrets()
            except Exception as e:
                print(f"Avertissement: erreur lors du rechargement après add_config_path: {e}")
                
        return self