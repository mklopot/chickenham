#!/usr/bin/python3.6

from pycoin.symbols.btc import network
# from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from bitcoinrpc.authproxy import AuthServiceProxy
from pathlib import Path
import config
import requests
import time
import threading
from termcolor import colored

import combine
import input_shares
import coinbase_utils

conf = config.Config(Path.home().joinpath('.chiknhamrc'))
if not conf.data.txid or not requests.get(
        "http://blockchain.info/tx/{}?show_adv=false&format=json".format(conf.data.txid)):
    c = coinbase_utils.CoinClient.new(conf)
    btc_account = coinbase_utils.user_choose_confirm(c, 'BTC', 'Bitcoin account')
    deposit_address = btc_account.create_address().address
    conf.set('btc_account_id', btc_account.id)
    usd_account = coinbase_utils.user_choose_confirm(c, "USD", 'USD account')
    conf.set('usd_account_id', usd_account.id)
    secret = None
    inputter = input_shares.UserInput()
    print(chr(27) + "[2J" + chr(27) + "[H")  # Clear Screen
    while not secret:
        shares = [share.code for share in inputter.input_batch()]
        combiner = combine.Combiner(len(shares))
        secret = combiner(shares)
        if not secret:
            print(colored("The Shared Codes could not be combined", "red"))
            print("Starting over...")
        else:
            print(colored("Shared Codes successfully combined!", "green"))

    private_key = network.keys.private(secret_exponent=int(secret, 16))
    wif = private_key.wif()

    # rpc_user and rpc_password are set in the bitcoin.conf file
    rpc_connection = AuthServiceProxy(
        "http://%s:%s@127.0.0.1:8332" % (conf.data.rpc_user, conf.data.rpc_password),
        timeout=4*60*60)
    # TODO Make sure bitcoind is caught up...
    local_balance_before_import = rpc_connection.getbalance()
    print("\nLocal balance before import: ") +
          colored("{} BTC".format(local_balance_before_import, "blue"))
    print(colored("\nBeginning key import and block scan", "green"))
    print(colored("The scan may take 3 hours or more.\n", "cyan"))

    def importkey(privkey):
        rpc_connection.importprivkey(privkey)

    scanner_thread = threading.Thread(target=importkey, args=(wif,))
    scanner_thread.run()
    spinner = ["\u25f4 ", "\u25f7 ", "\u25f6 ", "\u25f5 "]
    while scanner_thread.is_alive():
        index = int(time.time() * 8 % len(spinner))
        print("\b"*29 + spinner[index] + colored("  Scanning blocks...   ", "blue"),
              end="",
              flush=True)
        time.sleep(.05)

    balance = rpc_connection.getbalance()
    print("\nLocal balance after import: " + colored("{} BTC".format(balance), "blue"))

    if local_balance_before_import == balance:
        print(colored("No balance detected on this batch of shared codes", "red"))
        if balance > 0:
            print("Proceed with the local balance of " +
                  colored("{} BTC".format(balance), "blue") + "?")
            proceed = input("Proceed (Y/n): ")
            proceed = proceed.lower()
            if proceed[:1] == "n":
                exit(1)
        else:
            print(colored("No local balance detected", "red"))
            print("Cannot proceed...")
            exit(1)
    
    r = requests.get("https://bitcoinfees.earn.com/api/v1/fees/recommended")
    # convert to BTC/KB from satoshis/B, and quadruple it, just in case
    fee_recommended = round(r.json()["fastestFee"] * 0.00004, 8)
    fee = min(fee_recommended, 0.003)
    print("Setting transaction fee to " + colored("{} BTC".format(fee), "blue") + " per KB")
    rpc_connection.settxfee(fee)
    txid = rpc_connection.sendtoaddress(deposit_address, balance, "", "", True)
    conf.set('txid', txid)
else:
    txid = conf.data.txid
    c = coinbase_utils.CoinClient.new(conf)
    # TODO check that getting account objects succeeds
    # TODO track balances
    btc_account = c.get_account(conf.data.btc_account_id)
    usd_account = c.get_account(conf.data.usd_account_id)

