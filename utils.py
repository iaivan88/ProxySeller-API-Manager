from typing import List

def parse_user_selection(selection_input: str, max_value: int) -> List[int]:
    """
    Parses a string like '1,3,5' or '[10, 20]' into a list of valid integer selections.
    """
    selections = []
    
    if selection_input.strip().startswith('[') and selection_input.strip().endswith(']'):
        range_content = selection_input.strip()[1:-1]
        range_parts = [part.strip() for part in range_content.split(',')]
        
        if len(range_parts) == 2 and range_parts[0].isdigit() and range_parts[1].isdigit():
            start = int(range_parts[0])
            end = int(range_parts[1])
            selections = list(range(start, end + 1))
    else:
        selections = [int(x.strip()) for x in selection_input.split(',') if x.strip().isdigit()]
        
    valid_selections = []
    for selection in selections:
        if 1 <= selection <= max_value:
            valid_selections.append(selection)
            
    return valid_selections

def extract_countries(geo_info) -> List[str]:
    """Extracts a list of countries from a geo structure."""
    countries: List[str] = []
    if isinstance(geo_info, list):
        for geo in geo_info:
            if isinstance(geo, dict) and "country" in geo:
                countries.append(geo["country"])
    elif isinstance(geo_info, dict) and "country" in geo_info:
        countries.append(geo_info["country"])
    return countries
