"""Web UI for Telegram Media Downloader using NiceGUI."""

import logging
import os
import sys

try:
    from nicegui import app, ui
except ImportError:
    print("\n[ERROR] Web UI dependencies are not installed.")
    print(
        "The Web UI is now an optional installation to keep the base application lightweight."
    )
    print("To use the graphical interface, please run:")
    print("  make install_webui")
    print("  or")
    print("  pip install -r requirements-webui.txt\n")
    sys.exit(1)

from config_manager import load_config, save_config
from webui.config_tab import build_config_tab
from webui.execution_tab import build_execution_tab
from webui.history_tab import build_history_tab
from webui.styles import PREMIUM_CSS
from webui.tour import build_tour

logger = logging.getLogger("webui")
THIS_DIR = os.path.dirname(os.path.abspath(__file__))


@ui.page("/")
def index():
    ui.page_title("Telegram Media Downloader")
    config = load_config()
    ui.add_head_html(PREMIUM_CSS)
    dark_mode = ui.dark_mode()

    # ── State for navigation ──
    current_page = {"value": "config"}

    # We'll use a column-based layout: sidebar + main content
    with ui.row().classes("w-full h-screen").style("margin:0; padding:0; gap:0;"):

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        #  LEFT SIDEBAR
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        with ui.column().classes("sidebar").style(
            "width: 260px; min-width: 260px; height: 100vh; position: sticky; top: 0; padding: 24px 16px; "
            "display: flex; flex-direction: column; justify-content: space-between;"
        ):
            with ui.column().style("gap: 4px;"):
                # Logo / Branding
                with ui.row().classes("items-center").style(
                    "gap: 10px; padding: 8px 16px 24px 16px;"
                ):
                    ui.icon("cloud_download", size="sm", color="primary")
                    with ui.column().style("gap: 0;"):
                        ui.label("TG Downloader").style(
                            "font-size: 15px; font-weight: 700; letter-spacing: -0.025em; color: var(--text-primary); line-height: 1.2;"
                        )
                        ui.label("Media Manager").style(
                            "font-size: 11px; font-weight: 500; color: var(--text-tertiary); letter-spacing: 0.02em;"
                        )

                ui.html('<hr class="divider" style="margin: 0 0 8px 0;">')
                ui.label("WORKSPACE").style(
                    "font-size: 10px; font-weight: 600; color: var(--text-tertiary); "
                    "letter-spacing: 0.1em; padding: 0 16px 6px; text-transform: uppercase;"
                )

                # Nav Items
                def make_nav(label, icon, page_key):
                    active = current_page["value"] == page_key
                    cls = "nav-item active" if active else "nav-item"
                    with ui.element("div").classes(cls) as nav:
                        ui.icon(icon)
                        ui.label(label)

                        def navigate(pk=page_key, n=nav):
                            current_page["value"] = pk
                            tab_panels.set_value(pk)
                            for item, key in nav_items:
                                if key == pk:
                                    item.classes(replace="nav-item active")
                                else:
                                    item.classes(replace="nav-item")

                        nav.on("click", navigate)
                    return nav

                nav_items = []
                n1 = make_nav("Configuration", "tune", "config")
                nav_items.append((n1, "config"))
                n2 = make_nav("Execution", "play_circle_outline", "execution")
                nav_items.append((n2, "execution"))
                n3 = make_nav("History", "schedule", "history")
                nav_items.append((n3, "history"))

            # Bottom of sidebar
            with ui.column().style("gap: 8px; padding: 0 4px;"):
                ui.html('<hr class="divider" style="margin: 0;">')
                ui.button(
                    "Take Tour", on_click=lambda: show_tour(), icon="school"
                ).props("flat dense color=grey-7").style(
                    "width: 100%; justify-content: flex-start; font-size: 13px; padding: 6px 12px;"
                )
                with ui.row().classes("items-center justify-between").style(
                    "padding: 4px 12px;"
                ):
                    ui.label("Dark mode").style(
                        "font-size: 13px; font-weight: 500; color: var(--text-secondary);"
                    )
                    ui.switch(value=False, on_change=lambda: dark_mode.toggle()).props(
                        "dense"
                    )

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        #  TOUR (floating panel, built before content so show_tour is available)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # tab_panels will be assigned shortly; we create a forward-ref list
        # so the tour can navigate pages. nav_items is already populated.

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        #  MAIN CONTENT AREA
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        with ui.column().style(
            "flex: 1; height: 100vh; padding: 32px 40px; overflow-y: auto; "
            "background: var(--surface-dim);"
        ):

            # Media Viewing Modal
            with ui.dialog().props("maximized") as media_modal, ui.card().style(
                "background: #000; max-width: 900px; width: 90%; margin: auto; "
                "border-radius: var(--radius-xl); overflow: hidden; position: relative;"
            ):
                ui.button(icon="close", on_click=media_modal.close).props(
                    "flat dense round color=white"
                ).style("position: absolute; top: 12px; right: 12px; z-index: 50;")
                media_container = ui.column().style(
                    "width: 100%; min-height: 50vh; display: flex; align-items: center; "
                    "justify-content: center; padding: 24px;"
                )

            def open_media(url: str, filename: str):
                media_container.clear()
                ext = url.split(".")[-1].lower() if "." in url else ""
                with media_container:
                    if ext in ["mp4", "webm", "ogg"]:
                        ui.video(url).classes("w-full max-h-[80vh] object-contain")
                    elif ext in ["jpg", "jpeg", "png", "gif", "webp", "bmp", "svg"]:
                        ui.image(url).classes("w-full max-h-[80vh] object-contain")
                    elif ext in ["mp3", "wav", "oga", "m4a", "flac"]:
                        ui.audio(url).classes("w-full q-mt-xl")
                    elif ext == "pdf":
                        ui.html(
                            f'<iframe src="{url}" width="100%" height="600px" style="border:none;border-radius:12px;"></iframe>'
                        ).classes("w-full")
                    else:
                        ui.label("Preview not available for this file type.").style(
                            "color: white; padding: 40px; font-size: 16px;"
                        )
                        ui.link("Download / Open Raw File", url, new_tab=True).style(
                            "color: #818cf8; font-size: 15px; text-decoration: underline;"
                        )
                media_modal.open()

            # ── Tab Panels (hidden tabs, controlled by sidebar) ──
            with ui.tab_panels(value="config").classes("w-full").style(
                "background: transparent; padding: 0; margin: 0;"
            ).props("animated") as tab_panels:

                # ══════ CONFIGURATION PAGE ══════
                with ui.tab_panel("config").style("padding: 0;"):
                    global_inputs, chat_inputs = build_config_tab(config, save_config)

                # ══════ EXECUTION PAGE ══════
                with ui.tab_panel("execution").style("padding: 0;"):
                    build_execution_tab(
                        config, load_config, chat_inputs, open_media, THIS_DIR
                    )

                # ══════ HISTORY PAGE ══════
                with ui.tab_panel("history").style("padding: 0;"):
                    build_history_tab(config, open_media, THIS_DIR)

    # Build tour (needs tab_panels and nav_items)
    show_tour, check_first_visit = build_tour(current_page, tab_panels, nav_items)

    # Mount media files directory
    _init_cfg = load_config()
    _init_dl_dir = _init_cfg.get("download_directory", "")
    _base_media_path = os.path.abspath(_init_dl_dir) if _init_dl_dir else THIS_DIR
    if os.path.exists(_base_media_path):
        app.add_static_files("/media", _base_media_path)

    # Auto-show tutorial for first-time visitors (after 1s delay)
    ui.timer(1.0, check_first_visit, once=True)


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title="Telegram Media Downloader", port=8080, dark=False, show=False)
