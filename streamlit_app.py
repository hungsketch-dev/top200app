"""
Top 200 Free Apps Dashboard — App Store + Google Play
"""

import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Top 200 Free Apps", page_icon="📱", layout="wide")

APPLE_COUNTRIES = {
    "United States": "us", "United Kingdom": "gb", "Canada": "ca",
    "Australia": "au", "Germany": "de", "France": "fr", "Japan": "jp",
    "India": "in", "Brazil": "br", "Mexico": "mx", "Spain": "es",
    "Italy": "it", "Netherlands": "nl", "South Korea": "kr",
}

GOOGLE_COUNTRIES = {
    "United States": ("us", "en"), "United Kingdom": ("gb", "en"),
    "Canada": ("ca", "en"), "Australia": ("au", "en"),
    "Germany": ("de", "de"), "France": ("fr", "fr"),
    "Japan": ("jp", "ja"), "India": ("in", "en"),
    "Brazil": ("br", "pt"), "Mexico": ("mx", "es"),
    "Spain": ("es", "es"), "Italy": ("it", "it"),
    "Netherlands": ("nl", "nl"), "South Korea": ("kr", "ko"),
}


def fetch_apple(country_code: str) -> pd.DataFrame:
    url = f"https://rss.applemarketingtools.com/api/v2/{country_code}/apps/top-free/200/apps.json"
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    results = resp.json()["feed"]["results"]
    rows = []
    for rank, a in enumerate(results, start=1):
        genres = a.get("genres", [])
        rows.append({
            "Rank": rank,
            "Name": a.get("name", ""),
            "Developer": a.get("artistName", ""),
            "Category": genres[0]["name"] if genres else "Unknown",
            "Icon": a.get("artworkUrl100", ""),
            "URL": a.get("url", ""),
        })
    return pd.DataFrame(rows)


def fetch_google(country_code: str, lang: str) -> pd.DataFrame:
    from google_play_scraper.features.list_apps import list_apps
    results = list_apps(
        collection="TOP_FREE", category=None, age=None,
        num=200, lang=lang, country=country_code,
    )
    rows = []
    for rank, a in enumerate(results, start=1):
        app_id = a.get("appId", "")
        rows.append({
            "Rank": rank,
            "Name": a.get("title", ""),
            "Developer": a.get("developer", ""),
            "Category": a.get("genre") or "Unknown",
            "Icon": a.get("icon", ""),
            "URL": a.get("url") or f"https://play.google.com/store/apps/details?id={app_id}",
        })
    return pd.DataFrame(rows)


def render_list(df: pd.DataFrame, store_label: str):
    with st.sidebar:
        st.subheader(f"{store_label} filters")
        search_query = st.text_input(f"Search ({store_label})", "", key=f"search_{store_label}")
        categories = ["All categories"] + sorted(df["Category"].unique().tolist())
        category = st.selectbox("Category", options=categories, index=0, key=f"cat_{store_label}")

    filtered = df.copy()
    if category != "All categories":
        filtered = filtered[filtered["Category"] == category]
    if search_query.strip():
        q = search_query.strip().lower()
        mask = (filtered["Name"].str.lower().str.contains(q, na=False)
                | filtered["Developer"].str.lower().str.contains(q, na=False))
        filtered = filtered[mask]

    c1, c2, c3 = st.columns(3)
    c1.metric("Showing", f"{len(filtered)} apps")
    c2.metric("Total", len(df))
    c3.metric("Categories", df["Category"].nunique())
    st.divider()

    if filtered.empty:
        st.info("No apps match your filters.")
        return

    for _, row in filtered.iterrows():
        c_icon, c_info, c_link = st.columns([1, 6, 2])
        with c_icon:
            if row["Icon"]:
                st.image(row["Icon"], width=72)
        with c_info:
            st.markdown(f"**#{row['Rank']} · {row['Name']}**")
            st.caption(f"{row['Developer']} · {row['Category']}")
        with c_link:
            if row["URL"]:
                st.link_button(f"View in {store_label}", row["URL"])
        st.divider()


# BUILD MARKER: v3-applemarketingtools
st.title("📱 Top 200 Free Apps")
st.caption("Build: v3-applemarketingtools · Apple RSS + Google Play")

with st.sidebar:
    st.header("Global")
    country_name = st.selectbox("Country / storefront", options=list(APPLE_COUNTRIES.keys()), index=0)

tab_apple, tab_google = st.tabs(["🍎 App Store", "▶ Google Play"])

with tab_apple:
    try:
        with st.spinner(f"Loading App Store top 200 for {country_name}…"):
            df_apple = fetch_apple(APPLE_COUNTRIES[country_name])
        render_list(df_apple, "App Store")
    except Exception as e:
        st.error(f"App Store fetch failed: {e}")

with tab_google:
    try:
        gc, lang = GOOGLE_COUNTRIES[country_name]
        with st.spinner(f"Loading Google Play top 200 for {country_name}…"):
            df_google = fetch_google(gc, lang)
        render_list(df_google, "Google Play")
    except Exception as e:
        st.error(f"Google Play fetch failed: {e}")
        st.caption("Try: pip install -U google-play-scraper")
