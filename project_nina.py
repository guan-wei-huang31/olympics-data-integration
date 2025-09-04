import csv
import utils

def read_country_file(country_csv):
    """
    Reads a CSV file containing country and NOC (National Olympic Committee) information,
    and stores the rows in a dictionary keyed by the 'noc' code.

    Args:
        country_csv (str): Path to the "olympics_country.csv" CSV file.

    Returns:
        country_header (list): List of column headers from the CSV file.
                             Example: ['noc', 'country']
        country_dict (dict): Dictionary where keys are 'noc' values and values are row dictionaries.
                             Example: {
                                        'AFG': 
                                            {
                                                'noc': 'AFG', 'country': 'Afghanistan'
                                            }, ...
                                      }
    """
    country_dict = {}
    with open(country_csv, mode='r', encoding="utf-8-sig") as file:
        csv_reader = csv.DictReader(file)
        country_header = csv_reader.fieldnames
        for row in csv_reader:
            country_dict[row["noc"]] = row
    return country_header, country_dict

def append_new_country(country_dict, paris_noc_csv):
    """
    Appends new NOC-country entries from a Paris-specific CSV file to the existing country_dict.

    Args:
        country_dict (dict): A dictionary where keys are NOC codes and values are dicts with 'noc' and 'country' keys.
                          Example: {'AFG': {'noc': 'AFG', 'country': 'Afghanistan'}, ...}
        paris_noc_csv (str): Path to the "paris/nocs.csv" CSV file containing updated or new NOC-country data.
    """
    with open(paris_noc_csv, mode='r', encoding="utf-8-sig") as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            key = row["code"]
            # If the NOC is not already present in the original dictionary, add it
            if key not in country_dict:
                country_dict[key] = {
                    "noc": row["code"],
                    "country": row["country_long"]
                }
                
def sort_country_data_by_country_name(country_dict):
    """
    Sorts the country data from the given country_dict by country name in alphabetical order.

    Args:
        country_dict (dict): A dictionary where keys are NOC codes and values are dicts with 'noc' and 'country' keys.
                          Example: {'AFG': {'noc': 'AFG', 'country': 'Afghanistan'}, ...}

    Returns:
        sorted_data (list): A list of country dictionaries sorted by the 'country' field.
                          Example: [{'noc': 'AFG', 'country': 'Afghanistan'}, {'noc': 'USA', 'country': 'United States'}, ...]
    """
    country_list = list(country_dict.values())   #  # Convert values to a list of dicts, [{'noc': 'AFG', 'country': 'Afghanistan'},..]
    sorted_data = sorted(country_list, key=lambda row: row["country"])   # Sort by country name
    return sorted_data


def read_medallist_data(paris_medallist_csv):
    """
    Reads medallist data from a CSV file and returns a dictionary mapping each athlete's 
    participation in an event to their medal and team information.

    Args:
        paris_medallist_csv (str): Path to the medallist CSV file. (paris/medallists.csv)

    Returns:
        medallist_dict: A dictionary with keys as tuples and values
                    This is used to add new data (medal) from paris/athlete.csv to event.csv:
                    Example: { 
                                ("code_athlete", "discipline", "event"):
                                    {
                                        "medal_type": str,  # "Gold", "Silver", "Bronze", or ""
                                        "pos": str,         # "1", "2", "3", or ""
                                    }
                             }
    """
    medallist_dict = {}
    with open(paris_medallist_csv, mode='r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        for row in reader:
            code_athlete = row["code_athlete"]
            discipline = row["discipline"]
            event = row["event"]
            medal_type = row["medal_type"]

            key = (code_athlete, discipline, event)

            # Use startswith() to slightly improve performance over full split()
            if medal_type.startswith("Gold"):
                pos = "1"
            elif medal_type.startswith("Silver"):
                pos = "2"
            elif medal_type.startswith("Bronze"):
                pos = "3"
            else:
                pos = ""

            medallist_dict[key] = {
                "medal_type": medal_type.split(" ", 1)[0],  # Still want 'Gold' not 'Gold Medal'
                "pos": pos
            }

    return medallist_dict

def read_paris_team(paris_team_csv):
    """
    Reads a CSV file containing Paris team event data and returns a set of tuples 
    representing each athlete's participation in team events.

    The function parses the list of athlete codes for each row and creates a tuple
    (athlete_code, discipline, event) for each athlete, which is added to a set to 
    ensure uniqueness.

    Args:
        paris_team_csv (str): The file path to the CSV file containing team event data.

    Returns:
        set: A set of tuples, each containing (athlete_code, discipline, event) for 
             every athlete involved in a team event.
             Example: {
                 ('12345', 'Basketball', 'Basketball Men'),
                 ('67890', 'Basketball', 'Basketball Men'),
                 ...
             }
    """
    team_set = set()
    parse_list = utils.parse_list_field
    with open(paris_team_csv, mode='r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        for row in reader:
            discipline = row["discipline"]
            event = row["events"]
            for athlete_code in parse_list(row["athletes_codes"]):
                team_set.add((athlete_code, discipline, event))
    return team_set

def read_paris_event(paris_event_csv):
    """
    Reads a CSV file containing Paris 2024 sports and events data, and returns a set 
    of unique (sport, event) pairs.

    Args:
        paris_event_csv (str): File path to the Paris event CSV file.

    Returns:
        paris_event_set (set): A set of tuples, where each tuple contains a sport and its corresponding event.
             Example: {
                        ("Athletics", "100m Men"), 
                        ("Swimming", "200m Freestyle Women")
                        , ...
                       }
    """
    paris_event_set = set()
    with open(paris_event_csv, mode='r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        for row in reader:
            sport = row["sport"]
            event = row["event"]
            paris_event_set.add((sport, event))
    return paris_event_set