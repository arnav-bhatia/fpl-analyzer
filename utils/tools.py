import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

def build_aggrid_table(
    df, 
    col_defs=None, 
    pagination=False, 
    max_height=1000, 
    alt_row_colours=True, 
    FDR=False,
    pl_table=False
):
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_pagination(enabled=pagination)
    gb.configure_default_column(resizable=True, filter=False, sortable=True)

    grid_options = gb.build()

    if col_defs:
        grid_options["columnDefs"] = col_defs
    else:
        grid_options["autoSizeStrategy"] = {"type": "fitCellContents"}

    # Default alternating colors
    if alt_row_colours and not (FDR):
        row_style = JsCode("""
            function(params) {
                if (params.node.rowIndex % 2 === 0) {
                    return {'background-color': '#1E1E28', 'color': '#F5F7FA'};
                } else {
                    return {'background-color': '#232334', 'color': '#F5F7FA'};
                }
            }
        """)
        grid_options["getRowStyle"] = row_style

    # FDR coloring
    elif FDR:
        row_style = JsCode(f"""
            function(params) {{
                var raw = params.data["Fixture Difficulty Rating"];
                var m = String(raw).match(/\\d+/);
                if (!m) return null;
                var fdr = parseInt(m[0], 10);

                var bg = null, color = null;
                if (fdr === 1) {{ bg = '#364725'; color = 'white'; }}       // dark green
                else if (fdr === 2) {{ bg = '#07f978'; color = 'black'; }}  // light green
                else if (fdr === 3) {{ bg = '#DDDDDD'; color = 'black'; }}  // grey
                else if (fdr === 4) {{ bg = '#f91952'; color = 'white'; }}  // light red
                else if (fdr === 5) {{ bg = '#800a30'; color = 'white'; }}  // dark red

                if (bg) return {{ 'background-color': bg, 'color': color }};
                return null;
            }}
        """)
        grid_options["getRowStyle"] = row_style

    elif pl_table:
        row_style = JsCode(f"""
            function(params) {{
                var pos = parseInt(params.data["Position"], 10);
                if (isNaN(pos)) return {{
                    'background-color': '#41054b',
                    'color': 'white'
                }};

                // default values
                var baseBg = '#41054b';
                var textColor = 'white';
                var borderColor = baseBg;

                if (pos === 1) {{
                    borderColor = '#ffbf00';    // Champions
                }} else if (pos >= 2 && pos <= 5) {{
                    borderColor = '#3bb552';    // CL spots
                }} else if (pos === 6) {{
                    borderColor = '#288eea';    // Europa League
                }} else if (pos === 7) {{
                    borderColor = '#0ad8d8';    // Conference League
                }} else if (pos >= 18 && pos <= 20) {{
                    borderColor = 'red';        // Relegation
                }}

                return {{
                    'background-color': baseBg,
                    'color': textColor,
                    'border-left': '6px solid ' + borderColor
                }};
            }}
        """)
        grid_options["getRowStyle"] = row_style


    custom_css = {
        ".ag-header-cell": {
            "background-color": "#2A2A3A !important",
            "color": "white !important",
            "font-weight": "bold !important",
            "text-align": "center",
            "border": "1px solid #FF2DD1"
        }
    }

    return AgGrid(
        df,
        gridOptions=grid_options,
        height=min(max_height, (1 + len(df.index)) * 31),
        allow_unsafe_jscode=True,
        custom_css=custom_css
    )
    
def render_player_card(player_row, stat_label, stat_value):
    """
    Render a single player card with a modern and clean design.
    """
    player_name = player_row["Name"]
    code = player_row["photo_code"]
    team = player_row["Club"]
    photo_url = f"https://resources.premierleague.com/premierleague25/photos/players/110x140/{code}.png"

    st.markdown(
        f"""
        <div style="
            font-family: 'Segoe UI', Roboto, sans-serif;
            background: #2A2A3A;
            padding: 10px;
            border-radius: 15px;
            text-align: center;
            border: 1px solid #FF2DD1;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            margin-top: 5px;
            margin-bottom: 15px;
        ">
            <img src="{photo_url}" style="
                width: 100px;
                height: 100px;
                border-radius: 50%;
                border: 3px solid #FF2DD1;
                margin-bottom: 2px;
                object-fit: cover;
                object-position: 0 -5%;
                background-color: white;
            "><br>
            <strong style="
                font-size: 1em;
                font-weight: 600;
                color: white;
                display: block;
                margin-bottom: 0;
            ">{player_name}</strong>
            <p style="
                font-size: 0.9em;
                font-weight: 400;
                color: white;
                display: block;
                margin-bottom: 0;
            ">{team}</p>
            <span style="font-size: 0.9em; color: white;">
                {stat_label}: 
                <span style="color: #FF2DD1; font-weight: 700;">{stat_value}</span>
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )
    
def render_title_with_bg(title_text, margin_top=0):
    """
    Renders a centered title with a light background and rounded corners.
    """
    st.markdown(
        f"""
        <div style="
            padding: 1px;
            background-color: #2A2A3A;
            border-radius: 10px; 
            text-align: center; 
            margin-bottom: 10px;
            margin-top: {margin_top}px;
            border: 1px solid #FF2DD1;
        ">
            <h2 style="
                font-family: 'Segoe UI', Roboto, sans-serif; 
                font-weight: 700;
                font-size: 24px;
                margin: 0;
                color: white;
            ">{title_text}</h2>
        </div>
        """,
        unsafe_allow_html=True
    )
    
def render_subheaders(title_text, font_size=16, margin_top=1, margin_bottom=1):
    """
    Renders a centered title with a light background and rounded corners.
    """
    st.markdown(
        f"""
        <div style="
            padding: 8px;
            background-color: #2A2A3A;
            border-radius: 10px; 
            text-align: center; 
            margin-bottom: {margin_bottom}px;
            margin-top: {margin_top}px;
            border: 1px solid #FF2DD1;
        ">
            <p style="
                font-family: 'Segoe UI', Roboto, sans-serif; 
                font-size: {font_size}px;
                margin: 0;
                color: white;
            ">{title_text}</h2>
        </div>
        """,
        unsafe_allow_html=True
    )
    
def render_divider():
    """Renders a thin, gray horizontal line with no vertical margins."""
    st.markdown(
        """<hr style="height:1px; margin:0; border:none; background-color:#FF2DD1;" />""",
        unsafe_allow_html=True
    )
    
def calc_delta_colour(rank, type):
    if type == "fdr":
        if rank < 7:
            return "normal"
        elif rank < 15:  
            return "off"
        else:
            return "inverse"
    else:
        if rank < 10:
            return "normal"
        elif rank < 50:  
            return "off"
        else:
            return "inverse"
        
def map_fdr_colour(fdr):
    if fdr == 2:
        return "fdr-two"
    elif fdr == 3:
        return "fdr-three"
    elif fdr == 4:
        return "fdr-four"
    elif fdr == 5:
        return "fdr-five"

