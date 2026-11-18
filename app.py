"""MIND / MACHINE — THE DECISION STUDIO (Main Streamlit Application Entrypoint)."""

from __future__ import annotations

from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from ui.components.shell import render_sidebar_and_load_bundle, render_top_instrument_strip
from ui.screens.audit import render_audit_screen
from ui.screens.overview import render_overview_screen
from ui.screens.plan import render_plan_screen
from ui.screens.system import render_system_screen
from ui.screens.updates import render_updates_screen
from ui.styles import inject_editorial_styles


def main() -> None:
    st.set_page_config(
        page_title="MIND / MACHINE — THE DECISION STUDIO",
        page_icon="▪",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    load_dotenv(Path.cwd() / ".env")
    inject_editorial_styles()
    active_screen_id, bundle = render_sidebar_and_load_bundle()
    render_top_instrument_strip(active_screen_id, bundle)

    if active_screen_id == "overview":
        render_overview_screen(bundle)
    elif active_screen_id == "plan":
        render_plan_screen(bundle)
    elif active_screen_id == "audit":
        render_audit_screen(bundle)
    elif active_screen_id == "updates":
        render_updates_screen(bundle)
    elif active_screen_id == "system":
        render_system_screen(bundle)
    else:
        render_overview_screen(bundle)


if __name__ == "__main__":
    main()
