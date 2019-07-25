from coinbase.wallet.client import Client
import collections
from termcolor import colored


class CoinClient:
    @staticmethod
    def new_from_config(conf):
        attempt_load = True
        while attempt_load:
            attempt_load = False
            if conf.data.coinbase_api_key and conf.data.coinbase_api_secret:
                try:
                    print(colored("Attempting to load API key", "blue"))
                    client = Client(conf.data.coinbase_api_key, conf.data.coinbase_api_secret)
                    coinbase_user = client.get_current_user()
                    print("API Key Info:")
                    print("Name: " + colored(coinbase_user.name, "blue"))
                    print("Email: " + colored(coinbase_user.email, "blue"))
                    print("Country: " + colored(coinbase_user.country.name, "blue"))
                    print("Do you want to proceed using this account?")
                    print(colored("Type ", "cyan") + colored("yes", "yellow") +
                          colored(" and press ENTER to confirm.\n", "cyan") +
                          colored("Type ", "cyan") + colored("no", "yellow") +
                          colored(" and press ENTER to be prompted "
                                  "for a different API key.", "cyan"))
                    user_prompt = input("Confirm (yes/no): ")
                    user_prompt = user_prompt.lower()
                    if user_prompt[:1] == "y":
                        return client
                except Exception as e:
                    print(colored("The previously stored API Key or API Secret is invalid", "red"))
                    print(colored(e, "cyan"))
                    delete_api_key = input("Delete stored API key and API Secret? (yes/no): ")
                    delete_api_key = delete_api_key.lower()
                    if delete_api_key[:1] == "y":
                        conf.delete('coinbase_api_key')
                        conf.delete('coinbase_api_secret')
                        return
                    else:
                        attempt_load = True

    @staticmethod
    def new_from_prompt(conf):
        client = None
        while not client:
            coinbase_api_key = input('Enter API Key: ')
            coinbase_api_secret = input('Enter API Secret: ')
            print(chr(27) + "[2J" + chr(27) + "[H")  # Clear Screen
            try:
                client = Client(coinbase_api_key, coinbase_api_secret)
                coinbase_user = client.get_current_user()
                print("API Key Info:")
                print("Name: " + colored(coinbase_user.name, "blue"))
                print("Email: " + colored(coinbase_user.email, "blue"))
                print("Country: " + colored(coinbase_user.country.name, "blue"))
                print("Do you want to proceed using this account?")
                print(colored("Type ", "cyan") + colored("yes", "yellow") +
                      colored(" and press ENTER to confirm.\n", "cyan") +
                      colored("Type ", "cyan") + colored("no", "yellow") +
                      colored(" and press ENTER to be prompted "
                              "for a different API key.", "cyan"))
                user_prompt = input("Confirm (yes/no): ")
                user_prompt = user_prompt.lower()
                if user_prompt[:1] == "y":
                    conf.set('coinbase_api_key', coinbase_api_key)
                    conf.set('coinbase_api_secret', coinbase_api_secret)
                    return client
                else:
                    print(colored("Discarding the API KEY and API Secret "
                                  "you entered, starting over...", "red"))
            except Exception as e:
                print(colored("The API Key or API Secret you entered is invalid", "red"))
                print(colored(e, "cyan"))
                print("Try again...")

    @staticmethod
    def new(conf):
        client = CoinClient.new_from_config(conf)
        if not client:
            client = CoinClient.new_from_prompt(conf)
        return client


def get_accounts_by_currency(c, currency='BTC'):
    all_accounts = c.get_accounts()
    accounts = [x for x in all_accounts.data if x.currency == currency]
    while not accounts:
        print(colored("No {} account retrieved".format(currency), "red"))
        print(colored("Log on to https://coinbase.com and check API key permissions.", "cyan"))
        input("Press ENTER to retry ")
        all_accounts = c.get_accounts()
        accounts = [x for x in all_accounts.data if x.currency == 'BTC']
    return accounts


