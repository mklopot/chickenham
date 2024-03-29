import threading
import time

import requests
from pycoin.symbols.btc import network
from termcolor import colored

import bitcoin_utils
import cli
import coinbase_utils
import combine
import input_shares


def get_exchange_accounts(conf):
    c = coinbase_utils.CoinClient.new(conf)
    btc_account = coinbase_utils.user_choose_confirm(c, 'BTC', 'Bitcoin account')
    try:
        deposit_address = btc_account.create_address().address
    except Exception as e:
        print(colored("Error obtaining deposit address", "red"))
        print(colored(e, "cyan"))
        exit(1)
    conf.set('btc_account_id', btc_account.id)
    usd_account = coinbase_utils.user_choose_confirm(c, "USD", 'USD account')
    conf.set('usd_account_id', usd_account.id)
    return deposit_address


def get_wif():
    wif = None
    while not wif:
        inputter = input_shares.UserInput()
        cli.clear_screen()
        shares = [share.code for share in inputter.input_batch()]
        combiner = combine.Combiner(len(shares))
        cli.clear_screen()
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
    return wif


def get_balances(rpc_connection, wif):
    # TODO Make sure bitcoind is caught up...
    local_balance_before_import = float(rpc_connection.getbalance())
    print("\nLocal balance before import: " +
          colored("{:.8f} BTC".format(local_balance_before_import), "blue"))
    print(colored("\nBeginning key import and block scan", "green"))
    print(colored("The scan may take 3 hours or more.\n", "cyan"))

    scanner_thread = threading.Thread(target=rpc_connection.importprivkey, args=(wif,))
    scanner_thread.start()
    cli.spinner_notify_while(scanner_thread.is_alive, "Scanning blocks...   ")

    balance = round(rpc_connection.getbalance(), 8)
    print(colored("\nScan complete", "green"))
    print("\nLocal balance after import: " + colored("{:.8f} BTC".format(balance), "blue"))
    return (local_balance_before_import, balance)


def send_tx(conf, deposit_address, rpc_connection, local_balance_before_import, balance):
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
            print("Cannot proceed: nothing to transfer...")
            exit(1)
    try:
        r = requests.get("https://bitcoinfees.earn.com/api/v1/fees/recommended",
                         timeout=60)
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


def get_sell_info(conf, btc_account):
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
                reset_state(conf)
                print("Exiting...")
                exit(1)
    # TODO show sell info
    return sell


def wait_for_tx_confirmations(txid):
    print(colored("On-blockchain transfer initiated", "green"))
    print("Transaction ID: " + colored(txid, "blue"))
    print("To complete the transfer, 6 confirmations are required.")
    print(colored("This step usually takes less than two hours, "
                  "but sometimes may take as long as a few days.", "cyan"))
    confirmations = 0
    print("Last checked at: " +
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
    while confirmations < 6:
        confirmations_query = bitcoin_utils.get_confirmations(txid)
        if confirmations_query:
            confirmations = confirmations_query
        print("\x1b[2A")  # Go up two lines
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
    print(colored("Transfer transaction confirmed on the blockchain", "green"))


def sell_for_fiat(conf, client, btc_account, usd_account):
    # TODO check coinbase balance here...
    print("Initiating a sale from BTC to USD...")
    time.sleep(30)  # just in case coinbase needs to catch up

    fiat_accounts = [account for account in client.get_payment_methods().data
                     if account.type == 'fiat_account']
    usd_account_payment = [account for account in fiat_accounts
                           if account.fiat_account.id == usd_account.id][0]
    btc_account.refresh()
    sell = btc_account.sell(amount=btc_account.balance.amount,
                            currency=btc_account.balance.currency,
                            payment_method=usd_account_payment.id)
    conf.set("sell_id", sell.id)
    return sell


def wait_for_sell_complete(sell):
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
        # Go up two lines
        print("\x1b[3A")


def withdraw_fiat(c, usd_account):
    payment_method = coinbase_utils.user_choose_payment_method(c)
    print("Starting withdrawal of funds from https://coinbase.com to the linked account...")
    usd_account.refresh()
    withdrawal = c.withdraw(usd_account.id,
                            amount=usd_account.balance.amount,
                            currency=usd_account.balance.currency,
                            payment_method=payment_method.id)
    return withdrawal


def reset_state(conf):
    conf.delete('btc_account_id')
    conf.delete('usd_account_id')
    conf.delete('txid')
    conf.delete('sell_id')
    conf.delete('withdrawal_id')


def wait_for_withdrawal_complete(withdrawal):
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
    # Go up two lines
        print("\x1b[3A")
