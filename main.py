from coinbase.wallet.client import Client
import config
import collections
import getpass
import re
import combine

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
    coinbase_user = c.get_current_user()
    print("https://coinbase.com reports the API key you entered is associated with {} <{}> residing in {}. Is this correct?".format(
               coinbase_user.name, coinbase_user.email, coinbase_user.country.name))
    user_prompt = input("Type 'yes' and press ENTER to confirm. Type 'no' and press ENTER to provide a different API key: ")
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
          "Otherwise, press enter to confirm")
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

shares_list = []    
print("You will now be prompted for the batch number of each shared code, and then the code itself, one at a time. "
      "Make sure all codes that you will enter are part of the same batch.")
user_input = input("Enter batch number (or press ENTER if no more codes to input): ")

# Batch numbers look like this: 0-4-10-9
def parse_batch(batch_num):
    if not re.match(r"^[0-9-]+", batch_num):
        print("The batch number can only contain numbers and dashes")
        return False
    batchsplit = batch_num.split("-")
    if len(batchsplit) != 4:
        print "A batch number should contain only numbers and exactly three dashes"
        return False
    batch, threshold, num_shares, checksum = batchsplit[0], batchsplit[1], batchsplit[2], batchsplit[3]
    return int(batch), int(threshold), int(num_shares), int(checksum)

def parse_code(code_input):
    no_whitespace = "".join(split(code_input)).to_upper() 
    if not re.match(r"^[0-9A-F]{64}",no_whitespace):
        print("Shared code must be exactly 64 characters long and contain digits and/or letters A thru F")
        return False
    return no_whitespace
    

if user_input:    
    parsed_batch = parse_batch(user_input)     
    if parse:
        user_code_input = getpass.getpass("Enter shared code (you will not see the code as you type it): ") 
        parsed_code = parse_code(user_code_input)
        if parsed_code:
            shares_list.append((parsed_batch,parsed_code))

batches = set()        
for share in shares_list:
    batches.add((share[0][0], share[0][1], share[0][2]))
if len(batches) > 1:
    print("Inconsistent batch numbers")


