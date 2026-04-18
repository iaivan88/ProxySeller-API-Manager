import os
import sys
import logging
from dotenv import load_dotenv

from api import ProxySellerClient
from cli import ProxySellerCLI

from rich.console import Console
from rich.panel import Panel

console = Console()

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("app.log", encoding="utf-8"),
        ]
    )

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
    console.print("\n[yellow]API-ключ не найден в окружении.[/yellow]")
    console.print("[dim]Вы можете получить его в личном кабинете ProxySeller.[/dim]")
    api_key = console.input("[bold cyan]Введите ваш API-ключ для ProxySeller:[/bold cyan] ").strip()
    
    if not api_key:
        console.print("[bold red]ОШИБКА: API-ключ не может быть пустым.[/bold red]")
        sys.exit(1)
        
    console.print("\n[bold green]Сохраняем ключ в .env файл для безопасности...[/bold green]")
    try:
        with open(".env", "a", encoding="utf-8") as file:
            file.write(f"\nPROXY_SELLER_API_KEY={api_key}\n")
    except Exception as e:
        console.print(f"[red]Не удалось сохранить в .env:[/red] {e}")
        
    return api_key

def main():
    setup_logging()
    load_dotenv()
    
    api_key = get_api_key()
    api_client = ProxySellerClient(api_key=api_key)
    cli_app = ProxySellerCLI(api_client)

    try:
        while True:
            choice = cli_app.display_menu()

            if choice == "1":
                lists = cli_app.api.get_lists()
                cli_app.display_lists(lists)
                console.input("\n[dim]Нажмите Enter для продолжения...[/dim]")
            elif choice == "2":
                cli_app.download_proxies()
                console.input("\n[dim]Нажмите Enter для продолжения...[/dim]")
            elif choice == "3":
                cli_app.create_lists()
                console.input("\n[dim]Нажмите Enter для продолжения...[/dim]")
            elif choice == "4":
                cli_app.rename_list()
                console.input("\n[dim]Нажмите Enter для продолжения...[/dim]")
            elif choice == "5":
                cli_app.delete_list()
                console.input("\n[dim]Нажмите Enter для продолжения...[/dim]")
            elif choice == "0":
                console.print("\n[bold blue]Выход из программы...[/bold blue]")
                break
            else:
                console.print("\n[red]Неверный выбор. Пожалуйста, попробуйте снова.[/red]")

    except KeyboardInterrupt:
        console.print("\n\n[bold yellow]Программа прервана пользователем[/bold yellow]")
    except Exception as e:
        console.print(f"\n[bold red]Критическая ошибка:[/bold red] {e}")
        logging.exception("Critical error")

if __name__ == "__main__":
    main()