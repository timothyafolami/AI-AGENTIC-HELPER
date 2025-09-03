import os
import sys
from ai_agent import planning_agent


def main():
    thread_id = os.environ.get("THREAD_ID", "cli")
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
        print("You:", prompt)
        resp = planning_agent.chat(prompt, thread_id=thread_id)
        print("\nAssistant:\n" + resp)
        return

    print("🤖 AI Planning Assistant — CLI Demo")
    print("Type a message and press Enter. Ctrl+C to exit.\n")

    try:
        while True:
            msg = input("You: ").strip()
            if not msg:
                continue
            resp = planning_agent.chat(msg, thread_id=thread_id)
            print("\nAssistant:\n" + resp + "\n")
    except KeyboardInterrupt:
        print("\nBye!")


if __name__ == "__main__":
    main()
