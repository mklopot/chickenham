import yaml
from pathlib import Path

conffile = "~/.sellchiknham"


class Data:
    pass


class Config:
    def __init__(self, conffile):
        self.keys = ["coinbase_api_key", "coinbase_api_secret", "txid", "btc_account_id", "usd_account_id", "sell_id", "withdraw_id"]
        self.data = Data()
        if Path.is_file(conffile):
            config_on_disk = []
            with open(conffile, 'r') as f:
                try:
                    config_on_disk = yaml.load(f)
                except Exception:
                    pass
            for key in self.keys:
                if key in config_on_disk:
                    setattr(self.data, key, config_on_disk[key])
                else:
                    setattr(self.data, key, None)
        else:
            for key in self.keys:
                setattr(self.data, key, None)

    def set(self, attr, value):
        setattr(self.data, attr, value)
        self.save()

    def save(self):
        open(conffile, 'a').close()
        os.chmod(conffile, '0400')
        with open(conffile, 'w') as f:
            yaml.dump(self.data, f)

    def delete(self, attr):
        delattr(self.data, attr)
        self.save()
        
