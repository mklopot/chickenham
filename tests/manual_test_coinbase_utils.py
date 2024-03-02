#!/usr/bin/env python3
from chickenham import coinbase_utils
from unittest import TestCase


class Balance:
    def __init__(self, amount, currency):
        self.amount = amount
        self.currency = currency


class Account:
    def __init__(self, name, balance):
        self.name = name
        self.balance = balance
        self.currency = balance.currency


class PaymentMethod:
    def __init__(self, name, currency, allow_withdraw=True):
        self.name = name
        self.currency = currency
        self.allow_withdraw = allow_withdraw


class Data:
    def __init__(self, data):
        self.data = data


class Client:
    def __init__(self, accounts, payment_methods):
        self.accounts = accounts
        self.payment_methods = payment_methods

    def get_payment_methods(self):
        return Data(self.payment_methods)

    def get_accounts(self):
        return Data(self.accounts)


class TestInteractiveOneOption(TestCase):
    def setUp(self):
        print("*** One Option Test ***")
        self.c = Client([Account("My Wallet", Balance(12.33, "BTC")),
                         Account("Cash Money", Balance(0.01, "USD"))],
                        [PaymentMethod("My Cool Bank ****1027", "USD"),
                         PaymentMethod("Swiss Bank", "CHF"),
                         PaymentMethod("No Withdrawal Bank", "USD", False)])

    def test_user_choose_confirm_one_USD(self):
        result = coinbase_utils.user_choose_confirm(self.c, "USD")
        self.assertEqual(result.name, "Cash Money")

    def test_user_choose_confirm_one_BTC(self):
        result = coinbase_utils.user_choose_confirm(self.c, "BTC")
        self.assertEqual(result.name, "My Wallet")

    def test_user_choose_payment_method(self):
        result = coinbase_utils.user_choose_payment_method(self.c)
        self.assertEqual(result.name, "My Cool Bank ****1027")


class TestInteractiveMultiOption(TestCase):
    def setUp(self):
        print("*** Multi Option Test ***")
        self.c = Client([Account("My Wallet", Balance(12.33, "BTC")),
                         Account("Don't Choose Me Wallet", Balance(2.330921, "BTC")),
                         Account("Account of Failed Unit Tests ****3211", Balance(-20.00, "USD")),
                         Account("Cash Money", Balance(0.01, "USD"))],
                        [PaymentMethod("My Cool Bank ****1027", "USD"),
                         PaymentMethod("Don't Choose Me ****4021", "USD"),
                         PaymentMethod("Swiss Bank", "CHF"),
                         PaymentMethod("No Withdrawal Bank", "USD", False)])

    def test_user_choose_confirm_one_USD(self):
        result = coinbase_utils.user_choose_confirm(self.c, "USD")
        self.assertEqual(result.name, "Cash Money")

    def test_user_choose_confirm_one_BTC(self):
        result = coinbase_utils.user_choose_confirm(self.c, "BTC")
        self.assertEqual(result.name, "My Wallet")

    def test_user_choose_payment_method(self):
        result = coinbase_utils.user_choose_payment_method(self.c)
        self.assertEqual(result.name, "My Cool Bank ****1027")
