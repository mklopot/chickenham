from coinbase.wallet.client import Client
import config
import collections

my_conf = config.Config()
while True:
    while not my_conf.data.coinbase_api_key:
        coinbase_api_key = ""
        while not coinbase_api_key or not coinbase_api_secret:
            coinbase_api_key = raw_input('Enter API Key: ')
            coinbase_api_secret = raw_input('Enter API Secret: ')
        try:
            c = Client(coinbase_api_key, coinbase_api_secret)
        except Exception:
            coinbase_api_key = None
            coinbase_api_secret = None
            print("The key or secret you entered were not valid. Try again...")
    coinbase_user = c.get_current_user()
    print("https://coinbase.com reports the API key you entered is associated with {} <{}> residing in {}. Is this correct?".format(
               coinbase_user.name, coinbase_user.email, coinbase_user.country.name))
    user_prompt = raw_input("Type 'yes' and press ENTER to confirm. Type 'no' and press ENTER to provide a different API key: ")
    user_prompt = user_prompt.to_lower()
    if user_prompt[:2] == "yes":
        break
    else:
        print("You have chosen to use a different API key")

my_conf.set('coinbase_api_key', coinbase_api_key)
my_conf.set('coinbase_api_secret', coinbase_api_secret)   

def get_btc_account(c):
    btc_acounts = []
        all_accounts = c.get_accounts()
        btc_accounts = [x for x in all_accounts.data if x.currency == 'BTC' and x.allow_withdrawals]
    while not btc_accounts:
        print("No Bitcoin accounts that allow withdrawal are showing. "
              "This is unusual, there should be at least one by default. "
              "Contact https://coinbase.com. Once resolved, press ENTER to continue...")
        raw_input()
        all_accounts = c.get_accounts()
        btc_accounts = [x for x in all_accounts.data if x.currency == 'BTC' and x.allow_withdrawals]
    return btc_accounts

btc_accounts = get_btc_accounts(c)
if len(btc_accounts) == 1:
    print("One Bitcoin account found, called '{}', with a balance of {} {}.".format(
               btc_accounts[0].name, btc_accounts[0].balance.amount, btc_accounts[0].balance.amount.currency))
    print("This looks good. Press ENTER to confirm.\n\n"
          "If you have a very specific reason, and this is not the account you want to use, "
          "you will have to set another one up on https://coinbase.com. In that case, "
          "type 'no' and press ENTER once another account is set up, and you will have the option to select it")
    user_prompt = raw_input("Confirm: ")
    user_prompt = user_prompt.to_lower()
    # TODO: query accounts again here
    account = btc_accounts[0]
else:
    accounts_hash = collections.ordereddict()
    for i, account in zip(range(1,len(btc_accounts)+1),btc_accounts):
        accounts_hash[i] = account

    for account_index, account in accounts_hash.items():
        print("{} - '{}', with a balance of {} {}\n\n".format(account_index, account.name, account.balance.amount, account.balance.currency))
    print("{} - None of the above: You will need to set up another "
          "Bitcoin account on https://coinbase.com, then select this option".format(len(accounts_hash)))
    user_prompt = raw_input("Select an option (1-{}:) ".format(len(accounts_hash)))
    account = account_hash[int(user_prompt)]
    
deposit_address = account.create_address("Transfer from Veggie Chickenham {}".format(datetime.datetime.now().strftime(%m/%d/%Y)))    
    




    


