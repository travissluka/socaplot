def _load_configs():
    """load all the binning specifications in the config directory."""
    import pathlib
    import glob
    import yaml

    config_root = pathlib.Path(__file__).parent.resolve()
    configs = {}
    for level in ['l1a', 'l1b', 'l1c']:
        configs_lvl = {}
        for cf in glob.glob(str(config_root / f'{level}/*.yaml')):
            config = yaml.safe_load(open(cf))
            configs_lvl[config['name']] = config
        configs[level] = configs_lvl
    return configs
globals().update(_load_configs())

l1a: dict
l1b: dict
l1c: dict

__all__ = ['l1a', 'l1b', 'l1c']