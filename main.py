from telebot import types
import telebot
from typing import List, Dict
import requests
import json
import re
from datetime import datetime
from datetime import date, timedelta
from telegram_bot_calendar import DetailedTelegramCalendar
import app_logger


def main():

    """ Функция. Начало программы. Тут написан основной код """
    history_list = list()
    # Заполнение списка result_find
    result_find: Dict = dict()

    my_step_time = {'y': 'год', 'm': 'месяц', 'd': 'день'}

    def key_menu(message):
        markup: telebot = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        markup.add(types.KeyboardButton('Главное меню'))
        bot.send_message(message.chat.id, text='Введите название города', reply_markup=markup)

    def back_key(markup):
        markup.add(types.KeyboardButton('Назад'))
        markup.add(types.KeyboardButton('Главное меню'))

    def get_menu(message):
        logger.info("Вызываем меню")

        """ Функция создает в телеграм боте функциональные кнопки меню """
        markup: telebot = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        button_help: telebot = types.KeyboardButton(text='/help')
        button_lowprice: telebot = types.KeyboardButton(text='/lowprice')
        button_highprice: telebot = types.KeyboardButton(text='/highprice')
        button_bestdeal: telebot = types.KeyboardButton(text='/bestdeal')
        button_history: telebot = types.KeyboardButton(text='/history')
        button_sitting: telebot = types.KeyboardButton(text='/setting')
        markup.add(button_lowprice, button_highprice, button_bestdeal, button_history, button_help, button_sitting)
        bot.send_message(message.chat.id, text='Главное меню.\nВыберете команду:', reply_markup=markup)

    def write_json(date_j: requests) -> Dict:
        """
        Создание json файла
        :param date_j: запрос с сайта :requests
        :return: словарь в формате json
        :rtype: json
        """
        date_j: json = json.loads(date_j.text)
        return date_j

    def check_from_to(message: telebot,  func_name) -> bool:
        """
        Функция для поверки и заполнения фильтра команды /bestdeal
        :param message: сообщение из чата телеграмм, расстояние от центра или стоимость аренды: telebot
        :param func_name: имя функции из которой вызывает эта функция: str
        :return: возвращает False или True
        :rtype bool
        :except IndexError если значение до меньше чем значение от, то вызывается исключение
        :except ValueError если знание message не является целым числом, то вызывается исключение
        """
        name_key_dick = func_name[4:]
        if func_name.startswith('get_distance'):
            word_check = 'Радиус'
        else:
            word_check = 'Стоимость за ночь'
        if func_name.endswith('from'):
            from_flag = True
            from_to = 'от'
        else:
            from_flag = False
            from_to = 'до'

        try:
            message_convector = int(message.text)
            try:
                if message_convector >= 0:
                    if from_flag is False and name_key_dick.startswith('distance'):
                        if message_convector < result_find['distance_from']:
                            bot.send_message(message.chat.id,
                                             text=f'<b>Ошибка!!</b>\n{word_check} поиска "до" не может быть меньше '
                                                  f'чем "от"\nВведите {word_check.lower()} {from_to} которого '
                                                  f'искать еще раз', parse_mode='html')
                            raise IndexError
                    elif from_flag is False and name_key_dick.startswith('price'):
                        if message_convector < result_find['price_from']:
                            bot.send_message(message.chat.id,
                                             text=f'<b>Ошибка!!</b>\n{word_check} поиска "до" не может быть меньше '
                                                  f'чем "от"\nВведите {word_check.lower()} {from_to} которого '
                                                  f'искать еще раз', parse_mode='html')
                            raise IndexError
                    result_find[name_key_dick] = message_convector
                    return True

                else:
                    bot.send_message(message.chat.id,
                                     text=f'<b>Ошибка!!</b>\n{word_check} поиска не может быть меньше 0\nВведите '
                                          f'{word_check.lower()} {from_to} которого искать еще раз', parse_mode='html')
                    raise IndexError
            except IndexError:
                return False

        except ValueError:
            bot.send_message(message.chat.id, text=f'<b>Ошибка!!</b>\n{word_check} поиска должен быть числом\n'
                                                   f'Введите {word_check.lower()} {from_to} '
                                                   f'которого искать еще раз:', parse_mode='html')
            return False

    def get_city(message: telebot) -> None:
        """
        Функция проверяет наличие ключа/сообщения из чата в библиотеке locations/search
        :param message: сообщение города из чата телеграмм: telebot
        :except AttributeError: если не находит ключ "moresuggestions" в словаре, то вызывает исключение
        """
        if message.text == 'Главное меню':
            get_menu(message)
        else:
            logger.warning("Записываем в бд язык и волюту")
            result_find['language'] = result_find.get('language', ['ru_RU', 'KM'])
            result_find['currency'] = result_find.get('currency', ['RUB', '₽'])

            url_loc: str = "https://hotels4.p.rapidapi.com/locations/v2/search"
            querystring_loc: Dict = {"query": message.text, "locale": result_find['language'][0],
                                     "currency": result_find['currency'][0]}
            response_loc: requests = requests.request("GET", url_loc, headers=headers, params=querystring_loc)
            date_locations: Dict = write_json(response_loc)
            try:
                if date_locations.get("moresuggestions") > 0:
                    locations_and_id: List = [{''.join(re.sub(r"</span>", '',
                                               ''.join(re.sub(r"<span class='\w+'>", '', date_city["caption"])))):
                                              date_city["destinationId"]} for date_city in
                                              date_locations["suggestions"][0]["entities"]]
                    # Создаем кнопки (Уточнение города поиска)
                    markup: telebot = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
                    for i_dict in locations_and_id:
                        for i_key in i_dict.keys():
                            markup.add(types.KeyboardButton(i_key))
                    back_key(markup)
                    bot.send_message(message.chat.id, 'Выберете город из списка.', reply_markup=markup)
                    bot.register_next_step_handler(message, get_id_and_city, locations_and_id)

                else:
                    bot.send_message(message.chat.id, '<b>Ошибка!!</b>\nВведите название города.', parse_mode='html')
                    bot.register_next_step_handler(message, get_city)
            except AttributeError:
                bot.send_message(message.chat.id, '<b>Ошибка!!</b>\nВведите название города еще раз:',
                                 parse_mode='html')
                bot.register_next_step_handler(message, get_city)

    def get_id_and_city(message: telebot, locations_and_id) -> None:

        """
        :param locations_and_id:
        :param message: сообщение уточнённого города из чата телеграмм: telebot
        """
        logger.info("Вызываем функцию уточнения города")
        locations_and_id = list(locations_and_id)
        # 3 Country
        if message.text in [''.join(i_city) for i_city in [list(locale) for locale in locations_and_id]]:
            logger.warning("Записываем в бд выбранный город")
            result_find['Country'] = message.text
            for i_dict in locations_and_id:
                if i_dict.get(message.text) is not None:
                    # 4 DestinationId
                    result_find['DestinationId'] = int(i_dict.get(message.text))
                    break
            if result_find['SortOrder_distance'] is True:
                bot.send_message(message.chat.id, text=f'Искать в радиусе от ({result_find["language"][1]}):',
                             reply_markup=types.ReplyKeyboardRemove())
                bot.register_next_step_handler(message, get_distance_from)

            elif result_find['SortOrder_distance'] is False:
                bot.send_message(message.chat.id, text='Выберете дату заезда:',
                             reply_markup=types.ReplyKeyboardRemove())
                checkIn(message)
            else:
                bot.send_message(message.chat.id, text='<b>Ошибка!!</b>', parse_mode='html')
                get_menu(message)
        elif message.text == 'Назад':
            bot.send_message(message.chat.id, 'Введите название города.', reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(message, get_city)
        elif message.text == 'Главное меню':
            get_menu(message)
        else:
            bot.send_message(message.chat.id, text='<b>Ошибка!!</b>\nВыберете город из списка!', parse_mode='html')
            bot.register_next_step_handler(message, get_id_and_city, locations_and_id)

    def get_distance_from(message: telebot) -> None:

        """ Функция для установления значения от какого радиуса необходимо провести поиск отеля """
        logger.info("Вызываем функцию начального радиуса")

        if message.text == 'Назад':
            bot.send_message(message.chat.id, text='Введите название города:', reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(message, get_city)
        elif message.text == 'Главное меню':
            get_menu(message)
        elif check_from_to(message=message, func_name=get_distance_from.__name__):
            markup: telebot = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            back_key(markup)
            bot.send_message(message.chat.id, text=f'Искать в радиусе до ({result_find["language"][1]}):',
                             reply_markup=markup)
            bot.register_next_step_handler(message, get_distance_to)
        else:
            bot.register_next_step_handler(message, get_distance_from)

    def get_distance_to(message: telebot) -> None:
        """ Функция для установления значения до какого радиуса необходимо провести поиск отеля """
        logger.info("Вызываем функцию конечного радиуса")

        if message.text == 'Назад':
            markup: telebot = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            back_key(markup)
            bot.send_message(message.chat.id, text=f'Искать в радиусе от ({result_find["language"][1]}):',
                             reply_markup=markup)
            bot.register_next_step_handler(message, get_distance_from)
        elif message.text == 'Главное меню':
            get_menu(message)
        elif check_from_to(message=message, func_name=get_distance_to.__name__):
            markup: telebot = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            back_key(markup)
            bot.send_message(message.chat.id, text=f'Искать в стоимости за ночь от ({result_find["currency"][0]}):',
                             reply_markup=markup)
            bot.register_next_step_handler(message, get_price_from)
        else:
            bot.register_next_step_handler(message, get_distance_to)

    def get_price_from(message: telebot) -> None:
        """ Функция для установления значения минимальной стоимости ночи в отеле поиск отеля """
        logger.info("Вызываем функцию начальной стоимости")
        if message.text == 'Назад':
            bot.send_message(message.chat.id, text=f'Искать в радиусе до ({result_find["language"][1]}):')
            bot.register_next_step_handler(message, get_distance_to)
        elif message.text == 'Главное меню':
            get_menu(message)
        elif check_from_to(message=message, func_name=get_price_from.__name__):
            markup: telebot = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            back_key(markup)
            bot.send_message(message.chat.id, text=f'Искать в стоимости за ночь до ({result_find["currency"][0]}):',
                             reply_markup=markup)
            bot.register_next_step_handler(message, get_price_to)

        else:
            bot.register_next_step_handler(message, get_price_from)

    def get_price_to(message: telebot) -> None:
        """ Функция для установления значения максимальной стоимости ночи в отеле поиск отеля"""
        logger.info("Вызываем функцию конечной стоимости")

        if message.text == 'Назад':
            bot.send_message(message.chat.id, text=f'Искать в стоимости за ночь от ({result_find["currency"][0]}):',
                             reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(message, get_price_from)
        elif message.text == 'Главное меню':
            get_menu(message)
        elif check_from_to(message=message, func_name=get_price_to.__name__):
            markup: telebot = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            back_key(markup)
            bot.send_message(message.chat.id, text=f'Выберете дату выезда:', reply_markup=markup)
            checkIn(message)
        else:
            bot.register_next_step_handler(message, get_price_to)

    def checkIn(message: telebot) -> None:
        """
        Функция для получения даты заезда в отель из телеграмм чата при помощи InLineKeyboard
        :param message: сообщение заезда в отель из чата телеграмм: telebot
        """
        logger.info("Вызываем функцию даты заезда")

        calendar, step = DetailedTelegramCalendar(calendar_id=1, min_date=date.today(), locale='ru').build()

        bot.send_message(message.chat.id,
                         f"Выберете {my_step_time[step]}",
                         reply_markup=calendar)

    @bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=1))
    def cal(call):
        result, key, step = DetailedTelegramCalendar(min_date=date.today(),
                                                     locale='ru', calendar_id=1).process(call.data)
        if not result and key:
            bot.edit_message_text(f"Выберете {my_step_time[step]}",
                                  call.message.chat.id,
                                  call.message.message_id,
                                  reply_markup=key)
        elif result:
            bot.edit_message_text(f"Дата заезда: {result}.",
                                  call.message.chat.id,
                                  call.message.message_id)
            bot.send_message(call.message.chat.id, text='Выберете дату выезда:')
            logger.warning("Записываем в бд даты заезда")
            result_find['CheckIn'] = result
            checkOut(call.message)

    def checkOut(message: telebot) -> None:
        """
        Функция для получения даты съезда из отеля из телеграмм чата при помощи InLineKeyboard
        :param message: сообщение выезда из отеля из чата телеграмм: telebot
        """
        logger.info("Вызываем функцию даты выезда")

        calendar, step = DetailedTelegramCalendar(
            calendar_id=2, min_date=result_find.get('CheckIn')+timedelta(days=1), locale='ru').build()
        bot.send_message(message.chat.id,
                         f"Выберете {my_step_time[step]}",
                         reply_markup=calendar)

    @bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=2))
    def cal(call):
        result, key, step = DetailedTelegramCalendar(min_date=result_find['CheckIn']+timedelta(days=1),
                                                     locale='ru', calendar_id=2).process(call.data)
        if not result and key:
            bot.edit_message_text(f"Выберете {my_step_time[step]}",
                                  call.message.chat.id,
                                  call.message.message_id,
                                  reply_markup=key)
        elif result:
            bot.edit_message_text(f"Дата выезда: {result}.",
                                  call.message.chat.id,
                                  call.message.message_id)
            logger.warning("Записываем в бд даты выезда")
            result_find['CheckOut'] = result
            markup: telebot = types.ReplyKeyboardMarkup(resize_keyboard=True). \
                add(*(types.KeyboardButton(str(i_num)) for i_num in range(1, 9)), row_width=4)
            back_key(markup)
            bot.send_message(call.message.chat.id, text='Сколько человек будет проживать(Max 8):',
                             reply_markup=markup)
            bot.register_next_step_handler(call.message, get_resident)

    # get resident
    def get_resident(message):
        """
        Функция для получения значения жильцов в номере отеля
        :param message: сообщение количества жильцов проживающих в отеле из чата телеграмм: telebot
        """
        logger.info("Вызываем функцию числа резидентов")

        if message.text.isdigit() and 9 > int(message.text) > 0:
            # 7 Adults1
            logger.warning("Записываем в бд даты число резидентов")
            result_find['Adults1'] = int(message.text)

            markup: telebot = types.ReplyKeyboardMarkup(resize_keyboard=True).\
                add(*(types.KeyboardButton(str(i_num)) for i_num in range(1, 11)), row_width=5)
            back_key(markup)
            bot.send_message(message.chat.id, text='Сколько отелей показать(max 10)?', reply_markup=markup)
            bot.register_next_step_handler(message, get_count_hotel)

        elif message.text == 'Назад':
            markup: telebot = types.ReplyKeyboardMarkup(resize_keyboard=True)
            back_key(markup)
            bot.send_message(message.chat.id, text='Дата выезда(day.month.year):', reply_markup=markup)
            bot.register_next_step_handler(message, checkOut)

        elif message.text == 'Главное меню':
            get_menu(message)
        else:
            bot.send_message(message.chat.id, f'<b>Ошибка!!</b>\nВведите корректное число жильцов:', parse_mode='html')
            bot.register_next_step_handler(message, get_resident)

    # get_count_hotel
    def get_count_hotel(message: telebot) -> None:
        """
        Функция для получения числа отображаемых в чате отелей
        :param message: сообщение числа отображаемых отелей в результате из чата телеграмм: telebot
        """
        logger.info("Вызываем функцию число отелей")

        if message.text.isdigit() and int(message.text) > 0:
            count_hotel: int = int(message.text)
            if count_hotel >= 10:
                count_hotel: int = 10
            if result_find['SortOrder_distance'] is True:
                result_find['Count_hotel_for'] = count_hotel
                count_hotel = 100
            # 8 Count_hotel
            logger.warning("Записываем в бд число отелей")
            result_find['PageSize'] = int(count_hotel)
            markup: telebot = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            key_yes: telebot = types.KeyboardButton(text='Да')
            key_no: telebot = types.KeyboardButton(text='Нет')
            markup.add(key_yes, key_no)
            back_key(markup)
            bot.send_message(message.chat.id, text='Результат поиска показать с фото?', reply_markup=markup)
            bot.register_next_step_handler(message, get_photo)

        elif message.text == 'Назад':
            markup: telebot = types.ReplyKeyboardMarkup(resize_keyboard=True). \
                add(*(types.KeyboardButton(str(i_num)) for i_num in range(1, 9)), row_width=4)
            back_key(markup)
            bot.send_message(message.chat.id, text='Сколько человек будет проживать(Max 8):', reply_markup=markup)
            bot.register_next_step_handler(message, get_resident)

        elif message.text == 'Главное меню':
            get_menu(message)
        else:
            bot.send_message(message.chat.id, '<b>Ошибка!!</b>\nВведите корректное число отелей(Max 10):',
                             parse_mode='html')
            bot.register_next_step_handler(message, get_count_hotel)

    # get_photo
    def get_photo(message: telebot) -> None:
        """ Функция, которая спрашивает сколько отелей отобразить в результате поиска """
        logger.info("Вызываем функцию выбора отображать фото или нет")

        if message.text.lower() == 'да':
            # 9 Yes/No Photos
            logger.warning("Записываем в бд выбор отображения фото")
            result_find['Flag_Photos'] = True

            markup: telebot = types.ReplyKeyboardMarkup(resize_keyboard=True). \
                add(*(types.KeyboardButton(str(i_num)) for i_num in range(1, 11)), row_width=5)
            back_key(markup)
            bot.send_message(message.from_user.id, text='Сколько фото показать(max 10)?', reply_markup=markup)

            bot.register_next_step_handler(message, get_count_photo)
        elif message.text.lower() == 'нет':
            result_find['Flag_Photos'] = False
            get_result(message)
        elif message.text == 'Назад':
            markup: telebot = types.ReplyKeyboardMarkup(resize_keyboard=True).\
                add(*(types.KeyboardButton(str(i_num)) for i_num in range(1, 11)), row_width=5)
            back_key(markup)
            bot.send_message(message.chat.id, text='Сколько отелей показать(max 10)?', reply_markup=markup)
            bot.register_next_step_handler(message, get_count_hotel)
        elif message.text == 'Главное меню':
            get_menu(message)
        else:
            bot.send_message(message.chat.id, text='<b>Ошибка!!</b>\nНе верная команда!', parse_mode='html')
            bot.register_next_step_handler(message, get_count_hotel)

    # get_count_photo

    def get_count_photo(message: telebot) -> None:
        """ Функция, которая спрашивает необходимо ли отобразить фото в результате поиска"""
        logger.info("Вызываем функцию числа отображаемых фотографий")

        if message.text.isdigit() and int(message.text) > 0:
            count_photo: int = int(message.text)
            if count_photo >= 10:
                count_photo: int = 10

            # 10 Count_photo
            logger.warning("Записываем в бд число отображаемых фото")

            result_find['Count_photo'] = int(count_photo)
            get_result(message)

        elif message.text == 'Главное меню':
            get_menu(message)

        elif message.text == 'Назад':
            keyboard: telebot = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            key_yes: telebot = types.KeyboardButton(text='Да')
            key_no: telebot = types.KeyboardButton(text='Нет')
            keyboard.add(key_yes, key_no)
            bot.send_message(message.chat.id, text='Результат поиска показать с фото?', reply_markup=keyboard)
            bot.register_next_step_handler(message, get_photo)
        else:
            bot.send_message(message.chat.id, '<b>Ошибка!!</b>\nВведите корректное число фотографий(не более 10):',
                             parse_mode='html')
            bot.register_next_step_handler(message, get_count_photo)

    # get_result
    def get_result(message):
        """ Функция, которая выводит результат поиска в чаб бота """
        logger.info("Вызываем функцию отображения результатов")

        bot.send_message(message.chat.id, text=f'<u>Подождите, идет загрузка...</u>',
                         reply_markup=types.ReplyKeyboardRemove(), parse_mode='html')
        url_price: str = "https://hotels4.p.rapidapi.com/properties/list"
        querystring_price: Dict = {"destinationId": result_find['DestinationId'], "pageNumber": "1",
                                   "pageSize": result_find['PageSize'], "checkIn": result_find['CheckIn'],
                                   "checkOut": result_find['CheckOut'], "adults1": result_find['Adults1'],
                                   "sortOrder": result_find['SortOrder'],
                                   "locale": result_find['language'],
                                   "currency": result_find['currency']}
        response_price: requests = requests.request("GET", url_price, headers=headers, params=querystring_price)
        date_price: Dict = write_json(response_price)
        date_price: List = date_price["data"]["body"]["searchResults"]["results"]

        if result_find['SortOrder_distance'] is True:
            date_price: List = list(filter(
                lambda i_hotel_best: result_find.get('price_from') <
                int(''.join(re.findall(r'\d\S+', i_hotel_best["ratePlan"]["price"]["current"])).replace(',', ''))
                < result_find.get('price_to')
                and
                result_find.get('distance_from') <
                float(''.join(re.findall(r'\d\S+', i_hotel_best["landmarks"][0]["distance"])).replace(',', ''))
                < result_find.get('distance_to'), date_price))

            date_price: List = sorted(date_price, key=lambda elem: (elem["landmarks"][0]["distance"]))[:int(
                               result_find['Count_hotel_for'])]

        # History
        logger.warning("Записываем в бд историю поиска")

        command_str = result_find.get('Command')
        date_command: datetime.date = datetime.now().replace(microsecond=0).strftime("%H:%M:%S %d.%m.%Y")
        hotel_str: str = ', '.join([i_hotel_name["name"] for i_hotel_name in date_price])
        history_list.append({'Command': command_str, 'Date_time': date_command, 'Hotel_list': hotel_str})
        if len(date_price) == 0:
            bot.send_message(message.chat.id, text='Ничего не найдено.')
        else:
            logger.info("Отображаем результат")
            for i_hotel in date_price:
                id_hotel = i_hotel["id"]
                message_str = 'Отель: {hotel_name}\n' \
                              'Адрес: {hotel_address}\n' \
                              'Рейтинг {hotel_rating}\n' \
                              'Удаленность от центра {hotel_distance}\n' \
                              'Цена за ночь {price}\n' \
                              'Цена за все время: {all_price}\n' \
                              'Сайт: {website}'.format(
                                hotel_name=i_hotel.get("name"),
                                hotel_address=f'{i_hotel["address"]["locality"]}, '
                                              f'{i_hotel["address"].get("streetAddress")}',
                                hotel_rating=i_hotel.get("guestReviews", '-')["unformattedRating"],
                                hotel_distance=i_hotel["landmarks"][0].get("distance"),
                                price=str(result_find.get('currency')[1]) + str(int(''.join(re.findall(r'\d\S+',
                                i_hotel["ratePlan"]["price"]["current"])).replace(',', ''))),
                                all_price=str(result_find.get('currency')[1]) +
                                str(int(''.join(re.findall(r'\d\S+', i_hotel["ratePlan"]["price"]["current"])).
                                        replace(',', '')) * result_find.get("Adults1")
                                * int((result_find.get("CheckOut") - result_find.get("CheckIn")).days)),
                                website='https://www.hotels.com/ho' + str(i_hotel["id"]))

                if result_find['Flag_Photos']:
                    url_photo: str = "https://hotels4.p.rapidapi.com/properties/get-hotel-photos"
                    querystring_photo: Dict[str: int] = {"id": id_hotel}
                    response_photo: requests = requests.request("GET", url_photo, headers=headers,
                                                                params=querystring_photo)
                    date_img = write_json(response_photo)
                    img_str = [types.InputMediaPhoto(
                        date_img["hotelImages"][i_num]["baseUrl"].format(
                            size=date_img["hotelImages"][i_num]["sizes"][0]["suffix"]))
                        for i_num in range(result_find['Count_photo'])]
                    img_str[0]: List[:telebot] = types.InputMediaPhoto(
                        date_img["hotelImages"][0]["baseUrl"].format(
                            size=date_img["hotelImages"][0]["sizes"][0]["suffix"]), caption=message_str)
                    bot.send_media_group(message.chat.id, img_str)

                elif not result_find['Flag_Photos']:
                    bot.send_message(message.chat.id, message_str)
                else:
                    bot.send_message(message.chat.id, 'Произошла ошибка')

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True).add(types.KeyboardButton('ОК'))
        bot.send_message(message.chat.id, text=f'<b>Поиск завершен</b>', parse_mode='html', reply_markup=markup)

        bot.register_next_step_handler(message, find_end)
        
    def find_end(message):
        get_menu(message)

    # Команда Start

    @bot.message_handler(commands=['start'])
    def command_start(message: telebot) -> None:
        logger.info("Вызываем команду страт бота")

        """ Функция бля запуска команды /start """
        if message.from_user.first_name is None:
            message.from_user.first_name = ''
        if message.from_user.last_name is None:
            message.from_user.last_name = ''
        bot.send_message(message.chat.id, f'Привет {message.from_user.first_name} {message.from_user.last_name}')
        get_menu(message)

    # Команда Help

    @bot.message_handler(commands=['help'])
    def command_help(message: telebot) -> None:
        """ Функция для запуска команды /help """
        logger.info("Вызываем команду помощь")

        help_message = f'Топ самых <b>дешёвых</b> отелей в городе \n(команда <b><u>/lowprice</u></b>).\n' \
                       'Топ самых <b>дорогих</b> отелей в городе \n(команда <b><u>/highprice</u></b>).\n' \
                       'Топ отелей, <b>наиболее подходящих по цене и расположению от центра</b> \n(команда ' \
                       '<b><u>/bestdeal)</u></b>.\n' \
                       'Историю поиска отелей \n(команда <b><u>/history)</u></b>.\n' \
                       'Настройки \n(команда <b><u>/setting)</u></b>.'
        bot.send_message(message.chat.id, help_message, parse_mode='html')

    # Команда lowprice

    @bot.message_handler(commands=['lowprice'])
    def command_lowprice(message: telebot) -> None:
        """ Функция для запуска команды /lowprice """
        logger.info("Вызываем команду дешевые отели")

        # 0 SortOrder
        result_find['SortOrder'] = 'PRICE'
        # 1 SortOrder_distance
        result_find['SortOrder_distance'] = False
        # 2 Command
        result_find['Command'] = message.text
        key_menu(message)
        bot.register_next_step_handler(message, get_city)

    # Команда highprice

    @bot.message_handler(commands=['highprice'])
    def command_help(message):
        """ Функция для запуска команды /highprice """
        logger.info("Вызываем команду дорогие отели")

        # 0 SortOrder
        result_find['SortOrder'] = 'PRICE_HIGHEST_FIRST'
        # 1 SortOrder_distance
        result_find['SortOrder_distance'] = False
        # 2 Command
        result_find['Command'] = message.text
        key_menu(message)
        bot.register_next_step_handler(message, get_city)

    # Команда bestdeal

    @bot.message_handler(commands=['bestdeal'])
    def command_help(message):
        """ Функция для запуска команды /bestdeal """
        logger.info("Вызываем команду лучшие цены")

        # 0 SortOrder
        result_find['SortOrder'] = 'PRICE'
        # 1 SortOrder_distance
        result_find['SortOrder_distance'] = True

        # 2 Command
        result_find['Command'] = message.text
        key_menu(message)
        bot.register_next_step_handler(message, get_city)

    # Команда history

    @bot.message_handler(commands=['history'])
    def command_help(massage):
        """ Функция для запуска команды /history """
        logger.info("Вызываем команду история")

        bot.send_message(massage.chat.id, text=f'<u>История поиска:</u>', parse_mode='html')
        history_str = ''
        for i_num, index_history in enumerate(history_list):
            history_str += f'#{i_num + 1}\n' \
                           f'Время и дата: {str(index_history.get("Date_time"))}\n' \
                           f'Команда: {index_history.get("Command")}\n' \
                           f'Список отелей: {str(index_history.get("Hotel_list"))}\n\n'
        if history_str == '':
            bot.send_message(massage.chat.id, text='Вы ничего не искали.\nИстория поиска пуста.')
        else:
            bot.send_message(massage.chat.id, text=history_str)

    # Команда setting

    @bot.message_handler(commands=['setting'])
    def command_setting(message):
        logger.info("Вызываем команду настройки")
        markup: telebot = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        key_language: telebot = types.KeyboardButton('Язык')
        key_currency: telebot = types.KeyboardButton('Валюта')
        key_back: telebot = types.KeyboardButton('Назад')
        markup.add(key_currency, key_language, key_back)
        bot.send_message(message.chat.id, text=f'<b>Настройки</b>', reply_markup=markup, parse_mode='html')
        bot.register_next_step_handler(message, get_setting)

    def get_setting(message):
        bot.send_message(message.chat.id, message.text)
        if message.text.lower() == 'язык':
            markup: telebot = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            key_ru: telebot = types.KeyboardButton('Русский')
            key_en: telebot = types.KeyboardButton('Английский')
            key_back: telebot = types.KeyboardButton('Назад')
            markup.add(key_ru, key_en, key_back)
            bot.send_message(message.chat.id, text=f'<b>Выберете язык</b>', reply_markup=markup, parse_mode='html')
            bot.register_next_step_handler(message, get_language)
        elif message.text.lower() == 'валюта':
            markup: telebot = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            key_rub: telebot = types.KeyboardButton('Рубль')
            key_usd: telebot = types.KeyboardButton('Доллар')
            key_eur: telebot = types.KeyboardButton('Евро')
            key_back: telebot = types.KeyboardButton('Назад')
            markup.add(key_rub, key_usd, key_eur, key_back)
            bot.send_message(message.chat.id, text=f'<b>Выберете вид валюты</b>', reply_markup=markup,
                             parse_mode='html')
            bot.register_next_step_handler(message, get_currency)
        elif message.text.lower() == 'назад':
            get_menu(message)
        else:
            bot.send_message(message.chat.id, text=f'<b>Ошибка!</b>\n Выберете команду из списка.', parse_mode='html')
            bot.load_next_step_handlers(message.chat.id, get_setting)

    def get_language(message):
        if message.text.lower() == 'русский':
            logger.warning("Устанавливаем значение русского языка в бд")
            result_find['language'] = ['ru_RU', 'KM']
        elif message.text.lower() == 'английский':
            logger.warning("Устанавливаем значение английского языка в бд")
            result_find['language'] = ['en_EN', 'Mills']
        elif message.text.lower() == 'назад':
            get_setting(message)
        else:
            bot.send_message(message.chat.id, text=f'<b>Ошибка!</b>\nВыберете язык из списка.', parse_mode='html')
            bot.load_next_step_handlers(message.chat.id, get_language)
        bot.send_message(message.chat.id, text=f'Установлен язык: <u>{message.text.lower()}</u>', parse_mode='html')
        command_setting(message)

    def get_currency(message):
        if message.text.lower() == 'рубль':
            logger.warning("Устанавливаем значение волюты - рубль")
            result_find['currency'] = ['RUB', '₽']
        elif message.text.lower() == 'доллар':
            logger.warning("Устанавливаем значение волюты - доллар")
            result_find['currency'] = ['USD', '$']
        elif message.text.lower() == 'евро':
            logger.warning("Устанавливаем значение волюты - евро")
            result_find['currency'] = ['EUR', '€']
        elif message.text.lower() == 'назад':
            get_setting(message)
        else:
            bot.send_message(message.chat.id, text=f'<b>Ошибка!</b>\n Выберете волюту из списка.')
            bot.load_next_step_handlers(message.chat.id, get_language)
        bot.send_message(message.chat.id, text=f'Установленная волюта: <u>{message.text.lower()}</u>',
                         parse_mode='html')

        command_setting(message)

    @bot.message_handler(content_types=['text'])
    def handler_text(message):
        """ Функция для обработки сообщений и команд, которые не знает бот """
        logger.info("Введено некорректное сообщение")
        bot.send_message(message.chat.id, text='Неизвестная команда!')


if __name__ == '__main__':
    logger = app_logger.get_logger(__name__)
    headers: Dict = {'X-RapidAPI-Key': '0bb74c8119msh60cc93590327c4cp120b22jsn92f73a227f23',
                     'X-RapidAPI-Host': 'hotels4.p.rapidapi.com'}
    bot: telebot = telebot.TeleBot('5396252365:AAGJ_zNHywQVdVk-R560Ey5yC0usX5jHzcM')
    main()
    bot.polling(none_stop=True)
