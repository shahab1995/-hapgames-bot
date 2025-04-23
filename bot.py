import logging
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InputFile
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from openpyxl import Workbook, load_workbook
import os

API_TOKEN = '7895495605:AAFxv2IAfDEJnor0U5KZ3i7qn5R4XNPeiFk'
ADMIN_ID = 132035351

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# بازی‌های موجود برای سفارش جدید
available_games = ["Unmatched", "Virus", "Masquerade", "You've Got Crabs", "محصولات جانبی"]
# کل بازی‌ها برای گزارش مشکل
all_games = ["Unmatched", "Virus", "Masquerade", "You've Got Crabs", "Downforce", 
             "قهرمانان سرگردان", "Coloretto", "Point Salad", "Antidote", "محصولات جانبی"]

class OrderForm(StatesGroup):
    choosing_type = State()
    choosing_game = State()
    entering_name = State()
    entering_phone = State()
    entering_province = State()
    entering_city = State()
    entering_postal_code = State()
    entering_address = State()
    sending_photo = State()

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message, state: FSMContext):
    await state.finish()
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("سفارش جدید", "گزارش مشکل")
    await message.answer("به ربات هُپ گیمز خوش اومدی!\nیکی از گزینه‌ها رو انتخاب کن:", reply_markup=keyboard)
    await OrderForm.choosing_type.set()

@dp.message_handler(lambda msg: msg.text in ["سفارش جدید", "گزارش مشکل"], state=OrderForm.choosing_type)
async def choose_type(message: types.Message, state: FSMContext):
    await state.update_data(order_type=message.text)
    games = available_games if message.text == "سفارش جدید" else all_games
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(*games).add("انصراف")
    await message.answer("بازی مورد نظر رو انتخاب کن:", reply_markup=keyboard)
    await OrderForm.choosing_game.set()

@dp.message_handler(lambda msg: msg.text in available_games + all_games, state=OrderForm.choosing_game)
async def choose_game(message: types.Message, state: FSMContext):
    await state.update_data(game=message.text)
    await message.answer("نام و نام خانوادگی:", reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add("انصراف"))
    await OrderForm.entering_name.set()

@dp.message_handler(state=OrderForm.entering_name)
async def enter_name(message: types.Message, state: FSMContext):
    if message.text == "انصراف":
        await cancel_handler(message, state)
        return
    await state.update_data(name=message.text)
    await message.answer("شماره تماس:", reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add("انصراف"))
    await OrderForm.entering_phone.set()

@dp.message_handler(state=OrderForm.entering_phone)
async def enter_phone(message: types.Message, state: FSMContext):
    if message.text == "انصراف":
        await cancel_handler(message, state)
        return
    await state.update_data(phone=message.text)
    await message.answer("استان:", reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add("انصراف"))
    await OrderForm.entering_province.set()

@dp
