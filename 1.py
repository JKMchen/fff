# telethon_batch_10_mass_mpf_fixed.py - Kumpulin 10 CC → kirim mass /mpf benar ke pokahotmail_bot, file ke pokacc_bot
import re
import asyncio
import random
import logging
import io
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.types import InputFile

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────
api_id = 32189892
api_hash = 'ed094448a27b1c7c04f46bc30d3de1ae'
session_name = 'poka1337_telethon'

CHANNELS = ['@ccinfoz', '@kingscraperr']

CHECKER_BOT1 = '@pokacc_bot'      # kirim sebagai FILE 10 CC
CHECKER_BOT2 = '@pokahotmail_bot' # kirim /mpf + CC di baris pertama, sisanya baris baru

BATCH_SIZE = 10

# Regex CC
CC_REGEX = re.compile(r'(\d{16})[|\s:_•-]*(\d{1,2})[|\s:_•-]*(\d{2,4})[|\s:_•-]*(\d{3,4})', re.IGNORECASE)

client = TelegramClient(session_name, api_id, api_hash)

cc_buffer = []  # buffer global

def normalize_cc(cc_num, mm, yy, cvv):
    mm = mm.zfill(2)
    if len(yy) == 2:
        yy = "20" + yy if int(yy) < 50 else "19" + yy
    return f"{cc_num}|{mm}|{yy}|{cvv}"

async def process_batch():
    global cc_buffer
    if len(cc_buffer) < BATCH_SIZE:
        return

    logger.info(f"[BATCH SIAP] {len(cc_buffer)} CC → kirim mass ke kedua bot")

    batch_cc = cc_buffer[:BATCH_SIZE]
    cc_buffer = cc_buffer[BATCH_SIZE:]  # ambil 10, sisanya tetap di buffer kalau ada

    # 1. Kirim FILE ke @pokacc_bot
    file_content = "\n".join(batch_cc) + "\n"
    file_name = f"cc_batch_{len(batch_cc)}.txt"
    file_io = io.BytesIO(file_content.encode('utf-8'))
    file_io.name = file_name

    try:
        await client.send_file(CHECKER_BOT1, file_io, caption="Batch 10 CC", file_name=file_name)
        logger.info(f"[OK FILE] ke {CHECKER_BOT1}: {file_name} ({len(batch_cc)} CC)")
    except Exception as e:
        logger.error(f"[GAGAL FILE] {CHECKER_BOT1}: {str(e)}")

    await asyncio.sleep(random.uniform(2.0, 5.0))

    # 2. Kirim mass ke @pokahotmail_bot dengan format benar:
    # /mpf CC1
    # CC2
    # CC3
    # dst
    if batch_cc:
        mass_message = f"/mpf {batch_cc[0]}\n" + "\n".join(batch_cc[1:])
        try:
            await client.send_message(CHECKER_BOT2, mass_message)
            logger.info(f"[OK MASS] ke {CHECKER_BOT2}: /mpf + {len(batch_cc)} CC dalam 1 pesan")
        except Exception as e:
            logger.error(f"[GAGAL MASS] {CHECKER_BOT2}: {str(e)}")

    logger.info("[BATCH SELESAI] Buffer update. Siap kumpulin lagi")

@client.on(events.NewMessage(chats=CHANNELS))
async def cc_handler(event):
    global cc_buffer

    chat = await event.get_chat()
    chat_username = chat.username if hasattr(chat, 'username') and chat.username else 'unknown'
    sender = event.sender_id if event.sender_id else 'channel/anon'
    logger.info(f"[POST BARU] @{chat_username} | Msg ID: {event.id} | Sender: {sender} | {event.date}")

    if not event.message.text:
        logger.debug("Bukan text → skip")
        return

    text = event.message.text.strip()
    logger.info(f"[ISI POST] {text[:400]}{'...' if len(text) > 400 else ''}")

    matches = CC_REGEX.findall(text)
    if not matches:
        logger.info("[NO CC MATCH]")
        return

    added = 0
    for cc_num, mm, yy, cvv in matches:
        full_cc = normalize_cc(cc_num, mm, yy, cvv)
        if full_cc not in cc_buffer:
            cc_buffer.append(full_cc)
            added += 1

    logger.info(f"[DITAMBAH] {added} CC baru dari post ini → total buffer: {len(cc_buffer)} / {BATCH_SIZE}")

    if len(cc_buffer) >= BATCH_SIZE:
        await process_batch()

async def main():
    await client.start()
    me = await client.get_me()
    logger.info("╔════════════════════════════════════════════╗")
    logger.info("║ Telethon BATCH 10 + MASS /mpf FIXED ONLINE ║")
    logger.info(f"║ Akun : {me.first_name} (@{me.username or 'no username'}) | ID: {me.id} ║")
    logger.info(f"║ Monitor : {', '.join(CHANNELS)}            ║")
    logger.info(f"║ Batch ke : {CHECKER_BOT1} (FILE) & {CHECKER_BOT2} (/mpf + mass CC) ║")
    logger.info("╚════════════════════════════════════════════╝")
    logger.info(f"Kumpulin sampai >= {BATCH_SIZE}, lalu kirim mass dengan /mpf di baris pertama")

    # Test pull recent
    for channel in CHANNELS:
        try:
            logger.info(f"Pull 5 pesan terakhir dari {channel}...")
            async for msg in client.iter_messages(channel, limit=5):
                text_snip = msg.text[:150] if msg.text else 'no text'
                logger.info(f"[PULL OK] {channel} | ID {msg.id} | Date {msg.date} | Text: {text_snip}")
        except Exception as e:
            logger.warning(f"Gagal pull {channel}: {str(e)}")

    logger.info("Monitor real-time... (Ctrl+C stop)")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
