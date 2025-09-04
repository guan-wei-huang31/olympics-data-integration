import csv
import utils

def read_event_result_year(event_csv, game_dict):
    """
    Reads the Olympic athlete event results CSV and extracts relevant data including 
    athlete participation years, header fields, full event rows, and the maximum result ID.

    Args:
        event_csv (str): Path to the 'olympic_athlete_event_results.csv' file.
        game_dict (dict): Dictionary mapping edition_id to corresponding game data. 
                          Used to extract the year for each athlete's event.
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

    Returns:
        year_dict (dict): Maps each athlete_id to a list of years they participated in.
                         { "108546": [2004, 2008, 2012], ... }
        event_header (list): List of column headers from the input file, with an additional "age" column appended.
                        [ "edition", "edition_id", "country_noc", "sport", "event", "result_id", "athlete", "athlete_id", "pos", "medal", "isTeamSport", "age"]
        event_list (list): List of dictionaries, each representing one row from the input CSV.
                           Each row includes an empty "age" field for later use.
                        Example: [ 
                                    {
                                        'edition': '1908 Summer Olympics', 
                                        'edition_id': '5', 
                                        'country_noc': 'ANZ', 
                                        'sport': 'Athletics', 
                                        ...
                                        'age': ''
                                    }, ...
                                ]
        max_result_id (INT): The maximum result_id value found in the dataset, used to generate unique IDs for any new results.

    Notes:
        - The "age" field is initialized as an empty string for each row.
        - This function does not calculate age, but prepares the structure for later processing.
    """
    event_year_dict = {}
    event_list = []
    max_result_id = 0
    with open(event_csv, mode='r', encoding="utf-8-sig") as file:
        csv_reader = csv.DictReader(file)
        event_header = csv_reader.fieldnames + ["age"]

        for row in csv_reader:
            athlete_id = row["athlete_id"]
            edition_id = row["edition_id"]

            year = int(game_dict[edition_id]["year"])
            event_year_dict.setdefault(athlete_id, []).append(year)

            row["age"] = ""
            event_list.append(row)

            max_result_id = max(max_result_id, int(row["result_id"]))
    #print(event_year_dict.get("108546", "Not found"))
    #print(event_list[0])

    return event_year_dict, event_header, event_list, max_result_id


