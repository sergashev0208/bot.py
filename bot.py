import asyncio
import logging
import json
import aiohttp
import datetime
import os

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton,
    WebAppInfo, InputMediaPhoto, BufferedInputFile
)
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN, ADMIN_ID, MINI_APP_URL

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
users = set()


# ─── Main Menu ────────────────────────────────────────────────────────────────
def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛍 Katalog", web_app=WebAppInfo(url=MINI_APP_URL))],
            [KeyboardButton(text="📢 Telegram Kanal"), KeyboardButton(text="📸 Instagram")],
            [KeyboardButton(text="📞 Bog'lanish")],
            [KeyboardButton(text="💳 To'lov uchun karta raqami")],
        ],
        resize_keyboard=True
    )


# ─── /start ───────────────────────────────────────────────────────────────────
@dp.message(CommandStart())
async def cmd_start(message: Message):
    users.add(message.from_user.id)
    await message.answer(
        f"👋 Salom, <b>{message.from_user.first_name}</b>!\n\n"
        "💊 <b>🌱Vitaminki_maryam🌱</b> – Vitamin maxsulotlariga xush kelibsiz!\n\n"
        "🛍 Maxsulotlarni ko'rish uchun pastdagi katalog tugmani bosing:",
        parse_mode="HTML",
        reply_markup=main_menu()
    )


# ─── Telegram Kanal ───────────────────────────────────────────────────────────
@dp.message(F.text == "📢 Telegram Kanal")
async def telegram_kanal(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="📢 @Vitaminki_maryam kanaliga o'tish",
            url="https://t.me/Vitaminki_maryam"
        )]
    ])
    await message.answer(
        "📢 <b>Bizning Telegram kanalimiz:</b>\n\n"
        "🌱 Yangi mahsulotlar, chegirmalar va foydali ma'lumotlar uchun kanalimizga obuna bo'ling!",
        parse_mode="HTML",
        reply_markup=kb
    )


# ─── Instagram ────────────────────────────────────────────────────────────────
@dp.message(F.text == "📸 Instagram")
async def instagram(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="📸 @vitaminki_maryam sahifasiga o'tish",
            url="https://www.instagram.com/vitaminki_maryam"
        )]
    ])
    await message.answer(
        "📸 <b>Bizning Instagram sahifamiz:</b>\n\n"
        "🌿 Mahsulotlar haqida videolar, mijozlar fikrlari va aksiyalar uchun kuzatib boring!",
        parse_mode="HTML",
        reply_markup=kb
    )


# ─── Bog'lanish ───────────────────────────────────────────────────────────────
@dp.message(F.text == "📞 Bog'lanish")
async def boglanish(message: Message):
    await message.answer(
        "📞 <b>Biz bilan bog'laning:</b>\n\n"
        "👤 Menejer: @vitaminki_maryamm\n"
        "📱 Tel: +998 91 088 30 08\n"
        "🕐 Ish vaqti: 9:00 – 20:00",
        parse_mode="HTML",
        reply_markup=main_menu()
    )


# ─── Karta ───────────────────────────────────────────────────────────────────
@dp.message(F.text == "💳 To'lov uchun karta raqami")
async def karta(message: Message):
    await message.answer(
        "💳  <b>5614 6821 1843 6106  Otkurova Irodaxon</b>\n\n"
        "💰To'lovni amalga oshirib chekni shu yerga👉@vitaminki_maryamm👈 yuborishingizni so'raymiz\n"
        "💖Haridingizdan mamnunmiz",
        parse_mode="HTML",
        reply_markup=main_menu()
    )


# ─── Rasmni URL dan yuklab olish ──────────────────────────────────────────────
async def download_image(session: aiohttp.ClientSession, url: str) -> bytes | None:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Referer": "https://sergashev0208.github.io/",
        "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
    }
    try:
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            logging.info(f"Rasm yuklab olish: {url} → HTTP {resp.status}")
            if resp.status == 200:
                return await resp.read()
            logging.warning(f"Rasm yuklanmadi: HTTP {resp.status} | URL: {url}")
            return None
    except Exception as e:
        logging.warning(f"Rasm yuklab olishda xato: {e} | URL: {url}")
        return None


