import telebot
import requests
from telebot import types
from auth_data import token
import pprint
from auth_data import steam
from auth_data import KEY

pp = pprint.PrettyPrinter()

bot = telebot.TeleBot(token)


@bot.message_handler(commands=["start"])
def main_menu(message):
    bot.send_message(message.chat.id, "Привет, {0.first_name}!".format(message.from_user))

    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)

    item1 = types.KeyboardButton(text="Поиск актуальной инфы об игре")
    item2 = types.KeyboardButton(text="Поиск актуальной инфы по пользователю")
    item3 = types.KeyboardButton(text="Поиск общих игр у нескольких пользователей")

    markup.add(item1, item2, item3)
    bot.send_message(message.chat.id, "Чем могу служить ?", reply_markup=markup)


@bot.message_handler(content_types=["text"])
def main_menu_handler(message):
    if message.text == "Поиск актуальной инфы об игре":
        msg = bot.send_message(message.chat.id, "Введите название игры, инфу о которой вы хотите узнать. "
                                                "Постарайтесь ввести как можно более точное название игры, иначе "
                                                "поиск может быть неудачным.")
        bot.register_next_step_handler(msg, game_info_handler)

    if message.text == "Поиск актуальной инфы по пользователю":
        msg = bot.send_message(message.chat.id, "Введите id пользователя")
        bot.register_next_step_handler(msg, user_id_handler)

    if message.text == "Поиск общих игр у нескольких пользователей":
        user_ids = []

        msg = bot.send_message(message.chat.id, "Начните вводить id пользователей, отправьте 'stop', чтобы "
                                                "остановить ввод и получить результат")

        bot.register_next_step_handler(msg, common_games_handler, user_ids)


@bot.message_handler(func=lambda message: True)
def game_info_handler(message):
    game_name = message.text
    bot.reply_to(message, "название принято")

    response = steam.apps.search_games(game_name)
    pp.pprint(response)

    for app in response['apps']:

        extra = steam.apps.get_app_details(int(app['id']))

        pp.pprint(extra)

        genres = ''
        for genre in extra[str(app['id'])]['data']['genres']:
            genres += genre['description'] + ', '

        rel_date = extra[str(app['id'])]['data']['release_date']['date']
        if 'price_overview' in extra[str(app['id'])]['data']:
            price = extra[str(app['id'])]['data']['price_overview']['final_formatted']
        else:
            price = 'N/A'
        bot.send_message(message.chat.id, f'id игры: {app["id"]}\n'
                                          f''
                                          f'Название игры: {app["name"]}\n'
                                          f''
                                          f'Цена игры: {price}\n'
                                          f''
                                          f'Дата выхода: {rel_date}\n'
                                          f''
                                          f'Жанры: {genres}\n'
                                          f''
                                          f'Ссылка на игру в Steam: {app["link"]}\n'
                                          f''
                         )


@bot.message_handler(func=lambda message: True)
def user_id_handler(message):
    user_id = message.text
    bot.reply_to(message, "id принято")

    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)

    item1 = types.KeyboardButton(text='Общая информация')
    item2 = types.KeyboardButton(text='Список друзей')
    item3 = types.KeyboardButton(text='Список игр')
    item6 = types.KeyboardButton(text='Список недавно сыгранных игр')

    markup.add(item1, item2, item3, item6)

    msg = bot.send_message(message.chat.id, "Какую конкретно инфу вы хотите "
                                            "получить по данному пользователю ?", reply_markup=markup)

    bot.register_next_step_handler(msg, user_info_handler, user_id)


