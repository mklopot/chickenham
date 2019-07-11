from pycoin.symbols.btc import network
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import config
import collections
import getpass
import re
import combine
import input_shares
import coinbase_utils

conf = config.Config()
c = coinbase_utils.Client.new(conf)

if not conf.data.btc_account_id:
    btc_account = coinbase_utils.user_choose_confirm(c, 'BTC', 'Bitcoin account')
else:
    try:
        btc_account = c.get_account(conf.data.btc_account_id)    
    except Exception:
        print("Could not access previously used BTC account, check your API keys")
        raise
    
    deposit_address = btc_account.create_address().address
    conf.set('btc_acccount_id', btc_account.id)
    usd_account = coinbase_utils.user_choose_confirm(c, "USD", 'USD account')
    conf.set('usd_acccount_id', usd_account.id)
    secret = None
    
    while not secret:
        shares = [share.code for share in input_shares.input_batch()]
        combiner = combine.Combiner(len(shares))
        secret = combiner(shares)
        if not secret:
            print("The Shared Codes could not be combined. Try again. Starting over..."
        else:
            print("Shared Codes successfully combined!")

    private_key = network.keys.private(secret_exponent=secret)
    wif = private_key.wif()
                  
if not conf.data.txid or not requests.get("http://blockchain.info/tx/{}?show_adv=false&format=json".format(conf.data.txid)):
    # rpc_user and rpc_password are set in the bitcoin.conf file
    rpc_connection = AuthServiceProxy("http://%s:%s@127.0.0.1:8332"%(conf.data.rpc_user, conf.data.rpc_password))
    print("Balance before import: {} BTC".format(rpc_connection.getbalance()))
    rpc_connection.importprivkey(wif)
    balance = rpc_connection.getbalance()
    print("Balance after import: {} BTC".format(balance))
    r = requests.get("https://bitcoinfees.earn.com/api/v1/fees/recommended")
                  
    #convert to BTC from satoshis, multiply by approx. bytes per transaction, and double it, just in case
    fee_recommended = int(r.json()["fastestFee"]) * 0.00001
    fee = min(fee_recommended, 0.001)
    rpc_connection.settxfee(fee)
    conf.set('txid', txid)
    conf.set('btc_account_id', btc_account.id)
    txid = rpc_connection.sendtoaddress(deposit_address, balance)


print("On-blockchain transfer has been initiated, transaction: " + txid)
print("To complete the transfer, 6 confirmations are required.\n"
      "This usually takes less than two hours, but sometimes may take as long as a few days...")
confirmations = 0
print("{}Last checked at: [{}]     Confirmations: {}".format("\b"*100, time.strftime('%Y-%m-%d %I:%M:%S %p %Z', time.localtime()), confirmations), end="", flush=True)
while confirmations < 6:
    r = requests.get("http://blockchain.info/tx/{}?show_adv=false&format=json".format(txid))
    tx_block_height = r.json()["block_height"]
    time.sleep(20)
    current_block_height = int(requests.get("https://blockchain.info/q/getblockcount").text)
    confirmations = current_block_height - tx_block_height + 1
    print("{}Last checked at: [{}]     Confirmations: {}".format("\b"*100, time.strftime('%Y-%m-%d %I:%M:%S %p %Z', time.localtime()), confirmations), end="", flush=True)
    time.sleep(20)
print("Transfer transaction confirmation complete.")

if not conf.data.btc_account_id:
    
    conf.set("btc_account_id", btc_account.id)
             
if not conf.data.sell_id:
    print("Initiating a sale from BTC to USD...")
    sell = btc_account.sell(btc_account.balance.amount, currency = btc_account.balance.currency, payment_method = usd_account.id)
else:
    print("Retrieving previous sell information...")
    sell = btc_account.get_sell(conf.data.sell_id)              
                  
while sell.status != 'completed':
    print("{}Last checked at: [{}]     Sell status: {}".format("\b"*100, time.strftime('%Y-%m-%d %I:%M:%S %p %Z', time.localtime()), sell.status), end="", flush=True)
    sell.refresh() 
    sleep 10
                  
    
payment_methods = c.get_payment_methods()
payment_methods_withdraw = [p for p in payment_methods.data if p.withraw_allowed]
payment_method = payment_methods_withdraw[0]

withdraw = c.withdraw(usd_account.id, amount=usd_account.balance.amount, currency=usd_account.balance.currency, payment_method=payment_method.id)
while withdraw.status != 'completed':
    print("{}Last checked at: [{}]     Withdraw status: {}".format("\b"*100, time.strftime('%Y-%m-%d %I:%M:%S %p %Z', time.localtime()), withdraw.status), end="", flush=True)
    withdraw.refresh() 
    sleep 10
