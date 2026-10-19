import streamlit as st


def apply_navigation_styles():
    """Apply the navy-and-blue panel palette to the main Streamlit app."""
    st.markdown(
        """
        <style>
        :root {
            --dic-navy: #123653;
            --dic-blue: #1677B8;
            --dic-blue-dark: #10547F;
            --dic-ink: #183247;
            --dic-muted: #526B7D;
            --dic-line: #D4E1EB;
            --dic-canvas: #F2F6FA;
        }

        /* Pale blue page canvas with clean white content panels. */
        [data-testid="stAppViewContainer"] {
            background: var(--dic-canvas);
            color: var(--dic-ink);
        }
        [data-testid="stHeader"] {
            background: rgba(242, 246, 250, 0.94);
        }
        [data-testid="stMain"] h1,
        [data-testid="stMain"] h2,
        [data-testid="stMain"] h3 {
            color: var(--dic-navy);
            letter-spacing: -0.02em;
        }
        [data-testid="stMain"] p,
        [data-testid="stMain"] label,
        [data-testid="stMain"] [data-testid="stCaptionContainer"] {
            color: var(--dic-ink);
        }

        /* Navy sidebar echoes the dark information panel in the reference. */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #10324E 0%, #0C2941 100%);
            border-right: 1px solid #254B68;
        }
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
            color: #F2F7FB;
        }

        /* Sidebar navigation cards: visible outlines and a strong active state. */
        section[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] {
            display: flex;
            flex-direction: column;
            gap: 0.45rem;
        }
        section[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] > label,
        section[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] > div > label,
        section[data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"] {
            box-sizing: border-box;
            min-height: 2.75rem;
            margin: 0;
            padding: 0.65rem 0.85rem;
            border: 1px solid #42637C !important;
            border-radius: 0.7rem !important;
            background: #173B57 !important;
            color: #F2F7FB !important;
            font-weight: 650;
            transition: background-color 140ms ease, border-color 140ms ease, box-shadow 140ms ease;
        }
        section[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label:hover {
            border-color: #7CC4EE !important;
            background: #204E70 !important;
        }
        section[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked),
        section[data-testid="stSidebar"] [data-testid="stRadio"] label:has([aria-checked="true"]),
        section[data-testid="stSidebar"] [data-testid="stRadio"] label[aria-checked="true"] {
            border-color: #71C5F1 !important;
            background: var(--dic-blue) !important;
            color: #FFFFFF !important;
            box-shadow: 0 4px 12px rgba(3, 17, 30, 0.28);
        }
        section[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) *,
        section[data-testid="stSidebar"] [data-testid="stRadio"] label:has([aria-checked="true"]) *,
        section[data-testid="stSidebar"] [data-testid="stRadio"] label[aria-checked="true"] * {
            color: #FFFFFF !important;
        }
        section[data-testid="stSidebar"] [data-testid="stRadio"] label:focus-within {
            outline: 3px solid #F6C453;
            outline-offset: 2px;
        }

        /* Consistent panel borders, white surfaces and restrained shadows. */
        [data-testid="stMetric"],
        [data-testid="stForm"],
        [data-testid="stExpander"],
        [data-testid="stVerticalBlockBorderWrapper"] {
            border: 1px solid var(--dic-line) !important;
            border-radius: 0.75rem !important;
            background: #FFFFFF;
            box-shadow: 0 2px 8px rgba(18, 54, 83, 0.055);
        }
        [data-testid="stMetric"] {
            padding: 0.9rem 1rem;
            border-top: 3px solid #54A9D8 !important;
        }
        [data-testid="stMetricLabel"] {
            color: var(--dic-muted) !important;
            font-weight: 600;
        }
        [data-testid="stMetricValue"] {
            color: var(--dic-navy) !important;
        }
        [data-testid="stForm"] {
            padding: 1rem;
        }
        [data-testid="stExpander"] summary {
            color: var(--dic-navy);
            font-weight: 650;
        }

        /* Visible, restrained Streamlit tab treatment if a page uses st.tabs. */
        [data-testid="stTabs"] [role="tablist"] {
            gap: 0.35rem;
            border-bottom: 1px solid var(--dic-line);
        }
        [data-testid="stTabs"] button[role="tab"] {
            border: 1px solid transparent;
            border-radius: 0.65rem 0.65rem 0 0;
            color: var(--dic-muted);
            font-weight: 650;
        }
        [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
            border-color: var(--dic-line);
            border-bottom-color: #FFFFFF;
            background: #FFFFFF;
            color: var(--dic-blue-dark);
        }

        /* Buttons use the same blue accent while retaining readable contrast. */
        [data-testid="stMain"] [data-testid="stButton"] button[kind="primary"],
        [data-testid="stMain"] [data-testid="stFormSubmitButton"] button {
            border: 1px solid var(--dic-blue-dark);
            border-radius: 0.55rem;
            background: var(--dic-blue);
            color: #FFFFFF;
            font-weight: 650;
        }
        [data-testid="stMain"] [data-testid="stButton"] button[kind="primary"]:hover,
        [data-testid="stMain"] [data-testid="stFormSubmitButton"] button:hover {
            border-color: #0B456C;
            background: var(--dic-blue-dark);
            color: #FFFFFF;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
