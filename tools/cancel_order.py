import json
from strands import tool
from utils.shared import ORDERS

RESOLUTION_MAP = {
    "SHIPPED":   "CANCELLED",
    "DELIVERED": "REFUND",
    "REFUNDED":  "ALREADY_REFUNDED",
}


@tool
def cancel_order(orderId: str) -> str:
    """
    Process the cancellation of a previously validated order.
    Must only be called after get_order has confirmed the order exists
    and belongs to the authenticated customer.

    Args:
        orderId: The validated order ID to cancel.

    Returns:
        JSON string with the tool result envelope.
    """
    order = next((o for o in ORDERS if o["orderId"] == orderId), None)

    if not order:
        return json.dumps({
            "result": {
                "content": {},
                "isError": True,
                "errorDetail": {
                    "code": "ORDER_NOT_FOUND",
                    "retryable": False,
                    "message": f"Order {orderId} not found.",
                },
            }
        })

    resolution = RESOLUTION_MAP[order["status"]]
    return json.dumps({"result": {"content": {"orderId": orderId, "resolution": resolution}, "isError": False}})
