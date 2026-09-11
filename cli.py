from assistant import assistant

# ANSI цветове
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"

def main():
    print(f"{GREEN}🟢 Local AI Assistant — напиши ':exit' за изход.{RESET}\n")

    while True:
        user_input = input(f"{CYAN}👉 Въведи въпрос към AI:\n> {RESET}").strip()

        # --- Команди ---
        if user_input.startswith(":"):

            if user_input == ":exit":
                print(f"{GREEN}👋 Assistant: До утре, Стефан!{RESET}")
                break

            if user_input == ":help":
                print(f"""
{BLUE}Достъпни команди:{RESET}
:exit        - излизане от AI режима
:clear       - изчистване на историята
:reset       - рестарт на модела
:mode        - показва текущия режим
:mode dialog - диалогов режим
:mode analysis - анализен режим
:history     - показва историята
:memory      - показва запомнените факти
:remember k v - запомня ключ → стойност
:forget k    - забравя ключ
:note        - добавяне на бележка
:help        - показва този списък
                """)
                continue

            if user_input == ":clear":
                assistant.reset()
                print(f"{BLUE}🧹 Историята е изчистена.{RESET}\n")
                continue

            if user_input == ":reset":
                assistant.reset()
                print(f"{BLUE}🔄 Моделът е рестартиран.{RESET}\n")
                continue

            if user_input == ":mode":
                print(f"{BLUE}🔍 Текущ режим: {assistant.mode}{RESET}\n")
                continue

            if user_input == ":history":
                history = assistant.get_history()
                # оцветяване на ролите
                history = history.replace("[SYSTEM]", f"{BLUE}[SYSTEM]{RESET}")
                history = history.replace("[USER]", f"{GREEN}[USER]{RESET}")
                history = history.replace("[ASSISTANT]", f"{YELLOW}[ASSISTANT]{RESET}")
                print(history)
                print()
                continue

            if user_input == ":memory":
                mem = assistant.format_memory()
                print(f"{BLUE}{mem}{RESET}\n")
                continue

            if user_input.startswith(":remember"):
                parts = user_input.split(maxsplit=2)
                if len(parts) == 3:
                    key, value = parts[1], parts[2]
                    assistant.remember(key, value)
                    assistant.reset()
                    print(f"{GREEN}💾 Запомнено: {key} = {value}{RESET}\n")
                else:
                    print(f"{RED}⚠️ Формат: :remember ключ стойност{RESET}\n")
                continue

            if user_input.startswith(":forget"):
                parts = user_input.split()
                if len(parts) == 2:
                    key = parts[1]
                    assistant.forget(key)
                    assistant.reset()
                    print(f"{YELLOW}🗑 Забравено: {key}{RESET}\n")
                else:
                    print(f"{RED}⚠️ Формат: :forget ключ{RESET}\n")
                continue

            if user_input.startswith(":note"):
                print(f"{YELLOW}📝 Бележката е записана (AI я игнорира).{RESET}\n")
                continue

            print(f"{RED}⚠️ Непозната командa. Напиши :help.{RESET}\n")
            continue

        # --- AI логика ---
        if not user_input:
            print(f"{RED}⚠️ Assistant: (празен вход){RESET}\n")
            continue

        answer = assistant.ask(user_input)

        if not answer:
            print(f"{RED}⚠️ Assistant: (празен отговор){RESET}\n")
            continue

        print(f"\n{YELLOW}🤖 Assistant:{RESET}\n{answer}\n")

if __name__ == "__main__":
    main()
