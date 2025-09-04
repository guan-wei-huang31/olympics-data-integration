import csv
from datetime import datetime
import utils

def process_game_file(game_csv):
    """
    Process the Olympics game CSV file and return the updated header and a dictionary of game rows keyed by edition_id.

    Args:
        game_csv (str): Path to the input 'olympics_games.csv' file.

    Returns:
        game_header (list): List of column names.
                    Example:[
                             "edition", "edition_id", "edition_url", "year", "city", "country_flag_url", 
                             "country_noc", "start_date", "end_date", "competition_date", "isHeld"
                            ]
        game_dict (dict): Dictionary of game data keyed by edition_id.
                    Example:{ 
                                "63" : 
                                {
                                    'edition': '2024 Summer Olympics', 
                                    'edition_id': '63', 
                                    'edition_url': '/editions/63', 
                                    'year': '2024', 
                                    ...
                                    'start_dt_obj': datetime.datetime(2024, 7, 24, 0, 0), 
                                    'end_dt_obj': datetime.datetime(2024, 8, 11, 0, 0)}
                                },...
                            }
    """
    game_dict = {}
    normalize_date= utils.normalize_date
    with open(game_csv, mode='r', encoding="utf-8-sig") as file:
        csv_reader = csv.DictReader(file)
        game_header = csv_reader.fieldnames

        for game_row in csv_reader:
            edition_id = game_row["edition_id"]
            is_held = game_row["isHeld"].strip()

            if edition_id  == "63":  
                # Special case: Paris 2024 (manual entry)
                game_row["start_date"] = "26-Jul-2024"
                game_row["end_date"] = "11-Aug-2024"
                game_row["competition_date"] = "24-Jul-2024 to 11-Aug-2024"
            elif is_held == "":
                # Fill missing date fields if games were held (e.g., not during war)
                year = int(game_row["year"])
                game_row["start_date"] = normalize_date(game_row["start_date"], None, year)
                game_row["end_date"] = normalize_date(game_row["end_date"], None, year)
                game_row["competition_date"] = competition_date_transform(game_row["competition_date"], year)
            
            start_dt, end_dt = parse_competition_dates(game_row["competition_date"])
            game_row["start_dt_obj"] = start_dt
            game_row["end_dt_obj"] = end_dt
            

            game_dict[edition_id] = game_row
    return game_header, game_dict

def parse_competition_dates(date_range_str):
    """
    Convert a competition date range string into two datetime objects.
    Prepare for calculating age in event file.

    Handles various date_range_str (input formats) such as:
       1. '24-Jul-2024 to 11-Aug-2024'
       2. '—'

    Args:
        date_range_str (str): A string representing the competition date range.

    Returns:
        tuple(datetime, datetime): A tuple containing the start and end dates as datetime objects.
                                   Returns (None, None) if parsing fails.
    """
    if date_range_str.strip() == "—":
        return None, None
    
    start_str, end_str = date_range_str.split("to")
    start_dt = datetime.strptime(start_str.strip(), "%d-%b-%Y")
    end_dt = datetime.strptime(end_str.strip(), "%d-%b-%Y")
    return start_dt, end_dt

def competition_date_transform(competition_str, year):
    """
    Normalize a raw competition date string into a standard format: 'DD-MMM-YYYY to DD-MMM-YYYY'
    Handles various input formats such as:
       1. –
       2. 21 July –  8 August 2021
       3. 6 – 13 April
       4. 14 May – 28 October

    Args:
        competition_str (str): Raw competition date range string.
        year (int): Fallback year if not provided in the string.
    
    Returns:
        str: A formatted date range string like '06-Apr-2021 to 13-Apr-2021', or the original string if it cannot be parsed.
    """
    competition_str = competition_str.strip()
    parts = []
    for p in competition_str.split("–"):  # split into [start, end] by "–"
        parts.append(p.strip())
    if len(parts) != 2:    # If the content is empty (only "–"), return
        return competition_str
    
    start, end = parts[0], parts[1]

    # Extract end date components
    end_split = end.split()
    end_day, end_month = end_split[0], end_split[1]
    if len(end_split) == 3:  # If year is explicitly included in the end date (ex: 2020 Tokyo, year = 2021)
        year = end_split[2]
    
    start_split = start.split()
    start_day = start_split[0]
    if len(start_split) == 1: # If only day is given, assume same month as end
        start_month = end_month
    else:
        start_month = start_split[1]
        
    # Convert to datetime objects
    start_date = datetime.strptime(f"{int(start_day)} {start_month} {year}", "%d %B %Y")
    end_date = datetime.strptime(f"{int(end_day)} {end_month} {year}", "%d %B %Y")
    return f"{start_date.strftime('%d-%b-%Y')} to {end_date.strftime('%d-%b-%Y')}"


def process_athlete_file(athlete_csv, event_year_dict):
    """
    Process the athlete CSV file and normalize the 'born' field using event year data.

    Args:
        athlete_csv (str): File path to the athlete dataset (olympic_athletes.csv).
        event_year_dict (dict): A dictionary mapping each athlete_id to a list of event years 
                                in which the athlete participated.
                                Example:
                                {
                                    "108546": [2004, 2008, 2012],
                                    "64710": [1908], ...
                                }

    Returns:
        header (list): List of column names extracted from the CSV file.
        athlete_max_id (int): The highest athlete_id encountered in the dataset.
                              Used to assign new athlete data in another function.
        existing_keys (dict): A dictionary used to track unique athletes by their identifying info. 
                              The key is a tuple: (name.lower(), sex, normalized_born, country_noc), 
                              and the value is the athlete_id.
        athlete_dict (dict): Dictionary containing all athlete rows keyed by athlete_id.
                                     Each row has the 'born' field normalized to the format dd-Mon-yyyy.
                                     Example:
                                     {
                                         "64710": {
                                             'athlete_id': '64710',
                                             'name': 'Ernest Hutcheon',
                                             'sex': 'M',
                                             'born': '24-Nov-1873',
                                             ...
                                         }, ...
                                     }

    Notes:
        - This function ensures consistent date formatting for the 'born' field using event years.
        - The normalized format for 'born' is "dd-Mon-yyyy" ("04-Apr-1949").
        - It also creates a composite key for deduplication or identity matching purposes.
    """
    existing_keys = {}
    athlete_dict = {}
    athlete_max_id = 0
    normalize_date = utils.normalize_date
    with open(athlete_csv, mode='r', encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        athlete_header = reader.fieldnames

        for row in reader:
            athlete_id = row["athlete_id"]
            born = row["born"]
            #name = row["name"].strip().lower()
            name = row["name"].strip().split()[0]
            sex = row["sex"].strip()
            country_noc = row["country_noc"].strip()

            # Normalize birth date using event years (if available)
            normalized_born = normalize_date(born, event_year_dict[athlete_id])
            row["born"] = normalized_born

            # Update max athlete_id
            athlete_max_id = max(athlete_max_id, int(athlete_id))

            # Build existing key only if born is not empty
            if born.strip():
                #key_tuple = (name, sex, normalized_born.strip(), country_noc)
                key_tuple = (name, normalized_born.strip(), country_noc)
                existing_keys[key_tuple] = athlete_id

            athlete_dict[athlete_id] = row

    return athlete_header, athlete_max_id, existing_keys, athlete_dict
