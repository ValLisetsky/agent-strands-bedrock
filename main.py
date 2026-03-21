import os
from dotenv import load_dotenv

load_dotenv()

from agent import create_agent


def main():
    mode = os.environ.get("AGENT_MODE", "local")
    print(f"Starting order cancellation agent (mode: {mode}). Type 'exit' or 'quit' to stop.\n")

    agent = create_agent()

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break

        agent(user_input)
        print()


if __name__ == "__main__":
    main()
