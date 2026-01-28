# Sipariş Botu ve Yönetim Paneli

Bu proje, bir Telegram botu ve bir masaüstü yönetim panelinden oluşmaktadır.

## Kurulum

1.  Gerekli kütüphaneleri yükleyin:
    ```bash
    pip install python-telegram-bot customtkinter
    ```

2.  Projeyi çalıştırın:
    ```bash
    python main.py
    ```

## Özellikler

*   **Telegram Botu:**
    *   Müşteriler Kahve ve Kuru Meyve siparişi verebilir.
    *   Sepet sistemi ve ödeme onayı.
*   **Yönetim Paneli (Admin):**
    *   Gelen siparişleri görme ve durumunu güncelleme (Ödendi/Teslim Edildi).
    *   Ürün stok ve fiyat yönetimi.
    *   Geçmiş siparişler ve ciro takibi.
    *   Ayarlar (IBAN, Karşılama Mesajı).

## Notlar

*   Database otomatik olarak `shop.db` adıyla oluşturulur.
*   Bot token `src/bot_app.py` dosyasında tanımlıdır. Güvenlik için ortam değişkeni kullanmanız önerilir.
