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

    def get_config_dir(self):
        """Retourne le chemin vers le répertoire de configuration."""
        return self.config_path if hasattr(self, 'config_path') else '.hydra-conf'

    def get_resolved_config(self, debug=False):
        """Résout la configuration en suivant toutes les références et en les fusionnant."""
        import os
        import yaml
        
        # Charger le fichier de configuration principal
        config_file = os.path.join(self.config_path, f"{self.config_name}.yaml")
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        # Fonction récursive pour résoudre les références
        def resolve_references(config_data, base_path):
            if not isinstance(config_data, dict):
                return config_data
            
            # Copie pour éviter de modifier l'original pendant l'itération
            result = config_data.copy()
            
            # Traiter les références dans defaults
            if "defaults" in result and isinstance(result["defaults"], list):
                defaults_list = result.pop("defaults")  # Retirer defaults après traitement
                
                for item in defaults_list:
                    if debug:
                        print(f"Traitement de la référence: {item}")
                    
                    # Cas 1: Référence simple comme "config"
                    if isinstance(item, str):
                        ref_file = os.path.join(base_path, f"{item}.yaml")
                        if os.path.exists(ref_file):
                            with open(ref_file, 'r') as f:
                                ref_config = yaml.safe_load(f)
                                if ref_config:
                                    resolved_ref = resolve_references(ref_config, base_path)
                                    result = deep_merge(result, resolved_ref)
                    
                    # Cas 2: Référence avec groupe comme {"database": "dev"}
                    elif isinstance(item, dict) and len(item) == 1:
                        for group, option in item.items():
                            # Cas 2.1: Option simple
                            if isinstance(option, str):
                                group_path = os.path.join(base_path, group)
                                ref_file = os.path.join(group_path, f"{option}.yaml")
                                
                                if os.path.exists(ref_file):
                                    with open(ref_file, 'r') as f:
                                        group_config = yaml.safe_load(f)
                                        if group_config:
                                            resolved_group = resolve_references(group_config, base_path)
                                            # Ajouter le groupe comme clé de premier niveau
                                            if group not in result:
                                                result[group] = {}
                                            result[group] = deep_merge(result.get(group, {}), resolved_group)
                            
                            # Cas 2.2: Liste d'options
                            elif isinstance(option, list):
                                group_path = os.path.join(base_path, group)
                                
                                # Traiter chaque élément de la liste
                                if group not in result:
                                    result[group] = {}
                                    
                                for sub_option in option:
                                    ref_file = os.path.join(group_path, f"{sub_option}.yaml")
                                    
                                    if os.path.exists(ref_file):
                                        with open(ref_file, 'r') as f:
                                            sub_config = yaml.safe_load(f)
                                            if sub_config:
                                                # Ajouter sous une clé correspondant à sub_option
                                                result[group][sub_option] = sub_config
            
            # Résoudre récursivement les dictionnaires imbriqués
            for key, value in list(result.items()):
                if isinstance(value, dict):
                    result[key] = resolve_references(value, base_path)
            
            return result
        
        # Fonction utilitaire pour fusion profonde de dictionnaires
        def deep_merge(dict1, dict2):
            result = dict1.copy()
            
            for key, value in dict2.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    # Fusion récursive de dictionnaires
                    result[key] = deep_merge(result[key], value)
                else:
                    # Remplacement ou ajout de valeurs
                    result[key] = value
            
            return result
        
        # Résoudre la configuration
        resolved = resolve_references(config, self.config_path)
        return resolved