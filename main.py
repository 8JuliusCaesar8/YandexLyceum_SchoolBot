import datetime
import random
from itertools import chain
import sqlite3
from telegram.ext import CommandHandler, Application, MessageHandler, ConversationHandler, filters
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
import logging

weekdays = {0: "Понедельник", 1: "Вторник", 2: "Среда", 3: "Четверг",
            4: "Пятница", 5: "Суббота", 6: "Воскресенье"}
months = {1: "Январь", 2: "Февраль", 3: "Март",
          4: "Апрель", 5: "Май", 6: "Июнь",
          7: "Июль", 8: "Август", 9: "Сентябрь",
          10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"}
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)
logger = logging.getLogger(__name__)
reply_keyboard = [['Учитель физики', 'Учитель математики'],
                  ['Завуч', 'Директор']]
days_keyboard = [['Понедельник', 'Вторник', 'Среда'],
                 ['Четверг', 'Пятница']]
weekdays_list = ['Понедельник', 'Вторник', 'Среда',
                 'Четверг', 'Пятница']
task_keyboard = [['История', 'Математика']]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
task_markup = ReplyKeyboardMarkup(task_keyboard, one_time_keyboard=True)
schedule_change_markup = ReplyKeyboardMarkup(days_keyboard, one_time_keyboard=True)


async def start_question(update, context):
    await update.message.reply_text(
        "Выберите учителя, которому вы хотите задать вопрос\n",
        reply_markup=markup
    )
    return 1


async def first_response(update, context):
    context.user_data['person'] = update.message.text
    await update.message.reply_text(
        "Введите текст вопроса",
        reply_markup=ReplyKeyboardRemove())
    return 2


async def second_response(update, context):
    person = context.user_data["person"]
    text = update.message.text
    question = f'Вопрос: Кому: {person} Текст вопроса: {text}'
    with open('Letters.txt', 'w', encoding='utf-8') as r_file:
        r_file.write(question)
        r_file.close()
    await update.message.reply_text("Ваш вопрос отправлен, ожидайте ответа!")
    context.user_data.clear()
    return ConversationHandler.END


