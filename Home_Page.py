import logging
from dataclasses import dataclass
from typing import Any, Dict

import datetime
import pathlib
import pytz
import streamlit as st

import utils

st.set_page_config(page_title="FPL Analyzer", layout="wide", initial_sidebar_state="auto")

# Logger
logger = logging.getLogger("fpl_analyzer")
logger.setLevel(logging.INFO)


def load_css(file_path: pathlib.Path):
    """
    Load CSS relative to this file. Guards against FileNotFoundError and logs issues.
    """
    base_dir = pathlib.Path(__file__).parent
    css_file = file_path if file_path.is_absolute() else (base_dir / file_path)

    if not css_file.exists():
        st.warning(f"CSS file not found: {css_file}. Continuing without custom styles.")
        logger.warning("CSS not found: %s", css_file)
        return

    try:
        css_text = css_file.read_text(encoding="utf-8")
        st.markdown(f"<style>{css_text}</style>", unsafe_allow_html=True)
    except Exception:
        st.warning("Unable to load CSS. Continuing without custom styles.")
        logger.exception("Error loading CSS file: %s", css_file)


def normalize_manager_id(val: Any) -> str:
    """
    Normalise manager_id to a trimmed string.
    """
    if val is None:
        return ""
    return str(val).strip()


def is_valid_manager_id(mgr_id: str) -> bool:
    """
    Basic validation — FPL manager ids are numeric. Adjust if necessary.
    """
    return bool(mgr_id) and mgr_id.isdigit()


@dataclass
class FPLData:
    fetched_at: datetime.datetime
    manager_league_df: Any
    league_coldefs: Any
    manager_details_dict: Dict[str, Any]
    manager_gw_history: Any
    player_json: Dict[str, Any]
    current_gw: int
    pl_teams_dict: Dict[str, Any]
    pl_teams_list: Any
    position_dict: Dict[str, Any]
    status_dict: Dict[str, Any]
    player_df: Any
    fixtures_df: Any
    dreamteam_df: Any
    top_price_risers_df: Any
    top_price_fallers_df: Any
    fixture_col_defs: Any
    fixtures_database: Any
    fdr_database: Any
    fdr_avg_coldefs: Any
    team_fdr_rating_df: Any
    pl_table_df: Any
    pl_table_col_defs: Any
    dt_col_defs: Any
    pi_col_defs: Any
    pd_col_defs: Any


@st.cache_data(ttl=900, show_spinner=False)
def fetch_player_json():
    return utils.load_player_data()


@st.cache_data(ttl=900, show_spinner=False)
def fetch_fixtures_json():
    return utils.load_fixtures_data()


@st.cache_data(ttl=300, show_spinner=False)
def fetch_manager_details_and_league(manager_id: str):
    # returns (manager_league_df, league_coldefs, manager_details_dict)
    return utils.load_manager_details(manager_id=manager_id)


def assemble_all_data(manager_id: str) -> FPLData:
    """
    Compose cached fetchers and run transformations. Raises RuntimeError on failure.
    We show our own spinner here so the UI is responsive and informative.
    """
    try:
        with st.spinner("Loading FPL data — this may take a few seconds..."):
            fetched_at = datetime.datetime.now(tz=pytz.timezone("Asia/Kolkata"))

            manager_league_df, league_coldefs, manager_details_dict = fetch_manager_details_and_league(manager_id)
            manager_gw_history = utils.load_manager_gw_history(manager_id=manager_id)

            player_json = fetch_player_json()
            fixtures_json = fetch_fixtures_json()

            current_gw = utils.get_current_gameweek(player_json)
            pl_teams_dict, pl_teams_list = utils.get_pl_teams_dict_and_list(player_json)
            position_dict = utils.get_position_dict()
            status_dict = utils.get_status_dict()
            player_df = utils.return_player_df(player_json, pl_teams_dict, status_dict, position_dict)
            dreamteam_df, dt_col_defs = utils.get_dream_team(player_df)
            top_price_risers_df, pi_col_defs = utils.return_top_price_risers(player_df)
            top_price_fallers_df, pd_col_defs = utils.return_top_price_fallers(player_df)
            fixtures_df, fixture_col_defs = utils.return_fixtures_df(fixtures_json, pl_teams_dict, player_df)
            fixtures_database = utils.create_team_fixtures_database(fixtures_df, pl_teams_list)
            fdr_database, fdr_avg_coldefs = utils.create_team_fdr_database(fixtures_database)
            team_fdr_rating_df = utils.get_team_FDR_rating(fixtures_df, pl_teams_list)
            pl_table_df, pl_table_col_defs = utils.build_pl_table(pl_teams_list, fixtures_database, utils.get_team_fixtures)

            return FPLData(
                fetched_at=fetched_at,
                manager_league_df=manager_league_df,
                league_coldefs=league_coldefs,
                manager_details_dict=manager_details_dict,
                manager_gw_history=manager_gw_history,
                player_json=player_json,
                current_gw=current_gw,
                pl_teams_dict=pl_teams_dict,
                pl_teams_list=pl_teams_list,
                position_dict=position_dict,
                status_dict=status_dict,
                player_df=player_df,
                fixtures_df=fixtures_df,
                dreamteam_df=dreamteam_df,
                top_price_risers_df=top_price_risers_df,
                top_price_fallers_df=top_price_fallers_df,
                fixture_col_defs=fixture_col_defs,
                fixtures_database=fixtures_database,
                fdr_database=fdr_database,
                fdr_avg_coldefs=fdr_avg_coldefs,
                team_fdr_rating_df=team_fdr_rating_df,
                pl_table_df=pl_table_df,
                pl_table_col_defs=pl_table_col_defs,
                dt_col_defs=dt_col_defs,
                pi_col_defs=pi_col_defs,
                pd_col_defs=pd_col_defs,
            )
    except Exception as exc:
        logger.exception("Failed to assemble FPL data for manager_id=%s", manager_id)
        st.error("Unable to load FPL data. Please check your network connection or try again.")
        raise RuntimeError("Failed to assemble FPL data") from exc


