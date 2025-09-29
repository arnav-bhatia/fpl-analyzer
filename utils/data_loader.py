from typing import Tuple, Dict, List, Any
from urllib.parse import urljoin
from datetime import datetime
import pandas as pd
import requests
import pytz
import utils
import requests
import streamlit as st
from st_aggrid import JsCode

HEADERS = {"User-Agent": "FPL-Analyzer/1.0 (+https://github.com/arnav/fpl-analyzer)"}

def load_manager_details(ENTRY_URL: str = "https://fantasy.premierleague.com/api/entry", manager_id="5252797"):
    MANAGER_URL = urljoin(f"{ENTRY_URL}/", manager_id)
    delta_formatter = JsCode("""
    function(params) {
        if (params.value < 0) {
            return {
                'color': 'red',
                'fontWeight': 'bold',
            };
        } else {
            return {
                'color': 'green',
                'fontWeight': 'bold',
            };
        }
    };
    """)
    try:
        response = requests.get(MANAGER_URL, timeout=10, headers=HEADERS)
        response.raise_for_status()
        manager_json = response.json()
        manager_details = {
            'First Name': manager_json['player_first_name'],
            'Last Name': manager_json['player_last_name'],
            'Country': manager_json['player_region_name'],
            'Team Name': manager_json['name'],
            'Total Points': manager_json['summary_overall_points'],
            'Global Rank': manager_json['summary_overall_rank']
        }
        manager_league_list = []
        for league in manager_json['leagues']['classic']:
            league_details = {
                'Name': league['name'],
                'Rank': league['entry_rank'],
                'Previous Rank': league['entry_last_rank'],
                'Total Players': league['rank_count'],
            }
            manager_league_list.append(league_details)
    
        manager_league_df = pd.DataFrame(manager_league_list)
        manager_league_df['Percentile'] = round((manager_league_df['Rank']/manager_league_df['Total Players'])*100, 0)
        manager_league_df['Delta'] = manager_league_df['Previous Rank'] - manager_league_df['Rank'] 
        
        league_col_defs = [
        {"headerName": "League Name", "field": "Name", "flex": 2, "minWidth": 100, "pinned": "left", "cellStyle": {"font-weight": "bold", "text-transform": "uppercase"}},
        {"headerName": "Total Players", "field": "Total Players", "flex": 1, "minWidth": 90},
        {"headerName": "Current Rank", "field": "Rank", "flex": 1, "minWidth": 70},
        {"headerName": "Previous Rank", "field": "Previous Rank", "flex": 1, "minWidth": 70},
        {"headerName": "Delta", "field": "Delta", "flex": 1, "minWidth": 70, "cellStyle": delta_formatter},
        {"headerName": "Percentile", "field": "Percentile", "flex": 1, "minWidth": 70},

        ]
        
        return manager_league_df, league_col_defs, manager_details
        
    except requests.exceptions.HTTPError as http_err:
        raise RuntimeError(f"HTTP error occurred while fetching player data: {http_err}")
    except requests.exceptions.Timeout:
        raise RuntimeError("Request timed out while fetching player data.")
    except Exception as err:
        raise RuntimeError(f"An error occurred while fetching player data: {err}")

def load_manager_gw_history(ENTRY_URL: str = "https://fantasy.premierleague.com/api/entry", manager_id="5252797"):
    MANAGER_HISTORY_URL = urljoin(f"{ENTRY_URL}/", f"{manager_id}/history")
    try:
        response = requests.get(MANAGER_HISTORY_URL, timeout=10, headers=HEADERS)
        response.raise_for_status()
        gw_history_json = response.json()
        user_gw_history = []
        for gw in gw_history_json['current']:
            gw_details = {
                'GW': gw['event'],
                'Points': gw['points'],
                'Rank': gw['overall_rank']
            }
            user_gw_history.append(gw_details)
            
        user_gw_history_df = pd.DataFrame(user_gw_history)
        return user_gw_history_df
    except requests.exceptions.HTTPError as http_err:
        raise RuntimeError(f"HTTP error occurred while fetching player data: {http_err}")
    except requests.exceptions.Timeout:
        raise RuntimeError("Request timed out while fetching player data.")
    except Exception as err:
        raise RuntimeError(f"An error occurred while fetching player data: {err}")

def get_my_team(team_id: str):
    tokens = utils.authenticate()
    access_token = tokens["access_token"]

    url = f"https://fantasy.premierleague.com/api/my-team/{team_id}/"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch team data: {response.status_code} {response.text}")

def load_player_data(PLAYER_URL: str = "https://fantasy.premierleague.com/api/bootstrap-static/") -> Dict[str, Any]:
    """
    Loads player data from the FPL API and returns it in JSON format.

    Args:
        PLAYER_URL (str): URL of the API. Default is the official FPL bootstrap-static endpoint.

    Returns:
        Dict[str, Any]: JSON object containing player data.

    Raises:
        RuntimeError: If there is an HTTP error, timeout, or any other error during the API call.
    """
    try:
        response = requests.get(PLAYER_URL, timeout=10, headers=HEADERS)
        response.raise_for_status()
        player_json = response.json()
        return player_json
    except requests.exceptions.HTTPError as http_err:
        raise RuntimeError(f"HTTP error occurred while fetching player data: {http_err}")
    except requests.exceptions.Timeout:
        raise RuntimeError("Request timed out while fetching player data.")
    except Exception as err:
        raise RuntimeError(f"An error occurred while fetching player data: {err}")


