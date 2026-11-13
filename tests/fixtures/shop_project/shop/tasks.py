from celery import shared_task


@shared_task
def send_order_confirmation(order_id: int) -> None:
    """Placeholder task: sends a confirmation message for an order."""