def process_athlete_event_data(paris_athlete_csv, existing_keys, updated_athlete_dict, athlete_max_id, event_list, medallist_dict, max_result_id, paris_team_set, paris_event_set):
    """
    Processes athlete records and their associated event data from a Paris 2024 athlete file.
    1. Append unique data into updated_data with unique id and correct born date.
    2. Append 2024 Paris Event result (disciplines and event with medal and team) into event_list

    Args:
        paris_athlete_csv (str): Path to the paris/athlete.csv file.
        existing_keys (dict): Dictionary tracking unique athletes using a composite key 
                              The key is a tuple: (name.lower(), sex, normalized_born, country_noc), 
                              and the value is the athlete_id.
        updated_athlete_dict: Dictionary to store updated athlete data with correct born format.
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
        athlete_max_id (int): Current maximum athlete ID, used to assign new IDs.
        event_list (list): List to collect event result data.
                                Example: [ 
                                    {
                                        'edition': '1908 Summer Olympics', 
                                        'edition_id': '5', 
                                        'country_noc': 'ANZ', 
                                        'sport': 'Athletics', 
                                        ...
                                        'age': ''
                                    }, ...
                                ]
        medallist_dict (dict): Dictionary mapping (code, discipline, event) → medal and pos info.
                                Example: { 
                                            ("code_athlete", "discipline", "event"):
                                                {
                                                    "medal_type": str,  # "Gold", "Silver", "Bronze", or ""
                                                    "pos": str,         # "1", "2", "3", or ""
                                                }
                                          }
        max_result_id (int): Current maximum result ID, used to incrementally assign new result IDs.
        paris_team_set (set): Set of (code, discipline, event) tuples indicating team participation.
                            Example: {
                                        ('12345', 'Basketball', 'Basketball Men'),
                                        ('67890', 'Basketball', 'Basketball Men'),
                                        ...
                                      }
        paris_event_set: Set of valid (discipline, event) tuples to filter relevant events.
                            Example: {
                                        ("Athletics", "100m Men"), 
                                        ("Swimming", "200m Freestyle Women")
                                        , ...
                                      }

    Returns:
        None — This function modifies `updated_data`, `event_data_list`, `existing_keys` in-place.
    
    Notes:
        - Normalizes birth date before matching to avoid duplicates.
        - Ensures each new athlete gets a unique athlete_id based on `athlete_max_id`.
        - Ensures each new event gets correct medal and team.
    """
    paris_athlete_event_set = set()
    paris_id_to_athlete_id = {}
    discipline_result_id_map = {} 
    normalize_date = utils.normalize_date  
    with open(paris_athlete_csv, mode='r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        for row in reader:
            full_name = row.get("name_tv", "").strip()
            first_name = full_name.split()[0] if full_name else ""
            row["birth_date"] = normalize_date(row["birth_date"])
            key1 = (
                #row.get("name_tv", "").strip().lower(),
                first_name,  # match firstname only, prevent changed lastname
                #row["gender"].strip(),
                row["birth_date"],
                #row["country_code"].strip()
                row["nationality_code"].strip()
            )
            ###
            key1_1 = (
                first_name,  # match firstname only, prevent changed lastname
                #row["gender"].strip(),
                row["birth_date"],
                row["country_code"].strip()
            )
            ###
            """
            if key1 not in existing_keys:
                athlete_max_id += 1
                athlete_id = str(athlete_max_id)
                existing_keys[key1] = athlete_id
                merge_athlete_data(row, athlete_id, updated_athlete_dict)
            else:
                athlete_id = existing_keys[key1]
            """
            if key1 in existing_keys:
                athlete_id = existing_keys[key1]
            elif key1_1 in existing_keys:
                athlete_id = existing_keys[key1_1]
            else:
                # create new
                athlete_max_id += 1
                athlete_id = str(athlete_max_id)
                existing_keys[key1] = athlete_id
                merge_athlete_data(row, athlete_id, updated_athlete_dict)

            paris_id_to_athlete_id[row["code"]] = athlete_id

            # for event
            # max_result_id += 1
            max_result_id = merge_event_data(row, athlete_id, medallist_dict, event_list, max_result_id, paris_team_set, paris_event_set, paris_athlete_event_set, discipline_result_id_map)
    return paris_athlete_event_set, paris_id_to_athlete_id

def merge_athlete_data(paris_row, athlete_id, updated_athlete_dict):

    """
    Creates and appends a new athlete record if the athlete is not found in the existing dataset.

    Args:
        paris_row (dict): A row from the Paris athlete CSV file containing athlete details.
        athlete_id (str): new athlete id
        updated_athlete_dict: Dictionary to store updated athlete data with correct born format.
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
        - Appends a new athlete dictionary to `updated_athlete_dict`.
        - If `name_tv` is not available, falls back to reversing the `name` field.
        - Skips height and weight values that are "0".
    """
    updated_athlete_dict[athlete_id] = {
        "athlete_id": athlete_id,
        "name": (
            paris_row["name_tv"].strip().title()
            if paris_row.get("name_tv", "").strip()
            else reverse_name(paris_row.get("name", "")).title()
        ),
        "sex": paris_row["gender"],
        "born": paris_row["birth_date"],
        #"height": "" if paris_row["height"] == "0" else paris_row["height"],
        #"weight": "" if paris_row["weight"] == "0" else paris_row["weight"],
        "height": paris_row["height"],
        "weight": paris_row["weight"],
        "country": paris_row["country_long"],
        "country_noc": paris_row["country_code"]
    }

def merge_event_data(paris_row, athlete_id, medallist_dict, event_list, max_result_id, paris_team_set, paris_event_set, paris_athlete_event_set, discipline_result_id_map):

    """
    Creates and appends event participation records for a given athlete.
    Parses disciplines and events from a CSV row, checks if the event is valid,
    matches medal and team participation info, and appends a formatted event dictionary to the list.

    Args:
        paris_row: each row in paris athlete csv
        athlete_id (str): athlete id 
        medallist_dict (dict): Dictionary mapping (code, discipline, event) → medal and pos info.
                                Example: { 
                                            ("code_athlete", "discipline", "event"):
                                                {
                                                    "medal_type": str,  # "Gold", "Silver", "Bronze", or ""
                                                    "pos": str,         # "1", "2", "3", or ""
                                                }
                                          }
        event_list (list): List to collect event result data.
                                Example: [ 
                                    {
                                        'edition': '1908 Summer Olympics', 
                                        'edition_id': '5', 
                                        'country_noc': 'ANZ', 
                                        'sport': 'Athletics', 
                                        ...
                                        'age': ''
                                    }, ...
                                ]
        max_result_id (int): The highest result_id so far.
        paris_team_set (set): Set of (code, discipline, event) tuples indicating team participation.
                            Example: {
                                        ('12345', 'Basketball', 'Basketball Men'),
                                        ('67890', 'Basketball', 'Basketball Men'),
                                        ...
                                      }
        paris_event_set: Set of valid (discipline, event) tuples to filter relevant events.
                            Example: {
                                        ("Athletics", "100m Men"), 
                                        ("Swimming", "200m Freestyle Women")
                                        , ...
                                      }

    Notes:
        - Appends one or more event records to event_list.
        - Each (discipline, event) combination results in one event record if combination exists in paris_event_set.
        - Medal information and position are extracted from medallist_dict using athlete's code.
        - Team membership is flagged as "TRUE" if the (code, discipline, event) exists in team_set.
        - Athlete name is taken from name_tv if available; otherwise, falls back to reversed 'name'.
        - "age" is a placeholder and should be updated in a separate processing step.
    """
    parse_list = utils.parse_list_field
    disciplines = parse_list(paris_row["disciplines"])  # ['Cycling Road', 'Cycling Track']
    events = parse_list(paris_row["events"])            # ["Women's Road Race", "Women's Keirin", "Women's Sprint"]
    
    athlete_code = paris_row["code"]
    name_tv = paris_row.get("name_tv", "").strip()
    athlete_name = name_tv.title() if name_tv else reverse_name(paris_row.get("name", "")).title()
    country_code = paris_row["country_code"]

    for dis in disciplines:            
        for e in events:
            key1 = (dis, e)
            if key1 in paris_event_set:              
                key2 = (athlete_code, dis, e)
                paris_athlete_event_set.add(key2)

                if key1 in discipline_result_id_map:
                    result_id = discipline_result_id_map[key1]
                else:
                    max_result_id += 1
                    result_id = max_result_id
                    discipline_result_id_map[key1] = result_id

                medal_info = medallist_dict.get(key2, {})
                medal = medal_info.get("medal_type", "")
                pos = medal_info.get("pos", "")

                event_list.append({
                    "edition": "2024 Summer Olympics", 
                    "edition_id": "63", 
                    "country_noc": country_code, 
                    "sport": dis, 
                    "event": e,
                    "result_id": str(result_id),
                    "athlete": athlete_name,
                    "athlete_id": athlete_id, 
                    "pos": pos, 
                    "medal": medal, 
                    "isTeamSport": "TRUE" if key2 in paris_team_set else "FALSE",
                    "age": ""
                })
    return result_id

def reverse_name(name):
    """
    Reverses the order of a name from 'Surname Given' to 'Given Surname'.

    Args:
        name (str): The full name string with the surname appearing first.

    Returns:
        name (str): The name rearranged with the given name first, followed by the surname.

    Examples:
        reverse_name("Boers Isayah") to "Isayah Boers"
    """
    parts = name.strip().split()
    if len(parts) >= 2:
        surname = parts[0]
        given = " ".join(parts[1:])
        return f"{given} {surname}"
    return name
