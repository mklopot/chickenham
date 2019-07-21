import yaml
import os
from pathlib import Path
import stat


class Data:
    pass


class Config:
    def __init__(self, conffile):
        self.keys = ["coinbase_api_key",
                     "coinbase_api_secret",
                     "txid",
                     "btc_account_id",
                     "usd_account_id",
                     "sell_id",
                     "withdrawal_id",
                     "rpc_user",
                     "rpc_password"]
        self.data = Data()
        self.path = Path(conffile)
        if self.path.is_file():
            config_on_disk = {}
            with open(conffile, 'r') as f:
                try:
                    config_on_disk.update(yaml.safe_load(f))
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
        if attr not in self.keys:
            raise AttributeError("Unsupported Key")
        setattr(self.data, attr, value)
        self.save()

    def save(self):
        self.path.open('a').close()
        os.chmod(str(self.path), stat.S_IRUSR | stat.S_IWUSR)
        with self.path.open('w') as f:
            yaml.safe_dump(self.data.__dict__, f, default_flow_style=False)

    def delete(self, attr):
        delattr(self.data, attr)
        self.save()
