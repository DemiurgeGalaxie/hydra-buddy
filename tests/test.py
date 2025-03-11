#!/usr/bin/env python3
"""
Script pour lire et résoudre une configuration Hydra.
Utilisation: python read_config.py [nom_config] [chemin_config]
"""

import os
import sys
import yaml
from omegaconf import OmegaConf
import hydra
from hydra.core.global_hydra import GlobalHydra

def read_config(config_name="dev", config_path=None):
    """
    Lit et résout une configuration Hydra avec gestion spéciale pour les secrets.
    
    Args:
        config_name (str): Nom de la configuration à lire (sans extension .yaml)
        config_path (str): Chemin du dossier de configuration 
                          (par défaut: .hydra-conf dans le dossier courant)
    
    Returns:
        dict: Configuration résolue sous forme de dictionnaire
    """
    # Déterminer le chemin de configuration
    if config_path is None:
        config_path = os.path.join(os.getcwd(), 'hydra_buddies', '.hydra-conf')
    
    print(f"Lecture de la configuration '{config_name}' depuis '{config_path}'")
    
    # Réinitialiser Hydra si nécessaire
    if GlobalHydra().is_initialized():
        GlobalHydra.instance().clear()
    
    # Sauvegarder le répertoire courant
    original_cwd = os.getcwd()
    
    try:
        # Changer le répertoire de travail temporairement
        os.chdir(os.path.dirname(config_path))
        rel_config_dir = os.path.basename(config_path)
        
        # Initialiser Hydra avec le bon chemin
        hydra.initialize(config_path=rel_config_dir, version_base=None)
        
        # Composer la configuration
        cfg = hydra.compose(config_name=config_name)
        
        # Afficher la configuration chargée
        print("Configuration chargée:")
        
        
        # Version compatible avec les anciennes versions d'OmegaConf
        # Extraire tous les secrets et les promouvoir au niveau racine
        if 'secrets' in cfg:
            # Convertir en dictionnaire standard
            config_dict = OmegaConf.to_container(cfg, resolve=False)
            
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
            cfg = OmegaConf.create(config_dict)
        
        # Maintenant résoudre la configuration
        print("Tentative de résolution...")
        resolved_dict = OmegaConf.to_container(cfg, resolve=True)
        print("Résolution réussie!")
        print(OmegaConf.to_yaml(resolved_dict))
        return resolved_dict
    
    except Exception as e:
        print(f"Erreur lors de la résolution: {e}")
        if 'cfg' in locals():
            # Afficher la structure pour déboguer
            print("\nDébug - Structure de configuration avant résolution:")
            print(yaml.dump(OmegaConf.to_container(cfg, resolve=False)))
        raise
    
    finally:
        # Revenir au répertoire de travail original
        os.chdir(original_cwd)
        # Nettoyage de Hydra
        if GlobalHydra().is_initialized():
            GlobalHydra.instance().clear()

if __name__ == "__main__":
    config = read_config()
    print(config)