def load_fixtures_data(FIXTURES_URL: str = "https://fantasy.premierleague.com/api/fixtures/") -> Dict[str, Any]:
    """
    Loads fixture data from the FPL API and returns it in JSON format.

    Args:
        FIXTURES_URL (str): URL of the API. Default is the official FPL fixtures endpoint.

    Returns:
        Dict[str, Any]: JSON object containing fixture data.

    Raises:
        RuntimeError: If there is an HTTP error, timeout, or any other error during the API call.
    """
    try:
        response = requests.get(FIXTURES_URL, timeout=10, headers=HEADERS)
        response.raise_for_status()
        fixtures_json = response.json()
        return fixtures_json
    except requests.exceptions.HTTPError as http_err:
        raise RuntimeError(f"HTTP error occurred while fetching fixture data: {http_err}")
    except requests.exceptions.Timeout:
        raise RuntimeError("Request timed out while fetching fixture data.")
    except Exception as err:
        raise RuntimeError(f"An error occurred while fetching fixture data: {err}")

def get_current_gameweek(player_json: Dict[str, Any]):
    for gw in player_json['events']:
        if gw['is_current']:
            current_gw = gw['id']
    return current_gw
    
def get_pl_teams_dict_and_list(player_json: Dict[str, Any]) -> Tuple[Dict[int, str], List[str]]:
    """
    Returns all Premier League teams and their FPL IDs.

    Args:
        player_json (Dict[str, Any]): JSON object containing data from the FPL API.

    Returns:
        Tuple[Dict[int, str], List[str]]: 
            - Dictionary mapping team IDs to team names.
            - List of all team names.
    """
    pl_teams_dict: Dict[int, str] = {}
    pl_teams_list: List[str] = []
    for team in player_json["teams"]:
        pl_teams_dict[team["id"]] = team["name"]
        pl_teams_list.append(team["name"])
    return pl_teams_dict, pl_teams_list


def get_position_dict() -> Dict[int, str]:
    """
    Returns a dictionary mapping FPL position IDs to position names.

    Returns:
        Dict[int, str]: Mapping of FPL position IDs to position names.
    """
    position_dict = {
        1: "Goalkeeper",
        2: "Defender",
        3: "Midfielder",
        4: "Forward"
    }
    return position_dict


def get_status_dict() -> Dict[str, str]:
    """
    Returns a dictionary mapping FPL status codes to status descriptions.

    Returns:
        Dict[str, str]: Mapping of FPL status codes to descriptions.
    """
    status_dict = {
        'u': 'unavailable',
        'a': 'available',
        'd': 'doubtful',
        'i': 'injured',
        'n': 'not available',
        's': 'suspended'
    }
    return status_dict

# Player and Fixture Dataframes

def return_player_df(
    player_json: Dict[str, Any],
    team_dict: Dict[int, str],
    status_dict: Dict[str, str],
    position_dict: Dict[int, str]
) -> pd.DataFrame:
    """
    Extracts player data from the API JSON and returns a DataFrame.

    Args:
        player_json (Dict[str, Any]): JSON data containing player information.
        team_dict (Dict[int, str]): Mapping of team IDs to team names.
        status_dict (Dict[str, str]): Mapping of status codes to status descriptions.
        position_dict (Dict[int, str]): Mapping of position IDs to position names.

    Returns:
        pd.DataFrame: DataFrame containing player statistics.
    """
    player_database = []
    for player in player_json["elements"]:
        player_row = {
            "ID": player.get("id"),
            "Name": player.get("web_name"),
            "Availability": status_dict.get(player.get("status"), "Unknown"),
            "Position": position_dict.get(player.get("element_type"), "Unknown"),
            "Full Name": f"{player.get('first_name', '')} {player.get('second_name', '')}",
            "Club": team_dict.get(player.get("team"), "Unknown"),
            "Price": float(player.get("now_cost", 0) / 10),
            "Minutes Played": player.get('minutes'),
            "Total Points": player.get("total_points"),
            'Form': player.get('form'),
            'PPG': player.get('points_per_game'),
            'Value': player.get('value_season'),
            'Selected By (%)': player.get('selected_by_percent'),
            'Goals Scored': player.get('goals_scored'),
            'Assists': player.get('assists'),
            'Clean Sheets': player.get('clean_sheets'),
            'Goals Conceded': player.get('goals_conceded'),
            'Own Goals': player.get('own_goals'),
            'Price Increase': 0 if player.get('cost_change_start') < 0 else player.get('cost_change_start')/10,
            'Price Decrease': 0 if player.get('cost_change_start_fall') < 0 else (player.get('cost_change_start_fall')*-1)/10,
            'Penalties Saved': player.get('penalties_saved'),
            'Penalties Missed': player.get('penalties_missed'),
            'Yellow Cards': player.get('yellow_cards'),
            'Red Cards': player.get('red_cards'),
            'Saves': player.get('saves'),
            'Bonus': player.get('bonus'),
            'BPS': player.get('bps'),
            'Influence': player.get('influence'),
            'Creativity': player.get('creativity'),
            'Threat': player.get('threat'),
            'ICT Index': player.get('ict_index'),
            'photo_code': player.get('code'),
            'Defensive Contributions': player.get('defensive_contribution', 0),
            'Starts': player.get('starts'),
            'Expected Goals': player.get('expected_goals'),
            'Expected Assists': player.get('expected_assists'),
            'Expected Goal Involvements': player.get('expected_goal_involvements'),
            'Expected Goals Conceded': player.get('expected_goals_conceded'),
            'Influence Rank': player.get('influence_rank'),
            'Influence Rank Type': player.get('influence_rank_type'),
            'Creativity Rank': player.get('creativity_rank'),
            'Creativity Rank Type': player.get('creativity_rank_type'),
            'Threat Rank': player.get('threat_rank'),
            'Threat Rank Type': player.get('threat_rank_type'),
            'ICT Index Rank': player.get('ict_index_rank'),
            'ICT Index Rank Type': player.get('ict_index_rank_type'),
            'Expected Goals per 90': player.get('expected_goals_per_90'),
            'Saves per 90': player.get('saves_per_90'),
            'Expected Assists per 90': player.get('expected_assists_per_90'),
            'Expected Goal Involvement per 90': player.get('expected_goal_involvements_per_90'),
            'Expected Goals Conceded per 90': player.get('expected_goals_conceded_per_90'),
            'Goals Conceded per 90': player.get('goals_conceded_per_90'),
            'Form Rank': player.get('form_rank'),
            'Form Rank Type': player.get('form_rank_type'),
            'Points per Game Rank': player.get('points_per_game_rank'),
            'Points per Game Rank Type': player.get('points_per_game_rank_type'),
            'Clean Sheets per 90': player.get('clean_sheets_per_90'),
        }
        player_database.append(player_row)

    return pd.DataFrame(player_database)


