from uuid import uuid4
from yookassa import Configuration, Payment
from .core.config import settings

Configuration.account_id = settings.YK_SHOP_ID
Configuration.secret_key = settings.YK_API_KEY

def yk_create_payment(amount_rub: int, booking_id: int) -> tuple[str, str]:
    """
    Возвращает (confirmation_url, payment_id)
    """
    idem_key = str(uuid4())
    payment = Payment.create(
        {
            "amount": {"value": f"{amount_rub:.2f}", "currency": "RUB"},
            "confirmation": {
                "type": "redirect",
                "return_url": f"{settings.BASE_URL}/payments/return",
            },
            "capture": True,
            "description": f"Бронь #{booking_id}",
            "metadata": {"booking_id": booking_id},
        },
        idem_key,
    )
    return payment.confirmation.confirmation_url, payment.id
