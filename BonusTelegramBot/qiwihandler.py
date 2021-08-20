"""
Qiwi Handler
Handles all incoming payments
"""

import logging
import os
import time
import pyqiwi

from threading import Thread
from datetime import datetime


logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)


# logs into console (Level=INFO)
def log(msg):
    logging.info(msg)


bills = dict()

number = 'some_number'

wallet = pyqiwi.Wallet(token='some_token', number=number)


def get_bill(comment):
    return 'https://qiwi.com/payment/form/99?extra%5B%27account%27%5D={}&currency=643&comment={}&amountInteger=100&amountFraction=0&blocked%5B0%5D=account&blocked%5B1%5D=comment'\
            .format(number, comment)


class QiwiHandlerThread(Thread):

    def __init__(self, profiles, bot):
        """QiwiHandler initializer"""
        Thread.__init__(self)
        self.stop = False
        self.profiles = profiles
        self.bot = bot

    def run(self):
        """Thread start"""
        while not self.stop:
            date_now = datetime.now()
            transaction_list = wallet.history(operation='IN', end_date=date_now).get(
                'transactions')
            for transaction in transaction_list:
                comment = transaction.comment
                if comment is not None:
                    bill = bills.get(comment)
                    if bill is not None:
                        if comment == bill.chat_id:
                            if transaction.date.timestamp() >= bill.date_from.timestamp():
                                # make request in the db and change user balance
                                bill.date_from = date_now
                                profile = self.profiles.get(int(bill.chat_id))
                                if profile is not None:
                                    if transaction.sum is not None:
                                        profile.balance += transaction.sum.amount
                                        log("ID:{} пополнил баланс на {} руб.".format(bill.chat_id,
                                                                                      str(transaction.sum.amount)))
                                        self.bot.send_message(bill.chat_id, "Ваш баланс пополнен на {} руб.".format(
                                            str(transaction.sum.amount)))
            time.sleep(10)
