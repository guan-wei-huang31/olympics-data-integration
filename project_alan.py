from datetime import datetime

def add_missing_medallist_events(medallist_dict, paris_athlete_event_set, updated_athlete_dict, event_data_list,
        paris_team_set, paris_id_to_athlete_id):
    """
    Adds missing event entries to `event_data_list` for athletes who won medals but were not recorded in the original
    event data due to missing discipline/event information in the Paris athlete CSV file.

    For each medal record in `medallist_dict`, if the (code, discipline, event) combination is not found in 
    `paris_athlete_event_set`, this function reconstructs the corresponding event entry using athlete and medal data
    and appends it to `event_data_list`.

    Args:
        medallist_dict (dict): Dictionary mapping (code, discipline, event) → medal and pos info.
                                Example: { 
                                            ("code_athlete", "discipline", "event"):
                                                {
                                                    "medal_type": str,  # "Gold", "Silver", "Bronze", or ""
                                                    "pos": str,         # "1", "2", "3", or ""
                                                }
                                          }
        paris_athlete_event_set (set): Set of (code, discipline, event) tuples already present in event data.
                                       Used to prevent duplicate additions.

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
        event_data_list (list): List of dictionaries, each representing one row from the input CSV.
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
        paris_team_set (set): Set of (code, discipline, event) tuples indicating team participation.
                            Example: {
                                        ('12345', 'Basketball', 'Basketball Men'),
                                        ('67890', 'Basketball', 'Basketball Men'),
                                        ...
                                      }
        paris_id_to_athlete_id (dict): Mapping from the original Paris athlete 'code' to the internal 'athlete_id'
                                       used in 'updated_athlete_dict'.

    Returns:
        None — This function modifies 'event_data_list' in-place.
    
    Notes:
        - This function ensures all medal-winning performances are accounted for, even if the original CSV omitted the event.
    """
    for (code, dis, e), medal_info in medallist_dict.items():
        athlete_id = paris_id_to_athlete_id.get(code)
        key = (code, dis, e)
        if key in paris_athlete_event_set:
            continue  # Already processed from csv

        athlete = updated_athlete_dict[athlete_id]
        athlete_name = athlete["name"]
        athlete_id = athlete["athlete_id"]
        country_code = athlete["country_noc"]

        event_data_list.append({
            "edition": "2024 Summer Olympics",
            "edition_id": "63",
            "country_noc": country_code,
            "sport": dis,
            "event": e,
            "result_id": "",
            "athlete": athlete_name,
            "athlete_id": athlete_id,
            "pos": medal_info.get("pos", ""),
            "medal": medal_info.get("medal_type", ""),
            "isTeamSport": "TRUE" if key in paris_team_set else "FALSE",
            "age": ""
        })
        #print(f"Added missing medal event: {athlete_name} | {dis} | {e}")


def calculate_event_age_and_medal_amount(event_list, updated_athlete_dict, game_dict, country_dict):
    """
    Calculates athlete age at the time of the event and tallies medal counts per country per Olympic edition.

    For each event record in `event_list`, this function:
    - Computes the athlete's age using their birth date and the game's start date.
    - Updates the "age" field in the event record.
    - Aggregates medal counts by country and Olympic edition (Gold, Silver, Bronze, and Total).
    - Tracks the number of athletes per country per edition.

    Args:
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
        updated_athlete_dict (dict): Dictionary to store updated athlete data with correct born format.
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
        game_dict (dict): Dictionary of game data keyed by edition_id.
                        Example:{ 
                                    "63" : {
                                        'edition': '2024 Summer Olympics', 
                                        'edition_id': '63', 
                                        'edition_url': '/editions/63', 
                                        'year': '2024', 
                                        ...
                                        'start_dt_obj': datetime.datetime(2024, 7, 24, 0, 0), 
                                        'end_dt_obj': datetime.datetime(2024, 8, 11, 0, 0)}
                                    },...
                                }
        country_dict (dict) : Dictionary where keys are 'noc' values and values are row dictionaries.
                        Example: {
                                    'AFG': {
                                        'noc': 'AFG', 'country': 'Afghanistan'
                                    }, ...
                                  }
    Returns:
        tally_dict (dict): tally_dict (dict): A nested dictionary summarizing medal tallies and athlete counts.
                            Keys are tuples (edition, edition_id, country_noc)
                        Example: {
                                    (2024 Summer Olympics, 63, TPE): {
                                        'edition': '2024 Summer Olympics',
                                        'edition_id': '63',
                                        'Country': 'Chinese Taipei',
                                        'NOC': 'TPE',
                                        'number_of_athletes': '76',
                                        'gold_medal_count': '3',
                                        'silver_medal_count': '0',
                                        'bronze_medal_count': '5',
                                        'total_medals': '8'
                                    },...
                                }
    """
    # missing_ids = []  # no exist ['36110', '37833', '920957', '69534', '69534', '2302137', '902283'] in athlete
    tally_dict = {}
    athlete_tracker = {}
    team_medal_tracker = set()

    medal_map = {
        "Gold": "gold_medal_count",
        "Silver": "silver_medal_count",
        "Bronze": "bronze_medal_count"
    }

    for row in event_list:
        athlete_id = row["athlete_id"]
        if athlete_id in updated_athlete_dict:  # Find missing id which present in event.csv, but not athlete_bio.csv
            # calculate age
            born_part = updated_athlete_dict[athlete_id]["born"]
            if born_part:
                born_date = datetime.strptime(born_part, "%d-%b-%Y")
                game = game_dict[row["edition_id"]]
                start_date = game["start_dt_obj"]
                end_date = game["end_dt_obj"]
                age = start_date.year - born_date.year
                if born_date > end_date:
                    age -= 1
                row["age"] = age
        # Create tally dict
        key = (
            row["edition"], row["edition_id"], row["country_noc"]
        )
        tracker_key = (
            row["edition_id"], row["country_noc"]
        )

        if key not in tally_dict:
            tally_dict[key] = {
                "edition": row["edition"],
                "edition_id": row["edition_id"],
                "Country": country_dict[row["country_noc"]]["country"],
                "NOC": row["country_noc"],
                "number_of_athletes": 0,
                "gold_medal_count": 0,
                "silver_medal_count": 0,
                "bronze_medal_count": 0,
                "total_medals": 0
            }

        if tracker_key not in athlete_tracker:
            athlete_tracker[tracker_key] = set()
        if athlete_id not in athlete_tracker[tracker_key]:
            athlete_tracker[tracker_key].add(athlete_id)
            tally_dict[key]["number_of_athletes"] += 1

        tally = tally_dict[key]
        #tally["number_of_athletes"] += 1

        medal_type = row["medal"]

        if medal_type in medal_map:
            team_medal_key = (row["edition_id"], row["sport"], row["event"], row["country_noc"], medal_type)
            if team_medal_key not in team_medal_tracker:
                tally[medal_map[medal_type]] += 1
                tally["total_medals"] += 1
                team_medal_tracker.add(team_medal_key)
    return tally_dict
    #print(missing_ids)