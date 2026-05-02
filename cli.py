import os
import json
import logging
import re
from typing import List, Dict
from datetime import datetime, timedelta

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn

from api import ProxySellerClient
from models import ExportFormat, ProxyFormat
from utils import parse_user_selection, extract_countries
from locales import t, set_language

logger = logging.getLogger(__name__)
console = Console()

class ProxySellerCLI:
    def __init__(self, api_client: ProxySellerClient):
        self.api = api_client
        self.results_dir = "Results"

    def _results_filepath(self, filename: str) -> str:
        os.makedirs(self.results_dir, exist_ok=True)
        return os.path.join(self.results_dir, filename)

    def change_language(self):
        console.print("Select language / Выберите язык:")
        console.print("1. English")
        console.print("2. Русский")
        choice = console.input("[1/2]: ").strip()
        if choice == "2":
            set_language("ru")
            console.print("[green]Язык изменен на Русский.[/green]")
        else:
            set_language("en")
            console.print("[green]Language changed to English.[/green]")

    def display_menu(self):
        console.print("\n")
        menu_text = (
            f"{t('menu_1')}\n"
            f"{t('menu_2')}\n"
            f"{t('menu_3')}\n"
            f"{t('menu_4')}\n"
            f"{t('menu_5')}\n"
            f"{t('menu_6')}\n"
            f"{t('menu_7')}\n"
            f"{t('menu_0')}"
        )
        console.print(Panel(menu_text, title=t("menu_title"), border_style="cyan"))
        return console.input(t("menu_prompt"))

    def display_lists(self, lists: List[Dict]) -> List[Dict]:
        """Display lists in a formatted rich table."""
        if not lists:
            console.print(t("lists_not_found"))
            return []

        table = Table(title=t("lists_title"), show_header=True, header_style="bold magenta")
        table.add_column(t("col_num"), style="cyan", justify="right")
        table.add_column(t("col_id"), style="dim")
        table.add_column(t("col_name"), style="green")
        table.add_column(t("col_countries"), style="yellow")

        for i, item in enumerate(lists, 1):
            try:
                list_id = item.get('id', 'N/A')
                title = item.get('title', t("no_name"))
                countries = extract_countries(item.get("geo", []))
                countries_str = ", ".join(countries) if countries else t("not_specified")
                
                table.add_row(str(i), str(list_id), str(title), str(countries_str))
            except Exception as e:
                logger.error(f"Error displaying item: {e}")
                table.add_row(str(i), "-", t("list_display_error"), "-")
                
        console.print(table)
        return lists

    def download_proxies(self):
        """Interactive download process"""
        lists = self.api.get_lists()
        available_lists = self.display_lists(lists)
        if not available_lists:
            return

        console.print(t("select_ways"))
        console.print(t("select_way_1"))
        console.print(t("select_way_2"))
        selection_input = console.input(t("select_lists_dl"))

        valid_selections = parse_user_selection(selection_input, len(available_lists))
        if not valid_selections:
            console.print(t("invalid_selection"))
            return

        console.print(t("select_format"))
        console.print(t("format_1"))
        console.print(t("format_2"))
        console.print(t("format_3"))
        console.print(t("format_4"))
        
        format_choice = console.input(t("format_choice")) or "1"
        try:
            proxy_format = ProxyFormat(int(format_choice))
        except ValueError:
            proxy_format = ProxyFormat.LOGIN_PASS_HOST_PORT

        console.print(t("select_export"))
        console.print(t("export_1"))
        console.print(t("export_2"))
        console.print(t("export_3"))
        
        export_choice = console.input(t("export_choice")) or "1"
        export_type = ExportFormat.TXT
        if export_choice == "2":
            export_type = ExportFormat.CSV
        elif export_choice == "3":
            export_type = ExportFormat.JSON

        merge_files = console.input(t("merge_files")).lower() != 'n'

        all_proxies = []
        selected_list_names = []
        successful_downloads = 0

        # We'll use a progress bar for downloading
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True
        ) as progress:
            task = progress.add_task(t("dl_progress"), total=len(valid_selections))

            for selection in valid_selections:
                selected_list = available_lists[selection - 1]
                list_id = selected_list.get('id')
                list_title = selected_list.get('title', f'proxies_{list_id}')
                countries = extract_countries(selected_list.get("geo", []))
                countries_str = "_".join(countries) if countries else "no_country"

                progress.update(task, description=t("dl_list_progress", title=list_title))
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
                        console.print(t("dl_success", title=list_title, filename=filename))
                    
                    successful_downloads += 1
                else:
                    code = response.status_code if response else "Unknown"
                    console.print(t("dl_error", title=list_title, code=code))

                progress.advance(task)

        if merge_files and all_proxies:
            lists_part = "_".join(selected_list_names[:3])
            if len(selected_list_names) > 3:
                lists_part += f"_and_{len(selected_list_names) - 3}_more"
            
            merged_filename = self._results_filepath(f"{lists_part}.{export_type.value}")
            try:
                with open(merged_filename, "w", encoding="utf-8") as file:
                    file.write("\n".join(all_proxies))
                console.print(t("merged_success", filename=merged_filename))
            except Exception as e:
                console.print(t("file_save_error", error=e))

        console.print(t("processed_count", success=successful_downloads, total=len(valid_selections)))

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

        console.print(t("create_title"))
        title = console.input(t("enter_title"))
        
        try:
            num_lists = int(console.input(t("num_lists")) or "1")
            num_lists = max(1, num_lists)
        except ValueError:
            num_lists = 1

        console.print(t("preset_countries"))
        for key, preset in country_presets.items():
            console.print(f"[cyan]{key}[/cyan]. {preset['name']}")
        console.print(t("manual_countries"))

        preset_choice = console.input(t("preset_choice")).strip()
        
        if preset_choice in country_presets:
            country = country_presets[preset_choice]["countries"]
            console.print(t("selected_preset", name=country_presets[preset_choice]['name']))
        else:
            country = console.input(t("enter_countries")).upper().replace(" ", "")

        region = console.input(t("enter_region"))
        city = console.input(t("enter_city"))
        isp = console.input(t("enter_isp"))
        
        try:
            num_ports = int(console.input(t("num_ports")) or "1000")
            num_ports = min(1000, max(1, num_ports))
        except ValueError:
            num_ports = 1000
            
        whitelist = console.input(t("whitelist_ip"))
        
        console.print(t("select_format"))
        console.print(t("format_1"))
        console.print(t("format_2"))
        console.print(t("format_3"))
        console.print(t("format_4"))
        
        format_choice = console.input(t("format_choice")) or "1"
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
            task = progress.add_task(t("create_progress"), total=num_lists)

            for i in range(num_lists):
                list_title = title if num_lists == 1 else f"{title} #{i + 1}"
                progress.update(task, description=t("create_list_progress", title=list_title))
                response = self.api.create_list(list_title, country, region, city, isp, whitelist, num_ports)
                
                if response.success and isinstance(response.data, dict):
                    proxy_data = response.data
                    console.print(t("create_success", title=list_title))
                    proxy_list = self._generate_proxy_list(proxy_data, num_ports, proxy_format)
                    all_proxy_lists.extend(proxy_list)
                    total_proxies += len(proxy_list)
                else:
                    console.print(t("create_error", title=list_title, error=response.error))
                
                progress.advance(task)

        if all_proxy_lists:
            safe_title = ''.join(c for c in title if c.isalnum() or c in ' _-').replace(' ', '_')
            filename = self._results_filepath(f"{safe_title}_proxies.txt")
            try:
                with open(filename, "w", encoding="utf-8") as file:
                    file.write("\n".join(all_proxy_lists))
                console.print(t("total_created", total=total_proxies, filename=filename))
            except Exception as e:
                console.print(t("file_save_error", error=e))

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
            selection = int(console.input(t("select_list_num")))
            if selection < 1 or selection > len(available_lists):
                console.print(t("invalid_num"))
                return
                
            selected_list = available_lists[selection - 1]
            new_title = console.input(t("enter_new_title"))
            
            response = self.api.rename_list(selected_list.get('id'), new_title)
            if response.success:
                console.print(t("rename_success", title=new_title))
            else:
                console.print(t("error_prefix", error=response.error))
        except ValueError:
            console.print(t("invalid_format"))

    def delete_list(self):
        lists = self.api.get_lists()
        available_lists = self.display_lists(lists)
        if not available_lists:
            return

        console.print(t("select_ways"))
        console.print(t("select_way_1"))
        console.print(t("select_way_2"))
        selection_input = console.input(t("select_lists_del"))

        valid_selections = parse_user_selection(selection_input, len(available_lists))
        
        if not valid_selections:
            return
            
        console.print(t("selected_del"))
        selected_lists = []
        for selection in valid_selections:
            selected_list = available_lists[selection - 1]
            selected_lists.append(selected_list)
            console.print(f"- [yellow]{selected_list.get('title', 'N/A')}[/yellow] (ID: {selected_list.get('id')})")
            
        confirm = console.input(t("confirm_del", count=len(selected_lists)))
        if confirm.lower() != 'y':
            console.print(t("cancel_op"))
            return
            
        deleted_count = 0
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True
        ) as progress:
            task = progress.add_task(t("del_progress"), total=len(selected_lists))

            for l in selected_lists:
                response = self.api.delete_list(l.get('id'))
                if response.success:
                    console.print(t("del_success", title=l.get('title')))
                    deleted_count += 1
                else:
                    console.print(t("del_error", title=l.get('title'), error=response.error))
                progress.advance(task)
                
        console.print(t("del_count", deleted=deleted_count, total=len(selected_lists)))

    def get_consumption(self):
        console.print(t("cons_title"))
        console.print(t("cons_period"))
        console.print(t("period_1"))
        console.print(t("period_2"))
        console.print(t("period_3"))
        console.print(t("period_4"))
        
        period_choice = console.input(t("your_choice")) or "1"
        
        now = datetime.now()
        
        if period_choice == "1":
            date_start = (now - timedelta(days=1)).strftime("%d.%m.%Y")
            date_end = now.strftime("%d.%m.%Y")
        elif period_choice == "2":
            date_start = (now - timedelta(days=7)).strftime("%d.%m.%Y")
            date_end = now.strftime("%d.%m.%Y")
        elif period_choice == "3":
            date_start = (now - timedelta(days=30)).strftime("%d.%m.%Y")
            date_end = now.strftime("%d.%m.%Y")
        elif period_choice == "4":
            date_start = console.input(t("date_start"))
            date_end = console.input(t("date_end"))
        else:
            date_start = (now - timedelta(days=1)).strftime("%d.%m.%Y")
            date_end = now.strftime("%d.%m.%Y")
            
        login = console.input(t("login_filter"))
        login_filter = login if login else None
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True
        ) as progress:
            progress.add_task(t("fetch_cons_progress"), total=None)
            response = self.api.get_consumption(date_start, date_end, login=login_filter)
            
            progress.add_task(t("fetch_lists_progress"), total=None)
            existing_lists = self.api.get_lists()
            
        if response.success:
            console.print(t("cons_data_title", start=date_start, end=date_end))
            data = response.data
            if data:
                # Маппинг логинов в названия
                login_to_title = {}
                for lst in existing_lists:
                    l_login = lst.get('login')
                    l_title = lst.get('title')
                    if l_login and l_title:
                        login_to_title[l_login] = l_title

                # Общая статистика
                summary_text = (
                    t("bought_traffic", bytes=data.get('orders_bytes_formated', 'N/A'), amount=data.get('orders_amount', 'N/A')) +
                    t("used_traffic", bytes=data.get('used_bytes_formated', 'N/A'), amount=data.get('used_orders_amount', 'N/A')) +
                    t("price_per_gb", price=data.get('price_per_gb', 'N/A'))
                )
                console.print(Panel(summary_text, title=t("cons_summary"), border_style="blue"))
                
                # Таблица по прокси
                lists_data = data.get('lists', [])
                if lists_data:
                    table = Table(title=t("cons_details"), show_header=True, header_style="bold magenta")
                    table.add_column(t("col_group"), style="cyan")
                    table.add_column(t("col_used"), style="yellow", justify="right")
                    table.add_column(t("col_cost"), style="green", justify="right")
                    
                    # Группировка
                    grouped_data = {}
                    for item in lists_data:
                        login = item.get('login', 'N/A')
                        title = login_to_title.get(login)
                        
                        if title:
                            # Ищем ' #1', ' #2' и т.д. в конце строки
                            match = re.search(r'^(.*?)\s+#\d+$', title)
                            base_name = match.group(1).strip() if match else title
                        else:
                            base_name = login
                            
                        bytes_val = int(item.get('bytes', 0))
                        cost_str = str(item.get('cost', '$0')).replace('$', '')
                        try:
                            cost_val = float(cost_str)
                        except ValueError:
                            cost_val = 0.0
                            
                        if base_name not in grouped_data:
                            grouped_data[base_name] = {'bytes': 0, 'cost': 0.0, 'logins': []}
                        
                        grouped_data[base_name]['bytes'] += bytes_val
                        grouped_data[base_name]['cost'] += cost_val
                        grouped_data[base_name]['logins'].append(login)
                        
                    final_list = []
                    for base_name, grp in grouped_data.items():
                        final_list.append({
                            'base_name': base_name,
                            'bytes': grp['bytes'],
                            'cost': grp['cost'],
                            'count': len(grp['logins']),
                            'logins': grp['logins']
                        })
                        
                    # Сортируем по убыванию расхода
                    final_list.sort(key=lambda x: x['bytes'], reverse=True)
                    
                    for item in final_list:
                        base_name = item['base_name']
                        count = item['count']
                        
                        if count > 1:
                            display_name = f"{base_name}{t('lists_count_dim', count=count)}"
                        else:
                            login = item['logins'][0]
                            if base_name == login:
                                display_name = login
                            else:
                                display_name = f"{base_name}{t('login_dim', login=login)}"
                                
                        # Форматируем байты
                        size = float(item['bytes'])
                        power = 1024.0
                        n = 0
                        power_labels = {0: 'B', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
                        while size >= power and n < 4:
                            size /= power
                            n += 1
                        # Округляем до 1 знака после запятой
                        formatted_bytes = f"{size:.1f} {power_labels[n]}"
                        
                        # Форматируем стоимость
                        if item['cost'] == 0:
                            formatted_cost = "$0"
                        else:
                            formatted_cost = f"${item['cost']:.2f}"
                        
                        table.add_row(
                            display_name,
                            formatted_bytes,
                            formatted_cost
                        )
                    console.print(table)
            else:
                console.print(t("no_data"))
        else:
            console.print(t("fetch_error", error=response.error))
