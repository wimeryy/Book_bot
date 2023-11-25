from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message
from Book_bot.database.database import init_db, add_user
from Book_bot.filters.filters import IsDelBookmarkCallbackData, IsDigitCallbackData
from Book_bot.keyboards.bookmarks_kb import (create_bookmarks_keyboard,
                                            create_edit_keyboard)
from Book_bot.keyboards.pagination_kb import create_pagination_keyboard
from Book_bot.lexicon.lexicon import LEXICON
from Book_bot.services.file_handling import book

router = Router()


@router.message(CommandStart())
async def process_start_command(message: Message):
    await message.answer(LEXICON[message.text])

    conn, cursor = init_db()

    user_id = str(message.from_user.id)
    cursor.execute('SELECT pages FROM pages WHERE user_id = %s', (user_id,))
    existing_user = cursor.fetchone()

    if not existing_user:
        add_user(cursor, conn, user_id)


@router.message(Command(commands='help'))
async def process_help_command(message: Message):
    await message.answer(LEXICON[message.text])


@router.message(Command(commands='beginning'))
async def process_beginning_command(message: Message):

    page_number = 1

    text = book[page_number]

    await message.answer(
        text=text,
        reply_markup=create_pagination_keyboard(
            'backward',
            f'{page_number}/{len(book)}',
            'forward'
        )
    )



@router.message(Command(commands='continue'))
async def process_continue_command(message: Message):

    conn, cursor = init_db()
    user_id = str(message.from_user.id)
    cursor.execute("SELECT page_number FROM pages WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()

    if result != (0,):
        page_number = result[0]
    else:
        page_number = 1

        cursor.execute("UPDATE pages SET page_number = %s WHERE user_id = %s", (page_number, user_id))
        conn.commit()
    text = book[page_number]

    await message.answer(
        text=text,
        reply_markup=create_pagination_keyboard(
            'backward',
            f'{page_number}/{len(book)}',
            'forward'
        )
    )


@router.message(Command(commands='bookmarks'))
async def process_bookmarks_command(message: Message):
    user_id = str(message.from_user.id)

    conn, cursor = init_db()
    cursor.execute("SELECT bookmarks FROM pages WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()

    if result is not None and result[0]:
        bookmarks = result[0]
        await message.answer(
            text=LEXICON[message.text],
            reply_markup=create_bookmarks_keyboard(*bookmarks)
        )
    else:
        await message.answer(text=LEXICON['no_bookmarks'])


@router.callback_query(F.data == 'forward')
async def process_forward_press(callback: CallbackQuery):
    user_id = str(callback.from_user.id)

    conn, cursor = init_db()

    cursor.execute("SELECT page_number FROM pages WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()

    if result != (0,):
        current_page = result[0]
        next_page = current_page + 1

        if next_page < len(book):
            cursor.execute("UPDATE pages SET page_number = %s WHERE user_id = %s", (next_page, user_id))
            conn.commit()

            text = book[next_page]
            await callback.message.edit_text(
                text=text,
                reply_markup=create_pagination_keyboard(
                    'backward',
                    f'{next_page}/{len(book)}',
                    'forward'
                )
            )
        else:
            await callback.answer("Вы достигли последней страницы.")
    else:
        await callback.answer("Произошла ошибка. Пожалуйста, начните сначала.")


@router.callback_query(F.data == 'backward')
async def process_backward_press(callback: CallbackQuery):

    user_id = str(callback.from_user.id)

    conn, cursor = init_db()

    cursor.execute("SELECT page_number FROM pages WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()

    if result != (0,) and result != (1,):
        current_page = result[0]
        back_page = current_page - 1

        if back_page < len(book):
            cursor.execute("UPDATE pages SET page_number = %s WHERE user_id = %s", (back_page, user_id))
            conn.commit()

            text = book[back_page]
            await callback.message.edit_text(
                text=text,
                reply_markup=create_pagination_keyboard(
                    'backward',
                    f'{back_page}/{len(book)}',
                    'forward'
                )
            )
        else:
            await callback.answer("Вы достигли первой страницы.")
    else:
        await callback.answer("Произошла ошибка. Пожалуйста, начните сначала.")


@router.callback_query(lambda x: '/' in x.data and x.data.replace('/', '').isdigit())
async def process_page_press(callback: CallbackQuery):
    user_id = str(callback.from_user.id)

    conn, cursor = init_db()
    cursor.execute("SELECT page_number FROM pages WHERE user_id = %s", (user_id,))
    page = cursor.fetchone()

    cursor.execute("SELECT bookmarks FROM pages WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()

    if result is not None:
        bookmarks = result[0] if result[0] else []
    else:
        bookmarks = []

    if page not in bookmarks:
        bookmarks.append(page)

        cursor.execute("UPDATE pages SET bookmarks = %s WHERE user_id = %s", (bookmarks, user_id))
        conn.commit()

        await callback.answer('Страница добавлена в закладки!')
    else:
        await callback.answer('Страница уже в закладках.')


@router.callback_query(IsDigitCallbackData())
async def process_bookmark_press(callback: CallbackQuery):
    user_id = str(callback.from_user.id)
    page = int(callback.data)

    conn, cursor = init_db()

    cursor.execute("UPDATE pages SET page_number = %s WHERE user_id = %s", (page, user_id))
    conn.commit()

    text = book[page]
    await callback.message.edit_text(
        text=text,
        reply_markup=create_pagination_keyboard(
            'backward',
            f'{page}/{len(book)}',
            'forward'
        )
    )
    await callback.answer()

@router.callback_query(F.data == 'edit_bookmarks')
async def process_edit_press(callback: CallbackQuery):
    user_id = str(callback.from_user.id)

    conn, cursor = init_db()

    cursor.execute("SELECT bookmarks FROM pages WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()

    if result is not None:
        bookmarks = result[0] if result[0] else []

        if bookmarks:
            await callback.message.edit_text(
                text=LEXICON[callback.data],
                reply_markup=create_edit_keyboard(*bookmarks)
            )
        else:
            await callback.message.edit_text(text=LEXICON['no_bookmarks'])
        await callback.answer()
    else:
        await callback.answer("Произошла ошибка. Пожалуйста, начните сначала.")


@router.callback_query(F.data == 'cancel')
async def process_cancel_press(callback: CallbackQuery):
    await callback.message.edit_text(text=LEXICON['cancel_text'])
    await callback.answer()


@router.callback_query(IsDelBookmarkCallbackData())
async def process_del_bookmark_press(callback: CallbackQuery):
    user_id = str(callback.from_user.id)
    page_to_remove = int(callback.data[:-3])

    conn, cursor = init_db()

    cursor.execute("SELECT bookmarks FROM pages WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()

    if result is not None:
        bookmarks = result[0] if result[0] else []

        if page_to_remove in bookmarks:
            bookmarks.remove(page_to_remove)

            cursor.execute("UPDATE pages SET bookmarks = %s WHERE user_id = %s", (bookmarks, user_id))
            conn.commit()

            if bookmarks:
                await callback.message.edit_text(
                    text=LEXICON['/bookmarks'],
                    reply_markup=create_edit_keyboard(*bookmarks)
                )
            else:
                await callback.message.edit_text(text=LEXICON['no_bookmarks'])
            await callback.answer()
        else:
            await callback.answer("Страница не найдена в закладках.")
    else:
        await callback.answer("Произошла ошибка. Пожалуйста, начните сначала.")