css_path = pathlib.Path("assets/styles.css")
load_css(css_path)

st.title("FPL Analyzer - Home Page")

st.caption("Enter your FPL manager ID to load your dashboard")

if "manager_id" not in st.session_state:
    st.session_state.manager_id = ""

raw_input = st.text_input(
    label="",
    placeholder="Enter your FPL manager ID (e.g. 5252797)",
    help="Find your manager ID by visiting your FPL team page and looking at the URL 'entry/XXXXXX'.",
    label_visibility="collapsed",
    key="manager_id_input",
)

manager_id = normalize_manager_id(raw_input)

if manager_id and not is_valid_manager_id(manager_id):
    st.warning("Manager ID should be numeric. Please check and retry.")
    manager_id = "" 

with st.sidebar:
    st.caption("Data controls")
    if st.button("Refresh players & fixtures"):
        fetch_player_json.clear()
        fetch_fixtures_json.clear()
        st.rerun()

    if st.button("Clear all caches (full refresh)"):
        fetch_player_json.clear()
        fetch_fixtures_json.clear()
        fetch_manager_details_and_league.clear()
        st.session_state.pop("fpl_data", None)
        st.rerun()

    st.write("---")
    st.caption("Tip: use the refresh buttons if data seems stale.")

if manager_id:
    existing = st.session_state.get("fpl_data")
    same_manager = False
    if existing:
        try:
            same_manager = str(existing.manager_details_dict.get("id", "")).strip() == manager_id
        except Exception:
            same_manager = False

    if not existing or not same_manager:
        try:
            fpl_data = assemble_all_data(manager_id)
            st.session_state["fpl_data"] = fpl_data
        except RuntimeError:
            if "fpl_data" not in st.session_state:
                st.stop()
    else:
        fpl_data = existing

    if "fpl_data" in st.session_state:
        data: FPLData = st.session_state["fpl_data"]

        with st.sidebar:
            st.caption(f"Data last updated: {data.fetched_at.strftime('%b %d, %Y %I:%M %p %Z')}")

        st.subheader(f"Welcome, {data.manager_details_dict.get('First Name', '')} {data.manager_details_dict.get('Last Name', '')}!")
        utils.render_title_with_bg(f"{data.manager_details_dict.get('Team Name', 'My Team')} Summary")

        managersum1, managersum2 = st.columns([1.75, 1.25])
        with managersum1:
            utils.build_aggrid_table(data.manager_league_df, col_defs=data.league_coldefs)

        with managersum2:
            with st.container(key="fdr-metric"):
                try:
                    league_df = data.manager_league_df.set_index("Name", drop=True)
                except Exception:
                    league_df = data.manager_league_df

                st.metric(
                    "Total Points",
                    data.manager_details_dict.get("Total Points", ""),
                    delta=f"Average Points per GW: {round(data.manager_details_dict.get('Total Points', 0) / max(data.current_gw, 1), 2)}",
                    border=True,
                )

                try:
                    delta_overall = int(league_df.loc["Overall", "Percentile"])
                    delta_colour_overall = utils.calc_delta_colour(delta_overall, type="percentile")
                except Exception:
                    delta_overall = None
                    delta_colour_overall = None

                st.metric(
                    "Overall Rank",
                    data.manager_details_dict.get("Global Rank", ""),
                    delta=f"Percentile: {delta_overall if delta_overall is not None else 'N/A'}",
                    delta_color=delta_colour_overall,
                    border=True,
                )

                player_country = data.manager_details_dict.get("Country", "Country")
                try:
                    delta_country = int(league_df.loc[player_country, "Percentile"])
                    delta_colour_country = utils.calc_delta_colour(delta_country, type="percentile")
                    country_rank = league_df.loc[player_country, "Rank"]
                except Exception:
                    delta_country = None
                    delta_colour_country = None
                    country_rank = "N/A"

                st.metric(
                    f"{player_country} Rank",
                    country_rank,
                    delta=f"Percentile: {delta_country if delta_country is not None else 'N/A'}",
                    delta_color=delta_colour_country,
                    border=True,
                )
else:
    st.info("Enter your FPL manager ID to load your dashboard.")