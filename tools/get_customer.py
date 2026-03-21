import json
from strands import tool

CUSTOMERS = [
    {"email": "john.smith@gmail.com", "customerId": "10001", "firstName": "John", "lastName": "Smith"},
    {"email": "jane.dow@yahoo.com",   "customerId": "10002", "firstName": "Jane", "lastName": "Dow"},
    {"email": "jack.black@gmail.com", "customerId": "10003", "firstName": "Jack", "lastName": "Black"},
]


@tool
def get_customer(email: str) -> str:
    """
    Look up a customer by their email address.

    Args:
        email: The customer's email address.

    Returns:
        JSON string with the tool result envelope.
    """
    match = next((c for c in CUSTOMERS if c["email"].lower() == email.lower()), None)

    if match:
        content = {
            "customerId": match["customerId"],
            "firstName": match["firstName"],
            "lastName": match["lastName"],
        }
    else:
        content = {}

    return json.dumps({"result": {"content": content, "isError": False}})
