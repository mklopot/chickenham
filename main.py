#!/usr/bin/python3.6

from pycoin.symbols.btc import network
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from pathlib import Path
import config
import collections
import re
import requests
import time

import combine
import input_shares
import coinbase_utils

conf = config.Config(Path.home().joinpath('.chiknhamrc'))
if not conf.data.txid or not requests.get("http://blockchain.info/tx/{}?show_adv=false&format=json".format(conf.data.txid)):
    c = coinbase_utils.CoinClient.new(conf)
    btc_account = coinbase_utils.user_choose_confirm(c, 'BTC', 'Bitcoin account')
    deposit_address = btc_account.create_address().address
    conf.set('btc_account_id', btc_account.id)
    usd_account = coinbase_utils.user_choose_confirm(c, "USD", 'USD account')
    conf.set('usd_account_id', usd_account.id)
    secret = None
    inputter = input_shares.UserInput()    
    while not secret:
        shares = [share.code for share in inputter.input_batch()]
        combiner = combine.Combiner(len(shares))
        secret = combiner(shares)
        if not secret:
            print("The Shared Codes could not be combined. Try again. Starting over...")
        else:
            print("Shared Codes successfully combined!")

    private_key = network.keys.private(secret_exponent=int(secret,16))
    wif = private_key.wif()
                  
    # rpc_user and rpc_password are set in the bitcoin.conf file
    rpc_connection = AuthServiceProxy("http://%s:%s@127.0.0.1:8332"%(conf.data.rpc_user, conf.data.rpc_password))
    print("Balance before import: {} BTC".format(rpc_connection.getbalance()))
    rpc_connection.importprivkey(wif)
    balance = rpc_connection.getbalance()
    print("Balance after import: {} BTC".format(balance))
    r = requests.get("https://bitcoinfees.earn.com/api/v1/fees/recommended")
                  
    #convert to BTC/KB from satoshis/B, and quadruple it, just in case
    fee_recommended = round(r.json()["fastestFee"] * 0.00004, 8)
    fee = min(fee_recommended, 0.003)
    print("Setting transaction fee to {} BTC".format(fee))
    rpc_connection.settxfee(fee)
    txid = rpc_connection.sendtoaddress(deposit_address, balance, "", "", True)
    conf.set('txid', txid)
else:
    txid = conf.data.txid
    c = coinbase_utils.CoinClient.new(conf)
    #TODO check that getting accounts succeeds:
    btc_account = c.get_account(conf.data.btc_account_id)
    usd_account = c.get_account(conf.data.usd_account_id)

if not conf.data.sell_id:
    print("On-blockchain transfer has been initiated.\n"
          "Transaction ID: " + txid)
       `
    print("To complete the transfer, 6 confirmations are required.\n"
          "This usually takes less than two hours, but sometimes may take as long as a few days...")
    confirmations = 0
    print("{}Last checked at: [{}]     Confirmations: {}".format("\b"*100, time.strftime('%Y-%m-%d %I:%M:%S %p %Z', time.localtime()), confirmations), end="", flush=True)
    while confirmations < 6:
        r = requests.get("http://blockchain.info/tx/{}?show_adv=false&format=json".format(txid))
        try:
            tx_block_height = r.json()["block_height"]
        except Exception:
            continue
        time.sleep(20)
        current_block_height = int(requests.get("https://blockchain.info/q/getblockcount").text)
        confirmations = current_block_height - tx_block_height + 1
        print("{}Last checked at: [{}]     Confirmations: {}".format("\b"*100, time.strftime('%Y-%m-%d %I:%M:%S %p %Z', time.localtime()), confirmations), end="", flush=True)
        time.sleep(20)
    print("Transfer transaction confirmation complete.")

    print("Initiating a sale from BTC to USD...")
    fiat_accounts = [account for account in c.get_payment_methods if account.type == 'fiat_account']
    usd_account_payment = [account for account in fiat_accounts if account.fiat_account.id == usd_account.id]
    
    sell = btc_account.sell(amount=btc_account.balance.amount, currency=btc_account.balance.currency, payment_method=usd_account_payment.id)
    conf.set("sell_id", sell.id)
else:
    print("Retrieving previous sell information...")
    # TODO check that getting the sell object succeeds
    sell = btc_account.get_sell(conf.data.sell_id)              
                  
print("Waiting for sell completion...")
while sell.status != 'completed':
    print("{}Last checked at: [{}]     Sell status: {}".format("\b"*100, time.strftime('%Y-%m-%d %I:%M:%S %p %Z', time.localtime()), sell.status), end="", flush=True)
    sell.refresh() 
    time.sleep(10)
                  
if not conf.data.withdrawal_id:    
    payment_methods = c.get_payment_methods()
    payment_methods_withdraw = [p for p in payment_methods.data if p.allow_withdraw and p.currency == 'USD']
    #TODO user choose withdrawal account
    #payment_method = payment_methods_withdraw[0]
    payment_method = coinbase_utils.user_choose_payment_method(c)

    print("Withdrawing funds from https://coinbase.com to the linked account...")
    withdrawal = c.withdraw(usd_account.id, amount=usd_account.balance.amount, currency=usd_account.balance.currency, payment_method=payment_method.id)
    conf.set("withdrawal_id", withdrawal.id)
else:
    # TODO check that getting the withdraw object succeeds
    withdrawal = usd_account.get_withdrawal(conf.data.withdrawal_id)

print("Waiting for withdrawal completion...")
while withdrawal.status != 'completed':
    print("{}Last checked at: [{}]     Withdrawal status: {}".format("\b"*100, time.strftime('%Y-%m-%d %I:%M:%S %p %Z', time.localtime()), withdrawal.status), end="", flush=True)
    withdrawal.refresh() 
    time.sleep(10)

conf.delete('btc_account')
conf.delete('usd_account')
conf.delete('txid')
conf.delete('sell_id')
conf.delete('withdrawal_id')

print("Done.")
