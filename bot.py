
from aiogram import Bot, Dispatcher, types, executor
import logging
import os
import pandas as pd

API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)

user_data = {}
data_list = []

@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    user_data[user_id] = {}
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("سفارش جدید", "گزارش مشکل")
    await message.answer("سلام! یکی از گزینه‌ها رو انتخاب کن:", reply_markup=keyboard)

@dp.message_handler(lambda message: message.text in ["سفارش جدید", "گزارش مشکل"])
async def select_mode(message: types.Message):
    user_id = message.from_user.id
    user_data[user_id]["type"] = message.text
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Unmatched", "Virus", "Masquerade", "You’ve Got Crabs")
    if message.text == "گزارش مشکل":
        keyboard.add("Downforce", "قهرمانان سرگردان", "Coloretto", "Point Salad", "Antidote")
    keyboard.add("محصولات جانبی", "انصراف")
    await message.answer("لطفا بازی مورد نظر رو انتخاب کن:", reply_markup=keyboard)

@dp.message_handler(lambda message: message.text in ["Unmatched", "Virus", "Masquerade", "You’ve Got Crabs", "Downforce", "قهرمانان سرگردان", "Coloretto", "Point Salad", "Antidote", "محصولات جانبی"])
async def select_game(message: types.Message):
    user_id = message.from_user.id
    user_data[user_id]["game"] = message.text
    await message.answer("لطفا استان خود را وارد کنید:")

@dp.message_handler(lambda message: message.text == "انصراف")
async def cancel_handler(message: types.Message):
    user_data.pop(message.from_user.id, None)
    await message.answer("فرآیند لغو شد. برای شروع مجدد /start را بزنید.")

@dp.message_handler(lambda message: user_data.get(message.from_user.id, {}).get("game"))
async def collect_info(message: types.Message):
    user_id = message.from_user.id
    if "province" not in user_data[user_id]:
        user_data[user_id]["province"] = message.text
        await message.answer("شماره تماس خود را وارد کنید:")
    elif "phone" not in user_data[user_id]:
        user_data[user_id]["phone"] = message.text
        await message.answer("کد پستی را وارد کنید:")
    elif "postal_code" not in user_data[user_id]:
        user_data[user_id]["postal_code"] = message.text
        await message.answer("آدرس دقیق را وارد کنید:")
    elif "address" not in user_data[user_id]:
        user_data[user_id]["address"] = message.text
        data = user_data.pop(user_id)
        data["user_id"] = user_id
        data["username"] = message.from_user.username
        data_list.append(data)
        await message.answer("اطلاعات ذخیره شد. ممنون!")
        if ADMIN_ID:
            await bot.send_message(ADMIN_ID, f"کاربر جدید:
{data}")

@dp.message_handler(commands=["export"])
async def export_data(message: types.Message):
    if str(message.from_user.id) != ADMIN_ID:
        return
    df = pd.DataFrame(data_list)
    df.to_excel("orders.xlsx", index=False)
    with open("orders.xlsx", "rb") as file:
        await bot.send_document(chat_id=message.chat.id, document=file)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
