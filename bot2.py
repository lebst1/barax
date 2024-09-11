import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

API_TOKEN = '7114542919:AAF8Ct5Ag7YBhaDolTfVBcvZXSOloR4_8zs'
MODERATION_CHAT_ID = -4534707255
CHANNEL_ID = '@baraxolka_kamenka'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

class AdForm(StatesGroup):
    content = State()  # Добавить это состояние
    name = State()
    description = State()
    price = State()
    contact = State() 
    photo = State()

# Кнопки для формы объявления
keyboard_start = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard_start.add(KeyboardButton('Создать объявление'))

# Кнопки для добавления фото
keyboard_photo = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard_photo.add(KeyboardButton('Добавить фото'), KeyboardButton('Далее'))

# Кнопки для отправки объявления
keyboard_send = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard_send.add(KeyboardButton('Отправить'), KeyboardButton('Назад'))

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer('<b>Привет!</b> 👋 Прежде чем отправить объявление, используй команду <b>/help</b>', reply_markup=keyboard_start, parse_mode='HTML')

@dp.message_handler(commands=['help'])
async def help(message: types.Message):
    await message.answer('Чтобы создать объявление жми на кнопку "<b>Создать объявление</b>".\n  Если хочешь отправить несколько фото, то отправляй их по одной, а не сразу все\n Отправка объявления возможно только с наличием фото товара!', parse_mode='HTML')

@dp.message_handler(lambda message: message.text == 'Создать объявление')
async def create_ad(message: types.Message):
    await message.answer('Введите название пода:', reply_markup=types.ReplyKeyboardRemove())
    await AdForm.name.set()

@dp.message_handler(state=AdForm.name)
async def process_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text
    await message.answer('Введите описание, состояние пода:', reply_markup=types.ReplyKeyboardRemove())
    await AdForm.next()

@dp.message_handler(state=AdForm.description)
async def process_description(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['description'] = message.text
    await message.answer('Введите цену пода:', reply_markup=types.ReplyKeyboardRemove())
    await AdForm.next()

@dp.message_handler(state=AdForm.price)
async def process_price(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['price'] = message.text
    await message.answer('Введите юзернейм тг для связи(пример: @pasha):', reply_markup=types.ReplyKeyboardRemove())
    await AdForm.next() 

@dp.message_handler(state=AdForm.contact) # Обработчик для ввода контакта
async def process_contact(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['contact'] = message.text
    await message.answer('Нажмите на кнопку добавить фото и отправьте! (до 5), если фото несколько, то отправляйте по одной фотографии', reply_markup=keyboard_photo)
    await AdForm.next()

@dp.message_handler(lambda message: message.text == 'Добавить фото', state=AdForm.photo)
async def add_photo(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        # Инициализация списка photos, если его еще нет
        if 'photos' not in data:
            data['photos'] = []
        await message.answer('Отправьте фото. Вы можете добавить до 5 фото. После отправки нажмите "Далее"', reply_markup=keyboard_photo)

@dp.message_handler(content_types=['photo'], state=AdForm.photo)
async def process_photo(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['photos'].append(message.photo[-1].file_id)
        await message.answer('Фото добавлено! Отправьте еще, или нажмите "Далее"', reply_markup=keyboard_photo)

@dp.message_handler(lambda message: message.text == 'Далее', state=AdForm.photo)
async def send_ad(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if 'photos' not in data or not data['photos']:
            await message.answer('Фото обязательно нужно добавить! 📸')
            return
         
        text = f"<b>ПРОДАМ!</b>\n" \
               f"<b>Название:</b> {data['name']}\n" \
               f"<b>Описание:</b> {data['description']}\n" \
               f"<b>Цена:</b> {data['price']}\n" \
               f"<b>Контакт:</b> {data['contact']}"
         
        media = types.MediaGroup()
        first_photo = True
        for photo in data['photos']:
            if first_photo:
                media.attach(types.InputMediaPhoto(media=photo, caption=text, parse_mode='HTML'))
                first_photo = False
            else:
                media.attach(types.InputMediaPhoto(media=photo))
        await bot.send_media_group(chat_id=CHANNEL_ID, media=media)
        await message.answer('Объявление отправлено в канал! 🎉', reply_markup=keyboard_send)
        await state.finish()


@dp.message_handler(lambda message: message.text == 'Отправить', state=None)
async def confirm_send(message: types.Message):
    await message.answer('Объявление отправлено! 🎉')

@dp.message_handler(lambda message: message.text == 'Назад', state=None)
async def back_to_start(message: types.Message):
    await message.answer('Назад', reply_markup=keyboard_start)

@dp.message_handler(state=AdForm.content)
async def process_ad(message: types.Message, state: FSMContext):
    await state.update_data(content=message.text)
    moderation_keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton('Одобрить', callback_data='approve'))
    await bot.send_message(MODERATION_CHAT_ID, f"Объявление на модерацию:\n{message.text}", reply_markup=moderation_keyboard)
    await state.finish()

@dp.callback_query_handler(lambda c: c.data == 'approve')
async def process_callback_approve(callback_query: types.CallbackQuery):
    await bot.send_message(CHANNEL_ID, callback_query.message.text.replace("Объявление на модерацию:\n", ""))
    await bot.answer_callback_query(callback_query.id)
    await bot.edit_message_text(text=f"Одобрено: {callback_query.message.text}", chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
