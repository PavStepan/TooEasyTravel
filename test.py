
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP


import telebot
bot = telebot.TeleBot('5396252365:AAGJ_zNHywQVdVk-R560Ey5yC0usX5jHzcM')




@bot.message_handler(commands=['start'])
def start(message):
    calendar, step = DetailedTelegramCalendar(locale='ru').build()
    bot.send_message(message.chat.id,
                     f"Выберете {LSTEP[step]}",
                     reply_markup=calendar)


@bot.callback_query_handler(func=DetailedTelegramCalendar.func())
def cal(call):
    result, key, step = DetailedTelegramCalendar().process(call.data)
    if not result and key:
        bot.edit_message_text(f"Select {LSTEP[step]}",
                              call.message.chat.id,
                              call.message.message_id,
                              reply_markup=key)
    elif result:
        bot.edit_message_text(f"You selected {result}",
                              call.message.chat.id,
                              call.message.message_id)



bot.polling(none_stop=True)
