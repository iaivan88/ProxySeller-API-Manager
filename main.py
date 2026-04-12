import requests
import os
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class APIResponse:
    """Standardized API response"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None


class ProxySellerAPI:
    API_VERSION = "v1"
    BASE_DOMAIN = "https://proxy-seller.com/personal/api"

    def __init__(self):
        self.api_key = self.load_api_key()
        self.base_url = f'{self.BASE_DOMAIN}/{self.API_VERSION}/{self.api_key}/resident'
        self.session = self._create_session()
        self.output_file = "proxy_list.txt"
        self.results_dir = "Results"

    def _results_filepath(self, filename: str) -> str:
        os.makedirs(self.results_dir, exist_ok=True)
        return os.path.join(self.results_dir, filename)

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
        })
        return session

    def _make_request(self, method: str, endpoint: str, **kwargs) -> APIResponse:
        """HTTP request to resident API relative to base_url (e.g. lists, list/add)."""
        url = f"{self.base_url}/{endpoint}"
        try:
            response = self.session.request(method, url, **kwargs)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    return APIResponse(success=True, data=data.get("data"))
                errors = data.get("errors", "Unknown error")
                return APIResponse(success=False, error=str(errors))
            return APIResponse(
                success=False,
                error=f"HTTP {response.status_code}: {response.text}",
            )
        except requests.RequestException as e:
            return APIResponse(success=False, error=f"Request failed: {str(e)}")
        except json.JSONDecodeError as e:
            return APIResponse(success=False, error=f"Invalid JSON response: {str(e)}")
        except Exception as e:
            return APIResponse(success=False, error=f"Unexpected error: {str(e)}")

    def load_api_key(self, key_file: str = "api_key.txt") -> str:
        if os.path.exists(key_file):
            try:
                with open(key_file, "r", encoding="utf-8") as file:
                    api_key = file.read().strip()
                    if api_key:
                        return api_key
            except (OSError, UnicodeDecodeError) as e:
                print(f"Предупреждение: не удалось прочитать {key_file}: {e}")

        api_key = input("Введите ваш API-ключ для ProxySeller: ").strip()
        if not api_key:
            raise ValueError("API key cannot be empty")

        try:
            with open(key_file, "w", encoding="utf-8") as file:
                file.write(api_key)
        except OSError as e:
            print(f"Предупреждение: не удалось сохранить ключ в {key_file}: {e}")

        return api_key

    def get_lists(self) -> List[Dict]:
        """Get all existing IP lists"""
        response = self._make_request("GET", "lists")
        if not response.success:
            print(f"Ошибка при получении списков: {response.error}")
            return []

        data = response.data
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "items" in data:
            return data["items"]

        print("Ошибка: Неожиданная структура данных в ответе.")
        return []

    def _extract_countries(self, geo_info) -> List[str]:
        countries: List[str] = []
        if isinstance(geo_info, list):
            for geo in geo_info:
                if isinstance(geo, dict) and "country" in geo:
                    countries.append(geo["country"])
        elif isinstance(geo_info, dict) and "country" in geo_info:
            countries.append(geo_info["country"])
        return countries

    def display_lists(self, lists):
        """Display lists in a simple, comfortable format"""
        if not lists:
            print("Списков прокси не найдено или произошла ошибка при их получении.")
            return

        print("\n=== Доступные списки прокси ===")

        for i, item in enumerate(lists, 1):
            try:
                list_id = item.get('id', 'N/A')
                title = item.get('title', 'Без названия')
                countries = self._extract_countries(item.get("geo", []))
                countries_str = ", ".join(countries) if countries else "N/A"

                print(f"{i}. ID: {list_id} - {title} - Страны: {countries_str}")
            except Exception as e:
                print(f"Ошибка при отображении элемента списка: {str(e)}")
                # Print item structure for debugging
                print(f"Структура элемента: {type(item)}")
                if isinstance(item, dict):
                    print(f"Ключи элемента: {item.keys()}")

        print("=" * 30)

        # Return the lists for use in other functions
        return lists

    def download_proxies(self):
        """Download proxies from existing lists with support for range selection"""
        # First, get all lists
        lists = self.get_lists()
        available_lists = self.display_lists(lists)

        if not available_lists:
            return

        # Ask for list selection
        try:
            print("\nВы можете выбрать списки следующими способами:")
            print("1. Отдельные номера через запятую (например: 1,3,5)")
            print("2. Диапазон в квадратных скобках (например: [10, 20])")
            selection_input = input("\nВыберите номера списков для скачивания прокси: ")

            selections = []

            # Check if it's a range in square brackets
            if selection_input.strip().startswith('[') and selection_input.strip().endswith(']'):
                # Extract the range
                range_content = selection_input.strip()[1:-1]  # Remove the brackets
                range_parts = [part.strip() for part in range_content.split(',')]

                if len(range_parts) == 2 and range_parts[0].isdigit() and range_parts[1].isdigit():
                    start = int(range_parts[0])
                    end = int(range_parts[1])

                    # Create a list of all numbers in the range (inclusive)
                    selections = list(range(start, end + 1))
                else:
                    print("Ошибка: Неверный формат диапазона. Ожидается [start, end].")
                    return
            else:
                # Process as comma-separated list
                selections = [int(x.strip()) for x in selection_input.split(',') if x.strip().isdigit()]

            # Validate selections
            valid_selections = []
            for selection in selections:
                if 1 <= selection <= len(available_lists):
                    valid_selections.append(selection)
                else:
                    print(f"Предупреждение: Номер {selection} вне диапазона и будет пропущен.")

            if not valid_selections:
                print("Ошибка: Не выбрано ни одного действительного списка.")
                return

            # Choose proxy format
            print("\nВыберите формат прокси:")
            print("1. login:password@host:port (default)")
            print("2. login:password:host:port")
            print("3. host:port:login:password")
            print("4. host:port@login:password")

            format_choice = input("Выберите формат [1]: ") or "1"
            proxy_format = int(format_choice) if format_choice.isdigit() and 1 <= int(format_choice) <= 4 else 1

            # Choose export format
            print("\nВыберите формат экспорта:")
            print("1. txt (default)")
            print("2. csv")
            print("3. json")

            export_format = input("Выберите формат [1]: ") or "1"
            if export_format == "1":
                file_ext = "txt"
                export_type = "txt"
            elif export_format == "2":
                file_ext = "csv"
                export_type = "csv"
            elif export_format == "3":
                file_ext = "json"
                export_type = "json"
            else:
                file_ext = "txt"
                export_type = "txt"

            # Changed default to 'y' for merging files
            merge_files = input("\nОбъединить все прокси в один файл? (y/n, по умолчанию: y): ").lower() != 'n'

            # Process each selected list
            all_proxies = []
            selected_list_names = []
            successful_downloads = 0

            for selection in valid_selections:
                # Get the selected list
                selected_list = available_lists[selection - 1]
                list_id = selected_list.get('id')
                list_title = selected_list.get('title', f'proxies_{list_id}')

                countries = self._extract_countries(selected_list.get("geo", []))
                countries_str = "_".join(countries) if countries else "no_country"

                # Make API request to download proxies
                url = f'https://proxy-seller.com/personal/api/v1/{self.api_key}/proxy/download/resident'

                # Add listId parameter
                params = {
                    'format': export_type,
                    'listId': list_id
                }

                print(f"\nЗагрузка прокси из списка '{list_title}'...")

                try:
                    response = self.session.get(url, params=params)

                    if response.status_code == 200:
                        # Create a better filename based on list title and countries
                        safe_title = ''.join(c for c in list_title if c.isalnum() or c in ' _-').replace(' ', '_')
                        filename = self._results_filepath(f"{safe_title}_{countries_str}.{file_ext}")

                        # Keep track of list names for merged filename
                        selected_list_names.append(safe_title)

                        # Process the response based on the format
                        content = response.text
                        formatted_content = ""

                        # If user requested a specific format and we got raw data, convert it
                        if proxy_format != 1 and export_type == "txt":
                            # Assume one line per proxy in login:password@host:port format
                            lines = content.splitlines()
                            formatted_lines = []
                            for line in lines:
                                try:
                                    auth, host_port = line.split("@", 1)
                                    login, password = auth.split(":", 1)
                                    host, port = host_port.split(":", 1)

                                    if proxy_format == 2:
                                        formatted = f"{login}:{password}:{host}:{port}"
                                    elif proxy_format == 3:
                                        formatted = f"{host}:{port}:{login}:{password}"
                                    elif proxy_format == 4:
                                        formatted = f"{host}:{port}@{login}:{password}"
                                    else:
                                        formatted = line

                                    formatted_lines.append(formatted)
                                except Exception:
                                    formatted_lines.append(line)

                            # Join all formatted lines
                            formatted_content = "\n".join(formatted_lines)
                        else:
                            # Use the content as is
                            formatted_content = content

                        # If we're merging files, add to the list
                        if merge_files:
                            all_proxies.append(formatted_content)
                        else:
                            # Save to individual file
                            if export_type in ["txt", "csv"]:
                                with open(filename, "w", encoding="utf-8") as file:
                                    file.write(formatted_content)
                            elif export_type == "json":
                                try:
                                    json_data = response.json()
                                    with open(filename, "w", encoding="utf-8") as file:
                                        json.dump(json_data, file, indent=4, ensure_ascii=False)
                                except Exception as e:
                                    print(f"Ошибка при обработке JSON для списка '{list_title}': {str(e)}")
                                    with open(filename, "w", encoding="utf-8") as file:
                                        file.write(formatted_content)

                            print(f"Прокси успешно загружены и сохранены в файл '{filename}'.")

                        successful_downloads += 1
                    else:
                        print(
                            f'Ошибка при загрузке прокси из списка "{list_title}". Код ошибки: {response.status_code}')
                        print('Ответ сервера:', response.text)
                except Exception as e:
                    print(f"Произошла ошибка при загрузке прокси из списка '{list_title}': {str(e)}")

            # If we're merging files, save all proxies to one file
            if merge_files and all_proxies:
                # Create a filename based on selected list names
                if len(selected_list_names) <= 3:
                    # If 3 or fewer lists, include all names in the filename
                    lists_part = "_".join(selected_list_names)
                else:
                    # If more than 3 lists, use the first list name and a count
                    lists_part = f"{selected_list_names[0]}_and_{len(selected_list_names) - 1}_more"

                merged_filename = self._results_filepath(f"{lists_part}.{file_ext}")

                try:
                    with open(merged_filename, "w", encoding="utf-8") as file:
                        file.write("\n".join(all_proxies))

                    print(f"\nВсе прокси успешно объединены и сохранены в файл '{merged_filename}'.")
                except Exception as e:
                    print(f"Ошибка при сохранении объединенного файла: {str(e)}")

            print(f"\nУспешно обработано {successful_downloads} из {len(valid_selections)} выбранных списков.")

        except ValueError:
            print("Ошибка: Введите числовое значение.")
        except Exception as e:
            print(f"Произошла ошибка: {str(e)}")

    def create_lists(self):
        """Create one or multiple new IP lists with country presets"""
        # Define country presets
        country_presets = {
            "1": {"name": "Worldwide", "countries": ""},
            "2": {"name": "Europe",
                  "countries": "AT,AL,AD,BY,BE,BG,BA,GB,HU,DE,GR,GE,DK,IE,ES,IT,IS,LV,LT,LI,LU,MK,MT,MD,NO,PL,PT,RU,RO,SM,RS,SK,SI,UA,FI,FR,HR,ME,CZ,CH,SE,EE"},
            "3": {"name": "Asia",
                  "countries": "AZ,AM,AF,BD,BH,VN,IL,IN,ID,JO,IQ,IR,YE,KZ,KH,QA,CY,KG,CN,KP,KR,KW,LA,LB,MY,MV,MN,MM,NP,AE,OM,PK,PS,SA,SY,TJ,TH,TM,TR,UZ,PH,LK,JP"},
            "4": {"name": "South America", "countries": "AR,BO,BR,VE,GY,CO,PY,PE,SR,UY,CL,EC"},
            "5": {"name": "North America",
                  "countries": "AG,BS,BB,BZ,HT,GT,HN,GD,DM,DO,CA,CR,CU,MX,NI,PA,SV,VC,KN,LC,US,TT,JM"},
            "6": {"name": "Africa",
                  "countries": "DZ,AO,BJ,BW,BI,BF,GA,GM,GH,GN,GW,DJ,EG,ZM,CV,CM,KE,KM,CI,LS,LR,LY,MU,MR,MW,ML,MA,MZ,NA,NE,NG,RW,ST,SC,SN,SO,SD,SL,TZ,TG,TN,UG,CF,TD,PG,GQ,ER,ET,ZA,SS"}
        }

        print("\n=== Создание нового списка прокси ===")
        title = input("Введите название списка: ")

        # Ask how many lists to create
        try:
            num_lists = int(input("Сколько списков вы хотите создать (для получения более 1000 прокси)? [1]: ") or "1")
            if num_lists < 1:
                num_lists = 1
                print("Количество списков должно быть как минимум 1.")
        except ValueError:
            num_lists = 1
            print("Ошибка ввода. Установлено значение по умолчанию: 1 список.")

        print("\nПредустановленные паки стран:")
        for key, preset in country_presets.items():
            print(f"{key}. {preset['name']}")
        print("0. Ручной ввод стран (по умолчанию)")

        preset_choice = input("\nВыберите пак или 0 для ручного ввода: ").strip()

        if not preset_choice or preset_choice == "0":
            country = input(
                "Введите код или коды нескольких стран через запятую (https://www.iban.com/country-codes - коды стран): "
            ).upper().replace(" ", "")
        elif preset_choice in country_presets:
            country = country_presets[preset_choice]["countries"]
            print(f"Выбран пак: {country_presets[preset_choice]['name']}")
        else:
            print("Неверный выбор. Будет использован ручной ввод.")
            country = input(
                "Введите код или коды нескольких стран через запятую (https://www.iban.com/country-codes - коды стран): "
            ).upper().replace(" ", "")

        region = input("Введите регион (или оставьте пустым): ")
        city = input("Введите город (или оставьте пустым): ")
        isp = input("Введите провайдера (или оставьте пустым): ")

        # Получаем информацию о портах
        try:
            num_ports = int(input("Введите количество портов на список (максимум и по умолчанию 1000): ") or "1000")
            if num_ports > 1000:
                num_ports = 1000
                print("Максимальное количество портов ограничено до 1000.")
        except ValueError:
            num_ports = 1000
            print("Ошибка ввода. Установлено значение по умолчанию: 1000 портов.")

        # Получаем IP для белого списка
        whitelist = input("Введите IP-адреса для белого списка через запятую (или оставьте пустым): ")

        # Choose proxy format
        print("\nВыберите формат прокси:")
        print("1. login:password@host:port (default)")
        print("2. login:password:host:port")
        print("3. host:port:login:password")
        print("4. host:port@login:password")

        format_choice = input("Выберите формат [1]: ") or "1"
        proxy_format = int(format_choice) if format_choice.isdigit() and 1 <= int(format_choice) <= 4 else 1

        # Create lists
        total_proxies = 0
        all_proxy_lists = []

        for i in range(num_lists):
            list_title = title
            if num_lists > 1:
                list_title = f"{title} #{i + 1}"

            data = {
                'title': list_title,
                'whitelist': whitelist,
                'geo': {
                    'country': country,
                    'region': region,
                    'city': city,
                    'isp': isp
                },
                'ports': num_ports,
                'export': {
                    'ports': 10000,  # Начальный порт
                    'ext': 'txt'  # Формат экспорта
                }
            }

            try:
                response = self._make_request("POST", "list/add", json=data)
                if response.success and isinstance(response.data, dict):
                    proxy_data = response.data
                    print(f"\n=== Список прокси '{list_title}' успешно создан ===")
                    print(f"Название: {proxy_data.get('title', 'N/A')}")
                    proxy_list = self.generate_proxy_list(proxy_data, num_ports, proxy_format)
                    all_proxy_lists.extend(proxy_list)
                    total_proxies += len(proxy_list)
                else:
                    print("Ошибка при создании списка.")
                    if response.error:
                        print("Сообщение об ошибке:", response.error)
            except Exception as e:
                print(f"Произошла ошибка: {str(e)}")

        # Save all proxy lists to a single file
        if all_proxy_lists:
            # Create a safe filename
            safe_title = ''.join(c for c in title if c.isalnum() or c in ' _-').replace(' ', '_')
            filename = self._results_filepath(f"{safe_title}_proxies.txt")

            try:
                with open(filename, "w", encoding="utf-8") as file:
                    file.write("\n".join(all_proxy_lists))
                print(f"\nВсего создано {total_proxies} прокси в {num_lists} списках.")
                print(f"Прокси сохранены в файл '{filename}'.")
            except OSError as e:
                print(f"Ошибка при сохранении файла '{filename}': {e}")

        return total_proxies

    def generate_proxy_list(self, proxy_data, num_ports, format_type=1):
        """Generate proxy list in the specified format"""
        try:
            login = proxy_data.get("login")
            password = proxy_data.get("password")
            base_host = "res.proxy-seller.com"
            base_port = int(proxy_data.get("export", {}).get("ports", 10000))

            if login and password:
                # Generate proxy list in the specified format
                proxy_list = []

                for port in range(base_port, base_port + num_ports):
                    if format_type == 1:
                        # login:password@host:port
                        proxy = f"{login}:{password}@{base_host}:{port}"
                    elif format_type == 2:
                        # login:password:host:port
                        proxy = f"{login}:{password}:{base_host}:{port}"
                    elif format_type == 3:
                        # host:port:login:password
                        proxy = f"{base_host}:{port}:{login}:{password}"
                    elif format_type == 4:
                        # host:port@login:password
                        proxy = f"{base_host}:{port}@{login}:{password}"
                    else:
                        # Default format
                        proxy = f"{login}:{password}@{base_host}:{port}"

                    proxy_list.append(proxy)

                return proxy_list
            else:
                print("Ошибка: Не удалось получить логин и пароль из ответа сервера.")
        except Exception as e:
            print(f"Ошибка при генерации списка прокси: {str(e)}")

        return []

    def rename_list(self):
        """Rename an existing IP list"""
        # First, get all lists
        lists = self.get_lists()
        available_lists = self.display_lists(lists)

        if not available_lists:
            return

        # Ask for list selection
        try:
            selection = int(input("\nВыберите номер списка для переименования: "))

            if selection < 1 or selection > len(available_lists):
                print(f"Ошибка: выбран неверный номер списка.")
                return

            # Get the selected list
            selected_list = available_lists[selection - 1]
            list_id = selected_list.get('id')

            # Ask for new name
            new_title = input("Введите новое название для списка: ")

            data = {
                "id": list_id,
                "title": new_title,
            }

            response = self._make_request("POST", "list/rename", json=data)
            if response.success:
                print(f"Список успешно переименован в '{new_title}'.")
            else:
                print("Ошибка при переименовании списка.")
                print("Сообщение об ошибке:", response.error)
        except ValueError:
            print("Ошибка: Введите числовое значение.")
        except Exception as e:
            print(f"Произошла ошибка: {str(e)}")

    def delete_list(self):
        """Delete multiple existing IP lists with support for range selection"""
        # First, get all lists
        lists = self.get_lists()
        available_lists = self.display_lists(lists)

        if not available_lists:
            return

        # Ask for list selection
        try:
            print("\nВы можете выбрать списки следующими способами:")
            print("1. Отдельные номера через запятую (например: 1,3,5)")
            print("2. Диапазон в квадратных скобках (например: [10, 20])")
            selection_input = input("\nВыберите номера списков для удаления: ")

            selections = []

            # Check if it's a range in square brackets
            if selection_input.strip().startswith('[') and selection_input.strip().endswith(']'):
                # Extract the range
                range_content = selection_input.strip()[1:-1]  # Remove the brackets
                range_parts = [part.strip() for part in range_content.split(',')]

                if len(range_parts) == 2 and range_parts[0].isdigit() and range_parts[1].isdigit():
                    start = int(range_parts[0])
                    end = int(range_parts[1])

                    # Create a list of all numbers in the range (inclusive)
                    selections = list(range(start, end + 1))
                else:
                    print("Ошибка: Неверный формат диапазона. Ожидается [start, end].")
                    return
            else:
                # Process as comma-separated list
                selections = [int(x.strip()) for x in selection_input.split(',') if x.strip().isdigit()]

            # Validate selections
            valid_selections = []
            for selection in selections:
                if 1 <= selection <= len(available_lists):
                    valid_selections.append(selection)
                else:
                    print(f"Предупреждение: Номер {selection} вне диапазона и будет пропущен.")

            if not valid_selections:
                print("Ошибка: Не выбрано ни одного действительного списка.")
                return

            # Show selected lists
            print("\nВыбранные списки для удаления:")
            selected_lists = []
            for selection in valid_selections:
                selected_list = available_lists[selection - 1]
                list_id = selected_list.get('id')
                title = selected_list.get('title', 'Без названия')
                print(f"- {title} (ID: {list_id})")
                selected_lists.append((list_id, title))

            # Confirm deletion
            confirm = input(f"\nВы уверены, что хотите удалить {len(selected_lists)} выбранных списков? (y/n): ")
            if confirm.lower() != 'y':
                print("Операция отменена.")
                return

            # Delete each list
            deleted_count = 0
            for list_id, title in selected_lists:
                data = {"id": list_id}

                try:
                    # Документация: тело запроса с полем id (JSON)
                    response = self._make_request("DELETE", "list/delete", json=data)
                    if response.success:
                        print(f"Список '{title}' успешно удален.")
                        deleted_count += 1
                    else:
                        print(f"Ошибка при удалении списка '{title}'.")
                        print("Сообщение об ошибке:", response.error)
                except Exception as e:
                    print(f"Произошла ошибка при удалении списка '{title}': {str(e)}")

            print(f"\nУдалено {deleted_count} из {len(selected_lists)} выбранных списков.")

        except ValueError:
            print("Ошибка: Неверный формат ввода.")
        except Exception as e:
            print(f"Произошла ошибка: {str(e)}")


def display_menu():
    """Display the main menu"""
    print("\n" + "=" * 50)
    print("       ProxySeller API Manager")
    print("=" * 50)
    print("1. Получить существующие списки IP")
    print("2. Скачать прокси из существующего списка")
    print("3. Создать новый список (или несколько)")
    print("4. Переименовать список")
    print("5. Удалить списки")
    print("0. Выход")
    print("=" * 50)
    return input("Выберите опцию: ")


def main():
    try:
        proxy_api = ProxySellerAPI()

        while True:
            choice = display_menu()

            if choice == "1":
                lists = proxy_api.get_lists()
                proxy_api.display_lists(lists)
                input("\nНажмите Enter для продолжения...")

            elif choice == "2":
                proxy_api.download_proxies()
                input("\nНажмите Enter для продолжения...")

            elif choice == "3":
                proxy_api.create_lists()
                input("\nНажмите Enter для продолжения...")

            elif choice == "4":
                proxy_api.rename_list()
                input("\nНажмите Enter для продолжения...")

            elif choice == "5":
                proxy_api.delete_list()
                input("\nНажмите Enter для продолжения...")

            elif choice == "0":
                print("\nВыход из программы...")
                break

            else:
                print("\nНеверный выбор. Пожалуйста, попробуйте снова.")

    except KeyboardInterrupt:
        print("\n\nПрограмма прервана пользователем")
    except ValueError as e:
        print(f"\nОшибка: {e}")
    except Exception as e:
        print(f"\nКритическая ошибка: {e}")


if __name__ == "__main__":
    main()