# ─── WebApp order ─────────────────────────────────────────────────────────────
@dp.message(F.web_app_data)
async def web_app_order(message: Message):
    try:
        data  = json.loads(message.web_app_data.data)
        user  = message.from_user
        items = data['items']

        items_text = "\n".join(
            f"  • {item['name']} x{item['qty']} — {item['price'] * item['qty']:,} so'm"
            for item in items
        )

        # ── Joylashuv ma'lumotlari ────────────────────────────────────────────
        location = data.get('location')

        if location:
            lat = float(location['lat'])
            lng = float(location['lng'])
            yandex_url = f"https://yandex.com/maps/?pt={lng},{lat}&z=17&l=map"
            location_line_buyer = f"🗺 <a href='{yandex_url}'>Yandex Maps da ko'rish</a>"
            location_line_admin = (
                f"📡 GPS: <code>{location['lat']}, {location['lng']}</code>\n"
                f"🗺 <a href='{yandex_url}'>Yandex Maps da ochish</a>"
            )
        else:
            location_line_buyer = "📍 Joylashuv berilmagan"
            location_line_admin = "📡 GPS: berilmagan"

        # ── Xaridorga tasdiqlash ──────────────────────────────────────────────
        await message.answer(
            f"✅ <b>Buyurtmangiz qabul qilindi!</b>\n\n"
            f"📦 Mahsulotlar:\n{items_text}\n\n"
            f"💰 Jami: <b>{data['total']:,} so'm</b>\n"
            f"📍 Manzil: {data.get('address', 'Kiritilmagan')}\n"
            f"📱 Telefon: {data.get('phone', 'Kiritilmagan')}\n"
            f"{location_line_buyer}\n\n"
            f"⏳ Menejer tez orada siz bilan bog'lanadi!",
            parse_mode="HTML",
            reply_markup=main_menu()
        )

        # ── Admin uchun matn ──────────────────────────────────────────────────
        admin_text = (
            f"🛒 <b>YANGI ZAKAZ!</b>\n\n"
            f"👤 Xaridor: <a href='tg://user?id={user.id}'>{user.full_name}</a>\n"
            f"🆔 ID: <code>{user.id}</code>\n"
            f"📱 Username: @{user.username or 'yo`q'}\n\n"
            f"📦 Mahsulotlar:\n{items_text}\n\n"
            f"💰 Jami: <b>{data['total']:,} so'm</b>\n"
            f"📍 Manzil: {data.get('address', '—')}\n"
            f"📞 Telefon: {data.get('phone', '—')}\n"
            f"💬 Izoh: {data.get('comment', '—')}\n"
            f"{location_line_admin}"
        )

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Qabul qildim",  callback_data=f"accept_{user.id}")],
            [InlineKeyboardButton(text="❌ Bekor qilish",  callback_data=f"cancel_{user.id}")]
        ])

        items_with_image = [it for it in items if it.get('image')]

        logging.info(
            f"Zakaz: jami {len(items)} mahsulot | rasmli: {len(items_with_image)}"
        )

        # ── Admin ga xabar yuborish ───────────────────────────────────────────
        if not items_with_image:
            # Rasmlar yo'q — faqat matn yuboramiz
            await bot.send_message(ADMIN_ID, admin_text, parse_mode="HTML", reply_markup=kb)

        elif len(items_with_image) == 1:
            # Bitta rasm — oddiy send_photo
            async with aiohttp.ClientSession() as session:
                img_bytes = await download_image(session, items_with_image[0]['image'])

            try:
                if img_bytes:
                    buf = BufferedInputFile(img_bytes, filename="product.jpg")
                    await bot.send_photo(
                        ADMIN_ID,
                        photo=buf,
                        caption=admin_text,
                        parse_mode="HTML",
                        reply_markup=kb
                    )
                else:
                    # Yuklanmadi — URL orqali urinib ko'ramiz
                    await bot.send_photo(
                        ADMIN_ID,
                        photo=items_with_image[0]['image'],
                        caption=admin_text,
                        parse_mode="HTML",
                        reply_markup=kb
                    )
            except Exception as e:
                logging.warning(f"send_photo xatosi: {e} — matn sifatida yuboramiz")
                await bot.send_message(ADMIN_ID, admin_text, parse_mode="HTML", reply_markup=kb)

        else:
            # Bir nechta rasm — media_group
            # MUHIM: barcha rasmlarni bytes sifatida yuklab olamiz,
            # shunda aralash format muammosi bo'lmaydi
            async with aiohttp.ClientSession() as session:
                # Barcha rasmlarni parallel holda yuklab olamiz
                download_tasks = [
                    download_image(session, item['image'])
                    for item in items_with_image[:10]
                ]
                downloaded = await asyncio.gather(*download_tasks)

            # Muvaffaqiyatli yuklab olingan rasmlardan media_group tuzamiz
            media_group = []
            for i, (item, img_bytes) in enumerate(zip(items_with_image[:10], downloaded)):
                caption = admin_text if i == 0 else None

                if img_bytes:
                    buf = BufferedInputFile(img_bytes, filename=f"product_{item['id']}.jpg")
                    media_group.append(InputMediaPhoto(
                        media=buf,
                        caption=caption,
                        parse_mode="HTML" if caption else None
                    ))
                else:
                    # Bu mahsulot rasmi yuklanmadi — o'tkazib yuboramiz
                    logging.warning(f"Rasm o'tkazib yuborildi: {item['name']} | {item['image']}")

            if not media_group:
                # Hech bir rasm yuklanmadi — faqat matn
                logging.warning("Hech bir rasm yuklanmadi, matn sifatida yuboramiz")
                await bot.send_message(ADMIN_ID, admin_text, parse_mode="HTML", reply_markup=kb)

            elif len(media_group) == 1:
                # Faqat 1 ta rasm muvaffaqiyatli yuklanган — send_photo ishlatamiz
                # (media_group kamida 2 ta item talab qiladi)
                single = media_group[0]
                try:
                    await bot.send_photo(
                        ADMIN_ID,
                        photo=single.media,
                        caption=admin_text,
                        parse_mode="HTML",
                        reply_markup=kb
                    )
                except Exception as e:
                    logging.warning(f"send_photo xatosi: {e}")
                    await bot.send_message(ADMIN_ID, admin_text, parse_mode="HTML", reply_markup=kb)

            else:
                # 2 yoki undan ko'p rasm — media_group yuboramiz
                try:
                    await bot.send_media_group(ADMIN_ID, media=media_group)
                    # Tugmalar media_group ga qo'shib bo'lmaydi,
                    # shuning uchun alohida xabar sifatida yuboramiz
                    await bot.send_message(
                        ADMIN_ID,
                        "⬆️ Yuqoridagi zakaz:",
                        reply_markup=kb
                    )
                    logging.info(f"✅ Media group ({len(media_group)} ta rasm) muvaffaqiyatli yuborildi")
                except Exception as media_err:
                    logging.error(f"Media group xatosi: {media_err} — matn sifatida yuboramiz")
                    await bot.send_message(ADMIN_ID, admin_text, parse_mode="HTML", reply_markup=kb)

        # ── Admin ga Telegram location pin ───────────────────────────────────
        if location:
            try:
                await bot.send_location(
                    ADMIN_ID,
                    latitude=float(location['lat']),
                    longitude=float(location['lng'])
                )
                logging.info("✅ Telegram location pin yuborildi")
            except Exception as loc_err:
                logging.warning(f"Location pin yuborishda xato: {loc_err}")

    except Exception as e:
        logging.error(f"WebApp data error: {e}", exc_info=True)
        await message.answer("❌ Xatolik yuz berdi. Iltimos qayta urinib ko'ring.")


