"""History tab UI for the Telegram Media Downloader Web UI."""

import os
import urllib.parse

from nicegui import ui

import db


def build_history_tab(config: dict, open_media_fn, this_dir: str):
    """Build the History tab panel contents.

    Parameters
    ----------
    config : dict
        Loaded configuration dictionary.
    open_media_fn : callable
        ``open_media(url, filename)`` for the preview dialog.
    this_dir : str
        Absolute path to the project root directory.
    """
    with ui.column().style("gap: 2px; margin-bottom: 28px;"):
        ui.label("Download History").classes("section-title")
        ui.label("Browse and preview your previously downloaded media files.").classes(
            "section-subtitle"
        )

    with ui.element("div").classes("premium-card").style("padding: 24px;"):

        # ── Filters Row ──
        with ui.row().style(
            "gap: 12px; width: 100%; margin-bottom: 20px; align-items: center; flex-wrap: wrap;"
        ):
            search_input = (
                ui.input(label="Search files…")
                .style("flex: 1; min-width: 200px;")
                .props("outlined dense clearable")
            )
            search_input.on("keydown.enter", lambda: load_history())

            media_type_select = (
                ui.select(
                    ["All", "photo", "video", "document", "audio", "voice"],
                    value="All",
                    label="Type",
                )
                .style("width: 140px;")
                .props("outlined dense")
            )
            media_type_select.on("update:model-value", lambda: load_history())

            ui.button("Search", on_click=lambda: load_history(), icon="search").props(
                'unelevated dense color="primary"'
            ).style("font-size: 13px;")
            ui.button(
                "Refresh",
                on_click=lambda: load_history(),
                icon="refresh",
            ).props("flat dense color=grey-7").style("font-size: 13px;")

            def clear_history():
                db.reset_history()
                load_history()
                ui.notify("History cleared.", type="info")

            ui.button(
                "Clear All",
                on_click=clear_history,
                icon="delete_outline",
            ).props("flat dense color=negative").style("font-size: 13px;")

        # ── Table ──
        columns = [
            {
                "name": "timestamp",
                "label": "Time",
                "field": "download_timestamp",
                "sortable": True,
                "align": "left",
            },
            {
                "name": "chat",
                "label": "Chat",
                "field": "chat_id",
                "sortable": True,
                "align": "left",
            },
            {
                "name": "filename",
                "label": "File Name",
                "field": "file_name",
                "sortable": True,
                "align": "left",
            },
            {
                "name": "size",
                "label": "Size (MB)",
                "field": "size_mb",
                "sortable": True,
                "align": "right",
            },
            {
                "name": "media_type",
                "label": "Type",
                "field": "media_type",
                "sortable": True,
                "align": "left",
            },
            {
                "name": "file_path",
                "label": "Preview",
                "field": "file_path",
                "sortable": False,
                "align": "left",
            },
        ]

        history_table = (
            ui.table(columns=columns, rows=[], row_key="id")
            .style("width: 100%;")
            .props("flat bordered dense")
        )

        history_table.add_slot(
            "body-cell-file_path",
            """
            <q-td :props="props">
                <ui-button v-if="props.row.file_url" @click="$parent.$emit('open_media', props.row)" style="background: none; border: none; padding: 0; cursor: pointer; color: var(--accent); font-size: 13px; font-weight: 500; text-decoration: none;">
                    Open ↗
                </ui-button>
                <span v-else style="color: var(--text-tertiary); font-size: 12px;">—</span>
            </q-td>
            """,
        )
        history_table.on(
            "open_media",
            lambda e: open_media_fn(e.args["file_url"], e.args["file_name"]),
        )

        pagination = {
            "page": 1,
            "limit": 20,
            "total": 0,
            "sortBy": "timestamp",
            "descending": True,
        }
        global_download_dir = config.get("download_directory", "")

        def handle_table_request(e):
            props = e.args.get("pagination", {})
            if "sortBy" in props and props["sortBy"]:
                pagination["sortBy"] = props["sortBy"]
                pagination["descending"] = props.get("descending", False)
            load_history()

        history_table.on("request", handle_table_request)

        def load_history():
            offset = (pagination["page"] - 1) * pagination["limit"]
            sort_by = pagination["sortBy"]
            sort_desc = pagination["descending"]
            records, total = db.get_recent_downloads(
                limit=pagination["limit"],
                offset=offset,
                search_item=search_input.value or "",
                media_type=media_type_select.value,
                sort_by=sort_by,
                sort_desc=sort_desc,
            )
            pagination["total"] = total

            rows = []
            for r in records:
                MB = r["file_size"] / (1024 * 1024)
                fpath = r.get("file_path", "")
                file_url = ""
                if fpath:
                    try:
                        abs_fpath = os.path.abspath(fpath)
                        abs_base = (
                            os.path.abspath(global_download_dir)
                            if global_download_dir
                            else this_dir
                        )
                        if abs_fpath.startswith(abs_base):
                            rel_path = os.path.relpath(abs_fpath, abs_base)
                            rel_path = rel_path.replace("\\", "/")
                            encoded_path = urllib.parse.quote(rel_path, safe="/")
                            file_url = f"/media/{encoded_path}"
                    except Exception:
                        pass
                rows.append(
                    {
                        "id": r["id"],
                        "download_timestamp": r["download_timestamp"],
                        "chat_id": r["chat_id"],
                        "file_name": r["file_name"],
                        "size_mb": f"{MB:.2f}",
                        "media_type": r.get("media_type", ""),
                        "file_path": fpath,
                        "file_url": file_url,
                    }
                )
            history_table.rows = rows
            page_label.set_text(
                f"Page {pagination['page']} of {max(1, -(-total // pagination['limit']))} · {total} items"
            )

        # ── Pagination ──
        with ui.row().style(
            "width: 100%; justify-content: space-between; align-items: center; "
            "margin-top: 16px; padding-top: 16px; border-top: 1px solid var(--border-light);"
        ):

            def prev_page():
                if pagination["page"] > 1:
                    pagination["page"] -= 1
                    load_history()

            def next_page():
                if (pagination["page"] * pagination["limit"]) < pagination["total"]:
                    pagination["page"] += 1
                    load_history()

            ui.button(icon="chevron_left", on_click=prev_page).props(
                "flat dense round color=grey-7"
            )
            page_label = ui.label("Page 1").style(
                "font-size: 13px; font-weight: 500; color: var(--text-tertiary); font-variant-numeric: tabular-nums;"
            )
            ui.button(icon="chevron_right", on_click=next_page).props(
                "flat dense round color=grey-7"
            )

        load_history()
