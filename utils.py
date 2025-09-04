# supports the use of csv library
import csv
from datetime import datetime
def write_csv_file_dict_flexible(file_name, header, data):
    """
    Write a list or dict of dictionaries to a CSV file, ensuring only header-matching keys are written.

    Args:
        file_name (str): Output file name.
        header (list): List of column headers.
        data (dict or list): Either a dict of row dicts (with .values()), or a list of row dicts.
    """
    with open(file_name, mode='w', newline='', encoding='utf-8-sig') as file:
        writer = csv.DictWriter(file, fieldnames=header)
        writer.writeheader()

        # Standardize to list of dicts
        if isinstance(data, dict):
            data = data.values()

        for row in data:
            filtered_row = {key: row.get(key, "") for key in header}  # filter extra keys
            writer.writerow(filtered_row)

def normalize_date(date_str, event_data=None, default_year=None):
    """
    Normalize various date formats into a consistent format: 'dd-Mon-yyyy' ('04-Apr-1949').

    This function handles various date string formats found in Olympic-related datasets,
    such as athlete birthdates and event dates, and converts them to a unified format 
    used for downstream processing.

    Args:
        date_str (str): The original date string in one of the following possible formats:
            - 'yyyy-mm-dd' ('1991-10-21')
            - 'Mon-yy' ('Dec-67') — requires event_data to infer century
            - 'dd-Mon-yy' ('04-Apr-49') — requires event_data to infer century
            - 'dd Month yyyy' ('24 November 1873')
            - 'dd Month' ('6 April') — requires default_year
            - 'Month yyyy' ('July 1882')
            - 'yyyy' ('1879')
            - Dates within text ('(1926 or 1927)') — extracts first 4-digit year

        event_data (list, optional): A sequence where the first item is the reference year
            (used to infer the century in two-digit year formats like 'Dec-67').

        default_year (int, optional): A fallback year used when the date only contains day and month
            (e.g., '6 April').

    Returns:
        str: A normalized date string in 'dd-Mon-yyyy' format ('01-Jan-1926'),
             or an empty string if the input is invalid or cannot be parsed.
    """
    if not date_str or not str(date_str).strip():
        return ""

    date_str = str(date_str).strip()
    date_str = date_str.replace("–", "-").replace("—", "-").replace("‐", "-")
    date_str = date_str.strip('"').strip('“”').lower()

    # Case 1: yyyy-mm-dd
    parts = date_str.split("-")
    if len(parts) == 3 and all(part.isdigit() for part in parts):
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").strftime("%d-%b-%Y")
        except:
            return date_str

    # Case 2: Mon-yy
    if "-" in date_str and len(date_str) == 6 and event_data:
        mon, short_year = date_str.split("-")
        if short_year.isdigit():
            try:
                short_year = int(short_year)
                event_year = int(event_data[0])
                full_year = (event_year // 100) * 100 + short_year
                if full_year > event_year:
                    full_year -= 100
                return f"01-{mon.capitalize()}-{full_year}"
            except:
                return date_str

    # Case 3: dd-Mon-yy
    if "-" in date_str and event_data:
        parts = date_str.split("-")
        if len(parts) == 3 and parts[0].isdigit() and parts[2].isdigit():
            try:
                day, mon, short_year = parts
                short_year = int(short_year)
                event_year = int(event_data[0])
                full_year = (event_year // 100) * 100 + short_year
                if full_year > event_year:
                    full_year -= 100
                return f"{int(day):02d}-{mon.capitalize()}-{full_year}"
            except:
                return date_str

    # Case 4: dd Month yyyy
    words = date_str.split()
    if len(words) == 3 and words[0].isdigit() and words[2].isdigit():
        try:
            return datetime.strptime(date_str, "%d %B %Y").strftime("%d-%b-%Y")
        except:
            return date_str

    # Case 5: dd Month + default year
    if len(words) == 2 and words[0].isdigit() and default_year:
        try:
            full_date = f"{words[0]} {words[1]} {default_year}"
            return datetime.strptime(full_date, "%d %B %Y").strftime("%d-%b-%Y")
        except:
            return date_str

    # Case 6: Month yyyy
    if len(words) == 2 and words[1].isdigit():
        try:
            return datetime.strptime("01 " + date_str, "%d %B %Y").strftime("%d-%b-%Y")
        except:
            return date_str

    # Case 7: yyyy only
    if date_str.isdigit() and len(date_str) == 4:
        return f"01-Jan-{date_str}"

    # Case 8: text contains a 4-digit year
    digits = ""
    for i in range(len(date_str) - 3):
        if date_str[i:i+4].isdigit():
            digits = date_str[i:i+4]
            break
    if digits:
        return f"01-Jan-{digits}"

    return ""

def parse_list_field(s):
    """
    Parses a string representing a list into a Python list.

    Args:
        s (str): A string representation of a list field, possibly with surrounding quotes.

    Returns:
        list: A list of strings extracted from the input; returns an empty list if the input is empty or malformed.

    Notes:
        - Uses ast.literal_eval for safe parsing when possible.
        - Handles cases like:
            '"[\"Men's 100m\"]"'    -> ['Men\'s 100m']
            '["Women"]'             -> ['Women']
            '[]'                    -> []
            ''                      -> []
            '[Invalid]'            -> ['Invalid']  # fallback
    """
    s = s.strip()
    if not s:
        return []

    # Remove outer quotes if any
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        s = s[1:-1].strip()

    # Must start and end with brackets
    if not (s.startswith('[') and s.endswith(']')):
        return []

    # Get content inside brackets
    content = s[1:-1].strip()
    if not content:
        return []

    result = []
    i = 0
    n = len(content)
    while i < n:
        # Skip spaces or commas
        while i < n and content[i] in ' ,':
            i += 1
        if i >= n:
            break

        # Parse quoted item
        if content[i] in ['"', "'"]:
            quote = content[i]
            i += 1
            start = i
            while i < n and content[i] != quote:
                i += 1
            item = content[start:i]
            result.append(item)
            i += 1  # skip ending quote
        else:
            # Unquoted content, read until comma or end
            start = i
            while i < n and content[i] != ',':
                i += 1
            item = content[start:i].strip()
            if item:
                result.append(item)

    return result
