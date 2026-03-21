import json
from strands import tool
from utils.shared import ORDERS


@tool
def get_order(customerId: str, orderId: str) -> str:
    """
    Retrieve order details and validate the order belongs to the given customer.

    Args:
        customerId: The customer's ID (obtained from get_customer).
        orderId: The order ID to look up.

    Returns:
        JSON string with the tool result envelope.
    """
    match = next(
        (o for o in ORDERS if o["orderId"] == orderId and o["customerId"] == customerId),
        None,
    )

    if match:
        content = {"orderId": match["orderId"], "customerId": match["customerId"], "status": match["status"]}
    else:
        content = {}

    return json.dumps({"result": {"content": content, "isError": False}})