def get_dream_team(player_df, DREAM_TEAM_URL="https://fantasy.premierleague.com/api/dream-team/"):
    try:
        response = requests.get(DREAM_TEAM_URL, timeout=10, headers=HEADERS)
        response.raise_for_status()
        dream_team = response.json()
        players = player_df.copy()
        players = players.set_index('ID', drop=True)
        dt_players = []
        for row in dream_team['team']:
            points = row['points']
            player_row = players.loc[row['element'], :]
            name = player_row['Name']
            club = player_row['Club']
            position = player_row['Position']
            price = player_row['Price']
            form = player_row['Form']
            player = {
                "Name": name,
                "Position": position,
                "Club": club,
                "Price": price,
                "Points": points,
                "Form": form
            }
            dt_players.append(player)

        dt_col_defs = [
        {"headerName": "Name", "field": "Name", "flex": 2, "minWidth": 100, "pinned": "left", "cellStyle": {"font-weight": "bold", "text-transform": "uppercase"}},
        {"headerName": "Position", "field": "Position", "flex": 1, "minWidth": 90},
        {"headerName": "Club", "field": "Club", "flex": 1, "minWidth": 100},
        {"headerName": "Price", "field": "Price", "flex": 1, "minWidth": 70},
        {"headerName": "Points", "field": "Points", "flex": 1, "minWidth": 70, "cellStyle": {"font-weight": "bold"}},
        {"headerName": "Form", "field": "Form", "flex": 1, "minWidth": 70},

        ]

        return pd.DataFrame(dt_players), dt_col_defs
    except requests.exceptions.HTTPError as http_err:
        raise RuntimeError(f"HTTP error occurred while fetching dream team data: {http_err}")
    except requests.exceptions.Timeout:
        raise RuntimeError("Request timed out while fetching dream team data.")
    except Exception as err:
        raise RuntimeError(f"An error occurred while fetching dream team data: {err}")

def return_top_price_risers(player_df):
    price_increase_df = player_df[['Name', 'Club', 'Price Increase', 'Price']].sort_values(by='Price Increase', ascending=False).head(5)

    pi_col_defs = [
        {"headerName": "Name", "field": "Name", "flex": 2, "minWidth": 100, "pinned": "left", "cellStyle": {"font-weight": "bold", "text-transform": "uppercase"}},
        {"headerName": "Club", "field": "Club", "flex": 1, "minWidth": 100},
        {"headerName": "Price", "field": "Price", "flex": 1, "minWidth": 70},
        {"headerName": "Increase", "field": "Price Increase", "flex": 1, "minWidth": 90, "cellStyle": {"color":"green", "font-weight": "bold"}},
        ]
    return price_increase_df, pi_col_defs

def return_top_price_fallers(player_df):
    price_decrease_df = player_df[['Name', 'Club', 'Price Decrease', 'Price']].sort_values(by='Price Decrease', ascending=True).head(5)

    pd_col_defs = [
        {"headerName": "Name", "field": "Name", "flex": 2, "minWidth": 100, "pinned": "left", "cellStyle": {"font-weight": "bold", "text-transform": "uppercase"}},
        {"headerName": "Club", "field": "Club", "flex": 1, "minWidth": 100},
        {"headerName": "Price", "field": "Price", "flex": 1, "minWidth": 70},
        {"headerName": "Decrease", "field": "Price Decrease", "flex": 1, "minWidth": 90, "cellStyle": {"color":"red", "font-weight": "bold"}},
        ]
    return price_decrease_df, pd_col_defs

def convert_utc_to_ist(datetime_str: str) -> datetime:
    """
    Converts UTC time string to IST datetime.

    Args:
        datetime_str (str): UTC datetime in ISO format.

    Returns:
        datetime: Datetime object converted to IST.
    """
    utc_time = datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.utc)
    return utc_time.astimezone(pytz.timezone('Asia/Kolkata'))


def get_match_date(datetime_str: str) -> str:
    """
    Converts UTC datetime string to IST date string.

    Args:
        datetime_str (str): UTC datetime in ISO format.

    Returns:
        str: Date in YYYY-MM-DD format.
    """
    return convert_utc_to_ist(datetime_str).strftime('%Y-%m-%d')


def get_match_time(datetime_str: str) -> str:
    """
    Converts UTC datetime string to IST time string.

    Args:
        datetime_str (str): UTC datetime in ISO format.

    Returns:
        str: Time in hh:mm(am/pm) format.
    """
    return convert_utc_to_ist(datetime_str).strftime('%I:%M%p').lstrip('0').lower()