if not conf.data.sell_id:
    print(colored("On-blockchain transfer initiated", "green"))
    print("Transaction ID: " + colored(txid, "blue"))
    print("To complete the transfer, 6 confirmations are required.")
    print(colored("This step usually takes less than two hours, "
                  "but sometimes may take as long as a few days.", "cyan"))
    confirmations = 0
    print("Last checked at: " +
          colored("[{}]\n".format(time.strftime('%Y-%m-%d %I:%M:%S %p %Z',
                                                time.localtime())),
                  "yellow"))
    if confirmations > 5:
        color = "green"
    else:
        color = "blue"
    print("Confirmations: " + colored("{}".format(confirmations), color))
          end="",
          flush=True)
    while confirmations < 6:
        r = requests.get("http://blockchain.info/tx/{}?show_adv=false&format=json".format(txid))
        try:
            tx_block_height = r.json()["block_height"]
        except Exception:
            continue
        time.sleep(20)
        current_block_height = int(requests.get("https://blockchain.info/q/getblockcount").text)
        confirmations = current_block_height - tx_block_height + 1
        print("{}Last checked at: ".format("\b" * 50) +
              colored("[{}]\n".format(time.strftime('%Y-%m-%d %I:%M:%S %p %Z',
                                                    time.localtime())),
                      "yellow"))
        if confirmations > 5:
            color = "green"
        else:
            color = "blue"
        print("Confirmations: " + colored("{}".format(confirmations), color))
              end="",
              flush=True)
        time.sleep(20)
        print("\x1b[2A")  # Go up two lines
    print(colored("Transfer transaction confirmation complete", "green"))
    # TODO check coinbase balance here...
    print("Initiating a sale from BTC to USD...")
    time.sleep(30)  # just in case coinbase needs to catch up
    fiat_accounts = [account for account in c.get_payment_methods().data
                     if account.type == 'fiat_account']
    usd_account_payment = [account for account in fiat_accounts
                           if account.fiat_account.id == usd_account.id][0]
    btc_account.refresh()
    sell = btc_account.sell(amount=btc_account.balance.amount,
                            currency=btc_account.balance.currency,
                            payment_method=usd_account_payment.id)
    conf.set("sell_id", sell.id)
else:
    print("Retrieving previous sell information...")
    # TODO check that getting the sell object succeeds
    sell = btc_account.get_sell(conf.data.sell_id)
    # TODO show sell info

print("Waiting for sell completion...")
while sell.status != 'completed':
    sell.refresh()
    print("{}Last checked at: [{}]     Sell status: {}".format(
              "\b"*100,
              time.strftime('%Y-%m-%d %I:%M:%S %p %Z', time.localtime()),
              sell.status),
          end="",
          flush=True)
    time.sleep(10)

if not conf.data.withdrawal_id:
    payment_methods = c.get_payment_methods()
    payment_methods_withdraw = [p for p in payment_methods.data
                                if p.allow_withdraw and p.currency == 'USD']
    payment_method = coinbase_utils.user_choose_payment_method(c)

    print("Withdrawing funds from https://coinbase.com to the linked account...")
    usd_account.refresh()
    withdrawal = c.withdraw(usd_account.id,
                            amount=usd_account.balance.amount,
                            currency=usd_account.balance.currency,
                            payment_method=payment_method.id)
    conf.set("withdrawal_id", withdrawal.id)
else:
    withdrawal = usd_account.get_withdrawal(conf.data.withdrawal_id)

print("Waiting for withdrawal completion...")
while withdrawal.status != 'completed':
    withdrawal.refresh()
    print("{}Last checked at: [{}]     Withdrawal status: {}".format(
              "\b"*100,
              time.strftime('%Y-%m-%d %I:%M:%S %p %Z', time.localtime()),
              withdrawal.status),
          end="",
          flush=True)
    time.sleep(10)

conf.delete('btc_account')
conf.delete('usd_account')
conf.delete('txid')
conf.delete('sell_id')
conf.delete('withdrawal_id')

print(colored("Done", "green"))
