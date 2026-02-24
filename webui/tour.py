"""Tutorial walkthrough for the Telegram Media Downloader Web UI."""

from nicegui import ui

# ── Tour step definitions ──
TOUR_STEPS = [
    {
        "icon": "👋",
        "title": "Welcome to TG Downloader",
        "body": (
            "This tool helps you bulk-download media from Telegram chats and channels.\n\n"
            "We'll walk you through **every section** step by step so you can get set up quickly.\n\n"
            "Use **Next** to continue or **✕** to dismiss at any time."
        ),
    },
    {
        "icon": "🔑",
        "title": "Step 1 · API Credentials",
        "page": "config",
        "body": (
            "First, you need a Telegram API ID and Hash. Here's how:\n\n"
            "1. Go to [my.telegram.org](https://my.telegram.org) and log in with your phone number\n"
            "2. Click **API Development Tools**\n"
            "3. Create a new application (any name works)\n"
            "4. Copy the **API ID** (a number) and **API Hash** (a string)\n\n"
            "Paste them into the **API ID** and **API Hash** fields in the first card. "
            "The hash is hidden by default — click the eye icon to reveal it.\n\n"
            "> ⚠️ Keep these credentials private. They are stored only in your local `config.yaml`."
        ),
    },
    {
        "icon": "📂",
        "title": "Step 2 · Download Directory",
        "page": "config",
        "body": (
            "In the **Download Settings** card, set where your files will be saved:\n\n"
            "- **Download Directory** — The folder path where all media will be downloaded. "
            "Leave empty to use the app's own directory\n"
            "- The path can be absolute (e.g. `/Users/you/Downloads/telegram`) or "
            "relative to where the app is running\n\n"
            "Make sure the directory exists and is writable!"
        ),
    },
    {
        "icon": "⚡",
        "title": "Step 3 · Concurrency & Pacing",
        "page": "config",
        "body": (
            "These settings help you **avoid Telegram rate-limit bans**:\n\n"
            "- **Max Concurrent** — How many files download simultaneously. "
            "Start with `1`–`3` to be safe. Higher values are faster but riskier\n"
            "- **Download Delay (sec)** — Wait time between starting each file. "
            "Enter a single number like `2`, or a range like `1,5` for a random "
            "delay between 1–5 seconds\n\n"
            "> 💡 **Tip:** If you're downloading from a large channel for the first time, "
            "use conservative settings (max 2 concurrent, 2–3 sec delay)."
        ),
    },
    {
        "icon": "🎬",
        "title": "Step 4 · Media Types",
        "page": "config",
        "body": (
            "Still in **Download Settings**, choose which media types to download:\n\n"
            "- **photo** — Images and photos\n"
            "- **video** — Video files\n"
            "- **document** — PDFs, ZIPs, and other documents\n"
            "- **audio** — Music and audio files\n"
            "- **voice** — Voice messages and voice notes\n\n"
            "Click the ✕ on any chip to remove a type, or type in the field to add one back.\n\n"
            "Also check **Parallel Chats** if you want to download from multiple chats simultaneously."
        ),
    },
    {
        "icon": "💬",
        "title": "Step 5 · Target Chats",
        "page": "config",
        "body": (
            "In the **Target Chats** card, add the chats you want to download from:\n\n"
            "- Click **＋ Add Chat** to add a new chat entry\n"
            "- **Chat ID** — The numeric ID of the chat/channel. You can find this using bots "
            'like @userinfobot or by enabling "Show Chat ID" in Telegram Desktop settings\n'
            "- **From / To Msg ID** — Optionally limit to a message range. `0` means no limit\n"
            "- **Last Read Msg ID** — Tracks where the downloader left off. Updated automatically after each run\n\n"
            "Expand **Advanced Overrides** to set a per-chat download directory or select specific media types for that chat only."
        ),
    },
    {
        "icon": "💾",
        "title": "Step 6 · Save Your Config",
        "page": "config",
        "body": (
            "When you're done configuring, scroll to the bottom and click **Save Configuration**.\n\n"
            "This writes your settings to `config.yaml` in the app directory.\n\n"
            "- **Save Configuration** — Writes all current settings to disk\n"
            "- **Reload from Disk** — Discards unsaved changes and reloads from the file\n\n"
            "> 📌 You **must** save before running a download — the downloader reads from the saved config file."
        ),
    },
    {
        "icon": "▶️",
        "title": "Step 7 · Running Downloads",
        "page": "execution",
        "body": (
            "Switch to the **Execution** tab to start downloading:\n\n"
            "1. Click the **Start Download** button at the bottom\n"
            "2. The app connects to Telegram (you may need to authenticate on first run via the terminal)\n"
            "3. Watch the **status badge** in the top-right — it shows:\n"
            "   - 🔵 **Idle** — Ready to start\n"
            "   - 🟡 **Running** — Download in progress\n"
            "   - 🟢 **Complete** — Finished successfully\n"
            "   - 🔴 **Error** — Something went wrong\n\n"
            "The **Active Downloads** card shows real-time progress bars for each file being downloaded, "
            "with file size and percentage. Completed files show a ✓ mark and an **Open** button."
        ),
    },
    {
        "icon": "🖥️",
        "title": "Step 8 · Terminal Logs",
        "page": "execution",
        "body": (
            "Below Active Downloads, there's a collapsible **Terminal Output** section:\n\n"
            "- Click the header to **expand/collapse** it\n"
            "- Shows detailed logs: connection status, file-by-file progress, errors, and warnings\n"
            "- Useful for debugging if downloads fail or stall\n"
            "- Keeps the last 300 log lines — older entries are automatically removed\n\n"
            "> 💡 **Tip:** If a download seems stuck, expand the terminal to check for "
            "Telegram rate-limit warnings or authentication prompts."
        ),
    },
    {
        "icon": "📋",
        "title": "Step 9 · Download History",
        "page": "history",
        "body": (
            "The **History** tab shows every file that's been downloaded:\n\n"
            "- **Search** — Type a filename to filter results instantly\n"
            "- **Type filter** — Dropdown to show only photos, videos, documents, etc.\n"
            "- **Column sorting** — Click any column header to sort by Time, Chat, Name, or Size\n"
            "- **Pagination** — Navigate through pages at the bottom, 20 items per page\n"
            "- **Open ↗** — Click to preview files right in the browser (images, videos, audio, PDFs)\n"
            "- **Clear All** — Clears the history log (does not delete actual files)\n\n"
            "You're all set! Happy downloading 🎉"
        ),
    },
]


