from coinbase.wallet.client import Client
import collections
import config

class CoinClient:
    @staticmethod
    def new_from_config(conf):
        if conf.data.coinbase_api_key and conf.data.coinbase_api_secret:
            try:
                client = Client(conf.data.coinbase_api_key, conf.data.coinbase_api_secret)
                coinbase_user = client.get_current_user()
                print("https://coinbase.com reports the API key "
                      "you entered is associated with {} <{}> residing "
                      "in {}. Do you want to proceed using this account?".format(
                          coinbase_user.name, coinbase_user.email, coinbase_user.country.name))
                user_prompt = input("Type 'yes' and press ENTER to confirm. "
                                "Type 'no' and press ENTER to be prompted for a different API key: ")
                user_prompt = user_prompt.lower()
                if user_prompt[:3] == "yes":
                    return client
            except Exception:
                print("The previously stored API Key or API Secret was invalid, discaridng...")  
                conf.delete('coinbase_api_key')
                conf.delete('coinbase_api_secret')

    @staticmethod
    def new_from_prompt(conf):
        client = None
        while not client:
            coinbase_api_key = input('Enter API Key: ')
            coinbase_api_secret = input('Enter API Secret: ')
            print(chr(27) + "[2J" + chr(27) + "[H") #Clear Screen
            try:
                client = Client(coinbase_api_key, coinbase_api_secret)
                coinbase_user = client.get_current_user()
                print("https://coinbase.com reports the API key "
                      "you entered is associated with {} <{}> residing "
                      "in {}. Do you want to proceed using this account?".format(
                          coinbase_user.name, coinbase_user.email, coinbase_user.country.name))
                user_prompt = input("Type 'yes' and press ENTER to confirm. "
                                "Type 'no' and press ENTER to be prompted for a different API key: ")
                user_prompt = user_prompt.lower()
                if user_prompt[:3] == "yes":
                    conf.set('coinbase_api_key', coinbase_api_key)
                    conf.set('coinbase_api_secret', coinbase_api_secret)
                    return client
                else:
                    print("Discaring the API KEY and API Secret you entered, and starting over...")
            except Exception as e:
                 print(e)
                 print("The API Key or API Secret you entered was invalid. Try again...")

    @staticmethod
    def new(conf):
        client = CoinClient.new_from_config(conf) 
        if not client:
            client = CoinClient.new_from_prompt(conf)
        return client

def get_accounts_by_currency(c, currency='BTC'):
    acounts = []
    all_accounts = c.get_accounts()
    accounts = [x for x in all_accounts.data if x.currency == currency]
    while not accounts:
        print("No {} accounts are showing. Check API key permissions...".format(currency))
        input()
        all_accounts = c.get_accounts()
        accounts = [x for x in all_accounts.data if x.currency == 'BTC']
    return accounts

def user_choose_confirm(client, currency="BTC", desc="account"):
    account = None
    while not account:
        accounts = get_accounts_by_currency(client, currency)
        if not accounts:
            print("No {}s on https://coinbase.com are visible with the API Key provided. Check permissions...")
            input("Log on to https://coinbase.com, set up the necessary account, or change API Key permissions,\n"
                  "and press ENTER to continue...")
            continue
        if len(accounts) == 1:
            print("One {} found, called '{}', with a balance of {} {}.".format(
                      desc,
                      accounts[0].name,
                      accounts[0].balance.amount,
                      accounts[0].balance.currency))
            print("This looks good. Press ENTER to confirm.\n\n"
                  "If you have a very specific reason, and this is not the account you want to use, "
                  "you will have to set another one up on https://coinbase.com. In that case, "
                  "type 'no' and press ENTER once another account is set up, "
                  "and you will have the option to select it\n"
                  "To use this account, press ENTER")
            user_input = input("Confirm: ")
            user_input = user_input.lower()
            if user_input[:2] != "no":
                return accounts[0]
        else:
            accounts_hash = collections.ordereddict()
            for i, account in zip(range(1,len(btc_accounts)+1),btc_accounts):
                accounts_hash[i] = account

            for account_index, account in accounts_hash.items():
                print("{} - '{}', with a balance of {} {}\n\n".format(
                          account_index,
                          account.name,
                          account.balance.amount,
                          account.balance.currency))

            print("{} - None of the above: You will need to set up another "
                  "{} on https://coinbase.com, then select this option".format(
                       len(accounts_hash), desc))
            user_prompt = input("Select an option (1-{}) and press ENTER: ".format(
                                     len(accounts_hash)))
            try:
                account = account_hash[int(user_prompt)]
            except IndexError:
                pass

