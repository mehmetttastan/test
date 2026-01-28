import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)
from src.database import DatabaseManager

# --- CONFIG ---
TOKEN = "7810398939:AAFiR0mpnZJtcVL-Qw2LQ3yItr3v0y8he2Q"  # Provided by user
# ADMIN_ID will be fetched from DB or fallback

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- STATES ---
CATEGORY_SELECT, PRODUCT_SELECT, QUANTITY_SELECT, CART_ACTIONS, GET_INFO, DELIVERY_SELECT, COUPON_ASK, COUPON_INPUT, CONFIRM_ORDER, PAYMENT_WAIT = range(10)

db = DatabaseManager()

# --- HELPERS ---
def get_cart_text(cart):
    if not cart:
        return "Sepetiniz boş."
    text = "🛒 **GÜNCEL SEPETİNİZ**\n\n"
    total = 0
    for i, item in enumerate(cart, 1):
        text += f"{i}. {item['ad']}\n   _{item['adet']} Adet - {item['fiyat']} TL_\n"
        total += item['fiyat']
    text += f"\n💰 **Toplam Tutar: {total} TL**"
    return text

# --- HANDLERS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['sepet'] = []
    return await show_menu(update, context)

async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    welcome_msg = db.get_setting("welcome_message")
    if not welcome_msg:
        welcome_msg = "Hoşgeldiniz! Lütfen kategori seçin."
        
    keyboard = [
        [InlineKeyboardButton("☕ Kahve Çeşitleri", callback_data="Kahve")],
        [InlineKeyboardButton("🍎 Kuru Meyve Çeşitleri", callback_data="Kuru Meyve")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    msg_text = f"{welcome_msg}\n\n👇 **Lütfen bir kategori seçin:**"
    
    if update.message:
        await update.message.reply_text(msg_text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.callback_query.edit_message_text(msg_text, reply_markup=reply_markup, parse_mode='Markdown')
        
    return CATEGORY_SELECT

async def category_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    category = query.data
    context.user_data['current_category'] = category
    
    products = db.get_products_by_category(category)
    
    if not products:
        await query.edit_message_text(f"⚠️ {category} kategorisinde şu an ürün bulunmamaktadır.", 
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Geri Dön", callback_data="back")]]))
        return CATEGORY_SELECT # Actually logic needs to handle back

    keyboard = []
    for p in products:
        # p is a dict: {'id', 'name', 'price', ...}
        if p['stock'] > 0:
            btn_text = f"{p['name']} - {p['price']} TL"
            keyboard.append([InlineKeyboardButton(btn_text, callback_data=str(p['id']))])
        else:
            keyboard.append([InlineKeyboardButton(f"{p['name']} (Tükendi)", callback_data="ignore")])
            
    keyboard.append([InlineKeyboardButton("🔙 Kategori Seçimine Dön", callback_data="back_cat")])
    
    await query.edit_message_text(f"✨ **{category}** ürünleri:\nLütfen seçiminizi yapın:", 
                                  reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return PRODUCT_SELECT

async def product_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data == "back_cat":
        return await start(update, context)
    if data == "ignore":
        return PRODUCT_SELECT
        
    # Find product details again (or store them)
    product_id = int(data)
    # Simple lookup
    products = db.get_products_by_category(context.user_data['current_category'])
    selected_product = next((p for p in products if p['id'] == product_id), None)
    
    if not selected_product:
        await query.edit_message_text("Ürün bulunamadı.")
        return await start(update, context)
        
    context.user_data['temp_product'] = selected_product
    
    keyboard = [
        [
            InlineKeyboardButton("1", callback_data="1"),
            InlineKeyboardButton("2", callback_data="2"),
            InlineKeyboardButton("3", callback_data="3"),
            InlineKeyboardButton("4", callback_data="4"),
            InlineKeyboardButton("5", callback_data="5")
        ],
        [InlineKeyboardButton("🔙 Vazgeç", callback_data="cancel_item")]
    ]
    
    await query.edit_message_text(
        f"✅ Seçilen: *{selected_product['name']}*\n"
        f"Fiyat: {selected_product['price']} TL\n\n"
        "Kaç adet eklemek istersiniz? (Aşağıdan seçin veya yazın)",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    return QUANTITY_SELECT

async def quantity_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, qty_str: str):
    try:
        qty = int(qty_str)
        if qty <= 0: raise ValueError
    except ValueError:
        msg = await update.message.reply_text("Lütfen geçerli bir sayı girin.") if update.message else None
        return QUANTITY_SELECT

    product = context.user_data['temp_product']
    
    # Check stock
    if qty > product['stock']:
        text = f"⚠️ Yetersiz stok! Maksimum {product['stock']} adet alabilirsiniz.\nLütfen tekrar adet seçin:"
        
        # Re-show quantity buttons so user is not stuck
        keyboard = [
            [
                InlineKeyboardButton("1", callback_data="1"),
                InlineKeyboardButton("2", callback_data="2"),
                InlineKeyboardButton("3", callback_data="3"),
                InlineKeyboardButton("4", callback_data="4"),
                InlineKeyboardButton("5", callback_data="5")
            ],
            [InlineKeyboardButton("🔙 Vazgeç", callback_data="cancel_item")]
        ]
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return QUANTITY_SELECT

    total_price = product['price'] * qty
    
    # Add to cart
    context.user_data['sepet'].append({
        "id": product['id'],
        "ad": product['name'],
        "adet": qty,
        "fiyat": total_price
    })
    
    msg_text = f"📦 {product['name']} ({qty} adet) sepete eklendi.\nNe yapmak istersiniz?"
    keyboard = [
        [InlineKeyboardButton("➕ Başka Ürün Ekle", callback_data="add_more")],
        [InlineKeyboardButton("🛒 Sepeti Gör / Öde", callback_data="view_cart")]
    ]
    
    if update.callback_query:
        await update.callback_query.edit_message_text(msg_text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(msg_text, reply_markup=InlineKeyboardMarkup(keyboard))
        
    return CART_ACTIONS

async def quantity_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data == "cancel_item":
        # Go back to product list
        # Simulate category selection again
        # We need the update object to look like category selection
        update.callback_query.data = context.user_data['current_category']
        return await category_selected(update, context)
        
    return await quantity_handler(update, context, query.data)

async def quantity_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await quantity_handler(update, context, update.message.text)

async def cart_actions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    if query.data == "add_more":
        return await show_menu(update, context)
        
    if query.data == "view_cart":
        cart_text = get_cart_text(context.user_data['sepet'])
        keyboard = [
            [InlineKeyboardButton("➕ Ürün Ekle", callback_data="add_more")],
            [InlineKeyboardButton("✅ Siparişi Tamamla", callback_data="checkout")],
            [InlineKeyboardButton("🗑️ Sepeti Boşalt", callback_data="clear_cart")]
        ]
        await query.edit_message_text(cart_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return CART_ACTIONS
        
    if query.data == "clear_cart":
        context.user_data['sepet'] = []
        await query.edit_message_text("Sepet boşaltıldı.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Ana Menü", callback_data="add_more")]]))
        return CART_ACTIONS

    if query.data == "checkout":
        if not context.user_data['sepet']:
            await query.answer("Sepetiniz boş!", show_alert=True)
            return CART_ACTIONS
        await query.edit_message_text("👤 Lütfen **Ad, Soyad** ve **Telefon** numaranızı tek mesajda yazın:")
        return GET_INFO

async def get_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['customer_info'] = update.message.text
    
    keyboard = [
        [InlineKeyboardButton("🏢 Şirkete Teslimat", callback_data="Şirket")],
        [InlineKeyboardButton("📍 Maltepe Teslimatı", callback_data="Maltepe")],
        [InlineKeyboardButton("📍 Darıca Teslimatı", callback_data="Darıca")]
    ]
    await update.message.reply_text("🚚 Lütfen teslimat bölgesini seçin:", reply_markup=InlineKeyboardMarkup(keyboard))
    return DELIVERY_SELECT

async def delivery_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data['delivery'] = query.data
    
    # Ask for Coupon
    keyboard = [
        [InlineKeyboardButton("🎫 Kupon Kodu Gir", callback_data="yes_coupon")],
        [InlineKeyboardButton("⏩ Devam Et (Kupon Yok)", callback_data="no_coupon")]
    ]
    await query.edit_message_text("🎟️ **İndirim Kuponunuz var mı?**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return COUPON_ASK

async def coupon_ask(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    if query.data == "yes_coupon":
        await query.edit_message_text("Lütfen kupon kodunuzu yazın:")
        return COUPON_INPUT
    else:
        # No coupon
        context.user_data['coupon_code'] = None
        context.user_data['discount_amount'] = 0
        return await show_summary(update, context)

async def coupon_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    code = update.message.text.strip()
    coupon = db.get_coupon(code)
    
    msg_text = ""
    if coupon and coupon['is_active']:
        if coupon['usage_limit'] > 0 and coupon['used_count'] >= coupon['usage_limit']:
             msg_text = "❌ Bu kuponun kullanım limiti dolmuş."
             context.user_data['coupon_code'] = None
             context.user_data['discount_amount'] = 0
        else:
            # Valid
            total_price = sum(item['fiyat'] for item in context.user_data['sepet'])
            discount = (total_price * coupon['discount_percent']) / 100
            
            context.user_data['coupon_code'] = code
            context.user_data['discount_amount'] = discount
            
            msg_text = f"✅ **Kupon Uygulandı!**\n%{coupon['discount_percent']} indirim ({discount} TL) eklendi."
    else:
        msg_text = "❌ Geçersiz veya süresi dolmuş kupon kodu."
        context.user_data['coupon_code'] = None
        context.user_data['discount_amount'] = 0
        
    await update.message.reply_text(msg_text, parse_mode='Markdown')
    return await show_summary(update, context)

async def show_summary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    cart_text = get_cart_text(context.user_data['sepet'])
    discount = context.user_data.get('discount_amount', 0)
    
    total_raw = sum(item['fiyat'] for item in context.user_data['sepet'])
    final_total = total_raw - discount
    
    coupon_info = ""
    if discount > 0:
        coupon_info = f"\n🎟️ **İndirim:** -{discount} TL\n💰 **Ödenecek Tutar: {final_total} TL**"
    
    summary = (
        f"📋 **SİPARİŞ ÖZETİ**\n\n"
        f"{cart_text}\n"
        f"{coupon_info}\n\n"
        f"👤 **Müşteri:** {context.user_data['customer_info']}\n"
        f"🚚 **Teslimat:** {context.user_data['delivery']}\n\n"
        "Bilgiler doğruysa onaylayın."
    )
    
    keyboard = [
        [InlineKeyboardButton("✅ Onayla", callback_data="confirm")],
        [InlineKeyboardButton("❌ İptal", callback_data="cancel")]
    ]
    
    if update.message:
        await update.message.reply_text(summary, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    else:
         await update.callback_query.edit_message_text(summary, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
         
    return CONFIRM_ORDER

async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel":
        await query.edit_message_text("Sipariş iptal edildi.")
        return ConversationHandler.END
        
    # Show IBAN
    total_raw = sum(item['fiyat'] for item in context.user_data['sepet'])
    discount = context.user_data.get('discount_amount', 0)
    final_total = total_raw - discount
    
    iban_msg = db.get_setting("iban_message")
    
    msg = (
        "✅ **Siparişiniz Oluşturuldu!**\n\n"
        f"💰 **Ödenecek Toplam Tutar: {final_total} TL**\n\n"
        f"{iban_msg}\n\n"
        "Ödemeyi yaptıktan sonra lütfen aşağıdaki butona tıklayın:"
    )
    
    keyboard = [[InlineKeyboardButton("👨‍🍳 ÜRÜNLERİ HAZIRLA", callback_data="paid")]]
    
    await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return PAYMENT_WAIT

async def payment_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    # SAVE TO DB
    customer_info = context.user_data['customer_info']
    
    order_id = db.create_order(
        customer_name=customer_info, 
        phone="", # Parsing phone is hard without strict format
        delivery_method=context.user_data['delivery'], 
        cart_items=context.user_data['sepet'],
        coupon_code=context.user_data.get('coupon_code'),
        discount_amount=context.user_data.get('discount_amount', 0)
    )
    
    # Notify Admin
    admin_id = db.get_setting("admin_id")
    if admin_id:
        try:
            cart_summary = "\n".join([f"- {i['adet']}x {i['ad']}" for i in context.user_data['sepet']])
            final_total = sum(i['fiyat'] for i in context.user_data['sepet']) - context.user_data.get('discount_amount', 0)
            
            admin_msg = (
                f"🚨 **YENİ SİPARİŞ! #{order_id}**\n\n"
                f"{cart_summary}\n\n"
                f"👤 {customer_info}\n"
                f"🚚 {context.user_data['delivery']}\n"
                f"💰 {final_total} TL"
            )
            if context.user_data.get('coupon_code'):
                admin_msg += f"\n🎟️ Kupon: {context.user_data['coupon_code']}"
                
            await context.bot.send_message(chat_id=admin_id, text=admin_msg)
        except Exception as e:
            logger.error(f"Failed to send admin message: {e}")

    # Don't delete previous message (IBAN etc). Send NEW message.
    # Add restart button
    keyboard = [[InlineKeyboardButton("🔄 Yeni Sipariş Ver", callback_data="add_more")]]
            
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="🎉 Siparişiniz ve ödeme bildiriminiz alındı! Teşekkür ederiz.\nSiparişiniz hazırlanacaktır.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CART_ACTIONS # Return to state that handles "add_more" (re-mapped to start menu)

async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("İşlem iptal edildi.")
    return ConversationHandler.END

def create_bot_app():
    application = Application.builder().token(TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CATEGORY_SELECT: [CallbackQueryHandler(category_selected)],
            PRODUCT_SELECT: [CallbackQueryHandler(product_selected)],
            QUANTITY_SELECT: [
                CallbackQueryHandler(quantity_button),
                MessageHandler(filters.TEXT & ~filters.COMMAND, quantity_text)
            ],
            CART_ACTIONS: [CallbackQueryHandler(cart_actions)],
            GET_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_info)],
            DELIVERY_SELECT: [CallbackQueryHandler(delivery_select)],
            COUPON_ASK: [CallbackQueryHandler(coupon_ask)],
            COUPON_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, coupon_input)],
            CONFIRM_ORDER: [CallbackQueryHandler(confirm_order)],
            PAYMENT_WAIT: [CallbackQueryHandler(payment_received)]
        },
        fallbacks=[CommandHandler("cancel", cancel_handler)]
    )
    
    application.add_handler(conv_handler)
    return application

if __name__ == "__main__":
    app = create_bot_app()
    app.run_polling()
