import argparse

from app.llm import DEFAULT_MODEL, generate_response


def main():
    parser = argparse.ArgumentParser(description="Chatbot de Biaani (modo terminal)")
    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL,
        help="Modelo de Ollama que utilizará el chatbot",
    )
    args = parser.parse_args()

    model = args.model
    messages = []

    print("=" * 45)
    print("  CHATBOT BIAANI")
    print("=" * 45)
    print(f"Modelo utilizado: {model}")
    print("Escribe 'salir' para terminar.\n")

    while True:
        try:
            user_input = input("Tú: ").strip()

            if user_input.lower() == "salir":
                break
            if not user_input:
                continue

            messages.append({"role": "user", "content": user_input})
            answer = generate_response(messages, model)
            messages.append({"role": "assistant", "content": answer})

            print(f"\nBiaani: {answer}\n")

        except KeyboardInterrupt:
            print("\n\nChat interrumpido.")
            break

    print("\n" + "=" * 45)
    print(f"Modelo utilizado: {model}")
    print("Chatbot finalizado.")
    print("=" * 45)


if __name__ == "__main__":
    main()
