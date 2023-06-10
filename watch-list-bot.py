import psycopg2
import telebot
from telebot import types
import re
# Устанавливаем соединение с базой данных
conn = psycopg2.connect(
    database="postgres",
    user='postgres',
    password='Beka2004',
    host='localhost'
)
# Создаем курсор для выполнения операций с базой данных
cur = conn.cursor()

# Создаем таблицу movies, если она не существует
cur.execute("""CREATE TABLE IF NOT EXISTS movies (
                    id SERIAL PRIMARY KEY,
                    title TEXT,
                    user_id INTEGER
                );""")
conn.commit()


# Инициализируем бота
bot = telebot.TeleBot("6267210134:AAEtkFnmgUauPqbYUSGCXYaTx-Vb_U16KBU")

menu_commands = [
    telebot.types.BotCommand('start', 'Запустить бота'),
    telebot.types.BotCommand('add', 'Добавить в список'),
    telebot.types.BotCommand('list', 'Посмотреть ваш список'),
    telebot.types.BotCommand('delete', 'Удалить')
]
bot.set_my_commands(menu_commands)

# Обработчик команды /start


@bot.message_handler(commands=['start'])
def start_handler(message):
    bot.reply_to(message, "Привет! Я бот для создания списка просмотренных кино и сериалов. \n"
                          "Чтобы добавить фильм или сериал в список, просто введите команду /add 'назвние'.\n"
                          "Чтобы посмотреть список, введите команду /list. \n"
                          "Чтобы удалить фильм или сериал из списка, введите команду /delete и выберите фильм или сериал из списка.\n")
# Обработчик команды /add


@bot.message_handler(commands=['add'])
def add_movie_handler(message):
    if message.text.startswith('/add'):
        # Извлекаем название фильма или сериала из текста сообщения
        title = message.text.replace('/add', '').strip()

        # Проверяем, что название не пустое
        if len(title) == 0:
            bot.reply_to(message, "Вы не указали название фильма или сериала. Для добавления фильма или сериала используйте команду /add название_фильма_или_сериала.")
            return
        # Проверяем формат названия
        if not re.match(r'^[a-zA-Z0-9 \-\'\.]+$||а-яА-Я0-9 \-\'\.]+$', title):
            bot.reply_to(
                message, "Название фильма или сериала должно содержать только буквы, цифры, пробелы, тире, апострофы и точки.")
            return
        # Добавляем фильм или сериал в базу данных
    # Получаем id текущего пользователя
    user_id = message.from_user.id

    # Проверяем, есть ли фильм или сериал с таким названием уже в базе данных
    cur.execute(
        "SELECT * FROM movies WHERE title = %s AND user_id = %s", (title, user_id))
    row = cur.fetchone()
    if row is not None:
        # Если фильм или сериал уже есть в базе данных, сообщаем об этом пользователю
        bot.reply_to(
            message, f"Фильм или сериал '{title}' уже есть в вашем списке.")
    else:
        # Если фильм или сериал еще не добавлен в базу данных, добавляем его
        cur.execute(
            "INSERT INTO movies (title, user_id) VALUES (%s, %s)", (title, user_id))
        conn.commit()
        bot.reply_to(
            message, f"Фильм или сериал '{title}' был успешно добавлен в ваш список.")

# Обработчик команды /list


@bot.message_handler(commands=['list'])
def list_movies_handler(message):
    # Получаем id текущего пользователя
    user_id = message.from_user.id

    # Извлекаем список всех фильмов и сериалов текущего пользователя из базы данных
    cur.execute("SELECT title FROM movies WHERE user_id = %s", (user_id,))
    rows = cur.fetchall()

    if len(rows) > 0:
        # Если список не пустой, формируем сообщение со списком фильмов и сериалов
        message_text = "Список просмотренных фильмов и сериалов:\n"
        for row in rows:
            message_text += f"- {row[0]}\n"
        bot.reply_to(message, message_text)
    else:
        # Если список пустой, сообщаем об этом пользователю
        bot.reply_to(message, "Список просмотренных фильмов и сериалов пуст.")

# Обработчик команды /delete


@bot.message_handler(commands=['delete'])
def delete_movie_handler(message):
    # Извлекаем список всех фильмов и сериалов из базы данных
    cur.execute("SELECT title FROM movies")
    rows = cur.fetchall()

    if len(rows) > 0:
        # Если список не пустой, формируем сообщение с инлайн-кнопками для выбора фильма или сериала для удаления
        markup = types.InlineKeyboardMarkup()
        for row in rows:
            markup.add(types.InlineKeyboardButton(
                text=row[0], callback_data=row[0]))
        bot.reply_to(
            message, "Выберите фильм или сериал для удаления:", reply_markup=markup)
    else:
        # Если список пустой, сообщаем об этом пользователю
        bot.reply_to(message, "Список просмотренных фильмов и сериалов пуст.")

# Обработчик нажатия на инлайн-кнопку


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    # Извлекаем название фильма или сериала из callback_data
    title = call.data

    # Удаляем фильм или сериал из базы данных
    cur.execute("DELETE FROM movies WHERE title = %s", (title,))
    conn.commit()

    bot.answer_callback_query(
        call.id, f"Фильм или сериал '{title}' был успешно удален из списка.")


# Запускаем бота
bot.polling(none_stop=True)