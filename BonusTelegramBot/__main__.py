"""
bonusTelegramBot v0.1
E-Commerce bot
Author: @scraplls
"""

import os
import datetime
import logging
import time
import traceback

import telebot
import qiwihandler
import bonusdb
import product_hatch

from threading import Thread
from telebot import types
from random import random
from datetime import datetime
from bonusdb import Bill


def initialize_logger(output_dir):
    logger = logging.getLogger()

    # create error file handler and set level to error
    handler = logging.FileHandler(os.path.join(output_dir, "error.log"), "a", encoding="utf-8")
    handler.setLevel(logging.ERROR)
    formatter = logging.Formatter("%(asctime)s %(threadName)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # create debug file handler and set level to debug
    handler = logging.FileHandler(os.path.join(output_dir, "logger.log"), "a", encoding="utf-8")
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s %(threadName)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


# settings
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
initialize_logger(ROOT_DIR)
HATCH_DIR = os.path.join(ROOT_DIR, 'hatch\\')
REG_PATH = os.path.join(ROOT_DIR, 'reg_products.txt')
BOT_TOKEN = 'some_token'
db = bonusdb.DB()


console_menu_file = open(file=os.path.join(ROOT_DIR, 'resource\\console_menu.txt'), mode='r', encoding='utf-8')
console_menu_txt = ""
for console_menu_line in console_menu_file:
    console_menu_txt += console_menu_line
console_menu_file.close()

# welcome settings
welcome_file = open(file=os.path.join(ROOT_DIR, 'resource\\welcome.txt'), mode='r', encoding='utf-8')
welcome = ""
for welcome_line in welcome_file:
    welcome += welcome_line
welcome_file.close()

# rules settings
rules_file = open(file=os.path.join(ROOT_DIR, 'resource\\rules.txt'), mode='r', encoding='utf-8')
rules = ""
for rules_line in rules_file:
    rules += rules_line
rules_file.close()

profile_file = open(file=os.path.join(ROOT_DIR, 'resource\\profile.txt'), mode='r', encoding='utf-8')
profile_s = ""
for profile_line in profile_file:
    profile_s += profile_line
profile_file.close()

pay_msg_file = open(file=os.path.join(ROOT_DIR, 'resource\\pay_msg.txt'), mode='r', encoding='utf-8')
pay_msg = ""
for pay_msg_line in pay_msg_file:
    pay_msg += pay_msg_line
pay_msg_file.close()

product_list_t = "➖➖➖Shop - {} products➖➖➖\n"
product_info_t = "{} бонусов | Цена: {} руб | ID  товара: {}\n"

bot = telebot.TeleBot(BOT_TOKEN, threaded=True)

# Main menu keyboard settings
main_menu_keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
buy_button = types.KeyboardButton("Купить💰")
product_list_button = types.KeyboardButton("Наличие товаров")
profile_button = types.KeyboardButton("Личный кабинет👤")
balance_button = types.KeyboardButton("Баланс💵")
rules_button = types.KeyboardButton("Правила📜")
main_menu_keyboard.add(buy_button, product_list_button, profile_button, balance_button, rules_button)
main_menu_button = types.KeyboardButton("↪️Вернуться в главное меню↩️")
return_to_menu_keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
return_to_menu_keyboard.add(main_menu_button)
# Balance keyboard settings
balance_keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
deposit_button = types.KeyboardButton("Пополнить баланс➕")
balance_keyboard.add(deposit_button, main_menu_button)
# Buy keyboard settings
buy_keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
buy_active_button = types.KeyboardButton("Активные🟩")
buy_inactive_button = types.KeyboardButton("Неактивные🟦")
buy_keyboard.add(buy_active_button, buy_inactive_button, main_menu_button)
confirm_buy_keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
confirm_button = types.KeyboardButton("Подтвердить✅")
back_button = types.KeyboardButton("🔙Назад")
cancel_button = types.KeyboardButton("Отмена❌")
confirm_buy_keyboard.add(confirm_button, cancel_button)


profiles = dict()

MAX_FLOOD_COUNT = 10
MAX_FLOOD_DELAY = 5
FLOOD_DURATION = 300


# get random line from file
def random_line(file):
    lines = file.readlines()
    random_int = random.randint(0, len(lines) - 1)
    return lines[random_int]


# logs into console (Level=INFO)
def log(msg):
    logging.info(msg)


def update_last_msg(profile):
    last_msg_time = datetime.strptime(profile.last_msg_date, '%Y-%m-%d %H:%M:%S.%f').timestamp()
    now_date = datetime.now()
    now_time = now_date.timestamp()
    delay = now_time - last_msg_time
    if delay < MAX_FLOOD_DELAY:
        profile.flood_count += 1
    else:
        profile.flood_count = 1
    profile.last_msg_date = now_date.__str__()


def check_last_msg(profile):
    last_msg_time = datetime.strptime(profile.last_msg_date, '%Y-%m-%d %H:%M:%S.%f').timestamp()
    now_date = datetime.now()
    now_time = now_date.timestamp()
    delay = now_time - last_msg_time
    if delay >= FLOOD_DURATION:
        profile.flood_count = 0
        profile.flood = False


@bot.message_handler(commands=['start'])
def handle_start(message):
    profile_id = message.from_user.id
    profile = profiles.get(profile_id)
    if profile is None:
        profiles.update({profile_id: bonusdb.Profile(profile_id, 0, datetime.now().__str__(), 0, 0, 0, 0)})
        bot.send_message(profile_id, welcome, reply_markup=main_menu_keyboard)
    elif profile.banned:
        bot.send_message(profile_id, "Вы были заблокированы.")
    elif profile.flood:
        check_last_msg(profile)
        bot.send_message(profile_id, "Вы пока не можете отправлять сообщения. Причина: Флуд")
    else:
        if profile.flood_count > MAX_FLOOD_COUNT:
            profile.flood = True
            log('Профиль ID:{}@{} получил флуд'.format(profile.id, message.from_user.first_name))
        else:
            update_last_msg(profile)
            bot.send_message(message.from_user.id, "Воспользуйтесь клавиатурой.",
                             reply_markup=return_to_menu_keyboard)


@bot.message_handler(content_types=['text'])
def handle_main_menu(message):
    profile_id = message.from_user.id
    profile = profiles.get(profile_id)
    if profile is not None:
        if profile.banned:
            bot.send_message(profile_id, "Вы были заблокированы.")
        elif profile.flood:
            check_last_msg(profile)
            bot.send_message(profile_id, "Вы пока не можете отправлять сообщения. Причина: Флуд")
        else:
            if profile.flood_count > MAX_FLOOD_COUNT:
                profile.flood = True
                log('Профиль ID:{}@{} получил флуд'.format(profile.id, message.from_user.first_name))
            else:
                update_last_msg(profile)
                if message.text == "Правила📜":
                    bot.send_message(message.from_user.id, rules, reply_markup=main_menu_keyboard)
                elif message.text == "↪️Вернуться в главное меню↩️":
                    bot.send_message(message.from_user.id, "Главное меню", reply_markup=main_menu_keyboard)
                elif message.text == "Баланс💵":
                    # request in the db about user balance
                    balance = profile.balance
                    bot.send_message(message.from_user.id, "Ваш баланc: {} руб.".format(str(balance)),
                                     reply_markup=balance_keyboard)
                elif message.text == "Личный кабинет👤":
                    # request in the db about user data
                    msg = profile_s \
                        .replace('%id%', str(profile.id)) \
                        .replace('%name%', message.from_user.first_name) \
                        .replace('%bal%', str(profile.balance)) \
                        .replace('%dep%', str(profile.deposit_sum))
                    bot.send_message(message.from_user.id, msg, reply_markup=main_menu_keyboard)
                elif message.text == "Наличие товаров":
                    # request in the db about product list
                    msg = ''
                    msg += product_list_t.format('активные')
                    for active in db.get_active_products():
                        balance = active.get('balance')
                        price = active.get('price')
                        msg += product_info_t.format(str(balance), str(price), str(active.get('id')))
                    msg += product_list_t.format('неактивные')
                    for inactive in db.get_inactive_products():
                        balance = inactive.get('balance')
                        price = inactive.get('price')
                        msg += product_info_t.format(str(balance), str(price), str(inactive.get('id')))
                    bot.send_message(message.from_user.id, msg, reply_markup=main_menu_keyboard)
                elif message.text == "Пополнить баланс➕":
                    # bill user
                    comment = message.from_user.id
                    pay_url = qiwihandler.get_bill(comment)
                    qiwihandler.bills.update({str(profile_id): Bill(str(profile_id), datetime.now())})
                    msg = pay_msg.format(qiwihandler.number, comment)
                    pay_keyboard = types.InlineKeyboardMarkup()
                    pay_btn = types.InlineKeyboardButton(text='Пополнить баланс', url=pay_url)
                    pay_keyboard.add(pay_btn)
                    bot.send_message(message.from_user.id, msg, reply_markup=main_menu_keyboard)
                    bot.send_message(message.from_user.id, "Для пополнения баланса нажмите кнопку ниже🔽",
                                     reply_markup=pay_keyboard)
                elif message.text == "Купить💰":
                    msg = bot.send_message(message.from_user.id, "Выберите категорию", reply_markup=buy_keyboard)
                    bot.register_next_step_handler(msg, handle_buy)
                else:
                    bot.send_message(message.from_user.id, "Воспользуйтесь клавиатурой.",
                                     reply_markup=return_to_menu_keyboard)


def handle_buy(message):
    # request in the db about product list and make from it keyboard buttons
    buy_products_keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
    buy_products_keyboard.add(back_button)
    if message.text == "Активные🟩":
        # request in the db about active products
        # loop to make keyboard buttons
        for active in db.get_active_products():
            balance = active.get('balance')
            price = active.get('price')
            product_button = types.KeyboardButton(product_info_t.format(str(balance), str(price), str(active.get('id'))))
            buy_products_keyboard.add(product_button)
        msg = bot.send_message(message.from_user.id, "Выберите товар", reply_markup=buy_products_keyboard)
        bot.register_next_step_handler(msg, handle_buy_product)
    elif message.text == "Неактивные🟦":
        # request in the db about inactive products
        # loop to make keyboard buttons
        for inactive in db.get_inactive_products():
            balance = inactive.get('balance')
            price = inactive.get('price')
            product_button = types.KeyboardButton(product_info_t.format(str(balance), str(price), str(inactive.get('id'))))
            buy_products_keyboard.add(product_button)
        msg = bot.send_message(message.from_user.id, "Выберите товар", reply_markup=buy_products_keyboard)
        bot.register_next_step_handler(msg, handle_buy_product)
    elif message.text == "↪️Вернуться в главное меню↩️":
        bot.send_message(message.from_user.id, "Главное меню", reply_markup=main_menu_keyboard)
    else:
        bot.send_message(message.from_user.id, "Воспользуйтесь клавиатурой.", reply_markup=return_to_menu_keyboard)


def handle_buy_product(message):
    if message.text == "🔙Назад":
        msg = bot.send_message(message.from_user.id, "Выберите категорию", reply_markup=buy_keyboard)
        bot.register_next_step_handler(msg, handle_buy)
    else:
        # some security logic
        product_args = str(message.text).split('|')
        if len(product_args) == 3:
            if len(product_args[2].split(':')) == 2:
                product_id = product_args[2].split(':')[1].replace(' ', '')
                if str.isnumeric(product_id):
                    msg = bot.send_message(message.from_user.id, "Подтвердите покупку",
                                           reply_markup=confirm_buy_keyboard)
                    price = db.get_price(product_id)
                    bot.register_next_step_handler(msg, handle_buy_confirm, args=[product_id, price])
                else:
                    bot.send_message(message.from_user.id, "Воспользуйтесь клавиатурой.",
                                     reply_markup=return_to_menu_keyboard)
            else:
                bot.send_message(message.from_user.id, "Воспользуйтесь клавиатурой.",
                                 reply_markup=return_to_menu_keyboard)
        else:
            bot.send_message(message.from_user.id, "Воспользуйтесь клавиатурой.",
                             reply_markup=return_to_menu_keyboard)


def handle_buy_confirm(message, args):
    profile_id = message.from_user.id
    if message.text == "Отмена❌":
        bot.send_message(profile_id, "Вы отменили покупку. Возврат в главное меню",
                         reply_markup=main_menu_keyboard)
    elif message.text == "Подтвердить✅":
        # check in the db if profile and product_id exists
        profile = profiles.get(profile_id)
        if len(args) == 2 and profile is not None:
            product_id = args[0]
            price = args[1]
            new_balance = int(profile.balance) - int(price)
            new_deposit_sum = int(profile.deposit_sum) + int(price)
            if new_balance >= 0:
                # request in the db to check if the product exists
                product = db.get_product(product_id)
                if product is not None:
                    # delete product from db
                    db.delete_product(product_id)
                    # change user balance in db
                    profile.balance = new_balance
                    profile.deposit_sum = new_deposit_sum
                    # send a product
                    bot.send_message(profile_id, "Покупка завершена. ID товара: {}. Номер +{}"
                                     .format(product_id, product.get('num')),
                                     reply_markup=main_menu_keyboard)
                    hatch_path = os.path.join(HATCH_DIR, '{}.jpg'.format(product.get('product')))
                    if os.path.isfile(hatch_path):
                        hatch = open(hatch_path, 'rb')
                        bot.send_photo(profile_id, hatch)
                        hatch.close()
                        os.remove(hatch_path)
                    log("ID:{}:@{} купил товар {}".format(profile_id, message.from_user.first_name, product))
                else:
                    bot.send_message(profile_id, "Товар больше не действителен. Вернитесь в главное меню",
                                     reply_markup=return_to_menu_keyboard)
            else:
                bot.send_message(profile_id, "У вас недостаточно средств.",
                                 reply_markup=return_to_menu_keyboard)
    else:
        bot.send_message(profile_id, "Воспользуйтесь клавиатурой.", reply_markup=return_to_menu_keyboard)


class MenuThread(Thread):

    def __init__(self):
        """MenuThread initializer"""
        Thread.__init__(self)
        self.stop = False

    def run(self):
        """Thread start"""
        time.sleep(5)
        print(console_menu_txt)
        while not self.stop:
            msg = input().split(' ')
            msg_count = len(msg)
            if msg_count != 0:
                cmd = msg[0]
                args = None
                if msg_count > 1:
                    args = msg[1:]
                if cmd == "/stop":
                    self.stop = True
                    log("Остановка бота...")
                    bot.stop_bot()
                elif cmd == "/usage":
                    pass
                else:
                    if args is not None:
                        if cmd == "/block":
                            if len(args) == 1:
                                profile = profiles.get(int(args[0]))
                                if profile is not None:
                                    profile.banned = 1
                                    log("Профиль ID:{} забанен.".format(args[0]))
                                else:
                                    log("Ошибка! Профиль ID:{} не найден!".format(args[0]))
                        elif cmd == "/unblock":
                            if len(args) == 1:
                                profile = profiles.get(int(args[0]))
                                if profile is not None:
                                    profile.banned = 0
                                    log("Профиль ID:{} разбанен.".format(args[0]))
                                else:
                                    log("Ошибка! Профиль ID:{} не найден!".format(args[0]))
                        elif cmd == "/getprofile":
                            if len(args) == 1:
                                if args[0] == '*':
                                    for profile in profiles.values():
                                        log(profile)
                                else:
                                    profile = profiles.get(int(args[0]))
                                    if profile is not None:
                                        log(profile)
                                    else:
                                        log("Ошибка! Профиль ID:{} не найден!".format(args[0]))
                        elif cmd == "/setbalance":
                            if len(args) == 2:
                                profile = profiles.get(int(args[0]))
                                value = args[1]
                                if profile is not None and str.isnumeric(value):
                                    profile.balance = value
                                    log("Баланс профиля ID:{} был успешно изменен.".format(args[0]))
                                    bot.send_message(profile.id,
                                                     "Ваш баланс был изменен. Баланс: {} руб.".format(str(value)))
                                else:
                                    log("Ошибка! Профиль ID:{} не найден!".format(args[0]))
                        elif cmd == "/getbills":
                            bills = qiwihandler.bills.values()
                            for bill in bills:
                                log(bill)
                        elif cmd == "/sendmsg":
                            if len(args) >= 2:
                                msg = ""
                                for word in args[1:]:
                                    msg += word + " "
                                msg.strip()
                                if args[0] == '*':
                                    for profile in profiles.values():
                                        bot.send_message(profile.id, msg)
                                    log("Сообщение успешно отправлено всем профилям.")
                                else:
                                    profile = profiles.get(int(args[0]))
                                    if profile is not None:
                                        bot.send_message(profile.id, msg)
                                        log("Сообщение успешно отправлено профилю ID:{}.".format(args[0]))
                                    else:
                                        log("Ошибка! Профиль ID:{} не найден!".format(args[0]))
                    else:
                        log("Команда не найдена.")


def load_products():
    loaded = 0
    if os.path.isfile(REG_PATH):
        loaded = db.insert_products(REG_PATH)
        product_hatch.insert_hatches(REG_PATH)
        os.remove(REG_PATH)
    return loaded


def main():
    menu_thread = MenuThread()
    qiwi_handler_thread = qiwihandler.QiwiHandlerThread(profiles, bot)
    try:
        log("Enabling bonusTelegramBot...")
        log("Loading bonusTelegramBot profiles...")
        profiles.update(db.load_profiles())
        log("bonusTelegramBot {} profiles loaded.".format(len(profiles)))
        log("Loading bonusTelegramBot products...")
        loaded = load_products()
        log("bonusTelegramBot {} products loaded.".format(loaded))
        log("Enabling QiwiHandler...")
        qiwihandler.bills = db.load_bills()
        qiwi_handler_thread.start()
        log("QiwiHandler enabled.")
        menu_thread.start()
        log("bonusTelegramBot enabled.")
        bot.polling()
    except BaseException:
        logging.error("bonusTelegramBot got exception!")
        track = traceback.format_exc()
        logging.error(track)
    finally:
        log("Disabling bonusTelegramBot...")
        menu_thread.stop = True
        log("Disabling QiwiHandler...")
        db.save_bills(qiwihandler.bills)
        qiwi_handler_thread.stop = True
        log("QiwiHandler disabled.")
        log("Saving bonusTelegramBot profiles...")
        added = db.save_profiles(profiles)
        db.disconnect()
        log("bonusTelegramBot {} profiles saved.".format(added))
        log("bonusTelegramBot disabled.")


if __name__ == '__main__':
    main()
