import os
import io
import fitz
import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")

WATERMARK = "أكاديمية د. حسان"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "مرحباً بك في بوت أكاديمية د. حسان ❤️\n"
        "أرسل ملف PDF لإضافة إشعار الأكاديمية."
    )

def add_watermark(pdf_data):
    doc = fitz.open(stream=pdf_data, filetype="pdf")
    output = io.BytesIO()

    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    pdfmetrics.registerFont(TTFont("Arabic", font_path))

    for page in doc:
        width = page.rect.width
        height = page.rect.height

        overlay = io.BytesIO()
        c = canvas.Canvas(overlay, pagesize=(width, height))

        text = get_display(arabic_reshaper.reshape(WATERMARK))

        c.saveState()
        c.setFillAlpha(0.18)
        c.setFillColorRGB(0.2, 0.2, 0.2)
        c.setFont("Arabic", 27)
        c.translate(width / 2, height / 2)
        c.rotate(35)
        c.drawCentredString(0, 0, text)
        c.restoreState()

        c.save()

        overlay_doc = fitz.open(
            stream=overlay.getvalue(), filetype="pdf"
        )
        page.show_pdf_page(page.rect, overlay_doc, 0)
        overlay_doc.close()

    doc.save(output)
    doc.close()

    return output.getvalue()

async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    document = message.document

    if not document.file_name.lower().endswith(".pdf"):
        await message.reply_text("فضلاً أرسل ملف PDF فقط.")
        return

    if document.file_size > 20 * 1024 * 1024:
        await message.reply_text("حجم الملف أكبر من الحد المسموح.")
        return

    await message.reply_text("جاري إضافة إشعار أكاديمية د. حسان...")

    try:
        telegram_file = await document.get_file()
        source = io.BytesIO()
        await telegram_file.download_to_memory(out=source)

        result = add_watermark(source.getvalue())

        await message.reply_document(
            document=io.BytesIO(result),
            filename="DrHassan_Academy.pdf",
            caption="تم تجهيز الملف بواسطة أكاديمية د. حسان ❤️"
        )

    except Exception as e:
        await message.reply_text("حدث خطأ أثناء معالجة الملف.")

def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN is missing")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(filters.Document.ALL, handle_pdf)
    )

    app.run_polling()

if __name__ == "__main__":
    main()
