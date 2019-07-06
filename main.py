from coinbase.wallet.client import Client
from pycoin.symbols.btc import network
import config
import collections
import getpass
import re
import combine
import input_shares

my_conf = config.Config()
while True:
    while not my_conf.data.coinbase_api_key:
        coinbase_api_key = ""
        while not coinbase_api_key or not coinbase_api_secret:
            coinbase_api_key = input('Enter API Key: ')
            coinbase_api_secret = input('Enter API Secret: ')
        try:
            c = Client(coinbase_api_key, coinbase_api_secret)
        except Exception:
            coinbase_api_key = None
            coinbase_api_secret = None
            print("The key or secret you entered were not valid. Try again...")
            continue
    coinbase_user = c.get_current_user()
    print("https://coinbase.com reports the API key you entered is associated with {} <{}> residing in {}. Is this correct?".format(
               coinbase_user.name, coinbase_user.email, coinbase_user.country.name))
    user_prompt = input("Type 'yes' and press ENTER to confirm. Type 'no' and press ENTER to provide a different API key: ")
    user_prompt = user_prompt.to_lower()
    if user_prompt[:3] == "yes":
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
        input()
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
          "type 'no' and press ENTER once another account is set up, and you will have the option to select it"
          "To use this acocunt, press ENTER")
    user_prompt = input("Confirm: ")
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
    user_prompt = input("Select an option (1-{}:) ".format(len(accounts_hash)))
    account = account_hash[int(user_prompt)]
    
deposit_address = account.create_address("Transfer from Veggie Chickenham {}".format(datetime.datetime.now().strftime(%m/%d/%Y)))    

while True:
    shares = input_shares.input_batch()
    combiner = combine.Combiner(len(shares))
    secret = combiner(shares)
    if not secret:
        print("The Shared Codes could not be combined. Try again."
    else:
        print("Shared Codes successfully combined!")
        break

private_key = network.keys.private(secret_exponent=secret)
wif = private_key.wif()

from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException

# rpc_user and rpc_password are set in the bitcoin.conf file
rpc_connection = AuthServiceProxy("http://%s:%s@127.0.0.1:8332"%(rpc_user, rpc_password))
print("Balance before import: {} BTC".format(rpc_connection.getbalance()))
rpc_connection.importprivkey(wif)
balance = rpc_connection.getbalance()
print("Balance after import: {} BTC".format(balance))
r = requests.get("https://bitcoinfees.earn.com/api/v1/fees/recommended")
fee = int(r.json()["fastestFee"]) * 225 * 2 * 0.00000001 #convert to BTC from satoshis, multiply by approx. bytes per transaction, and double it, just in case
rpc_connection.settxfee(fee)
txid = rpc_connection.sendtoaddress(deposit_address, balance)
my_conf.set('txid', txid)   

print("Initiated on-chain transfer, transaction: " + txid)
print("To complete the transfer, 6 confirmations are required. This usually takes less than two hours, but sometimes may take as long as a few days...")
confirmations = 0
while confirmations < 6:
    r = requests.get("http://bitcoin.info/tx/{}?show_adv=false&format=json".format(tx))
    tx_block_height = r.json()["block_height"]
    time.sleep(20)
    current_block_height = requests.get("https://blockchain.info/q/getblockcount")
    confirmations = current_block_height - tx_block_height + 1
    print("\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\bConfirmations: {}".format(confirmations), end="")
    time.sleep(20)

print("Confirmation complete. Initiationg withdrawal of funds to bank account..."
wthdraw = c.withdraw(account.id, account.balance, account.currency, payment_method.id)
