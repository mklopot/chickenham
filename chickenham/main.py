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


print("       ___          _        _   ")
print("      | _ \_ _ ___ (_)___ __| |_ ")
print("      |  _/ '_/ _ \| / -_) _|  _|")
print("      |_| |_| \___// \___\__|\__|")
print("  ___ _    _    _ |__/       _  _ ")
print(" / __| |_ (_)__| |_____ _ _ | || |__ _ _ __  ")
print("| (__| ' \| / _| / / -_) ' \| __ / _` | '  \ ")
print(" \___|_||_|_\__|_\_\___|_||_|_||_\__,_|_|_|_|")

conf = config.Config(Path.home().joinpath('.chiknhamrc'))
if not conf.data.txid or not requests.get(
        "http://blockchain.info/tx/{}?show_adv=false&format=json".format(conf.data.txid)):
    c = coinbase_utils.CoinClient.new(conf)
    btc_account = coinbase_utils.user_choose_confirm(c, 'BTC', 'Bitcoin account')
    try:
        deposit_address = btc_account.create_address().address
    except Exception as e:
        print(colored("Error obtaining deposit address", "red"))
        print(colored(e, "cyan"))
    conf.set('btc_account_id', btc_account.id)
    usd_account = coinbase_utils.user_choose_confirm(c, "USD", 'USD account')
    conf.set('usd_account_id', usd_account.id)
    wif = None
    while not wif:
        inputter = input_shares.UserInput()
        print(chr(27) + "[2J" + chr(27) + "[H")  # Clear Screen
        shares = [share.code for share in inputter.input_batch()]
        combiner = combine.Combiner(len(shares))
        secret = combiner(shares)
        if not secret:
            print(colored("The Shared Codes could not be combined", "red"))
            print("Starting over...")
            continue
        else:
            try:
                private_key = network.keys.private(secret_exponent=int(secret, 16))
                wif = private_key.wif()
            except Exception:
                print(colored("The Shared Codes could not be combined", "red"))
                print("Starting over...")
                continue

    print(colored("Shared Codes successfully combined!", "green"))

    # rpc_user and rpc_password are set in the bitcoin.conf file
    rpc_connection = AuthServiceProxy(
        "http://%s:%s@127.0.0.1:8332" % (conf.data.rpc_user, conf.data.rpc_password),
        timeout=4*60*60)
    # TODO Make sure bitcoind is caught up...
    local_balance_before_import = float(rpc_connection.getbalance())
    print("\nLocal balance before import: " +
          colored("{} BTC".format(local_balance_before_import), "blue"))
    print(colored("\nBeginning key import and block scan", "green"))
    print(colored("The scan may take 3 hours or more.\n", "cyan"))

    def importkey(privkey):
        rpc_connection.importprivkey(privkey)

    scanner_thread = threading.Thread(target=importkey, args=(wif,))
    scanner_thread.start()
    spinner = ["\u25f4 ", "\u25f7 ", "\u25f6 ", "\u25f5 "]
    while scanner_thread.is_alive():
        index = int(time.time() * 8 % len(spinner))
        print("\b"*29 + spinner[index] + colored("  Scanning blocks...   ", "blue"),
              end="",
              flush=True)
        time.sleep(.05)

    balance = round(rpc_connection.getbalance(), 8)
    print(colored("\nScan complete", "green"))
    print("\nLocal balance after import: " + colored("{} BTC".format(balance), "blue"))

    if local_balance_before_import == balance:
        print(colored("No balance detected on this batch of shared codes", "red"))
        if balance > 0:
            print("Proceed with the local balance of " +
                  colored("{} BTC".format(balance), "blue") + "?")
            proceed = input("Proceed (Y/n): ")
            proceed = proceed.lower()
            if proceed[:1] != "y":
                exit(1)
        else:
            print(colored("No local balance detected", "red"))
            print("Cannot proceed...")
            exit(1)
    try:
        r = requests.get("https://bitcoinfees.earn.com/api/v1/fees/recommended")
        # convert to BTC/KB from satoshis/B, and quadruple it, just in case
        fee_recommended = round(r.json()["fastestFee"] * 0.00004, 8)
        fee = min(fee_recommended, 0.003)
    except Exception as e:
        print(colored("Could not retrieve recommended fee", "red"))
        print(colored(e, "cyan"))
        fee = 0.002
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
    print("Confirmations: " + colored("{}".format(confirmations), color),
          end="",
          flush=True)
    print("\x1b[2A")  # Go up two lines
    while confirmations < 6:
        try:
            r = requests.get("http://blockchain.info/tx/{}?show_adv=false&format=json".format(txid))
            tx_block_height = r.json()["block_height"]
        except Exception:
            continue
        time.sleep(20)
        try:
            current_block_height = int(requests.get("https://blockchain.info/q/getblockcount").text)
        except Exception:
            continue
        confirmations = current_block_height - tx_block_height + 1
        print("{}Last checked at: ".format("\b" * 50) +
              colored("{}".format(time.strftime('%Y-%m-%d %I:%M:%S %p %Z',
                                                time.localtime())),
                      "yellow"))
        if confirmations > 5:
            color = "green"
        else:
            color = "blue"
        print("Confirmations: " + colored("{}".format(confirmations), color),
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
    sell = None
    while not sell:
        try:
            sell = btc_account.get_sell(conf.data.sell_id)
        except Exception as e:
            print(colored("Could not retrieve existing SELL info", "red"))
            print(colored(e, "cyan"))
            print(colored("Verify API permissions.", "cyan"))
            retry = input("Retry (y/N): ")
            retry = retry.lower()
            if retry[:1] != "y":
                print(colored("Abandoning workflow", "red"))
                print(colored("You may need to manually log in to ", "cyan") +
                      colored("https://coinbase.com\n", "yellow") +
                      colored("and initiate a withdrawal.", "cyan"))
                conf.delete('btc_account_id')
                conf.delete('usd_account_id')
                conf.delete('txid')
                conf.delete('sell_id')
                conf.delete('withdrawal_id')
                print("Exiting...")
                exit(1)
    # TODO show sell info

print("Waiting for SELL action to complete...")
while sell.status != 'completed':
    sell.refresh()
    status = sell.status
    if status == "completed":
        color = "green"
    else:
        color = "blue"

    print("{}Last checked at: ".format("\b"*100) +
          colored("{}".format(time.strftime('%Y-%m-%d %I:%M:%S %p %Z',
                                            time.localtime())),
                  "yellow"))
    print("Status: " + colored(status, color))
    time.sleep(10)
    print("\x1b[3A")  # Go up two lines

if not conf.data.withdrawal_id:
    payment_methods = c.get_payment_methods()
    payment_methods_withdraw = [p for p in payment_methods.data
                                if p.allow_withdraw and p.currency == 'USD']
    payment_method = coinbase_utils.user_choose_payment_method(c)

    print("Starting withdrawal of funds from https://coinbase.com to the linked account...")
    usd_account.refresh()
    withdrawal = c.withdraw(usd_account.id,
                            amount=usd_account.balance.amount,
                            currency=usd_account.balance.currency,
                            payment_method=payment_method.id)
    conf.set("withdrawal_id", withdrawal.id)
else:
    print("Attempting to load existing withdrawal info")
    try:
        withdrawal = usd_account.get_withdrawal(conf.data.withdrawal_id)
    except Exception as e:
        print(colored("Error loading withdrawal info", "red"))
        print(colored(e, "cyan"))
        print(colored("To track the withdrawal, log on to ", "cyan") +
              colored("https://coinbase.com", "yellow"))
        conf.delete('btc_account_id')
        conf.delete('usd_account_id')
        conf.delete('txid')
        conf.delete('sell_id')
        conf.delete('withdrawal_id')
        print("Exiting...")
        exit(1)

print("Waiting for withdrawal completion...")
while withdrawal.status != 'completed':
    withdrawal.refresh()
    status = withdrawal.status
    if status == "completed":
        color = "green"
    else:
        color = "blue"
    print("{}Last checked at: ".format("\b" * 50) +
          colored("{}".format(time.strftime('%Y-%m-%d %I:%M:%S %p %Z',
                                            time.localtime())),
                  "yellow"))
    print("Status: " + colored(status, color))
    time.sleep(10)
    print("\x1b[3A")  # Go up two lines

conf.delete('btc_account_id')
conf.delete('usd_account_id')
conf.delete('txid')
conf.delete('sell_id')
conf.delete('withdrawal_id')

print(colored("Done", "green"))
