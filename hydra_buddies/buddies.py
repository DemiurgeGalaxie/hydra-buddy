from hydra import initialize, compose
from typing import Any
import os
from omegaconf import OmegaConf, DictConfig
import copy
import asyncio  

config_paths = [
    ".hydra-conf",

]

initialize(config_path=config_paths[0], version_base="1.1")

class TheReader(dict):
    def __init__(self, cfg_name: str):
        self.config_paths = copy.deepcopy(config_paths)
        cfg = compose(config_name=cfg_name, overrides=[f"+config_path={path}" for path in config_paths[1:]])
        self.cfg = OmegaConf.create(cfg)
        OmegaConf.resolve(self.cfg)
        self.context = []
        self.cursor = copy.deepcopy(self.cfg)
        
    def update_path(self, path:str):
        if not self.context:
            self.config_paths.append(path)
            initialize(config_path=self.config_paths[0], version_base="1.1")
            cfg = compose(config_name=self.cfg_name, overrides=[f"+config_path={path}" for path in self.config_paths[1:]])
            self.cfg = OmegaConf.create(cfg)
            OmegaConf.resolve(self.cfg)
        else:
            raise ValueError("Context already set, update path out of context")

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

    def __exit__(self):
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