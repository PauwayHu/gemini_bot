from ai_client import GeminiChatBot


def main():
    print("正在啟動阿橘聊天模組...（輸入 exit 離開）")
    bot = GeminiChatBot()
    print("啟動完成！可以直接開始對話。\n")

    while True:
        try:
            user_input = input("你：")
            if user_input.strip().lower() in {"exit", "quit"}:
                print("阿橘：掰啦，記得早點睡！")
                break

            reply = bot.ask(user_input)
            print(f"阿橘：{reply}\n")

        except KeyboardInterrupt:
            print("\n阿橘：強制關機喔？掰啦！")
            break


if __name__ == "__main__":
    main()