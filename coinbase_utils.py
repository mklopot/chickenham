from coinbase.wallet.client import Client
import config

class Client:
    @staticmethod
    def new_from_config(conf):
        if conf.data.coinbase_api_key and conf.data.coinbase_api_secret:
            try:
                client = Client(conf.coinbase_api_key, conf.coinbase_api_secret)
                coinbase_user = client.get_current_user()
                print("https://coinbase.com reports the API key "
                      "you entered is associated with {} <{}> residing "
                      "in {}. Do you want to proceed using this account?".format(
                          coinbase_user.name, coinbase_user.email, coinbase_user.country.name))
                user_prompt = input("Type 'yes' and press ENTER to confirm. "
                                "Type 'no' and press ENTER to be prompted for a different API key: ")
            user_prompt = user_prompt.to_lower()
            if user_prompt[:3] == "yes":
                return client
            except Exception:
                print("The previously stored API Key or API Secret was invalid, discaridng...")  
                conf.del('coinbase_api_key')
                conf.del('coinbase_api_secret')

    @staticmethod
    def new_from_prompt(conf):
        client = None
        while not client:
            coinbase_api_key = input('Enter API Key: ')
            coinbase_api_secret = input('Enter API Secret: ')
            print(chr(27) + "[2J") #Clear Screen
            try:
                client = Client(coinbase_api_key, coinbase_api_secret)
                coinbase_user = client.get_current_user()
                print("https://coinbase.com reports the API key "
                      "you entered is associated with {} <{}> residing "
                      "in {}. Do you want to proceed using this account?".format(
                          coinbase_user.name, coinbase_user.email, coinbase_user.country.name))
                user_prompt = input("Type 'yes' and press ENTER to confirm. "
                                "Type 'no' and press ENTER to be prompted for a different API key: ")
                user_prompt = user_prompt.to_lower()
                if user_prompt[:3] == "yes":
                    conf.set('coinbase_api_key', coinbase_api_key)
                    conf.set('coinbase_api_secret', coinbase_api_secret)
                    return client
                else:
                    print("Discaring the API KEY and API Secret you entered, and starting over...")
             except Exception:
                 print("The API Key or API Secret you entered was invalid. Try again...")
                 pass

    @staticmethod
    def new(self, conf):
        client = Client.new_from_config(conf) 
        if not client:
            client = new_from_prompt(conf)
        return client