def return_fixtures_df(fixtures_json: List[Dict[str, Any]], team_dict: Dict[int, str], player_df) -> pd.DataFrame:
    """
    Converts fixture JSON into a DataFrame.

    Args:
        fixtures_json (List[Dict[str, Any]]): List of fixture dictionaries.
        team_dict (Dict[int, str]): Mapping of team IDs to team names.

    Returns:
        pd.DataFrame: DataFrame containing fixture details.
    """
    fixtures = []
    for match in fixtures_json:
        h_a = ['h', 'a']
        home_goals = []
        away_goals = []
        home_assists = []
        away_assists = []
        bonus_getters = []
        home_team = team_dict.get(match.get("team_h"), "Unknown")
        away_team = team_dict.get(match.get("team_a"), "Unknown")

        try:
            goals_scored = match['stats'][0]
            assists = match['stats'][1]

            for team in h_a:
                # Goals
                if goals_scored[team]:
                    for goal in goals_scored[team]:
                        player_id = goal['element']
                        player = player_df.loc[player_df['ID'] == player_id, 'Name'].iloc[0]
                        goals = goal['value']
                        if team == 'h':
                            home_goals.append(f"{player}({goals})")
                        else:
                            away_goals.append(f"{player}({goals})")

                # Assists
                if assists[team]:
                    for assist in assists[team]:
                        player_id = assist['element']
                        player = player_df.loc[player_df['ID'] == player_id, 'Name'].iloc[0]
                        assisted = assist['value']
                        if team == 'h':
                            home_assists.append(f"{player}({assisted})")
                        else:
                            away_assists.append(f"{player}({assisted})")
        except:
            pass

        
        try:
            bonus = match['stats'][8]
            temp_bonus = []
            for team in h_a:
                if bonus[team]:
                    for bp in bonus[team]:
                        player_id = bp['element']
                        player = player_df.loc[player_df['ID'] == player_id, 'Name'].iloc[0]
                        bp_received = int(bp['value'])
                        temp_bonus.append((player, bp_received))

            temp_bonus.sort(key=lambda x: x[1], reverse=True)
            bonus_getters = [f"{player}({bp})" for player, bp in temp_bonus]

        except:
            pass

        match_dict = {
            "Gameweek": match.get("event"),
            "Home Team": home_team,
            "Home Team Difficulty": match.get('team_h_difficulty'),
            "Away Team": away_team,
            "Away Team Difficulty": match.get('team_a_difficulty'),
            "Date": match.get('kickoff_time'),
            "Score": f"{match.get('team_h_score')} : {match.get('team_a_score')}",
            "Home Team Scorers": ", ".join(home_goals) if home_goals else "",
            "Away Team Scorers": ", ".join(away_goals) if away_goals else "",
            "Home Team Assisters": ", ".join(home_assists) if home_assists else "",
            "Away Team Assisters": ", ".join(away_assists) if away_assists else "",
            "Bonus Points": ", ".join(bonus_getters) if bonus_getters else "",
        }

        fixtures.append(match_dict)

    fixtures_df = pd.DataFrame(fixtures)
    fixtures_df.loc[fixtures_df['Score'] == 'None : None', 'Score'] = 'Yet to Happen'
    fixtures_df['Match Date'] = fixtures_df['Date'].apply(get_match_date)
    fixtures_df['Match Time (IST)'] = fixtures_df['Date'].apply(get_match_time)
    fixtures_df.drop('Date', axis=1, inplace=True)
    
    fixtures_col_defs = [
        {"headerName": "GW", "field": "Gameweek", "flex": 1, "minWidth": 70},
        {"headerName": "Home Team", "field": "Home Team", "flex": 1.5, "minWidth": 100},
        {"headerName": "Away Team", "field": "Away Team", "flex": 1.5, "minWidth": 100},
        {"headerName": "Score", "field": "Score", "flex": 2, "minWidth": 70, "cellStyle": {"font-weight": "bold"}},
        {"headerName": "Date", "field": "Match Date", "flex": 1, "minWidth": 70},
        {"headerName": "Time (IST)", "field": "Match Time (IST)", "flex": 1, "minWidth": 70},        
        {"headerName": "Home Scorers", "field": "Home Team Scorers", "flex": 2, "minWidth": 100},
        {"headerName": "Away Scorers", "field": "Away Team Scorers", "flex": 2, "minWidth": 100},
        {"headerName": "Home Assisters", "field": "Home Team Assisters", "flex": 2, "minWidth": 100},
        {"headerName": "Away Assisters", "field": "Away Team Assisters", "flex": 2, "minWidth": 100},
        {"headerName": "Bonus Points", "field": "Bonus Points", "flex": 2, "minWidth": 140},
    ]

    return fixtures_df, fixtures_col_defs


def create_team_fixtures_database(fixtures_df: pd.DataFrame, team_list: List[str]) -> Dict[str, pd.DataFrame]:
    """
    Creates a dictionary of DataFrames containing fixtures for each team.

    Args:
        fixtures_df (pd.DataFrame): DataFrame containing all fixtures.
        team_list (List[str]): List of all team names.

    Returns:
        Dict[str, pd.DataFrame]: Mapping of team name to their fixtures DataFrame.
    """
    team_fixtures_database = {}

    for team in team_list:
        team_fixtures = fixtures_df[(fixtures_df['Home Team'] == team) | (fixtures_df['Away Team'] == team)].reset_index(drop=True)
        team_fixture_list = []

        for gw in range(len(team_fixtures)):
            game = team_fixtures.iloc[gw]
            if game['Home Team'] == team:
                venue = 'Home'
                opponent = game['Away Team']
                difficulty = game['Home Team Difficulty']
            else:
                venue = 'Away'
                opponent = game['Home Team']
                difficulty = game['Away Team Difficulty']

            gw_dict = {
                "Game Week": game['Gameweek'],
                "Opponent": opponent,
                "Venue": venue,
                'Fixture Difficulty Rating': int(difficulty) if difficulty is not None else None,
                'Date': game['Match Date'],
                'Time (IST)': game['Match Time (IST)'],
                "Score": game['Score'],

            }
            team_fixture_list.append(gw_dict)

        team_fixture_df = pd.DataFrame(team_fixture_list)
        team_fixtures_database[team] = team_fixture_df

    return team_fixtures_database