def build_tour(current_page: dict, tab_panels, nav_items: list):
    """Build the floating tour panel and return (show_tour, check_first_visit) functions.

    Parameters
    ----------
    current_page : dict
        Mutable dict with ``{"value": "config"}`` for sidebar navigation state.
    tab_panels : nicegui TabPanels element
        The tab panels container to switch pages.
    nav_items : list[tuple]
        List of ``(nav_element, page_key)`` tuples for sidebar highlighting.

    Returns
    -------
    tuple[callable, callable]
        ``(show_tour, check_first_visit)`` functions.
    """
    tour_panel = ui.element("div").style(
        "position: fixed; bottom: 24px; right: 24px; z-index: 9999; "
        "width: 420px; max-width: calc(100vw - 320px); "
        "background: var(--surface); border: 1px solid var(--border); "
        "border-radius: var(--radius-xl); box-shadow: var(--shadow-lg); "
        "overflow: hidden; display: none; transition: all 0.3s ease;"
    )
    tour_state = {"step": 0}

    with tour_panel:
        # Header bar
        with ui.row().classes("items-center justify-between").style(
            "padding: 12px 16px; border-bottom: 1px solid var(--border); background: var(--surface-dim);"
        ):
            with ui.row().classes("items-center").style("gap: 8px;"):
                tour_icon = ui.label("").style("font-size: 20px;")
                tour_title = ui.label("").style(
                    "font-size: 14px; font-weight: 700; color: var(--text-primary); letter-spacing: -0.01em;"
                )
            ui.button(icon="close", on_click=lambda: finish_tour()).props(
                "flat dense round size=sm color=grey-6"
            )

        # Body
        tour_body = ui.markdown("").style(
            "font-size: 13px; color: var(--text-secondary); line-height: 1.65; "
            "padding: 16px 20px 12px; max-height: 320px; overflow-y: auto;"
        )

        # Footer: progress + buttons
        with ui.column().style("padding: 0 20px 16px; gap: 10px;"):
            with ui.row().classes("items-center").style("gap: 8px; width: 100%;"):
                tour_progress = (
                    ui.linear_progress(value=0, show_value=False)
                    .props("instant-feedback color=primary size=3px rounded")
                    .style("flex: 1;")
                )
                tour_counter = ui.label("").style(
                    "font-size: 11px; font-weight: 600; color: var(--text-tertiary); "
                    "white-space: nowrap;"
                )

            with ui.row().style(
                "width: 100%; justify-content: space-between; gap: 8px;"
            ):
                tour_back_btn = (
                    ui.button("Back", on_click=lambda: tour_navigate(-1))
                    .props("flat dense color=grey-7")
                    .style("font-size: 12px;")
                )
                tour_next_btn = (
                    ui.button("Next", on_click=lambda: tour_navigate(1))
                    .props('unelevated dense color="primary"')
                    .style("font-size: 12px; padding: 4px 20px;")
                )

    def show_tour():
        tour_state["step"] = 0
        render_tour_step()
        ui.run_javascript(
            f"document.querySelector('[id=\"c{tour_panel.id}\"]').style.display = 'block'"
        )

    def render_tour_step():
        s = TOUR_STEPS[tour_state["step"]]
        tour_icon.set_text(s["icon"])
        tour_title.set_text(s["title"])
        tour_body.set_content(s["body"])

        # Navigate to relevant page
        if "page" in s:
            current_page["value"] = s["page"]
            tab_panels.set_value(s["page"])
            for item, key in nav_items:
                if key == s["page"]:
                    item.classes(replace="nav-item active")
                else:
                    item.classes(replace="nav-item")

        # Update counter + progress
        total = len(TOUR_STEPS)
        current = tour_state["step"] + 1
        tour_counter.set_text(f"{current}/{total}")
        tour_progress.set_value(current / total)

        # Update buttons
        is_first = tour_state["step"] == 0
        is_last = tour_state["step"] == len(TOUR_STEPS) - 1
        tour_back_btn.set_visibility(not is_first)
        if is_last:
            tour_next_btn.set_text("Finish")
        else:
            tour_next_btn.set_text("Next")

    def tour_navigate(direction):
        new_step = tour_state["step"] + direction
        if new_step >= len(TOUR_STEPS):
            finish_tour()
            return
        tour_state["step"] = max(0, new_step)
        render_tour_step()

    def finish_tour():
        ui.run_javascript(
            f"document.querySelector('[id=\"c{tour_panel.id}\"]').style.display = 'none'"
        )
        tour_state["step"] = 0
        ui.run_javascript("localStorage.setItem('tg_dl_tour_seen', '1')")

    async def check_first_visit():
        result = await ui.run_javascript("localStorage.getItem('tg_dl_tour_seen')")
        if not result:
            show_tour()

    return show_tour, check_first_visit
