#!/usr/bin/env python3

from pathlib import Path

import requests
# from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from bitcoinrpc.authproxy import AuthServiceProxy
from termcolor import colored

import cli
import coinbase_utils
import config
import workflow_utils
from connectivity import connectivity_check

cli.greeting()
cli.notify_until(connectivity_check, "Connect to the Internet to continue (or press Ctrl-C to exit)")

conf = config.Config(Path.home().joinpath('.chickenhamrc'))

if not conf.data.txid or not requests.get(
        "http://blockchain.info/tx/{}?show_adv=false&format=json".format(conf.data.txid),
        timeout=60):
    deposit_address = workflow_utils.get_exchange_accounts(conf)

    # WIF stands for "Wallet Input Format" for secret keys
    wif = workflow_utils.get_wif()

    # rpc_user and rpc_password are set in the bitcoin.conf file
    rpc_connection = AuthServiceProxy(
        "http://%s:%s@127.0.0.1:8332" % (conf.data.rpc_user, conf.data.rpc_password),
        timeout=4*60*60)

    local_balance_before_import, balance = workflow_utils.get_balances(rpc_connection, wif)
    workflow_utils.send_tx(conf, deposit_address, rpc_connection, local_balance_before_import, balance)
else:
    txid = conf.data.txid
    c = coinbase_utils.CoinClient.new(conf)
    # TODO check that getting account objects succeeds
    # TODO track balances
    btc_account = None
    usd_account = None
    while not btc_account or not usd_account:
        try:
            btc_account = c.get_account(conf.data.btc_account_id)
            usd_account = c.get_account(conf.data.usd_account_id)
        except Exception as e:
            print(colored("Error referencing previously used BTC or USD "
                          "account on https://coinbase.com", "red"))
            print(colored(e, "cyan"))
            print("Check API permissions and retry, or log on to " +
                  colored("https://coinbase.com", "yellow") +
                  " and manually complete the sell and withdraw.")
            retry = input("Retry (y/N): ")
            retry = retry.lower()
            if retry[:1] == "y":
                continue
            workflow_utils.reset_state(conf)
            print("Exiting...")
            exit(1)

workflow_utils.wait_for_tx_confirmations(txid)

if not conf.data.sell_id:
    sell = workflow_utils.sell_for_fiat(conf, txid, c, btc_account, usd_account)
    conf.set("sell_id", sell.id)
else:
    sell = workflow_utils.get_sell_info(conf, btc_account)

workflow_utils.wait_for_sell_complete(sell)

if not conf.data.withdrawal_id:
    withdrawal = workflow_utils.withdraw_fiat(c, usd_account)
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
        workflow_utils.reset_state(conf)
        print("Exiting...")
        exit(1)

workflow_utils.wait_for_withdrawal_complete(withdrawal)
workflow_utils.reset_state(conf)
print(colored("Done", "green"))
