from telebot import types
import telebot
import sqlite3
import requests
from bs4 import BeautifulSoup as bs
import os


TOKEN = ""

bot = telebot.TeleBot(TOKEN)

db = sqlite3.connect("data.sqlite3", check_same_thread=False)
cur = db.cursor()


@bot.message_handler(commands=["start"])
def welcome(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Искать🎲", callback_data="get_first_anime")
    )
    reply_text = "Привет!👋\nЭто бот для поиска рандомных аниме!\nСоздатель:@Akhmetov_Adil"
    bot.send_message(message.chat.id, reply_text, reply_markup=markup)
    cur.execute(
        f"""CREATE TABLE IF NOT EXISTS u{message.chat.id}(description text, main_text text, link text)"""
    )
    db.commit()


@bot.message_handler(commands=["get_anime"])
def send_anime(message):
    try:
        r = requests.get("https://animego.org/anime/random")
        html = bs(r.text, "lxml")
        try:
            episodes = (
                html.find("div", class_="anime-info")
                .findAll("dd", class_="col-6 col-sm-8 mb-1")[1]
                .text
            )
        except:
            try:
                bot.send_message(
                    950479413,
                    html.find("div", class_="anime-title").find("h1").text,
                )
            except:
                pass
            r = requests.get("https://animego.org/anime/random")
            html = bs(r.text, "lxml")
            episodes = (
                html.find("div", class_="anime-info")
                .findAll("dd", class_="col-6 col-sm-8 mb-1")[1]
                .text
            )
        try:
            int(
                html.find("div", class_="anime-info")
                .findAll("dd", class_="col-6 col-sm-8 mb-1")[1]
                .text
            )
        except:
            if (
                "/"
                in html.find("div", class_="anime-info")
                .findAll("dd", class_="col-6 col-sm-8 mb-1")[1]
                .text
            ):
                episodes = (
                    html.find("div", class_="anime-info")
                    .findAll("dd", class_="col-6 col-sm-8 mb-1")[1]
                    .text
                )
            else:
                episodes = 1
        # adding photo
        photo_res = requests.get(
            html.find(
                "div", class_="anime-poster position-relative cursor-pointer"
            )
            .find("img")
            .get("src")
        )
        photo = open(f"images/{message.chat.id}.jpg", "wb")
        photo.write(photo_res.content)
        photo.close()
        # name
        name = html.find("div", class_="anime-title").find("h1").text
        # genres
        genres = ", ".join(
            [
                x.text
                for x in html.find(
                    "dd", class_="col-6 col-sm-8 mb-1 overflow-h"
                ).findAll("a")
            ]
        )
        if "a" >= genres[0][0] <= "Z" or "1" >= genres <= "0":
            genres = "Нет"
        # link
        link = html.find("link", rel="canonical").get("href")
        # description
        description = html.find("div", class_="description pb-3").text
        # rating
        rate = str(html.find("div", class_="pr-2").text)[:3]
        markup1 = types.InlineKeyboardMarkup()
        markup1.add(types.InlineKeyboardButton("Смотреть⏎", url=link))
        markup1.add(
            types.InlineKeyboardButton("Дальше🔮", callback_data="get_anime")
        )
        markup1.add(
            types.InlineKeyboardButton(
                "Описание🔍", callback_data="get_description"
            )
        )
        main_text = (
            f"{name}\nЭпизоды: {episodes}\nРейтинг: {rate}⭐️\nЖанры: {genres}"
        )
        cur.execute(f"""DROP TABLE u{message.chat.id}""")
        db.commit()
        cur.execute(
            f"""CREATE TABLE IF NOT EXISTS u{message.chat.id}(description text, main_text text, link text)"""
        )
        db.commit()
        cur.execute(
            f"""INSERT INTO u{message.chat.id} VALUES('{description}', '{main_text}', '{link}')"""
        )
        db.commit()
        # send photo to user
        with open(f"images/{message.chat.id}.jpg", "rb") as photo:
            bot.send_photo(message.chat.id, photo)
        bot.send_message(message.chat.id, main_text, reply_markup=markup1)
        os.remove(f"images/{message.chat.id}.jpg")
    except:
        send_anime(message)


@bot.callback_query_handler(func=lambda call: True)
def answ(call):
    if call.data == "get_anime":
        try:
            bot.delete_message(
                chat_id=call.message.chat.id, message_id=call.message.id
            )
            bot.delete_message(
                chat_id=call.message.chat.id, message_id=call.message.id - 1
            )
        except:
            bot.delete_message(
                chat_id=call.message.chat.id, message_id=call.message.id - 2
            )
        send_anime(call.message)
    elif call.data == "get_first_anime":
        try:
            bot.delete_message(
                chat_id=call.message.chat.id, message_id=call.message.id - 1
            )
        except:
            pass
        send_anime(call.message)
    elif call.data == "get_description":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Назад", callback_data="back"))
        cur.execute(f"""SELECT description FROM u{call.message.chat.id}""")
        description = cur.fetchall()[0][0]
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.id,
                text=description,
                reply_markup=markup,
            )
        except:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.id,
                text="Нет",
                reply_markup=markup,
            )
    elif call.data == "back":
        cur.execute(f"""SELECT link FROM u{call.message.chat.id}""")
        link = cur.fetchall()[0][0]
        cur.execute(f"""SELECT main_text from u{call.message.chat.id}""")
        main_text = cur.fetchall()[0][0]
        markup1 = types.InlineKeyboardMarkup()
        markup1.add(types.InlineKeyboardButton("Смотреть⏎", url=link))
        markup1.add(
            types.InlineKeyboardButton("Дальше🔮", callback_data="get_anime")
        )
        markup1.add(
            types.InlineKeyboardButton(
                "Описание🔍", callback_data="get_description"
            )
        )
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.id,
            text=main_text,
            reply_markup=markup1,
        )


bot.infinity_polling()
