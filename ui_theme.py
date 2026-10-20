import streamlit as st


def apply_navigation_styles():
    """Apply the navy-and-blue panel palette to the main Streamlit app."""
    st.html(
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
            background: var(--dic-canvas) !important;
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

        /* Light blue sidebar surface, with dark readable labels. */
        [data-testid="stSidebar"],
        [data-testid="stSidebar"] > div,
        [data-testid="stSidebarContent"] {
            background: #EAF2F8 !important;
            border-right: 1px solid #D4E1EB;
        }
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
            color: var(--dic-ink);
        }

        /* Bordered sidebar menu cards with a brighter selected option.
           The broad selectors support the label and wrapper layouts used by
           different Streamlit/BaseWeb versions. */
        [data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] {
            display: flex;
            flex-direction: column;
            gap: 0.45rem;
        }
        [data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] > *,
        [data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label,
        [data-testid="stSidebar"] [data-testid="stRadio"] [role="radio"],
        [data-testid="stSidebar"] [data-testid="stRadio"] [data-baseweb="radio"] {
            box-sizing: border-box;
            min-height: 2.65rem;
            margin: 0;
            padding: 0.55rem 0.75rem;
            border: 1px solid #B9D0E2 !important;
            border-radius: 0.65rem !important;
            background: #FFFFFF !important;
            color: #183247 !important;
            font-weight: 600;
            transition: background-color 140ms ease, border-color 140ms ease, box-shadow 140ms ease;
        }
        [data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] > *:hover,
        [data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label:hover {
            border-color: #5A9BC7 !important;
            background: #E8F3FC !important;
            box-shadow: 0 2px 7px rgba(18, 54, 83, 0.1);
        }
        [data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked),
        [data-testid="stSidebar"] [data-testid="stRadio"] label:has([aria-checked="true"]),
        [data-testid="stSidebar"] [data-testid="stRadio"] label[aria-checked="true"],
        [data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] > *:has(input:checked),
        [data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] > *:has([aria-checked="true"]),
        [data-testid="stSidebar"] [data-testid="stRadio"] [role="radio"][aria-checked="true"] {
            border-color: #1D4ED8 !important;
            background: #DCEBFF !important;
            color: #123653 !important;
            box-shadow: inset 0 0 0 1px #1D4ED8, 0 3px 8px rgba(18, 54, 83, 0.1);
        }
        [data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) *,
        [data-testid="stSidebar"] [data-testid="stRadio"] label:has([aria-checked="true"]) *,
        [data-testid="stSidebar"] [data-testid="stRadio"] label[aria-checked="true"] *,
        [data-testid="stSidebar"] [data-testid="stRadio"] [role="radio"][aria-checked="true"] * {
            color: #123653 !important;
        }
        [data-testid="stSidebar"] [data-testid="stRadio"] label:focus-within {
            outline: 3px solid #F6C453;
            outline-offset: 2px;
        }

        /* Give the new native navigation buttons a firmer outline. */
        [data-testid="stSidebar"] [data-testid="stButton"] button {
            border: 3px solid #7899B4 !important;
            border-radius: 0.65rem !important;
        }
        [data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"] {
            border-color: #123653 !important;
            box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.65);
        }
        [data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"],
        [data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"] * {
            color: #FFFFFF !important;
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
            color: #FFFFFF !important;
            font-weight: 650;
        }
        [data-testid="stMain"] [data-testid="stFormSubmitButton"] button,
        [data-testid="stMain"] [data-testid="stFormSubmitButton"] button * {
            color: #FFFFFF !important;
        }
        [data-testid="stMain"] [data-testid="stButton"] button[kind="primary"]:hover,
        [data-testid="stMain"] [data-testid="stFormSubmitButton"] button:hover {
            border-color: #0B456C;
            background: var(--dic-blue-dark);
            color: #FFFFFF !important;
        }
        </style>
        """
    )
