import os
import json
import logging
from typing import List, Dict

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn

from api import ProxySellerClient
from models import ExportFormat, ProxyFormat
from utils import parse_user_selection, extract_countries

logger = logging.getLogger(__name__)
console = Console()

class ProxySellerCLI:
    def __init__(self, api_client: ProxySellerClient):
        self.api = api_client
        self.results_dir = "Results"

    def _results_filepath(self, filename: str) -> str:
        os.makedirs(self.results_dir, exist_ok=True)
        return os.path.join(self.results_dir, filename)

    def display_menu(self):
        console.print("\n")
        menu_text = (
            "1. Получить существующие списки IP\n"
            "2. Скачать прокси из существующего списка\n"
            "3. Создать новый список (или несколько)\n"
            "4. Переименовать список\n"
            "5. Удалить списки\n"
            "0. Выход"
        )
        console.print(Panel(menu_text, title="ProxySeller API Manager", border_style="cyan"))
        return console.input("[bold cyan]Выберите опцию:[/bold cyan] ")

    def display_lists(self, lists: List[Dict]) -> List[Dict]:
        """Display lists in a formatted rich table."""
        if not lists:
            console.print("[yellow]Списков прокси не найдено или произошла ошибка при их получении.[/yellow]")
            return []

        table = Table(title="Доступные списки прокси", show_header=True, header_style="bold magenta")
        table.add_column("№", style="cyan", justify="right")
        table.add_column("ID", style="dim")
        table.add_column("Название", style="green")
        table.add_column("Страны", style="yellow")

        for i, item in enumerate(lists, 1):
            try:
                list_id = item.get('id', 'N/A')
                title = item.get('title', 'Без названия')
                countries = extract_countries(item.get("geo", []))
                countries_str = ", ".join(countries) if countries else "Не указано"
                
                table.add_row(str(i), str(list_id), str(title), str(countries_str))
            except Exception as e:
                logger.error(f"Error displaying item: {e}")
                table.add_row(str(i), "-", "[red]Ошибка отображения списка[/red]", "-")
                
        console.print(table)
        return lists

    def download_proxies(self):
        """Interactive download process"""
        lists = self.api.get_lists()
        available_lists = self.display_lists(lists)
        if not available_lists:
            return

        console.print("\n[bold]Вы можете выбрать списки следующими способами:[/bold]")
        console.print("1. Отдельные номера через запятую (например: [cyan]1,3,5[/cyan])")
        console.print("2. Диапазон в квадратных скобках (например: [cyan][10, 20][/cyan])")
        selection_input = console.input("\n[bold cyan]Выберите номера списков для скачивания прокси:[/bold cyan] ")

        valid_selections = parse_user_selection(selection_input, len(available_lists))
        if not valid_selections:
            console.print("[red]Ошибка: Не выбрано ни одного действительного списка.[/red]")
            return

        console.print("\n[bold]Выберите формат прокси:[/bold]")
        console.print("1. [cyan]login:password@host:port[/cyan] (default)")
        console.print("2. [cyan]login:password:host:port[/cyan]")
        console.print("3. [cyan]host:port:login:password[/cyan]")
        console.print("4. [cyan]host:port@login:password[/cyan]")
        
        format_choice = console.input("Выберите формат [dim][1][/dim]: ") or "1"
        try:
            proxy_format = ProxyFormat(int(format_choice))
        except ValueError:
            proxy_format = ProxyFormat.LOGIN_PASS_HOST_PORT

        console.print("\n[bold]Выберите формат экспорта:[/bold]")
        console.print("1. [cyan]txt[/cyan] (default)")
        console.print("2. [cyan]csv[/cyan]")
        console.print("3. [cyan]json[/cyan]")
        
        export_choice = console.input("Выберите формат [dim][1][/dim]: ") or "1"
        export_type = ExportFormat.TXT
        if export_choice == "2":
            export_type = ExportFormat.CSV
        elif export_choice == "3":
            export_type = ExportFormat.JSON

        merge_files = console.input("\nОбъединить все прокси в один файл? (y/n, по умолчанию: y): ").lower() != 'n'

        all_proxies = []
        selected_list_names = []
        successful_downloads = 0

        # We'll use a progress bar for downloading
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True
        ) as progress:
            task = progress.add_task("[green]Скачивание прокси...", total=len(valid_selections))

            for selection in valid_selections:
                selected_list = available_lists[selection - 1]
                list_id = selected_list.get('id')
                list_title = selected_list.get('title', f'proxies_{list_id}')
                countries = extract_countries(selected_list.get("geo", []))
                countries_str = "_".join(countries) if countries else "no_country"

                progress.update(task, description=f"Загрузка прокси из '{list_title}'...")
                response = self.api.download_proxies_from_list(list_id, export_type)
                
                if response and response.status_code == 200:
                    safe_title = ''.join(c for c in list_title if c.isalnum() or c in ' _-').replace(' ', '_')
                    filename = self._results_filepath(f"{safe_title}_{countries_str}.{export_type.value}")
                    selected_list_names.append(safe_title)
                    
                    content = response.text
                    formatted_content = content
                    
                    if proxy_format != ProxyFormat.LOGIN_PASS_HOST_PORT and export_type == ExportFormat.TXT:
                        lines = content.splitlines()
                        formatted_lines = []
                        for line in lines:
                            try:
                                auth, host_port = line.split("@", 1)
                                login, password = auth.split(":", 1)
                                host, port = host_port.split(":", 1)
                                
                                if proxy_format == ProxyFormat.LOGIN_PASS_COLON_HOST_PORT:
                                    formatted = f"{login}:{password}:{host}:{port}"
                                elif proxy_format == ProxyFormat.HOST_PORT_LOGIN_PASS:
                                    formatted = f"{host}:{port}:{login}:{password}"
                                elif proxy_format == ProxyFormat.HOST_PORT_AT_LOGIN_PASS:
                                    formatted = f"{host}:{port}@{login}:{password}"
                                else:
                                    formatted = line
                                formatted_lines.append(formatted)
                            except Exception:
                                formatted_lines.append(line)
                        formatted_content = "\n".join(formatted_lines)

                    if merge_files:
                        all_proxies.append(formatted_content)
                    else:
                        if export_type in [ExportFormat.TXT, ExportFormat.CSV]:
                            with open(filename, "w", encoding="utf-8") as file:
                                file.write(formatted_content)
                        elif export_type == ExportFormat.JSON:
                            try:
                                json_data = response.json()
                                with open(filename, "w", encoding="utf-8") as file:
                                    json.dump(json_data, file, indent=4, ensure_ascii=False)
                            except Exception as e:
                                logger.error(f"Error saving JSON: {e}")
                                with open(filename, "w", encoding="utf-8") as file:
                                    file.write(formatted_content)
                        console.print(f"[green]✔[/green] Список '{list_title}' сохранен в '{filename}'.")
                    
                    successful_downloads += 1
                else:
                    code = response.status_code if response else "Unknown"
                    console.print(f"[red]✖ Ошибка при загрузке '{list_title}'. Код: {code}[/red]")

                progress.advance(task)

        if merge_files and all_proxies:
            lists_part = "_".join(selected_list_names[:3])
            if len(selected_list_names) > 3:
                lists_part += f"_and_{len(selected_list_names) - 3}_more"
            
            merged_filename = self._results_filepath(f"{lists_part}.{export_type.value}")
            try:
                with open(merged_filename, "w", encoding="utf-8") as file:
                    file.write("\n".join(all_proxies))
                console.print(f"\n[bold green]✔ Все прокси объединены в файл '{merged_filename}'.[/bold green]")
            except Exception as e:
                console.print(f"[red]Ошибка при сохранении файла: {e}[/red]")

        console.print(f"\n[cyan]Обработано {successful_downloads} из {len(valid_selections)} выбранных списков.[/cyan]")

    def create_lists(self):
        """Interactive create lists process"""
        country_presets = {
            "1": {"name": "Worldwide", "countries": ""},
            "2": {"name": "Europe", "countries": "AT,AL,AD,BY,BE,BG,BA,GB,HU,DE,GR,GE,DK,IE,ES,IT,IS,LV,LT,LI,LU,MK,MT,MD,NO,PL,PT,RU,RO,SM,RS,SK,SI,UA,FI,FR,HR,ME,CZ,CH,SE,EE"},
            "3": {"name": "Asia", "countries": "AZ,AM,AF,BD,BH,VN,IL,IN,ID,JO,IQ,IR,YE,KZ,KH,QA,CY,KG,CN,KP,KR,KW,LA,LB,MY,MV,MN,MM,NP,AE,OM,PK,PS,SA,SY,TJ,TH,TM,TR,UZ,PH,LK,JP"},
            "4": {"name": "South America", "countries": "AR,BO,BR,VE,GY,CO,PY,PE,SR,UY,CL,EC"},
            "5": {"name": "North America", "countries": "AG,BS,BB,BZ,HT,GT,HN,GD,DM,DO,CA,CR,CU,MX,NI,PA,SV,VC,KN,LC,US,TT,JM"},
            "6": {"name": "Africa", "countries": "DZ,AO,BJ,BW,BI,BF,GA,GM,GH,GN,GW,DJ,EG,ZM,CV,CM,KE,KM,CI,LS,LR,LY,MU,MR,MW,ML,MA,MZ,NA,NE,NG,RW,ST,SC,SN,SO,SD,SL,TZ,TG,TN,UG,CF,TD,PG,GQ,ER,ET,ZA,SS"}
        }

        console.print("\n[bold magenta]=== Создание нового списка прокси ===[/bold magenta]")
        title = console.input("[bold cyan]Введите название списка:[/bold cyan] ")
        
        try:
            num_lists = int(console.input("[bold cyan]Сколько списков вы хотите создать (для получения более 1000 прокси)? [dim][1][/dim]:[/bold cyan] ") or "1")
            num_lists = max(1, num_lists)
        except ValueError:
            num_lists = 1

        console.print("\n[bold]Предустановленные паки стран:[/bold]")
        for key, preset in country_presets.items():
            console.print(f"[cyan]{key}[/cyan]. {preset['name']}")
        console.print("[cyan]0[/cyan]. Ручной ввод стран (по умолчанию)")

        preset_choice = console.input("\n[bold cyan]Выберите пак или 0 для ручного ввода:[/bold cyan] ").strip()
        
        if preset_choice in country_presets:
            country = country_presets[preset_choice]["countries"]
            console.print(f"Выбран пак: [green]{country_presets[preset_choice]['name']}[/green]")
        else:
            country = console.input("[bold cyan]Введите код или коды нескольких стран через запятую\n(подсказка: коды стран можно найти на https://www.iban.com/country-codes):[/bold cyan] ").upper().replace(" ", "")

        region = console.input("[bold cyan]Введите регион (или оставьте пустым):[/bold cyan] ")
        city = console.input("[bold cyan]Введите город (или оставьте пустым):[/bold cyan] ")
        isp = console.input("[bold cyan]Введите провайдера (или оставьте пустым):[/bold cyan] ")
        
        try:
            num_ports = int(console.input("[bold cyan]Введите количество портов на список (максимум и по умолчанию 1000):[/bold cyan] ") or "1000")
            num_ports = min(1000, max(1, num_ports))
        except ValueError:
            num_ports = 1000
            
        whitelist = console.input("[bold cyan]Введите IP-адреса для белого списка через запятую (или оставьте пустым):[/bold cyan] ")
        
        console.print("\n[bold]Выберите формат прокси:[/bold]")
        console.print("1. [cyan]login:password@host:port[/cyan] (default)")
        console.print("2. [cyan]login:password:host:port[/cyan]")
        console.print("3. [cyan]host:port:login:password[/cyan]")
        console.print("4. [cyan]host:port@login:password[/cyan]")
        
        format_choice = console.input("[bold cyan]Выберите формат [dim][1][/dim]:[/bold cyan] ") or "1"
        try:
            proxy_format = ProxyFormat(int(format_choice))
        except ValueError:
            proxy_format = ProxyFormat.LOGIN_PASS_HOST_PORT

        total_proxies = 0
        all_proxy_lists = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True
        ) as progress:
            task = progress.add_task("[green]Создание списков...", total=num_lists)

            for i in range(num_lists):
                list_title = title if num_lists == 1 else f"{title} #{i + 1}"
                progress.update(task, description=f"Создание списка '{list_title}'...")
                response = self.api.create_list(list_title, country, region, city, isp, whitelist, num_ports)
                
                if response.success and isinstance(response.data, dict):
                    proxy_data = response.data
                    console.print(f"[green]✔[/green] Список '{list_title}' успешно создан.")
                    proxy_list = self._generate_proxy_list(proxy_data, num_ports, proxy_format)
                    all_proxy_lists.extend(proxy_list)
                    total_proxies += len(proxy_list)
                else:
                    console.print(f"[red]✖ Ошибка создания списка '{list_title}': {response.error}[/red]")
                
                progress.advance(task)

        if all_proxy_lists:
            safe_title = ''.join(c for c in title if c.isalnum() or c in ' _-').replace(' ', '_')
            filename = self._results_filepath(f"{safe_title}_proxies.txt")
            try:
                with open(filename, "w", encoding="utf-8") as file:
                    file.write("\n".join(all_proxy_lists))
                console.print(f"\n[bold green]Всего создано {total_proxies} прокси. Сохранены в '{filename}'.[/bold green]")
            except Exception as e:
                console.print(f"[red]Ошибка сохранения файла: {e}[/red]")

    def _generate_proxy_list(self, proxy_data: dict, num_ports: int, format_type: ProxyFormat) -> List[str]:
        login = proxy_data.get("login")
        password = proxy_data.get("password")
        base_host = "res.proxy-seller.com"
        base_port = int(proxy_data.get("export", {}).get("ports", 10000))
        
        if not (login and password):
            logger.error("Failed to get login/password from response")
            return []

        proxy_list = []
        for port in range(base_port, base_port + num_ports):
            if format_type == ProxyFormat.LOGIN_PASS_HOST_PORT:
                proxy = f"{login}:{password}@{base_host}:{port}"
            elif format_type == ProxyFormat.LOGIN_PASS_COLON_HOST_PORT:
                proxy = f"{login}:{password}:{base_host}:{port}"
            elif format_type == ProxyFormat.HOST_PORT_LOGIN_PASS:
                proxy = f"{base_host}:{port}:{login}:{password}"
            elif format_type == ProxyFormat.HOST_PORT_AT_LOGIN_PASS:
                proxy = f"{base_host}:{port}@{login}:{password}"
            else:
                proxy = f"{login}:{password}@{base_host}:{port}"
            proxy_list.append(proxy)
        return proxy_list

    def rename_list(self):
        lists = self.api.get_lists()
        available_lists = self.display_lists(lists)
        if not available_lists:
            return

        try:
            selection = int(console.input("\n[bold cyan]Выберите номер списка:[/bold cyan] "))
            if selection < 1 or selection > len(available_lists):
                console.print("[red]Неверный номер.[/red]")
                return
                
            selected_list = available_lists[selection - 1]
            new_title = console.input("[bold cyan]Введите новое название:[/bold cyan] ")
            
            response = self.api.rename_list(selected_list.get('id'), new_title)
            if response.success:
                console.print(f"[bold green]Список переименован в '{new_title}'.[/bold green]")
            else:
                console.print(f"[bold red]Ошибка:[/bold red] {response.error}")
        except ValueError:
            console.print("[red]Неверный формат ввода.[/red]")

    def delete_list(self):
        lists = self.api.get_lists()
        available_lists = self.display_lists(lists)
        if not available_lists:
            return

        console.print("\n[bold]Вы можете выбрать списки следующими способами:[/bold]")
        console.print("1. Отдельные номера через запятую (например: [cyan]1,3,5[/cyan])")
        console.print("2. Диапазон в квадратных скобках (например: [cyan][10, 20][/cyan])")
        selection_input = console.input("\n[bold cyan]Выберите номера списков для удаления:[/bold cyan] ")

        valid_selections = parse_user_selection(selection_input, len(available_lists))
        
        if not valid_selections:
            return
            
        console.print("\n[bold]Выбранные списки для удаления:[/bold]")
        selected_lists = []
        for selection in valid_selections:
            selected_list = available_lists[selection - 1]
            selected_lists.append(selected_list)
            console.print(f"- [yellow]{selected_list.get('title', 'N/A')}[/yellow] (ID: {selected_list.get('id')})")
            
        confirm = console.input(f"\n[bold red]Удалить {len(selected_lists)} списков? (y/n):[/bold red] ")
        if confirm.lower() != 'y':
            console.print("[yellow]Операция отменена.[/yellow]")
            return
            
        deleted_count = 0
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True
        ) as progress:
            task = progress.add_task("[red]Удаление списков...", total=len(selected_lists))

            for l in selected_lists:
                response = self.api.delete_list(l.get('id'))
                if response.success:
                    console.print(f"[green]✔[/green] Список '{l.get('title')}' удален.")
                    deleted_count += 1
                else:
                    console.print(f"[red]✖ Ошибка удаления '{l.get('title')}': {response.error}[/red]")
                progress.advance(task)
                
        console.print(f"\n[bold cyan]Удалено {deleted_count} из {len(selected_lists)} списков.[/bold cyan]")
