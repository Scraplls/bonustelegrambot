import os
import sqlite3

from datetime import datetime


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
VITA_DB = os.path.join(ROOT_DIR, 'db\\bonus.db')


class Profile:
    """
    Class to represent profile in the telegram bot.
    All data from it's object will store in the db
    :parameter chat_id : chat_id in telegram
    """

    def __init__(self, chat_id, flood_count, last_msg_date, balance, deposit_sum, banned, flood):
        self.id = chat_id
        self.flood_count = flood_count
        self.last_msg_date = last_msg_date
        self.balance = balance
        self.deposit_sum = deposit_sum
        self.banned = banned
        self.flood = flood

    def __str__(self):
        return "[id: {}, flood_count: {}, last_msg_date: {}, balance: {}, deposit_sum: {}, banned: {}, flood: {}]" \
            .format(self.id, self.flood_count, self.last_msg_date, self.balance, self.deposit_sum, self.banned,
                    self.flood)


class Bill:

    def __init__(self, chat_id, date_from):
        self.chat_id = chat_id
        self.date_from = date_from

    def __str__(self):
        return "[chat_id: {}, date_from: {}]".format(self.chat_id, self.date_from)


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


class DB:

    def __init__(self):
        self.connection = sqlite3.connect(database=VITA_DB, check_same_thread=False)
        self.connection.row_factory = dict_factory
        self.cur = self.connection.cursor()

    def add_profile(self, profile):
        if self.get_profile(profile.id) is None:
            self.cur.execute("INSERT INTO profiles "
                             "(id, last_msg_date, balance, deposit_sum, banned) "
                             "VALUES ({}, '{}', {}, {}, {})"
                             .format(profile.id, profile.last_msg_date, profile.balance,
                                     profile.deposit_sum, profile.banned))
            self.connection.commit()
            return 1
        self.cur.execute("UPDATE profiles "
                         "SET last_msg_date = '{}', balance = {}, deposit_sum = {}, banned = {} "
                         "WHERE id = {}"
                         .format(profile.last_msg_date, profile.balance,
                                 profile.deposit_sum, profile.banned, profile.id))
        self.connection.commit()
        return 0

    def get_profile(self, chat_id):
        self.cur.execute("SELECT * FROM profiles WHERE id = {}".format(chat_id))
        return self.cur.fetchone()

    def delete_profile(self, chat_id):
        self.cur.execute("DELETE FROM profiles WHERE id = {}".format(chat_id))
        self.connection.commit()

    def get_profiles(self):
        self.cur.execute("SELECT * FROM profiles")
        return self.cur.fetchall()

    def load_profiles(self):
        rows = self.get_profiles()
        profiles = dict()
        for row in rows:
            profile = Profile(
                chat_id=row.get('id'),
                flood_count=0,
                last_msg_date=row.get('last_msg_date'),
                balance=row.get('balance'),
                deposit_sum=row.get('deposit_sum'),
                banned=row.get('banned'),
                flood=False
            )
            profiles.update({row.get('id'): profile})
        return profiles

    def save_profiles(self, profiles):
        added = 0
        for profile in profiles.values():
            added += self.add_profile(profile)
        return added

    def insert_product(self, product_id, active, balance, number, card):
        self.cur.execute("INSERT INTO products (id, active, balance, num, card, price) values ({}, {}, {}, {}, {}, {})"
                         .format(product_id, active, balance, number, card, str(int(balance) / 2)))

    def insert_products(self, reg_path):
        cards = open(reg_path, mode='r')
        index = 0
        for line in cards:
            index += 1
            data = line.split(":")
            self.insert_product(index, int(data[3]), int(data[2]), data[0], data[1])
            self.connection.commit()
        cards.close()
        return index

    def get_product_list(self):
        self.cur.execute("SELECT id, active, balance, price FROM products")
        return self.cur.fetchall()

    def get_active_products(self):
        self.cur.execute("SELECT id, balance, price FROM products WHERE active = 1")
        return self.cur.fetchall()

    def get_inactive_products(self):
        self.cur.execute("SELECT id, balance, price FROM products WHERE active = 0")
        return self.cur.fetchall()

    def get_product(self, product_id):
        self.cur.execute("SELECT * FROM products WHERE id = {}".format(product_id))
        return self.cur.fetchone()

    def get_price(self, product_id):
        self.cur.execute("SELECT price FROM products WHERE id = {}".format(product_id))
        return self.cur.fetchone().get('price')

    def delete_product(self, product_id):
        self.cur.execute("DELETE FROM products WHERE id = {}".format(product_id))
        self.connection.commit()

    def add_bill(self, bill):
        if self.get_bill(bill.chat_id) is None:
            self.cur.execute("INSERT INTO bills (id, date_from) values ({}, '{}')"
                             .format(bill.chat_id, bill.date_from))
            self.connection.commit()
        else:
            self.cur.execute("UPDATE bills "
                             "SET date_from = '{}' "
                             "WHERE id = {}"
                             .format(bill.date_from, bill.chat_id))
            self.connection.commit()

    def get_bills(self):
        self.cur.execute("SELECT * FROM bills")
        return self.cur.fetchall()

    def get_bill(self, chat_id):
        self.cur.execute("SELECT * FROM bills WHERE id = {}".format(chat_id))
        return self.cur.fetchone()

    def load_bills(self):
        rows = self.get_bills()
        bills = dict()
        for row in rows:
            bill = Bill(
                chat_id=row.get('id'),
                date_from=datetime.strptime(row.get('date_from'), "%Y-%m-%d %H:%M:%S.%f")
            )
            bills.update({row.get('id'): bill})
        return bills

    def save_bills(self, bills):
        for bill in bills.values():
            self.add_bill(bill)

    def disconnect(self):
        self.connection.close()
