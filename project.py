import utils
import project_alan
import project_daniel
import project_tzuyi
import project_nina
import time
# Feel free to add additional python files to this project and import
# them in this file. However, do not change the name of this file
# Avoid the names ms1check.py and ms2check.py as those file names
# are reserved for the autograder

# To run your project use:
#     python runproject.py

# This will ensure that your project runs the way it will run in the
# the test environment

############################

def process_country_file(country_csv, paris_country_csv):
    country_header, country_dict = project_nina.read_country_file(country_csv)
    project_nina.append_new_country(country_dict, paris_country_csv)
    country_sorted_list = project_nina.sort_country_data_by_country_name(country_dict)
    return country_dict, country_sorted_list, country_header

def process_event_and_athlete_files(event_csv, athlete_csv, game_dict):
    #start_time = time.time()
    event_year_dict, event_header, event_list, max_result_id = project_daniel.read_event_result_year(event_csv, game_dict)
    #end_time = time.time()
    #print(f"--------[read_event_result_year] Runtime: {end_time - start_time:.4f} seconds")

    #start_time = time.time()
    athlete_header, athlete_max_id, existing_keys, updated_athlete_dict = project_tzuyi.process_athlete_file(athlete_csv, event_year_dict)
    #end_time = time.time()
    #print(f"--------[process_athlete_file] Runtime: {end_time - start_time:.4f} seconds")
    
    return event_header, event_list, max_result_id, athlete_header, athlete_max_id, existing_keys, updated_athlete_dict

def generate_outputs(new_athlete_output_name, athlete_header, updated_athlete_dict,
                     new_event_output_name, event_header, event_data_list,
                     new_tally_output_name, tally_header, medal_dict,
                     new_game_output_name, game_header, cleaned_game_data,
                     new_country_output_name, country_header, country_dict):
    utils.write_csv_file_dict_flexible(new_athlete_output_name, athlete_header, updated_athlete_dict)
    utils.write_csv_file_dict_flexible(new_event_output_name, event_header, event_data_list)
    utils.write_csv_file_dict_flexible(new_tally_output_name, tally_header, medal_dict)
    utils.write_csv_file_dict_flexible(new_game_output_name, game_header, cleaned_game_data)
    utils.write_csv_file_dict_flexible(new_country_output_name, country_header, country_dict)

# This main function is the function that the runner will call
# The function prototype cannot be changed
def main():

    #start_time = time.time()
    game_header, game_dict = project_tzuyi.process_game_file("olympics_games.csv")
    #end_time = time.time()
    #print(f"[process_game_file] Runtime: {end_time - start_time:.4f} seconds")

    #start_time = time.time()
    country_dict, country_sorted_list, country_header = process_country_file("olympics_country.csv", "paris/nocs.csv")
    #end_time = time.time()
    #print(f"[process_country_file] Runtime: {end_time - start_time:.4f} seconds")

    #start_time = time.time()
    event_header, event_data_list, max_result_id, athlete_header, athlete_max_id, existing_keys, updated_athlete_dict = process_event_and_athlete_files("olympic_athlete_event_results.csv", "olympic_athlete_bio.csv", game_dict)
    #end_time = time.time()
    #print(f"[process_event_and_athlete_files] Runtime: {end_time - start_time:.4f} seconds")

    #start_time = time.time()
    medallist_dict = project_nina.read_medallist_data("paris/medallists.csv")
    #end_time = time.time()
    #print(f"[read_medallist_data] Runtime: {end_time - start_time:.4f} seconds")

    #start_time = time.time()
    paris_team_set = project_nina.read_paris_team("paris/teams.csv")
    #end_time = time.time()
    #print(f"[read_paris_team] Runtime: {end_time - start_time:.4f} seconds")

    #start_time = time.time()
    paris_event_set = project_nina.read_paris_event("paris/events.csv")
    #end_time = time.time()
    #print(f"[read_paris_team] Runtime: {end_time - start_time:.4f} seconds")

    #start_time = time.time()
    paris_athlete_event_set, paris_id_to_athlete_id = project_daniel.process_athlete_event_data(
        "paris/athletes.csv", existing_keys, updated_athlete_dict, athlete_max_id,
        event_data_list, medallist_dict, max_result_id, paris_team_set, paris_event_set
    )
    #end_time = time.time()
    #print(f"[process_athlete_event_data] Runtime: {end_time - start_time:.4f} seconds")

    project_alan.add_missing_medallist_events(medallist_dict, paris_athlete_event_set, updated_athlete_dict, event_data_list,
        paris_team_set, paris_id_to_athlete_id
    )

    #start_time = time.time()
    tally_dict = project_alan.calculate_event_age_and_medal_amount(event_data_list, updated_athlete_dict, game_dict, country_dict)
    #end_time = time.time()
    #print(f"[calculate_event_age_and_medal_amount] Runtime: {end_time - start_time:.4f} seconds")

    #start_time = time.time()
    tally_header = ["edition", "edition_id", "Country", "NOC", "number_of_athletes",
                    "gold_medal_count", "silver_medal_count", "bronze_medal_count", "total_medals"]
    generate_outputs("new_olympic_athlete_bio.csv", athlete_header, updated_athlete_dict,
                     "new_olympic_athlete_event_results.csv", event_header, event_data_list,
                     "new_medal_tally.csv", tally_header, tally_dict,
                     "new_olympics_games.csv", game_header, game_dict,
                     "new_olympics_country.csv", country_header, country_sorted_list)
    #end_time = time.time()
    #print(f"[generate_outputs] Runtime: {end_time - start_time:.4f} seconds")