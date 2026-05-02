import os
import sys
import logging
from dotenv import load_dotenv

from api import ProxySellerClient
from cli import ProxySellerCLI
from locales import t, get_language, set_language

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

console = Console()

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("app.log", encoding="utf-8"),
        ]
    )

def check_language():
    if not get_language():
        console.print("Select language / Выберите язык:")
        console.print("1. English")
        console.print("2. Русский")
        choice = console.input("[1/2]: ").strip()
        if choice == "2":
            set_language("ru")
        else:
            set_language("en")

def get_api_key(key_file: str = "api_key.txt") -> str:
    # 1. Try environment variable
    api_key = os.getenv("PROXY_SELLER_API_KEY")
    if api_key:
        return api_key.strip()
        
    # 2. Try old key_file fallback
    if os.path.exists(key_file):
        try:
            with open(key_file, "r", encoding="utf-8") as file:
                api_key = file.read().strip()
                if api_key:
                    return api_key
        except Exception:
            pass

    # 3. Prompt user and save to .env
    console.print(t("api_key_not_found"))
    console.print(t("api_key_hint"))
    api_key = Prompt.ask(t("api_key_prompt"), password=True).strip()
    
    if not api_key:
        console.print(t("api_key_empty"))
        sys.exit(1)
        
    console.print(t("api_key_saving"))
    try:
        with open(".env", "a", encoding="utf-8") as file:
            file.write(f"\nPROXY_SELLER_API_KEY={api_key}\n")
    except Exception as e:
        console.print(t("api_key_save_error", error=e))
        
    return api_key

def main():
    setup_logging()
    load_dotenv()
    
    check_language()
    
    api_key = get_api_key()
    api_client = ProxySellerClient(api_key=api_key)
    cli_app = ProxySellerCLI(api_client)

    try:
        while True:
            choice = cli_app.display_menu()

            if choice == "1":
                lists = cli_app.api.get_lists()
                cli_app.display_lists(lists)
                console.input(t("press_enter"))
            elif choice == "2":
                cli_app.download_proxies()
                console.input(t("press_enter"))
            elif choice == "3":
                cli_app.create_lists()
                console.input(t("press_enter"))
            elif choice == "4":
                cli_app.rename_list()
                console.input(t("press_enter"))
            elif choice == "5":
                cli_app.delete_list()
                console.input(t("press_enter"))
            elif choice == "6":
                cli_app.get_consumption()
                console.input(t("press_enter"))
            elif choice == "7":
                cli_app.change_language()
                console.input(t("press_enter"))
            elif choice == "0":
                console.print(t("exiting"))
                break
            else:
                console.print(t("invalid_choice"))

    except KeyboardInterrupt:
        console.print(t("interrupted"))
    except Exception as e:
        console.print(t("critical_error", error=e))
        logging.exception("Critical error")

if __name__ == "__main__":
    main()