@bot.message_handler(func=lambda message: True)
def user_info_handler(message, user_id):
    if message.text == "Общая информация":
        url = "http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002"
        params = {
            'key': KEY,
            'steamids': user_id
        }
        response = requests.get(url, params=params)

        if response.status_code == 200:
            res = response.json()

            pp.pprint(res)

            bot.send_photo(message.chat.id, res["response"]["players"][0]["avatarfull"])
            bot.send_message(message.chat.id, f'id пользователя: {res["response"]["players"][0]["steamid"]}\n'
                                              f''
                                              f'Ник: {res["response"]["players"][0]["personaname"]}\n'
                                              f''
                                              f'Страна: {res["response"]["players"][0]["loccountrycode"]}\n'
                                              f''
                                              f'Ссылка на профиль: {res["response"]["players"][0]["profileurl"]}'
                             )
        else:
            msg = bot.send_message(message.chat.id, "Ошибка. Возвожно, данный профиль закрытый,"
                                                    " или id указан неправильно. Попробуйте снова")
            bot.register_next_step_handler(msg, user_id_handler)

    if message.text == "Список друзей":
        url = "http://api.steampowered.com/ISteamUser/GetFriendList/v0001/"
        params = {
            'key': '1F40A7E94200E3EB36C8834DA6599903',
            'steamid': user_id,
            'relationship': 'friend'
        }
        response = requests.get(url, params=params)

        if response.status_code == 200:
            res = response.json()
            friends_ids = []

            for friend in res['friendslist']['friends']:
                friends_ids.append(friend['steamid'])

            for steamid in friends_ids:
                url = "http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002"
                params = {
                    'key': KEY,
                    'steamids': steamid
                }
                temp_res = requests.get(url, params=params)
                temp_resj = temp_res.json()

                bot.send_message(message.chat.id, f'id друга: {temp_resj["response"]["players"][0]["steamid"]}\n'
                                                  f''
                                                  f'Ник: {temp_resj["response"]["players"][0]["personaname"]}\n'
                                                  f''
                                                  f'Ссылка на профиль: {temp_resj["response"]["players"][0]["profileurl"]}')
        else:
            msg = bot.send_message(message.chat.id, "Ошибка. Возвожно, данный профиль закрытый,"
                                                    " или id указан неправильно. Попробуйте снова")
            bot.register_next_step_handler(msg, user_id_handler)

    if message.text == "Список игр":
        url = "http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001"
        params = {
            'key': KEY,
            'steamid': user_id,
            'include_played_free_games': 'false',
            'include_appinfo': 'true'
        }
        response = requests.get(url, params=params)

        if response.status_code == 200:

            res = response.json()

            games_list = ''
            for game in res['response']['games']:
                games_list += game['name'] + '\n'

            bot.send_message(message.chat.id, "Список игр: \n" + games_list)
        else:
            msg = bot.send_message(message.chat.id, "Ошибка. Возвожно, данный профиль закрытый,"
                                                    " или id указан неправильно. Попробуйте снова")
            bot.register_next_step_handler(msg, user_id_handler)

    if message.text == "Список недавно сыгранных игр":
        url = "http://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v0001"
        params = {
            'key': KEY,
            'steamid': user_id,
            'include_played_free_games': 'false'
        }
        response = requests.get(url, params=params)

        if response.status_code == 200:
            res = response.json()

            for game in res['response']['games']:
                bot.send_message(message.chat.id, f"{game['name']} \n"
                                                  f"Наиграно за 2 недели: {str(game['playtime_2weeks'] // 60)} ч. \n"
                                                  f"Наиграно всего: {str(game['playtime_forever'] // 60)} ч. \n")

            pp.pprint(response.json())

        else:
            msg = bot.send_message(message.chat.id, "Ошибка. Возвожно, данный профиль закрытый,"
                                                    " или id указан неправильно. Попробуйте снова")
            bot.register_next_step_handler(msg, user_id_handler)


@bot.message_handler(func=lambda message: True)
def common_games_handler(message, user_ids):
    if message.text == 'stop':
        bot.reply_to(message, "Получено сообщение 'stop'. Список id: " + str(user_ids))

        primary_list = []

        url = "http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001"
        params = {
            'key': KEY,
            'steamid': user_ids[0],
            'include_played_free_games': 'false',
            'include_appinfo': 'true'
        }

        response = requests.get(url, params=params)

        if response.status_code == 200:

            res = response.json()

            for game in res['response']['games']:
                primary_list.append(game['name'])

            for i in range(1, len(user_ids)):
                temp_list = []

                params = {
                    'key': KEY,
                    'steamid': user_ids[i],
                    'include_played_free_games': 'false',
                    'include_appinfo': 'true'
                }

                response = requests.get(url, params=params)

                if response.status_code == 200:
                    res = response.json()

                    for game in res['response']['games']:
                        temp_list.append(game['name'])

                    primary_list = list(set(primary_list) & set(temp_list))

                else:
                    msg = bot.send_message(message.chat.id, "Ошибка. Возможно, данный профиль закрытый "
                                                            "или введён неверный id. Начинаю приём id заново.")
                    user_ids = []
                    bot.register_next_step_handler(msg, common_games_handler, user_ids)

            games_list = ''
            for game in primary_list:
                games_list += game + '\n'

            bot.send_message(message.chat.id, "Список общих игр:")
            bot.send_message(message.chat.id, games_list)

        else:
            msg = bot.send_message(message.chat.id, "Ошибка. Возможно, данный профиль закрытый "
                                                    "или введён неверный id. Начинаю приём id заново.")
            user_ids = []
            bot.register_next_step_handler(msg, common_games_handler, user_ids)
    else:
        user_ids.append(message.text)
        msg = bot.reply_to(message, "id добавлен. Введите следующий id "
                                    "или 'stop', чтобы закончить ввод.")

        bot.register_next_step_handler(msg, common_games_handler, user_ids)


bot.polling(non_stop=True)