# ─── Admin callback ───────────────────────────────────────────────────────────
@dp.callback_query(F.data.startswith("accept_"))
async def accept_order(call: CallbackQuery):
    user_id = int(call.data.split("_")[1])
    await bot.send_message(
        user_id,
        "✅ Buyurtmangiz tasdiqlandi! Yetkazib berish vaqti: 1-2 kun."
    )
    await call.message.edit_text(
        call.message.text + "\n\n✅ <b>TASDIQLANDI</b>",
        parse_mode="HTML"
    )


@dp.callback_query(F.data.startswith("cancel_"))
async def cancel_order(call: CallbackQuery):
    user_id = int(call.data.split("_")[1])
    await bot.send_message(
        user_id,
        "❌ Afsuski, buyurtmangiz bekor qilindi. Savollar uchun: @vitaminki_maryamm"
    )
    await call.message.edit_text(
        call.message.text + "\n\n❌ <b>BEKOR QILINDI</b>",
        parse_mode="HTML"
    )


# ─── Weekly Broadcast ────────────────────────────────────────────────────────
async def weekly_broadcast():
    while True:
        now = datetime.datetime.now()
        if now.weekday() == 6 and now.hour == 12 and now.minute == 0:
            for user_id in users:
                try:
                    await bot.send_message(
                        user_id,
                        "🌱 <b>Mahsulotlarimiz sizga manzur kevotimi?</b>\n\n"
                        "😍 Chegirmalardan foydalanib qolin!",
                        parse_mode="HTML"
                    )
                except Exception as e:
                    logging.warning(f"Userga yuborilmadi {user_id}: {e}")
            await asyncio.sleep(60)
        await asyncio.sleep(30)


# ─── Run ──────────────────────────────────────────────────────────────────────
async def main():
    asyncio.create_task(weekly_broadcast())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