def user_choose_confirm(client, currency="BTC", desc="account"):
    sel_account = None
    while not sel_account:
        accounts = get_accounts_by_currency(client, currency)
        if not accounts:
            continue
        if len(accounts) == 1:
            print("\nOne {} {} found:".format(currency, desc))
            print("Name: " + colored("{}".format(accounts[0].name), "blue"))
            print("Balance: " + colored("{} {}".format(accounts[0].balance.amount,
                                                       accounts[0].balance.currency), "blue"))
            print("To use this account, press ENTER")
            print(colored("If this is not the account you want to use,\n"
                          "you can set up another {} account "
                          "on https://coinbase.com".format(currency), "cyan"))
            print(colored("In that case, type ", "cyan") + colored("no", "yellow") +
                  colored(" and press ENTER once another account is set up,\n"
                          "and you will have the option to select it.\n", "cyan"))
            user_input = input("Use this account (Y/n): ")
            user_input = user_input.lower()
            if user_input[:1] != "n":
                return accounts[0]
        else:
            print("\nSelect a {} account:".format(currency))
            accounts_hash = collections.OrderedDict()
            for i, account in zip(range(1, len(accounts)+1), accounts):
                accounts_hash[i] = account

            for account_index, account in accounts_hash.items():
                print(colored("{} - ".format(account_index), "blue") +
                      colored("{}   ", "blue").format(account.name) +
                      "(" + colored("{} {}".format(
                                  account.balance.amount,
                                  account.balance.currency),
                              "blue") + ")")

            print("{} - None of the above\n".format(len(accounts_hash)+1) +
                  colored("        You can set up another {} {} on\n"
                          "        https://coinbase.com, then select this option.".format(
                              currency, desc),
                          "cyan"))
            user_prompt = input("\nSelect an option (1-{}) and press ENTER: ".format(
                                     len(accounts_hash)+1))
            try:
                sel_account = accounts_hash[int(user_prompt)]
                return sel_account
            except (KeyError, ValueError):
                continue


def user_choose_payment_method(c):
    sel_method = None
    while not sel_method:
        payment_methods = c.get_payment_methods()
        methods = [p for p in payment_methods.data if p.allow_withdraw and p.currency == 'USD']
        if not methods:
            print(colored("No linked USD withdrawal accounts could be retrieved"
                  "with the API Key provided", "red"))
            input("Log on to https://coinbase.com, set up the necessary account,\n"
                  "or change API Key permissions.\n"
                  "Then press ENTER to continue...")
            continue
        if len(methods) == 1:
            print("\nOne linked account found: " + colored("{}".format(
                      methods[0].name), "blue"))
            print("To use this account, press ENTER")
            print(colored("If this is not the account you want to use, you can set up another\n"
                          "linked USD withdrawal account up on https://coinbase.com", "cyan"))
            print(colored("In that case, type ", "cyan") + colored("no", "yellow") +
                  colored(" and press ENTER once another account is set up,\n"
                          "and you will have the option to select it.", "cyan"))
            user_input = input("Use this account (Y/n): ")
            user_input = user_input.lower()
            if user_input[:1] != "n":
                return methods[0]
        else:
            print("\nSelect a linked USD withdrawal account:")
            methods_hash = collections.OrderedDict()
            for i, method in zip(range(1, len(methods)+1), methods):
                methods_hash[i] = method

            for method_index, method in methods_hash.items():
                print("{} - ".format(method_index) + colored("{}".format(method.name), "blue"))
            print("{} - None of the above\n".format(len(methods_hash)+1) +
                  colored("     You can set up another linked USD withdrawal method on\n"
                          "     https://coinbase.com, then select this option.", "cyan"))

            user_prompt = input("\nSelect an option (1-{}) and press ENTER: ".format(
                                     len(methods_hash)+1))
            try:
                sel_method = methods_hash[int(user_prompt)]
                return sel_method
            except (KeyError, ValueError):
                continue
