"""
app.py
------
VoiceScope — Customer Intelligence, Distilled.

Main Streamlit application. Loads the pre-analyzed reviews CSV and presents insights through an interactive UI:
fading preview table, category + rating charts, and CSV / PNG download options.

Run with:
    streamlit run app.py
"""

import time
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG — must be the very first Streamlit call
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title            = "VoiceScope",
    page_icon             = "🔍",
    layout                = "centered",
    initial_sidebar_state = "collapsed",
)


# ─────────────────────────────────────────────────────────────────────────────
# DATA
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data
def load_data() -> pd.DataFrame:
    """
    Load the pre-analyzed reviews CSV.
    Sorted newest-first so the preview table shows recent entries.
    """
    df = pd.read_csv("data/reviews.csv", parse_dates=["date"])
    df = df.sort_values("date", ascending=False).reset_index(drop=True)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────
def inject_css() -> None:
    """
    Inject custom CSS to match the portfolio design system.
    Loads Syne (headings) and DM Sans (body) from Google Fonts.
    All CSS variables mirror the portfolio's :root definitions.
    """
    st.markdown(
        """
        <style>
        /* ── Google Fonts ───────────────────────────────────────────── */
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;1,9..40,300&display=swap');

        /* ── Base ───────────────────────────────────────────────────── */
        .stApp {
            background-color: #F7F5F2;
            font-family: 'DM Sans', sans-serif;
            color: #1C1C1C;
        }

        /* Hide default Streamlit chrome */
        #MainMenu, footer, header { visibility: hidden; }

        /* Main content padding */
        .block-container {
            padding-top: 4rem    !important;
            padding-bottom: 4rem !important;
            max-width: 860px     !important;
        }

        /* ── Hero text ──────────────────────────────────────────────── */
        .vs-title {
            text-align: center;
            font-family: 'Syne', sans-serif;
            font-size: 3rem !important;
            font-weight: 800;
            color: #1C1C1C;
            margin: 0;
            letter-spacing: -1.5px;
            line-height: 1.1;
        }
        .vs-title span { color: #C4622D; }

        .vs-subtitle {
            text-align: center;
            font-family: 'DM Sans', sans-serif;
            font-size: 1rem;
            color: #6B6864;
            margin-top: 0.5rem;
            margin-bottom: 2.5rem;
            letter-spacing: 0.02em;
        }

        /* ── Meta badge ─────────────────────────────────────────────── */
        .vs-meta-wrap { text-align: center; margin-bottom: 2rem; }
        .vs-meta {
            display: inline-block;
            font-family: 'DM Sans', sans-serif;
            font-size: 0.82rem;
            color: #6B6864;
            background: #EFEDE9;
            border: 1px solid #E5E2DD;
            border-radius: 4px;
            padding: 0.45rem 1.1rem;
        }

        /* ── Divider ────────────────────────────────────────────────── */
        hr.vs-divider {
            border: none;
            border-top: 1px solid #E5E2DD;
            margin: 2.5rem 0;
        }

        /* ── Section labels ─────────────────────────────────────────── */
        .vs-section {
            font-family: 'Syne', sans-serif;
            font-size: 1.05rem;
            font-weight: 700;
            color: #1C1C1C;
            text-align: center;
            margin-bottom: 0.4rem;
        }
        .vs-caption {
            font-family: 'DM Sans', sans-serif;
            font-size: 0.8rem;
            color: #6B6864;
            text-align: center;
            margin-bottom: 0.9rem;
        }

        /* ── Fading preview table ───────────────────────────────────── */
        .table-wrap {
            position: relative;
            max-height: 265px;
            overflow: hidden;
            border-radius: 8px;
            border: 1px solid #E5E2DD;
            background: #FFFFFF;
            margin-bottom: 0.5rem;
        }
        .table-fade {
            position: absolute;
            bottom: 0; left: 0; right: 0;
            height: 110px;
            /* Fades text AND borders toward the background color */
            background: linear-gradient(rgba(247,245,242,0), #F7F5F2 90%);
            pointer-events: none;
        }
        table.vs-table {
            width: 100%;
            border-collapse: collapse;
            font-family: 'DM Sans', sans-serif;
            font-size: 0.88rem;
        }
        table.vs-table th {
            background: #EFEDE9;
            padding: 0.7rem 1.1rem;
            text-align: left;
            font-weight: 500;
            color: #6B6864;
            border-bottom: 1px solid #E5E2DD;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.07em;
        }
        table.vs-table td {
            padding: 0.7rem 1.1rem;
            border-bottom: 1px solid #E5E2DD;
            color: #1C1C1C;
            vertical-align: middle;
        }
        table.vs-table tr:last-child td { border-bottom: none; }

        /* Sentiment color classes */
        .pos { color: #2A7A47; font-weight: 500; }
        .neu { color: #6B6864; font-weight: 500; }
        .neg { color: #C4622D; font-weight: 500; }

        /* ── Buttons ────────────────────────────────────────────────── */
        /* Primary — Analyze */
        .stButton > button {
            background-color: #C4622D !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 4px !important;
            font-family: 'DM Sans', sans-serif !important;
            font-weight: 500 !important;
            font-size: 0.95rem !important;
            padding: 0.65rem 2rem !important;
            transition: background-color 0.3s ease !important;
            width: 100% !important;
            white-space: nowrap !important;
            letter-spacing: 0.01em !important;
        }
        .stButton > button:hover {
            background-color: #A34E22 !important;
            color: #FFFFFF !important;
        }

        /* Outlined — Downloads — fill column and center */
        .stDownloadButton {
            text-align: center !important;
        }
        .stDownloadButton > button {
            margin: 0 auto !important;
            background-color: transparent !important;
            color: #C4622D !important;
            border: 1.5px solid #C4622D !important;
            border-radius: 4px !important;
            font-family: 'DM Sans', sans-serif !important;
            font-weight: 500 !important;
            font-size: 0.88rem !important;
            width: 100% !important;
            transition: all 0.3s ease !important;
        }
        .stDownloadButton > button:hover {
            background-color: #C4622D !important;
            color: #FFFFFF !important;
        }

        /* ── Download row — centered flex ───────────────────────── */
        .vs-dl-row {
            display: flex;
            justify-content: center;
            gap: 1rem;
            margin-top: 0.5rem;
        }
        .vs-dl-btn {
            display: inline-block;
            width: 200px;
            text-align: center;
            background-color: transparent;
            color: #C4622D !important;
            border: 1.5px solid #C4622D;
            border-radius: 4px;
            font-family: 'DM Sans', sans-serif;
            font-weight: 500;
            font-size: 0.88rem;
            padding: 0.6rem 1.6rem;
            text-decoration: none !important;
            transition: all 0.3s ease;
            white-space: nowrap;
        }
        .vs-reset-btn {
            background-color: #C4622D;
            color: #FFFFFF;
            border: none;
            border-radius: 4px;
            font-family: 'DM Sans', sans-serif;
            font-weight: 500;
            font-size: 0.95rem;
            padding: 0.65rem 2.5rem;
            cursor: pointer;
            transition: background-color 0.3s ease;
            white-space: nowrap;
        }
        .vs-reset-btn:hover { background-color: #A34E22; }



        .vs-dl-btn:hover {
            background-color: #C4622D;
            color: #FFFFFF !important;
        }
        .vs-dl-note {
            font-family: 'DM Sans', sans-serif;
            font-size: 0.8rem;
            color: #6B6864;
            align-self: center;
        }

        /* ── Spinner text ───────────────────────────────────────────── */
        .stSpinner > div {
            font-family: 'DM Sans', sans-serif !important;
            color: #6B6864 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
STAR_MAP = {5: "★★★★★", 4: "★★★★☆", 3: "★★★☆☆", 2: "★★☆☆☆", 1: "★☆☆☆☆"}
SENTIMENT_CLASS = {"Positive": "pos", "Neutral": "neu", "Negative": "neg"}

# Chart palette — harmonized with portfolio accent
CHART_COLORS = {
    "category": [
        "#C4622D",   # primary accent (top bar)
        "#D4845A",
        "#E3A888",
        "#EFCDB5",
        "#B89A8A",
        "#8C7068",
        "#6B6864",
    ],
    "rating": {
        1: "#8B2000",
        2: "#C4622D",
        3: "#D4956A",
        4: "#5B9E6E",
        5: "#2A7A47",
    },
}

PLOTLY_LAYOUT_DEFAULTS = dict(
    paper_bgcolor = "#F7F5F2",
    plot_bgcolor  = "#F7F5F2",
    font          = dict(family="DM Sans", color="#1C1C1C"),
    margin        = dict(l=16, r=16, t=52, b=20),
    showlegend    = False,
)


def build_preview_html(df: pd.DataFrame) -> str:
    """
    Return the HTML for the fading 5-row preview table.
    The gradient overlay creates the fade effect on both text and borders.
    """
    rows = ""
    for _, row in df.head(5).iterrows():
        date_str = (
            row["date"].strftime("%b %d, %Y")
            if hasattr(row["date"], "strftime")
            else str(row["date"])[:10]
        )
        sentiment_class = SENTIMENT_CLASS.get(row["sentiment"], "neu")
        stars           = STAR_MAP.get(int(row["rating"]), str(row["rating"]))

        rows += f"""
        <tr>
            <td>{date_str}</td>
            <td>{stars}</td>
            <td>{row['category']}</td>
            <td><span class="{sentiment_class}">{row['sentiment']}</span></td>
        </tr>"""

    return f"""
    <div class="table-wrap">
        <table class="vs-table">
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Rating</th>
                    <th>Category</th>
                    <th>Sentiment</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
        <div class="table-fade"></div>
    </div>
    """


def build_category_chart(df: pd.DataFrame) -> go.Figure:
    """
    Horizontal stacked bar chart - per category - broken down by sentiment.
    Each bar shows Positive / Neutral / Negative counts so CS teams can immediately see not just volume but the
    emotional split per topic.
    """
    SENTIMENT_COLORS = {
        "Positive": "#2A7A47",
        "Neutral":  "#D4956A",
        "Negative": "#8B2000",
    }

    # Order categories by total review count descending (largest at top)
    cat_order = (
        df["category"].value_counts().sort_values(ascending=True).index.tolist()
    )

    fig = go.Figure()

    for sentiment in ["Negative", "Neutral", "Positive"]:   # stack order: neg at base
        subset = df[df["sentiment"] == sentiment]
        counts = subset["category"].value_counts()
        values = [counts.get(cat, 0) for cat in cat_order]

        fig.add_trace(
            go.Bar(
                name             = sentiment,
                x                = values,
                y                = cat_order,
                orientation      = "h",
                marker_color     = SENTIMENT_COLORS[sentiment],
                text             = [v if v > 0 else "" for v in values],
                textposition     = "inside",
                insidetextanchor = "middle",
                textfont         = dict(family="DM Sans", size=11, color="#FFFFFF"),
                hovertemplate    = f"<b>%{{y}}</b><br>{sentiment}: %{{x}}<extra></extra>",
            )
        )

    fig.update_layout(
        paper_bgcolor = "#F7F5F2",
        plot_bgcolor  = "#F7F5F2",
        font          = dict(family="DM Sans", color="#1C1C1C"),
        showlegend    = True,
        barmode       = "stack",
        title         = dict(
            text = "Category Breakdown by Sentiment",
            font = dict(family="Syne", size=15, color="#1C1C1C"),
            x    = 0.5,
        ),
        height = 380,
        legend = dict(
            orientation = "h",
            x           = 0.5,
            xanchor     = "center",
            y           = -0.12,
            font        = dict(family="DM Sans", size=11),
        ),
        xaxis  = dict(showgrid=False, showticklabels=False, zeroline=False),
        yaxis  = dict(
            tickfont   = dict(family="DM Sans", size=11, color="#1C1C1C"),
            automargin = True,
        ),
        margin = dict(l=8, r=40, t=52, b=20),
    )
    return fig


def build_rating_chart(df: pd.DataFrame) -> go.Figure:
    """Vertical bar chart — review count per star rating (1–5)."""
    counts = df["rating"].value_counts().sort_index()
    colors = [CHART_COLORS["rating"].get(r, "#C4622D") for r in counts.index]

    fig = go.Figure(
        go.Bar(
            x            = counts.index,
            y            = counts.values,
            marker_color = colors,
            text         = counts.values,
            textposition = "outside",
            textfont     = dict(family="DM Sans", size=12, color="#6B6864"),
            hovertemplate= "<b>%{x} ★</b><br>%{y} reviews<extra></extra>",
        )
    )
    fig.update_layout(
        **PLOTLY_LAYOUT_DEFAULTS,
        title  = dict(
            text = "Rating Distribution",
            font = dict(family="Syne", size=15, color="#1C1C1C"),
            x    = 0.5,
        ),
        height = 360,
        xaxis  = dict(
            tickmode = "array",
            tickvals = [1, 2, 3, 4, 5],
            ticktext = ["1 ★", "2 ★", "3 ★", "4 ★", "5 ★"],
            tickfont = dict(family="DM Sans", size=12),
        ),
        yaxis  = dict(showgrid=False, showticklabels=False, zeroline=False),
    )
    return fig


def export_png(fig_cat: go.Figure, fig_rat: go.Figure) -> bytes | None:
    """
    Attempt to export both charts as a single combined PNG.
    Returns None if kaleido is not installed - Plotly's built-in camera icon on each chart serves as the fallback.
    """
    try:
        import kaleido # noqa: F401 - Confirms kaleido is importable before pio call
        import plotly.io as pio
        from plotly.subplots import make_subplots

        fig = make_subplots(
            rows               = 1,
            cols               = 2,
            subplot_titles     = ("Category Breakdown by Sentiment", "Rating Distribution"),
            horizontal_spacing = 0.14,
        )
        for trace in fig_cat.data:
            fig.add_trace(trace, row=1, col=1)
        for trace in fig_rat.data:
            # Hide rating traces from legend — they'd show as "trace N"
            trace.showlegend = False
            fig.add_trace(trace, row=1, col=2)

        fig.update_layout(
            paper_bgcolor = "#F7F5F2",
            plot_bgcolor  = "#F7F5F2",
            font          = dict(family="DM Sans", color="#1C1C1C"),
            barmode       = "stack",
            height        = 500,
            width         = 1400,
            showlegend    = True,
            legend        = dict(
                orientation = "h",
                x=0.5, xanchor="center", y=-0.08,
                font=dict(family="DM Sans", size=11),
            ),
            margin        = dict(l=160, r=60, t=80, b=80),
        )
        return pio.to_image(fig, format="png", scale=2)
    except Exception as e:
        return str(e)   # return error string instead of None so UI can display it


# ─────────────────────────────────────────────────────────────────────────────
# APP
# ─────────────────────────────────────────────────────────────────────────────
def main() -> None:
    inject_css()

    # ── Session state ──────────────────────────────────────────────────
    if "analyzed" not in st.session_state:
        st.session_state.analyzed = False

    # ── Load data ──────────────────────────────────────────────────────
    df          = load_data()
    total       = len(df)
    latest_date = df["date"].max()
    date_str    = (
        latest_date.strftime("%B %d, %Y")
        if hasattr(latest_date, "strftime")
        else str(latest_date)[:10]
    )

    # ── Hero ───────────────────────────────────────────────────────────
    st.markdown('<p class="vs-title">Voice<span>Scope</span></p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="vs-subtitle">Customer Intelligence, Distilled.</p>',
        unsafe_allow_html=True,
    )

    # Meta badge - centered via columns
    _, col_meta, _ = st.columns([1, 2, 1])
    with col_meta:
        st.markdown(
            f'<div class="vs-meta-wrap">'
            f'<span class="vs-meta">'
            f'📅 Data last collected: {date_str}&nbsp;&nbsp;·&nbsp;&nbsp;'
            f'{total} reviews collected'
            f'</span></div>',
            unsafe_allow_html=True,
        )

    st.markdown('<hr class="vs-divider">', unsafe_allow_html=True)

    # ── Analyze button (pre-results) ────────────────────────────────────
    if not st.session_state.analyzed:
        st.markdown(
            '<p style="text-align:center;font-family:\'DM Sans\',sans-serif;'
            'color:#6B6864;font-size:0.93rem;margin-bottom:1.5rem;">'
            'Tap below to run sentiment and category analysis across all '
            f'{total} collected reviews.'
            '</p>',
            unsafe_allow_html=True,
        )
        _, col_btn, _ = st.columns([1.5, 1, 1.5])
        with col_btn:
            if st.button("Analyze Reviews →"):
                with st.spinner(f"Analyzing {total} reviews..."):
                    time.sleep(1.6)   # brief pause - feels intentional
                st.session_state.analyzed = True
                st.rerun()

    # ── Results ─────────────────────────────────────────────────────────
    if st.session_state.analyzed:

        # ── Preview table ──────────────────────────────────────────────
        st.markdown('<p class="vs-section">Preview</p>', unsafe_allow_html=True)
        st.markdown(
            f'<p class="vs-caption">Showing 5 of {total} analyzed reviews</p>',
            unsafe_allow_html=True,
        )
        st.markdown(build_preview_html(df), unsafe_allow_html=True)

        st.markdown('<hr class="vs-divider">', unsafe_allow_html=True)

        # ── Insights charts ────────────────────────────────────────────
        st.markdown('<p class="vs-section">Insights</p>', unsafe_allow_html=True)

        fig_cat = build_category_chart(df)
        fig_rat = build_rating_chart(df)

        col_chart_l, col_chart_r = st.columns(2)
        with col_chart_l:
            st.plotly_chart(
                fig_cat,
                use_container_width = True,
                config = {"displaylogo": False, "toImageButtonOptions": {"format": "png"}},
            )
        with col_chart_r:
            st.plotly_chart(
                fig_rat,
                use_container_width = True,
                config = {"displaylogo": False, "toImageButtonOptions": {"format": "png"}},
            )

        st.markdown('<hr class="vs-divider">', unsafe_allow_html=True)

        # ── Export ─────────────────────────────────────────────────────
        st.markdown('<p class="vs-section">Export</p>', unsafe_allow_html=True)
        st.markdown(
            '<p class="vs-caption">Download the full dataset or the chart visualisation.</p>',
            unsafe_allow_html=True,
        )

        csv_bytes = df.to_csv(index=False).encode("utf-8")
        png_bytes = export_png(fig_cat, fig_rat)

        # Encode CSV for inline HTML download link
        import base64
        csv_b64 = base64.b64encode(csv_bytes).decode()
        csv_filename = f"voicescope_intercom_{datetime.now().strftime('%Y%m%d')}.csv"

        if png_bytes:
            png_b64 = base64.b64encode(png_bytes).decode()
            png_filename = f"voicescope_charts_{datetime.now().strftime('%Y%m%d')}.png"
            png_btn = f'''<a href="data:image/png;base64,{png_b64}" download="{png_filename}" class="vs-dl-btn">⬇ &nbsp;Download Chart PNG</a>'''
        else:
            err = st.session_state.get('png_error', 'unknown error')
            png_btn = f'<span class="vs-dl-note">PNG export failed: {err}</span>'

        st.markdown(f'''
        <div class="vs-dl-row">
            <a href="data:text/csv;base64,{csv_b64}" download="{csv_filename}" class="vs-dl-btn">⬇ &nbsp;Download CSV</a>
            {png_btn}
        </div>''', unsafe_allow_html=True)

        st.markdown('<hr class="vs-divider">', unsafe_allow_html=True)

        # ── Reset ──────────────────────────────────────────────────────
        st.markdown('''
        <div style="display:flex;justify-content:center;margin-top:0.5rem;" id="reset-anchor"></div>
        ''', unsafe_allow_html=True)
        _, col_reset, _ = st.columns([2.5, 1, 2.5])
        with col_reset:
            if st.button("↺  Start Over"):
                st.session_state.analyzed = False
                st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()