async def stop(update, context):
    await update.message.reply_text("Работа остановлена",
                                    reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


async def help(update, context):
    await update.message.reply_text(
        """Здравствуйте! Это телеграм бот для помощи в учебе
        Он может:
        📃 Присылать расписание /schedule
        📩 Изменять расписание /changeschedule
        👨‍🏫 Задавать вопросы учителям и директору /question
        📓 Давать задачи для проверки знаний /zadacha
        🔔 Присылать расписание звонков /callschedule
        Надеемся что ваш бот смог помочь нам
        Разработчик:""",
        reply_markup=ReplyKeyboardRemove())


async def call_schedule(update, context):
    now = datetime.datetime.now().time()
    breaks = chain(range(841, 851), range(931, 951), range(1031, 1051),
                   range(1131, 1151), range(1221, 1231), range(1311, 1321))
    timed = int(now.strftime("%H%M"))
    if timed not in range(801, 1401):
        timed = 'неучебное время'
    elif timed in breaks:
        timed = 'перемена'
    else:
        timed = 'урок'
    await update.message.reply_text(
        f"""Расписание звонков:
        8:00-8:40 - Первый урок
        8:40-8:50 - Перемена
        8:50-9:30 - Второй урок
        9:30-9:50 - Перемена
        9:50-10:30 - Третий урок
        10:30-10:50 - Перемена
        10:50-11:30 - Четвертый урок
        11:30-11:40 - Перемена
        11:40-12:20 - Пятый урок
        12:20-12:30 - Перемена
        12:30-13:10 - Шестой урок
        13:10-13:20 - Перемена
        13:20-14:00 - Седьмой урок
        Сейчас: {timed}"""
    )


async def schedule_func(update, context):
    today = int(datetime.date.today().weekday())
    if today == 5 or today == 6:
        await update.message.reply_text(
            "Сегодня выходной, можешь отдыхать."
        )
    else:
        photo_path = f"schedule_list/{weekdays[today]}.png"
        await context.bot.send_photo(
            update.message.chat_id,
            photo=open(photo_path, 'rb'),
            caption=f"Расписание: {weekdays[today]}, {datetime.datetime.today().date().day} "
                    f"{months[datetime.datetime.today().date().month]}"
        )


async def start_tasks(update, context):
    await update.message.reply_text(
        "Выберите предмет по которому хотите решить задачу",
        reply_markup=task_markup
    )
    return 1


async def task_handler(update, context):
    if str(update.message.text).lower() == 'история':
        con = sqlite3.connect("Questions/Questions_base.db")
        cur = con.cursor()
        result = cur.execute("""Select Questions, Answers FROM Zadachi 
        WHERE Subject = 'история'""").fetchall()
        question_id = random.randint(0, len(result) - 1)
        question, answer = result[question_id]
        context.user_data['answer'] = answer
        con.close()
        await update.message.reply_text(
            question
        )
        return 2
    elif str(update.message.text).lower() == 'математика':
        first = int(random.randint(3000, 5000))
        second = int(random.randint(3000, 5000))
        multiplier = int(random.randint(10, 30))
        answer = first + second * multiplier
        example = f"{first} + {second} * {multiplier}"
        context.user_data['answer'] = answer
        await update.message.reply_text(
            f"Решите пример: {example}"
        )
        return 3
    else:
        await update.message.reply_text(
            'Выбран неправильный предмет'
        )
        return ConversationHandler.END


async def task_history(update, context):
    if str(update.message.text).lower() == str(context.user_data['answer']):
        await update.message.reply_text(
            'Правильно!'
        )
    else:
        await update.message.reply_text(
            'Неправильно!'
        )
    context.user_data.clear()
    return ConversationHandler.END


async def task_math(update, context):
    otvet = context.user_data['answer']
    if int(update.message.text) == otvet:
        await update.message.reply_text(
            'Правильно!'
        )
    else:
        await update.message.reply_text(
            f'Неправильно, правильный ответ: {str(otvet)}'
        )
    return ConversationHandler.END


async def start_change_schedule(update, context):
    await update.message.reply_text(
        "Выберите день, расписание на который вы хотите изменить",
        reply_markup=schedule_change_markup
    )
    return 1


async def change_schedule(update, context):
    if update.message.text not in weekdays_list:
        await update.message.reply_text(
            "Выбран неправильный параметр"
        )
        return ConversationHandler.END
    else:
        context.user_data['day'] = update.message.text
        await update.message.reply_text(
            "Пришлите новое расписание в формате фото"
        )
        return 2


async def image_schedule_handler(update, context):
    photo_file = await update.message.photo[-1].get_file()
    await photo_file.download_to_drive(f"schedule_list/{context.user_data['day']}.png")
    await update.message.reply_text(
        "Расписание успешно изменено"
    )
    return ConversationHandler.END


async def start_search(update, context):
    await update.message.reply_text(
        "Введите слово для поиска"
    )
    return 1


task_conversation_handler = ConversationHandler(
    entry_points=[CommandHandler('zadacha', start_tasks)],
    states={
        1: [MessageHandler(filters.TEXT & ~filters.COMMAND, task_handler)],
        2: [MessageHandler(filters.TEXT & ~filters.COMMAND, task_history)],
        3: [MessageHandler(filters.TEXT & ~filters.COMMAND, task_math)]
    },
    fallbacks=[CommandHandler('stop', stop)]
)
question_handler = ConversationHandler(
    entry_points=[CommandHandler('question', start_question)],
    states={
        1: [MessageHandler(filters.TEXT & ~filters.COMMAND, first_response)],
        2: [MessageHandler(filters.TEXT & ~filters.COMMAND, second_response)]
    },
    fallbacks=[CommandHandler('stop', stop)]
)
schedule_change_handler = ConversationHandler(
    entry_points=[CommandHandler('changeschedule', start_change_schedule)],
    states={
        1: [MessageHandler(filters.TEXT & ~filters.COMMAND, change_schedule)],
        2: [MessageHandler(filters.PHOTO, image_schedule_handler)]
    },
    fallbacks=[CommandHandler('stop', stop)]
)


def main():
    application = Application.builder().token("TOKEN").build()
    application.add_handler(question_handler)
    application.add_handler(task_conversation_handler)
    application.add_handler(schedule_change_handler)
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("schedule", schedule_func))
    application.add_handler(CommandHandler("callschedule", call_schedule))
    application.run_polling()


if __name__ == '__main__':
    main()
