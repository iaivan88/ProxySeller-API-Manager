import os
import json

SETTINGS_FILE = "settings.json"

LANGUAGES = {
    "ru": "Русский",
    "en": "English"
}

_current_lang = None

def get_language():
    global _current_lang
    if _current_lang is not None:
        return _current_lang
        
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                settings = json.load(f)
                _current_lang = settings.get("language")
        except Exception:
            pass
            
    return _current_lang

def set_language(lang):
    global _current_lang
    _current_lang = lang
    settings = {}
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                settings = json.load(f)
        except Exception:
            pass
    settings["language"] = lang
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4)
    except Exception:
        pass

TRANSLATIONS = {
    "ru": {
        "api_key_not_found": "[yellow]API-ключ не найден в окружении.[/yellow]",
        "api_key_hint": "[dim]Вы можете получить его в личном кабинете ProxySeller.[/dim]",
        "api_key_prompt": "[bold cyan]Введите ваш API-ключ для ProxySeller:[/bold cyan] ",
        "api_key_empty": "[bold red]ОШИБКА: API-ключ не может быть пустым.[/bold red]",
        "api_key_saving": "\n[bold green]Сохраняем ключ в .env файл для безопасности...[/bold green]",
        "api_key_save_error": "[red]Не удалось сохранить в .env:[/red] {error}",
        "press_enter": "\n[dim]Нажмите Enter для продолжения...[/dim]",
        "exiting": "\n[bold blue]Выход из программы...[/bold blue]",
        "invalid_choice": "\n[red]Неверный выбор. Пожалуйста, попробуйте снова.[/red]",
        "interrupted": "\n\n[bold yellow]Программа прервана пользователем[/bold yellow]",
        "critical_error": "\n[bold red]Критическая ошибка:[/bold red] {error}",
        
        "menu_title": "ProxySeller API Manager",
        "menu_1": "1. Получить существующие списки IP",
        "menu_2": "2. Скачать прокси из существующего списка",
        "menu_3": "3. Создать новый список (или несколько)",
        "menu_4": "4. Переименовать список",
        "menu_5": "5. Удалить списки",
        "menu_6": "6. Получить информацию о расходе",
        "menu_7": "7. Сменить язык / Change language",
        "menu_0": "0. Выход",
        "menu_prompt": "[bold cyan]Выберите опцию:[/bold cyan] ",
        
        "lists_not_found": "[yellow]Списков прокси не найдено или произошла ошибка при их получении.[/yellow]",
        "lists_title": "Доступные списки прокси",
        "col_num": "№",
        "col_id": "ID",
        "col_name": "Название",
        "col_countries": "Страны",
        "no_name": "Без названия",
        "not_specified": "Не указано",
        "list_display_error": "[red]Ошибка отображения списка[/red]",
        
        "select_ways": "\n[bold]Вы можете выбрать списки следующими способами:[/bold]",
        "select_way_1": "1. Отдельные номера через запятую (например: [cyan]1,3,5[/cyan])",
        "select_way_2": "2. Диапазон в квадратных скобках (например: [cyan][10, 20][/cyan])",
        "select_lists_dl": "\n[bold cyan]Выберите номера списков для скачивания прокси:[/bold cyan] ",
        "invalid_selection": "[red]Ошибка: Не выбрано ни одного действительного списка.[/red]",
        "select_format": "\n[bold]Выберите формат прокси:[/bold]",
        "format_1": "1. [cyan]login:password@host:port[/cyan] (default)",
        "format_2": "2. [cyan]login:password:host:port[/cyan]",
        "format_3": "3. [cyan]host:port:login:password[/cyan]",
        "format_4": "4. [cyan]host:port@login:password[/cyan]",
        "format_choice": "Выберите формат [dim][1][/dim]: ",
        "select_export": "\n[bold]Выберите формат экспорта:[/bold]",
        "export_1": "1. [cyan]txt[/cyan] (default)",
        "export_2": "2. [cyan]csv[/cyan]",
        "export_3": "3. [cyan]json[/cyan]",
        "export_choice": "Выберите формат [dim][1][/dim]: ",
        "merge_files": "\nОбъединить все прокси в один файл? (y/n, по умолчанию: y): ",
        "dl_progress": "[green]Скачивание прокси...",
        "dl_list_progress": "Загрузка прокси из '{title}'...",
        "dl_success": "[green]✔[/green] Список '{title}' сохранен в '{filename}'.",
        "dl_error": "[red]✖ Ошибка при загрузке '{title}'. Код: {code}[/red]",
        "merged_success": "\n[bold green]✔ Все прокси объединены в файл '{filename}'.[/bold green]",
        "file_save_error": "[red]Ошибка при сохранении файла: {error}[/red]",
        "processed_count": "\n[cyan]Обработано {success} из {total} выбранных списков.[/cyan]",
        
        "create_title": "\n[bold magenta]=== Создание нового списка прокси ===[/bold magenta]",
        "enter_title": "[bold cyan]Введите название списка:[/bold cyan] ",
        "num_lists": "[bold cyan]Сколько списков вы хотите создать (для получения более 1000 прокси)? [dim][1][/dim]:[/bold cyan] ",
        "preset_countries": "\n[bold]Предустановленные паки стран:[/bold]",
        "manual_countries": "[cyan]0[/cyan]. Ручной ввод стран (по умолчанию)",
        "preset_choice": "\n[bold cyan]Выберите пак или 0 для ручного ввода:[/bold cyan] ",
        "selected_preset": "Выбран пак: [green]{name}[/green]",
        "enter_countries": "[bold cyan]Введите код или коды нескольких стран через запятую\n(подсказка: коды стран можно найти на https://www.iban.com/country-codes):[/bold cyan] ",
        "enter_region": "[bold cyan]Введите регион (или оставьте пустым):[/bold cyan] ",
        "enter_city": "[bold cyan]Введите город (или оставьте пустым):[/bold cyan] ",
        "enter_isp": "[bold cyan]Введите провайдера (или оставьте пустым):[/bold cyan] ",
        "num_ports": "[bold cyan]Введите количество портов на список (максимум и по умолчанию 1000):[/bold cyan] ",
        "whitelist_ip": "[bold cyan]Введите IP-адреса для белого списка через запятую (или оставьте пустым):[/bold cyan] ",
        "create_progress": "[green]Создание списков...",
        "create_list_progress": "Создание списка '{title}'...",
        "create_success": "[green]✔[/green] Список '{title}' успешно создан.",
        "create_error": "[red]✖ Ошибка создания списка '{title}': {error}[/red]",
        "total_created": "\n[bold green]Всего создано {total} прокси. Сохранены в '{filename}'.[/bold green]",
        
        "select_list_num": "\n[bold cyan]Выберите номер списка:[/bold cyan] ",
        "invalid_num": "[red]Неверный номер.[/red]",
        "enter_new_title": "[bold cyan]Введите новое название:[/bold cyan] ",
        "rename_success": "[bold green]Список переименован в '{title}'.[/bold green]",
        "error_prefix": "[bold red]Ошибка:[/bold red] {error}",
        "invalid_format": "[red]Неверный формат ввода.[/red]",
        
        "select_lists_del": "\n[bold cyan]Выберите номера списков для удаления:[/bold cyan] ",
        "selected_del": "\n[bold]Выбранные списки для удаления:[/bold]",
        "confirm_del": "\n[bold red]Удалить {count} списков? (y/n):[/bold red] ",
        "cancel_op": "[yellow]Операция отменена.[/yellow]",
        "del_progress": "[red]Удаление списков...",
        "del_success": "[green]✔[/green] Список '{title}' удален.",
        "del_error": "[red]✖ Ошибка удаления '{title}': {error}[/red]",
        "del_count": "\n[bold cyan]Удалено {deleted} из {total} списков.[/bold cyan]",
        
        "cons_title": "\n[bold magenta]=== Информация о расходе (Traffic Consumption) ===[/bold magenta]",
        "cons_period": "Выберите период:",
        "period_1": "1. [cyan]Последние 24 часа[/cyan]",
        "period_2": "2. [cyan]Последняя неделя[/cyan]",
        "period_3": "3. [cyan]Последний месяц[/cyan]",
        "period_4": "4. [cyan]Произвольные даты[/cyan]",
        "your_choice": "\n[bold cyan]Ваш выбор [dim][1][/dim]:[/bold cyan] ",
        "date_start": "[bold cyan]Введите начальную дату (DD.MM.YYYY):[/bold cyan] ",
        "date_end": "[bold cyan]Введите конечную дату (DD.MM.YYYY):[/bold cyan] ",
        "login_filter": "\n[bold cyan]Введите логин для фильтрации (или оставьте пустым):[/bold cyan] ",
        "fetch_cons_progress": "[green]Получение данных о расходе...",
        "fetch_lists_progress": "[green]Получение списков для сопоставления названий...",
        "cons_data_title": "\n[bold green]Данные о расходе за период {start} - {end}:[/bold green]",
        "cons_summary": "Общая статистика",
        "bought_traffic": "[bold]Куплено трафика:[/bold] {bytes} ([green]{amount}[/green])\n",
        "used_traffic": "[bold]Использовано:[/bold] [yellow]{bytes}[/yellow] ([red]{amount}[/red])\n",
        "price_per_gb": "[bold]Цена за ГБ:[/bold] {price}",
        "cons_details": "Детализация по спискам",
        "col_group": "Название / Группа",
        "col_used": "Использовано трафика",
        "col_cost": "Стоимость",
        "lists_count_dim": " [dim]({count} списков)[/dim]",
        "login_dim": " [dim]({login})[/dim]",
        "no_data": "[yellow]Нет данных за этот период (или пусто).[/yellow]",
        "fetch_error": "\n[red]Ошибка при получении данных: {error}[/red]",
    },
    "en": {
        "api_key_not_found": "[yellow]API key not found in environment.[/yellow]",
        "api_key_hint": "[dim]You can get it in your ProxySeller dashboard.[/dim]",
        "api_key_prompt": "[bold cyan]Enter your ProxySeller API key:[/bold cyan] ",
        "api_key_empty": "[bold red]ERROR: API key cannot be empty.[/bold red]",
        "api_key_saving": "\n[bold green]Saving key to .env file for security...[/bold green]",
        "api_key_save_error": "[red]Failed to save to .env:[/red] {error}",
        "press_enter": "\n[dim]Press Enter to continue...[/dim]",
        "exiting": "\n[bold blue]Exiting...[/bold blue]",
        "invalid_choice": "\n[red]Invalid choice. Please try again.[/red]",
        "interrupted": "\n\n[bold yellow]Program interrupted by user[/bold yellow]",
        "critical_error": "\n[bold red]Critical error:[/bold red] {error}",
        
        "menu_title": "ProxySeller API Manager",
        "menu_1": "1. Get existing IP lists",
        "menu_2": "2. Download proxies from existing list",
        "menu_3": "3. Create new list(s)",
        "menu_4": "4. Rename list",
        "menu_5": "5. Delete lists",
        "menu_6": "6. Get consumption info",
        "menu_7": "7. Change language / Сменить язык",
        "menu_0": "0. Exit",
        "menu_prompt": "[bold cyan]Select option:[/bold cyan] ",
        
        "lists_not_found": "[yellow]No proxy lists found or an error occurred.[/yellow]",
        "lists_title": "Available Proxy Lists",
        "col_num": "#",
        "col_id": "ID",
        "col_name": "Name",
        "col_countries": "Countries",
        "no_name": "Unnamed",
        "not_specified": "Not specified",
        "list_display_error": "[red]Error displaying list[/red]",
        
        "select_ways": "\n[bold]You can select lists in the following ways:[/bold]",
        "select_way_1": "1. Individual numbers separated by comma (e.g.: [cyan]1,3,5[/cyan])",
        "select_way_2": "2. Range in square brackets (e.g.: [cyan][10, 20][/cyan])",
        "select_lists_dl": "\n[bold cyan]Select list numbers to download proxies:[/bold cyan] ",
        "invalid_selection": "[red]Error: No valid list selected.[/red]",
        "select_format": "\n[bold]Select proxy format:[/bold]",
        "format_1": "1. [cyan]login:password@host:port[/cyan] (default)",
        "format_2": "2. [cyan]login:password:host:port[/cyan]",
        "format_3": "3. [cyan]host:port:login:password[/cyan]",
        "format_4": "4. [cyan]host:port@login:password[/cyan]",
        "format_choice": "Select format [dim][1][/dim]: ",
        "select_export": "\n[bold]Select export format:[/bold]",
        "export_1": "1. [cyan]txt[/cyan] (default)",
        "export_2": "2. [cyan]csv[/cyan]",
        "export_3": "3. [cyan]json[/cyan]",
        "export_choice": "Select format [dim][1][/dim]: ",
        "merge_files": "\nMerge all proxies into one file? (y/n, default: y): ",
        "dl_progress": "[green]Downloading proxies...",
        "dl_list_progress": "Downloading proxies from '{title}'...",
        "dl_success": "[green]✔[/green] List '{title}' saved to '{filename}'.",
        "dl_error": "[red]✖ Error downloading '{title}'. Code: {code}[/red]",
        "merged_success": "\n[bold green]✔ All proxies merged into file '{filename}'.[/bold green]",
        "file_save_error": "[red]Error saving file: {error}[/red]",
        "processed_count": "\n[cyan]Processed {success} of {total} selected lists.[/cyan]",
        
        "create_title": "\n[bold magenta]=== Create New Proxy List ===[/bold magenta]",
        "enter_title": "[bold cyan]Enter list name:[/bold cyan] ",
        "num_lists": "[bold cyan]How many lists do you want to create (to get >1000 proxies)? [dim][1][/dim]:[/bold cyan] ",
        "preset_countries": "\n[bold]Preset country packs:[/bold]",
        "manual_countries": "[cyan]0[/cyan]. Manual country entry (default)",
        "preset_choice": "\n[bold cyan]Select a pack or 0 for manual entry:[/bold cyan] ",
        "selected_preset": "Selected pack: [green]{name}[/green]",
        "enter_countries": "[bold cyan]Enter country code(s) separated by comma\n(hint: country codes can be found at https://www.iban.com/country-codes):[/bold cyan] ",
        "enter_region": "[bold cyan]Enter region (or leave empty):[/bold cyan] ",
        "enter_city": "[bold cyan]Enter city (or leave empty):[/bold cyan] ",
        "enter_isp": "[bold cyan]Enter ISP (or leave empty):[/bold cyan] ",
        "num_ports": "[bold cyan]Enter number of ports per list (max and default 1000):[/bold cyan] ",
        "whitelist_ip": "[bold cyan]Enter whitelist IP addresses separated by comma (or leave empty):[/bold cyan] ",
        "create_progress": "[green]Creating lists...",
        "create_list_progress": "Creating list '{title}'...",
        "create_success": "[green]✔[/green] List '{title}' successfully created.",
        "create_error": "[red]✖ Error creating list '{title}': {error}[/red]",
        "total_created": "\n[bold green]Total {total} proxies created. Saved to '{filename}'.[/bold green]",
        
        "select_list_num": "\n[bold cyan]Select list number:[/bold cyan] ",
        "invalid_num": "[red]Invalid number.[/red]",
        "enter_new_title": "[bold cyan]Enter new name:[/bold cyan] ",
        "rename_success": "[bold green]List renamed to '{title}'.[/bold green]",
        "error_prefix": "[bold red]Error:[/bold red] {error}",
        "invalid_format": "[red]Invalid input format.[/red]",
        
        "select_lists_del": "\n[bold cyan]Select list numbers to delete:[/bold cyan] ",
        "selected_del": "\n[bold]Selected lists to delete:[/bold]",
        "confirm_del": "\n[bold red]Delete {count} lists? (y/n):[/bold red] ",
        "cancel_op": "[yellow]Operation cancelled.[/yellow]",
        "del_progress": "[red]Deleting lists...",
        "del_success": "[green]✔[/green] List '{title}' deleted.",
        "del_error": "[red]✖ Error deleting '{title}': {error}[/red]",
        "del_count": "\n[bold cyan]Deleted {deleted} of {total} lists.[/bold cyan]",
        
        "cons_title": "\n[bold magenta]=== Traffic Consumption Info ===[/bold magenta]",
        "cons_period": "Select period:",
        "period_1": "1. [cyan]Last 24 hours[/cyan]",
        "period_2": "2. [cyan]Last week[/cyan]",
        "period_3": "3. [cyan]Last month[/cyan]",
        "period_4": "4. [cyan]Custom dates[/cyan]",
        "your_choice": "\n[bold cyan]Your choice [dim][1][/dim]:[/bold cyan] ",
        "date_start": "[bold cyan]Enter start date (DD.MM.YYYY):[/bold cyan] ",
        "date_end": "[bold cyan]Enter end date (DD.MM.YYYY):[/bold cyan] ",
        "login_filter": "\n[bold cyan]Enter login to filter (or leave empty):[/bold cyan] ",
        "fetch_cons_progress": "[green]Fetching consumption data...",
        "fetch_lists_progress": "[green]Fetching lists to match names...",
        "cons_data_title": "\n[bold green]Consumption data for period {start} - {end}:[/bold green]",
        "cons_summary": "Overall Statistics",
        "bought_traffic": "[bold]Traffic bought:[/bold] {bytes} ([green]{amount}[/green])\n",
        "used_traffic": "[bold]Used:[/bold] [yellow]{bytes}[/yellow] ([red]{amount}[/red])\n",
        "price_per_gb": "[bold]Price per GB:[/bold] {price}",
        "cons_details": "Details by lists",
        "col_group": "Name / Group",
        "col_used": "Used traffic",
        "col_cost": "Cost",
        "lists_count_dim": " [dim]({count} lists)[/dim]",
        "login_dim": " [dim]({login})[/dim]",
        "no_data": "[yellow]No data for this period (or empty).[/yellow]",
        "fetch_error": "\n[red]Error fetching data: {error}[/red]",
    }
}

def t(key, **kwargs):
    lang = get_language() or "en"
    text = TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)
    if kwargs:
        return text.format(**kwargs)
    return text
