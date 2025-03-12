from hydra.core.hydra_config import HydraConfig
import hydra
from omegaconf import OmegaConf
@hydra.main(config_path=None, config_name=None)
def main(cfg):
    # Afficher la structure complète
    print(OmegaConf.to_yaml(HydraConfig.instance().get_config()))

if __name__ == "__main__":
    main()