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
available_games = ["Unmatched", "Virus", "Masquerade", "You’ve Got Crabs", "محصولات جانبی"]
# کل بازی‌ها برای گزارش مشکل
all_games = ["Unmatched", "Virus", "Masquerade", "You’ve Got Crabs", "Downforce", "قهرمانان سرگردان", "Coloretto", "Point Salad", "Antidote", "محصولات جانبی"]

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
    confirmation = State()

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message, state: FSMContext):
    await state.finish()
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("سفارش جدید", "گزارش مشکل")
    await message.answer("به ربات هُپ گیمز خوش اومدی!
یکی از گزینه‌ها رو انتخاب کن:", reply_markup=keyboard)
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
    await state.update_data(name=message.text)
    await message.answer("شماره تماس:", reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add("انصراف"))
    await OrderForm.entering_phone.set()

@dp.message_handler(state=OrderForm.entering_phone)
async def enter_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await message.answer("استان:", reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add("انصراف"))
    await OrderForm.entering_province.set()

@dp.message_handler(state=OrderForm.entering_province)
async def enter_province(message: types.Message, state: FSMContext):
    await state.update_data(province=message.text)
    await message.answer("شهر:", reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add("انصراف"))
    await OrderForm.entering_city.set()

@dp.message_handler(state=OrderForm.entering_city)
async def enter_city(message: types.Message, state: FSMContext):
    await state.update_data(city=message.text)
    await message.answer("کد پستی:", reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add("انصراف"))
    await OrderForm.entering_postal_code.set()

@dp.message_handler(state=OrderForm.entering_postal_code)
async def enter_postal_code(message: types.Message, state: FSMContext):
    await state.update_data(postal_code=message.text)
    await message.answer("آدرس کامل:", reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add("انصراف"))
    await OrderForm.entering_address.set()

@dp.message_handler(state=OrderForm.entering_address)
async def enter_address(message: types.Message, state: FSMContext):
    await state.update_data(address=message.text)
    await message.answer("در صورت وجود عکس از مشکل، لطفاً ارسال کن یا بزن روی انصراف.", reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add("انصراف"))
    await OrderForm.sending_photo.set()

@dp.message_handler(content_types=['photo'], state=OrderForm.sending_photo)
async def get_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    file_id = message.photo[-1].file_id
    await bot.send_photo(ADMIN_ID, file_id, caption=f"درخواست جدید:
{data}")
    await message.answer("درخواست ثبت شد! ممنون از شما.")
    save_to_excel(data)
    await state.finish()

@dp.message_handler(state=OrderForm.sending_photo)
async def skip_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await bot.send_message(ADMIN_ID, f"درخواست جدید:
{data}")
    await message.answer("درخواست ثبت شد! ممنون از شما.")
    save_to_excel(data)
    await state.finish()

@dp.message_handler(lambda msg: msg.text == "انصراف", state="*")
async def cancel_handler(message: types.Message, state: FSMContext):
    await message.answer("فرآیند لغو شد. برای شروع دوباره /start رو بزن.", reply_markup=types.ReplyKeyboardRemove())
    await state.finish()

def save_to_excel(data):
    file_path = "orders.xlsx"
    if os.path.exists(file_path):
        wb = load_workbook(file_path)
        ws = wb.active
    else:
        wb = Workbook()
        ws = wb.active
        ws.append(["نوع", "بازی", "نام", "شماره", "استان", "شهر", "کد پستی", "آدرس"])
    ws.append([
        data.get("order_type"), data.get("game"), data.get("name"),
        data.get("phone"), data.get("province"), data.get("city"),
        data.get("postal_code"), data.get("address")
    ])
    wb.save(file_path)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
