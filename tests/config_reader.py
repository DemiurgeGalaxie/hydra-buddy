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
    Lit et résout une configuration Hydra.
    
    Args:
        config_name (str): Nom de la configuration à lire (sans extension .yaml)
        config_path (str): Chemin du dossier de configuration 
                          (par défaut: .hydra-conf dans le dossier courant)
    
    Returns:
        dict: Configuration résolue sous forme de dictionnaire
    """
    # Déterminer le chemin de configuration
    if config_path is None:
        config_path = os.path.join(os.getcwd(), '.hydra-conf')
    
    print(f"Lecture de la configuration '{config_name}' depuis '{config_path}'")
    
    # Réinitialiser Hydra si nécessaire
    if GlobalHydra().is_initialized():
        GlobalHydra.instance().clear()
    
    # Sauvegarder le répertoire courant
    original_cwd = os.getcwd()
    
    try:
        # Changer le répertoire de travail temporairement pour que Hydra puisse
        # trouver les répertoires de configuration
        os.chdir(os.path.dirname(config_path))
        rel_config_dir = os.path.basename(config_path)
        
        # Initialiser Hydra avec le bon chemin
        hydra.initialize(config_path=rel_config_dir, version_base=None)
        
        # Composer la configuration
        cfg = hydra.compose(config_name=config_name)
        
        # Résoudre toutes les interpolations
        resolved_dict = OmegaConf.to_container(cfg, resolve=True)
        
        return resolved_dict
    
    finally:
        # Revenir au répertoire de travail original
        os.chdir(original_cwd)
        # Nettoyage de Hydra
        if GlobalHydra().is_initialized():
            GlobalHydra.instance().clear()

def main():
    """Fonction principale"""
    # Récupérer les arguments
    config_name = sys.argv[1] if len(sys.argv) > 1 else "dev"
    config_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        # Lire et résoudre la configuration
        config = read_config(config_name, config_path)
        
        # Afficher le résultat
        print("\nConfiguration résolue:")
        print(yaml.dump(config, default_flow_style=False, sort_keys=False))
        
        # Exemple d'accès direct à certaines valeurs
        if "project" in config:
            print(f"\nNom du projet: {config['project']['name']}")
        
        if "database" in config and "credentials" in config["database"]:
            print(f"Utilisateur DB: {config['database']['credentials']['username']}")
    
    except Exception as e:
        print(f"Erreur lors de la lecture de la configuration: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

# Alternative utilisant directement TheReader de hydra-buddies
def read_with_reader(config_name="dev", config_path=None):
    """
    Lit et résout une configuration en utilisant TheReader.
    
    Args:
        config_name (str): Nom de la configuration à lire
        config_path (str): Chemin du dossier de configuration
    
    Returns:
        dict: Configuration résolue sous forme de dictionnaire
    """
    try:
        # Importer TheReader depuis hydra-buddies
        from hydra_buddies import TheReader
        
        # Créer une instance de TheReader
        reader = TheReader(config_name)
        
        # Mettre à jour le chemin si nécessaire
        if config_path:
            reader.update_path(config_path)
        
        # Convertir en dictionnaire avec résolution
        resolved_dict = OmegaConf.to_container(reader.cfg, resolve=True)
        
        return resolved_dict
    
    except ImportError:
        print("Impossible d'importer TheReader. Vérifiez que hydra-buddies est installé.")
        return None

if __name__ == "__main__":
    # Décommentez la ligne ci-dessous pour utiliser TheReader à la place
    # config = read_with_reader("dev")
    # if config:
    #     print(yaml.dump(config, default_flow_style=False, sort_keys=False))
    # else:
    #     sys.exit(1)
    
    sys.exit(main())