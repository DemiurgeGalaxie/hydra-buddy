#!/usr/bin/env python3
"""
Script de test pour la classe TheReader avec promotion des secrets.

Ce script démontre comment:
1. Charger différentes configurations
2. Accéder aux valeurs avec résolution d'interpolation
3. Naviguer dans la structure de configuration
4. Afficher la configuration résolue complète
"""

import os
import sys
import yaml
from omegaconf import OmegaConf

# Assurez-vous que le package hydra_buddies est dans le PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from hydra_buddies.buddies import TheReader

def test_reader():
    """Fonction principale de test pour TheReader."""
    
    # Configuration à tester
    config_name = "config"  # ou "dev" pour une configuration spécifique
    
    # Chemin vers le répertoire de configuration
    config_path = os.path.join(os.path.dirname(__file__), '.hydra-conf')
    if not os.path.exists(config_path):
        # Essayer un autre chemin courant
        config_path = os.path.join(os.getcwd(), '.hydra-conf')
    
    print(f"\n=== Test de TheReader avec '{config_name}' depuis '{config_path}' ===\n")
    
    # 1. Chargement de base avec chemin explicite
    print("1. Chargement de la configuration")
    reader = TheReader(config_name)

    print(f"Configuration chargée: {config_name}")
    
    # 2. Afficher la structure de premier niveau
    print("\n2. Structure de premier niveau")
    print("-" * 40)
    for key in reader.cfg.keys():
        print(f"• {key}")
    
    # 3. Accéder aux valeurs
    print("\n3. Accès aux valeurs (sans résolution)")
    print("-" * 40)
    if 'project' in reader.cfg:
        print(f"Nom du projet: {reader.cfg.project.name}")
        print(f"Version: {reader.cfg.project.version}")
    
    if 'database' in reader.cfg:
        print(f"Base de données: {reader.cfg.database.host}:{reader.cfg.database.port}")
    
    # 4. Tester la navigation contextuelle
    print("\n4. Navigation contextuelle")
    print("-" * 40)
    with reader.walk('database'):
        if hasattr(reader, 'host'):
            print(f"Hôte DB: {reader.host}")
        if hasattr(reader, 'credentials'):
            print(f"Identifiants DB: {reader.credentials}")
    
    # 5. Tester la résolution des interpolations (avec promotion des secrets)
    print("\n5. Résolution des interpolations")
    print("-" * 40)
    try:
        resolved_config = reader.get_resolved_config()
        print("Résolution réussie!")
        
        # Afficher quelques valeurs résolues
        if 'database' in resolved_config and 'credentials' in resolved_config['database']:
            print(f"Username résolu: {resolved_config['database']['credentials']['username']}")
            print(f"Password résolu: {resolved_config['database']['credentials']['password']}")
        
        if 'logging' in resolved_config and 'loggers' in resolved_config['logging']:
            if 'app' in resolved_config['logging']['loggers']:
                app_logger = resolved_config['logging']['loggers']['app']
                if 'credentials' in app_logger:
                    print(f"Logger credentials: {app_logger['credentials']}")
    
    except Exception as e:
        print(f"Erreur lors de la résolution: {e}")
    
    # 6. Tester avec update_path
    print("\n6. Test avec update_path")
    print("-" * 40)
    config_path = os.path.join(os.getcwd(), 'hydra_buddies', '.hydra-conf')
    if os.path.exists(config_path):
        try:
            reader.update_path(config_path)
            print(f"Chemin mis à jour: {config_path}")
            
            # Vérifier que la configuration est chargée
            if 'project' in reader.cfg:
                print(f"Nom du projet (après update_path): {reader.cfg.project.name}")
            
            # Tester à nouveau la résolution
            resolved_config = reader.get_resolved_config()
            print("Résolution après update_path réussie!")
            
        except Exception as e:
            print(f"Erreur lors de l'update_path: {e}")
    else:
        print(f"Chemin {config_path} introuvable, test update_path ignoré")
    
    # 7. Tester avec dev
    print("\n7. Test avec configuration dev")
    print("-" * 40)
    try:
        dev_reader = TheReader("dev")
        dev_reader.update_path(config_path)  # Même chemin mais configuration différente
        print("Configuration dev chargée")
        
        resolved_dev = dev_reader.get_resolved_config()
        print("Résolution de dev réussie!")
        
        # Vérifier l'environnement
        if 'env' in resolved_dev:
            print(f"Environnement: {resolved_dev['env']}")
        
        # Vérifier que les overrides fonctionnent
        if 'database' in resolved_dev:
            print(f"DB Host (dev): {resolved_dev['database']['host']}")
            
    except Exception as e:
        print(f"Erreur lors du test dev: {e}")
    
    print("\n=== Fin des tests ===\n")

if __name__ == "__main__":
    test_reader()