def get_team_fixtures(team: str, team_fixtures_database: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Retrieves fixtures for a specific team.

    Args:
        team (str): Name of the team.
        team_fixtures_database (Dict[str, pd.DataFrame]): Mapping of team name to their fixtures DataFrame.

    Returns:
        pd.DataFrame: DataFrame containing the team's fixtures.
    """
    team_df = team_fixtures_database.get(team, pd.DataFrame())
    cols_to_str = ['Game Week', 'Fixture Difficulty Rating']
    team_df[cols_to_str] = team_df[cols_to_str].astype(str)

    col_defs = [
        {"headerName": "GW", "field": "Game Week", "flex": 1, "minWidth": 70},
        {"headerName": "Opponent", "field": "Opponent", "flex": 2, "minWidth": 160, "cellStyle": {"font-weight": "bold"}},
        {"headerName": "Venue", "field": "Venue", "flex": 1, "minWidth": 100},
        {"headerName": "FDR", "field": "Fixture Difficulty Rating", "flex": 1, "minWidth": 70, "cellStyle": {"font-weight": "bold"}},
        {"headerName": "Date", "field": "Date", "flex": 1, "minWidth": 100},
        {"headerName": "Time (IST)", "field": "Time (IST)", "flex": 1, "minWidth": 100},
        {"headerName": "Score", "field": "Score", "flex": 2, "minWidth": 120},
    ]

    return team_df, col_defs

def build_pl_table(pl_teams_list, fixtures_database, get_team_fixtures):
    """
    Build a Premier League-style table from fixtures data.

    Parameters
    ----------
    pl_teams_list : list
        List of team names.
    fixtures_database : pd.DataFrame
        The complete fixtures dataset.
    get_team_fixtures : function
        A function that returns (team_fixt, other_data) when given (team, fixtures_database).

    Returns
    -------
    pd.DataFrame, list
        League table sorted by Points and Goal Difference, plus AgGrid col defs.
    """
    def result_checker(scored, conceded):
        if scored > conceded:
            return 3, "Wins"
        elif scored < conceded:
            return 0, "Losses"
        else:
            return 1, "Draws"

    pl_table_list = []

    for team in pl_teams_list:
        team_fixt, _ = get_team_fixtures(team, fixtures_database)
        team_fixt = team_fixt.set_index('Game Week')
        team_fixt.index = team_fixt.index.astype(str)

        team_dict = {
            'Team': team,
            'Matches Played': 0,
            'Wins': 0,
            'Draws': 0,
            'Losses': 0,
            'Goals Scored': 0,
            'Goals Conceded': 0,
            'Points': 0,
            'Goal Difference': 0,
        }

        for i, (gw, match) in enumerate(team_fixt.iterrows(), start=1):
            if match['Score'] == "Yet to Happen":
                continue

            score = match["Score"]
            venue = match["Venue"]

            left, right = [s.strip() for s in score.split(':')]
            goals_scored, goals_conceded = int(left), int(right)
            if venue == "Away":
                goals_scored, goals_conceded = goals_conceded, goals_scored

            team_dict['Matches Played'] = i
            team_dict['Goals Scored'] += goals_scored
            team_dict['Goals Conceded'] += goals_conceded
            team_dict['Goal Difference'] += (goals_scored - goals_conceded)

            points, result = result_checker(goals_scored, goals_conceded)
            team_dict[result] += 1
            team_dict['Points'] += points

        pl_table_list.append(team_dict)

    pl_table_df = (
        pd.DataFrame(pl_table_list)
          .sort_values(by=['Points', 'Goal Difference'], ascending=False)
          .reset_index(drop=True)
    )

    pl_table_df.insert(0, 'Position', range(1, 21))

    pl_table_col_defs = [
        {"headerName": "P", "field": "Position", "flex": 1, "maxWidth": 50},
        {"headerName": "Team", "field": "Team", "flex": 2, "minWidth": 120,"cellStyle": {"font-weight": "bold", "text-transform": "uppercase"}},
        {"headerName": "Matches", "field": "Matches Played", "flex": 1, "minWidth": 70},
        {"headerName": "Wins", "field": "Wins", "flex": 1, "minWidth": 70},
        {"headerName": "Draws", "field": "Draws", "flex": 1, "minWidth": 70},
        {"headerName": "Losses", "field": "Losses", "flex": 1, "minWidth": 70},
        {"headerName": "Pts", "field": "Points", "flex": 1, "minWidth": 100, "cellStyle": {"font-weight": "bold", "color": "white"}},
        {"headerName": "GD", "field": "Goal Difference", "flex": 1, "minWidth": 70},
        {"headerName": "GS", "field": "Goals Scored", "flex": 1, "minWidth": 70},
        {"headerName": "GC", "field": "Goals Conceded", "flex": 1, "minWidth": 70},
    ]

    return pl_table_df, pl_table_col_defs

def get_team_FDR_rating(fixtures_df: pd.DataFrame, team_list: list[str]) -> pd.DataFrame:
    out = []
    for team in team_list:
        home_row = fixtures_df.loc[fixtures_df['Home Team'] == team, 'Away Team Difficulty'].dropna()
        away_row = fixtures_df.loc[fixtures_df['Away Team'] == team, 'Home Team Difficulty'].dropna()
        if not home_row.empty and not away_row.empty:
            out.append({
                'Team': team,
                'Home FDR': int(home_row.iloc[0]),
                'Away FDR': int(away_row.iloc[0]),
            })
    return pd.DataFrame(out)

def create_team_fdr_database(team_fixtures_database):
    fdr_list = []
    for team in team_fixtures_database:
        df = team_fixtures_database[team]
        df = df[df['Score'] == 'Yet to Happen']
        df['Fixture Difficulty Rating'] = df['Fixture Difficulty Rating'].apply(pd.to_numeric)
        avg_5 = round(df.head(5)['Fixture Difficulty Rating'].mean(), 2)
        avg_10 = round(df.head(10)['Fixture Difficulty Rating'].mean(), 2)
        team_fdr_avg = {
            'Team' : team,
            '5 GW FDR Avg' : avg_5,
            '10 GW FDR Avg' : avg_10
        }
        fdr_list.append(team_fdr_avg)
    
    fdr_avg_df = pd.DataFrame(fdr_list)
    fdr_avg_df = fdr_avg_df.sort_values(by='5 GW FDR Avg')
    fdr_avg_df = fdr_avg_df.reset_index(drop=True)
    fdr_avg_df.index = range(1, 21)
    
    col_defs = [
        {"headerName": "Club", "field": "Team", "flex": 2, "minWidth": 140, "cellStyle": {"font-weight": "bold"}},
        {"headerName": "5 Gameweek Avg", "field": "5 GW FDR Avg", "flex": 1, "minWidth": 100},
        {"headerName": "10 Gameweek Avg", "field": "10 GW FDR Avg", "flex": 1, "minWidth": 100},
    ]
    
    return fdr_avg_df, col_defs

def return_top_players_points(player_database: pd.DataFrame, top_n: int = 10) -> tuple:
    cols = ['Name', 'Club', 'Position', 'Price', 'Minutes Played', 'BPS', 
            'Selected By (%)', 'Form', 'Value', 'PPG', 'Total Points']
    
    df = (
        player_database[cols]
        .sort_values(by='Total Points', ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )

    # Define col_defs for AgGrid
    col_defs = [
        {"headerName": "Name", "field": "Name", "flex": 2, "minWidth": 100, "pinned": "left", "cellStyle": {"font-weight": "bold", "text-transform": "uppercase"}},
        {"headerName": "Club", "field": "Club", "flex": 1, "minWidth": 100},
        {"headerName": "Position", "field": "Position", "flex": 1, "minWidth": 90},
        {"headerName": "Price", "field": "Price", "flex": 1, "minWidth": 70},
        {"headerName": "Points", "field": "Total Points", "flex": 1, "minWidth": 70, "cellStyle": {"font-weight": "bold"}},
        {"headerName": "SBP", "field": "Selected By (%)", "flex": 1, "minWidth": 70},
        {"headerName": "MP", "field": "Minutes Played", "flex": 1, "minWidth": 70},    
        {"headerName": "Form", "field": "Form", "flex": 1, "minWidth": 70},
        {"headerName": "PPG", "field": "PPG", "flex": 1, "minWidth": 70},
        {"headerName": "Value", "field": "Value", "flex": 1, "minWidth": 70},
        {"headerName": "BPS", "field": "BPS", "flex": 1, "minWidth": 70},
    ]
    
    return df, col_defs

def return_top_players_form(player_database: pd.DataFrame, top_n: int = 10) -> tuple:
    player_database = player_database.copy()
    player_database['Form'] = pd.to_numeric(player_database['Form'], errors='coerce')
    
    cols = ['Name', 'Club', 'Position', 'Price', 'Minutes Played', 'BPS', 
            'Selected By (%)', 'Form', 'Value', 'PPG', 'Total Points']
    df = (
        player_database[cols]
        .sort_values(by='Form', ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )

    # Define col_defs for AgGrid
    col_defs = [
        {"headerName": "Name", "field": "Name", "flex": 2, "minWidth": 100, "pinned": "left", "cellStyle": {"font-weight": "bold", "text-transform": "uppercase"}},
        {"headerName": "Club", "field": "Club", "flex": 1, "minWidth": 100},
        {"headerName": "Position", "field": "Position", "flex": 1, "minWidth": 90},
        {"headerName": "Form", "field": "Form", "flex": 1, "minWidth": 70, "cellStyle": { "font-weight": "bold"}},
        {"headerName": "Price", "field": "Price", "flex": 1, "minWidth": 70},
        {"headerName": "Points", "field": "Total Points", "flex": 1, "minWidth": 70},
        {"headerName": "SBP", "field": "Selected By (%)", "flex": 1, "minWidth": 70},
        {"headerName": "MP", "field": "Minutes Played", "flex": 1, "minWidth": 70},    
        {"headerName": "PPG", "field": "PPG", "flex": 1, "minWidth": 70},
        {"headerName": "Value", "field": "Value", "flex": 1, "minWidth": 70},
        {"headerName": "BPS", "field": "BPS", "flex": 1, "minWidth": 70},
    ]
    
    return df, col_defs

def return_top_players_value(player_database: pd.DataFrame, top_n: int = 10) -> tuple:
    cols = ['Name', 'Club', 'Position', 'Price', 'Minutes Played', 'BPS', 
            'Selected By (%)', 'Form', 'Value', 'PPG', 'Total Points']
    
    df = (
        player_database[cols]
        .sort_values(by='Value', ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )

    # Define col_defs for AgGrid
    col_defs = [
        {"headerName": "Name", "field": "Name", "flex": 2, "minWidth": 100, "pinned": "left", "cellStyle": {"font-weight": "bold", "text-transform": "uppercase"}},
        {"headerName": "Club", "field": "Club", "flex": 1, "minWidth": 100},
        {"headerName": "Position", "field": "Position", "flex": 1, "minWidth": 90},
        {"headerName": "Value", "field": "Value", "flex": 1, "minWidth": 70, "cellStyle": { "font-weight": "bold"}},
        {"headerName": "Price", "field": "Price", "flex": 1, "minWidth": 70},
        {"headerName": "Points", "field": "Total Points", "flex": 1, "minWidth": 70},
        {"headerName": "Form", "field": "Form", "flex": 1, "minWidth": 70},
        {"headerName": "SBP", "field": "Selected By (%)", "flex": 1, "minWidth": 70},
        {"headerName": "MP", "field": "Minutes Played", "flex": 1, "minWidth": 70},    
        {"headerName": "PPG", "field": "PPG", "flex": 1, "minWidth": 70},
        {"headerName": "BPS", "field": "BPS", "flex": 1, "minWidth": 70},
    ]
    
    return df, col_defs

def return_top_goalkeepers(player_database: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """
    Return the top goalkeepers based on total points.

    Args:
        player_database (pd.DataFrame): DataFrame containing player data.
        top_n (int, optional): Number of top goalkeepers to return. Defaults to 10.

    Returns:
        pd.DataFrame: DataFrame of the top goalkeepers sorted by total points.
    """
    cols = ['Name', 'Club', 'Price', 'Starts', 'Selected By (%)', 
            'Form', 'Value', 'Clean Sheets', 'Goals Conceded', 
            'Saves', 'BPS', 'Total Points']
    
    df = (
        player_database[player_database['Position'] == 'Goalkeeper'][cols]
        .sort_values(by='Total Points', ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )

    col_defs = [
        {"headerName": "Name", "field": "Name", "flex": 2, "minWidth": 100, "pinned": "left", "cellStyle": {"font-weight": "bold", "text-transform": "uppercase"}},
        {"headerName": "Club", "field": "Club", "flex": 1, "minWidth": 100},
        {"headerName": "Price", "field": "Price", "flex": 1, "minWidth": 70},
        {"headerName": "Points", "field": "Total Points", "flex": 1, "minWidth": 70, "cellStyle": { "font-weight": "bold"}},
        {"headerName": "CS", "field": "Clean Sheets", "flex": 1, "minWidth": 50, "maxWidth": 90},
        {"headerName": "Saves", "field": "Saves", "flex": 1, "minWidth": 70},
        {"headerName": "GC", "field": "Goals Conceded", "flex": 1, "minWidth": 70},
        {"headerName": "SBP", "field": "Selected By (%)", "flex": 1, "minWidth": 70},
        {"headerName": "Starts", "field": "Starts", "flex": 1, "minWidth": 70},    
        {"headerName": "Form", "field": "Form", "flex": 1, "minWidth": 70},
        {"headerName": "Value", "field": "Value", "flex": 1, "minWidth": 70},
        {"headerName": "BPS", "field": "BPS", "flex": 1, "minWidth": 70},
    ]
    
    return df, col_defs

def return_top_defenders(player_database: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """
    Return the top defenders based on total points.

    Args:
        player_database (pd.DataFrame): DataFrame containing player data.
        top_n (int, optional): Number of top defenders to return. Defaults to 10.

    Returns:
        pd.DataFrame: DataFrame of the top defenders sorted by total points.
    """
    cols = ['Name', 'Club', 'Price', 'Starts', 'Selected By (%)', 
            'Form', 'Value', 'Clean Sheets', 'Goals Conceded', 
            'Defensive Contributions', 'ICT Index', 'ICT Index Rank Type', 
            'Assists', 'Goals Scored', 'Total Points', 'BPS']
    
    df =  (
        player_database[player_database['Position'] == 'Defender'][cols]
        .sort_values(by='Total Points', ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )

    col_defs = [
        {"headerName": "Name", "field": "Name", "flex": 2, "minWidth": 100, "pinned": "left", "cellStyle": {"font-weight": "bold", "text-transform": "uppercase"}},
        {"headerName": "Club", "field": "Club", "flex": 1, "minWidth": 100},
        {"headerName": "Price", "field": "Price", "flex": 1, "minWidth": 70},
        {"headerName": "Points", "field": "Total Points", "flex": 1, "minWidth": 70, "cellStyle": { "font-weight": "bold"}},
        {"headerName": "Starts", "field": "Starts", "flex": 1, "minWidth": 70},
        {"headerName": "CS", "field": "Clean Sheets", "flex": 1, "minWidth": 50, "maxWidth": 90},
        {"headerName": "GC", "field": "Goals Conceded", "flex": 1, "minWidth": 70},
        {"headerName": "DC", "field": "Defensive Contributions", "flex": 1, "minWidth": 70},
        {"headerName": "SBP", "field": "Selected By (%)", "flex": 1, "minWidth": 70},
        {"headerName": "ICT", "field": "ICT Index", "flex": 1, "minWidth": 70},
        {"headerName": "ICT Rank", "field": "ICT Index Rank Type", "flex": 1, "minWidth": 70},
        {"headerName": "Assists", "field": "Assists", "flex": 1, "minWidth": 70},
        {"headerName": "Goals", "field": "Goals Scored", "flex": 1, "minWidth": 70},
        {"headerName": "Form", "field": "Form", "flex": 1, "minWidth": 70},
        {"headerName": "Value", "field": "Value", "flex": 1, "minWidth": 70},
        {"headerName": "BPS", "field": "BPS", "flex": 1, "minWidth": 70},    
    ]
    
    return df, col_defs


def return_top_midfielders(player_database: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """
    Return the top midfielders based on total points.

    Args:
        player_database (pd.DataFrame): DataFrame containing player data.
        top_n (int, optional): Number of top midfielders to return. Defaults to 10.

    Returns:
        pd.DataFrame: DataFrame of the top midfielders sorted by total points.
    """
    cols = ['Name', 'Club', 'Price', 'Starts', 'Selected By (%)', 
            'Form', 'Value', 'Defensive Contributions', 
            'Expected Goal Involvements', 'ICT Index', 'BPS',
            'ICT Index Rank Type', 'Assists', 'Goals Scored', 'Total Points']
    
    df =  (
        player_database[player_database['Position'] == 'Midfielder'][cols]
        .sort_values(by='Total Points', ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )

    col_defs = [
        {"headerName": "Name", "field": "Name", "flex": 2, "minWidth": 100, "pinned": "left", "cellStyle": {"font-weight": "bold", "text-transform": "uppercase"}},
        {"headerName": "Club", "field": "Club", "flex": 1, "minWidth": 100},
        {"headerName": "Price", "field": "Price", "flex": 1, "minWidth": 70},
        {"headerName": "Points", "field": "Total Points", "flex": 1, "minWidth": 70, "cellStyle": { "font-weight": "bold"}},
        {"headerName": "Starts", "field": "Starts", "flex": 1, "minWidth": 70},
        {"headerName": "xGI", "field": "Expected Goal Involvements", "flex": 1, "minWidth": 70},
        {"headerName": "DC", "field": "Defensive Contributions", "flex": 1, "minWidth": 70},
        {"headerName": "SBP", "field": "Selected By (%)", "flex": 1, "minWidth": 70},
        {"headerName": "ICT", "field": "ICT Index", "flex": 1, "minWidth": 70},
        {"headerName": "ICT Rank", "field": "ICT Index Rank Type", "flex": 1, "minWidth": 70},
        {"headerName": "Assists", "field": "Assists", "flex": 1, "minWidth": 70},
        {"headerName": "Goals", "field": "Goals Scored", "flex": 1, "minWidth": 70},
        {"headerName": "Form", "field": "Form", "flex": 1, "minWidth": 70},
        {"headerName": "Value", "field": "Value", "flex": 1, "minWidth": 70},
        {"headerName": "BPS", "field": "BPS", "flex": 1, "minWidth": 70},    
    ]
    
    return df, col_defs

def return_top_forwards(player_database: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """
    Return the top forwards based on total points.

    Args:
        player_database (pd.DataFrame): DataFrame containing player data.
        top_n (int, optional): Number of top forwards to return. Defaults to 10.

    Returns:
        pd.DataFrame: DataFrame of the top forwards sorted by total points.
    """
    cols = ['Name', 'Club', 'Price', 'Starts', 'Selected By (%)', 
            'Form', 'Value', 'Expected Goal Involvements', 
            'ICT Index', 'ICT Index Rank Type', 'Assists', 
            'Expected Goals', 'Goals Scored', 'Total Points', 'BPS']
    
    df =  (
        player_database[player_database['Position'] == 'Forward'][cols]
        .sort_values(by='Total Points', ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )

    col_defs = [
        {"headerName": "Name", "field": "Name", "flex": 2, "minWidth": 100, "pinned": "left", "cellStyle": {"font-weight": "bold", "text-transform": "uppercase"}},
        {"headerName": "Club", "field": "Club", "flex": 1, "minWidth": 100},
        {"headerName": "Price", "field": "Price", "flex": 1, "minWidth": 70},
        {"headerName": "Points", "field": "Total Points", "flex": 1, "minWidth": 70, "cellStyle": { "font-weight": "bold"}},
        {"headerName": "Starts", "field": "Starts", "flex": 1, "minWidth": 70},
        {"headerName": "xGI", "field": "Expected Goal Involvements", "flex": 1, "minWidth": 70},
        {"headerName": "Assists", "field": "Assists", "flex": 1, "minWidth": 70},
        {"headerName": "Goals", "field": "Goals Scored", "flex": 1, "minWidth": 70},
        {"headerName": "xG", "field": "Expected Goals", "flex": 1, "minWidth": 70},
        {"headerName": "SBP", "field": "Selected By (%)", "flex": 1, "minWidth": 70},
        {"headerName": "ICT", "field": "ICT Index", "flex": 1, "minWidth": 70},
        {"headerName": "ICT Rank", "field": "ICT Index Rank Type", "flex": 1, "minWidth": 70},
        {"headerName": "Form", "field": "Form", "flex": 1, "minWidth": 70},
        {"headerName": "Value", "field": "Value", "flex": 1, "minWidth": 70},
        {"headerName": "BPS", "field": "BPS", "flex": 1, "minWidth": 70},    
    ]
    
    return df, col_defs

def get_top_stats_for_player_cards(player_df):
    df = player_df.copy()
    cols_to_numeric = ['Total Points', 'Selected By (%)', 'Goals Scored', 'Assists', 'ICT Index', 'Clean Sheets', 'Form', 'Value', 'Defensive Contributions', 'Expected Goal Involvements', 'Saves', 'BPS']
    df[cols_to_numeric] = df[cols_to_numeric].apply(pd.to_numeric, errors='coerce')
    df = df.rename(columns={'Selected By (%)': 'Selected (%)', 'Expected Goal Involvements': 'xGI'})
    most_points = df.nlargest(1, 'Total Points', keep='first') 
    most_goals = df.nlargest(1, 'Goals Scored', keep='first') 
    most_assists = df.nlargest(1, 'Assists', keep='first') 
    top_ict = df.nlargest(1, 'ICT Index', keep='first') 
    most_cleansheets = df.nlargest(1, 'Clean Sheets', keep='first') 
    most_defensive_contributions = df.nlargest(1, 'Defensive Contributions', keep='first')
    most_selected = df.nlargest(1, 'Selected (%)', keep='first') 
    top_form = df.nlargest(1, 'Form', keep='first') 
    top_value = df.nlargest(1, 'Value', keep='first') 
    top_xGI = df.nlargest(1, 'xGI', keep='first') 
    most_saves = df.nlargest(1, 'Saves', keep='first') 
    most_bps = df.nlargest(1, 'BPS', keep='first') 
    return { 
            'Total Points' : most_points,
            'Selected (%)' : most_selected,
            'Clean Sheets' : most_cleansheets, 
            'Goals Scored' : most_goals, 
            'Assists' : most_assists,
            'BPS' : most_bps,
            'Saves' : most_saves,      
            'Defensive Contributions' : most_defensive_contributions,
            'xGI' : top_xGI,
            'ICT Index' : top_ict, 
            'Form' : top_form,
            'Value' : top_value,
            }
