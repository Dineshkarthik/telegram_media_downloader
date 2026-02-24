"""Execution tab UI for the Telegram Media Downloader Web UI."""

import logging
import os
import urllib.parse

from nicegui import ui

import media_downloader


def build_execution_tab(
    config: dict, load_config_fn, chat_inputs: list, open_media_fn, this_dir: str
):
    """Build the Execution tab panel contents.

    Parameters
    ----------
    config : dict
        Loaded configuration dictionary.
    load_config_fn : callable
        Function to reload config from disk.
    chat_inputs : list
        List of chat input dicts (from config tab) to update last_read after run.
    open_media_fn : callable
        ``open_media(url, filename)`` for the preview dialog.
    this_dir : str
        Absolute path to the project root directory.
    """
    with ui.column().style("gap: 2px; margin-bottom: 28px;"):
        with ui.row().classes("items-center justify-between").style("width: 100%;"):
            with ui.column().style("gap: 2px;"):
                ui.label("Execution").classes("section-title")
                ui.label("Start downloading media from your configured chats.").classes(
                    "section-subtitle"
                )
            status_label = ui.html(
                '<span class="status-badge status-idle"><span style="width:6px;height:6px;border-radius:50%;background:currentColor;display:inline-block;"></span> Idle</span>'
            )

    # ── Download Progress ──
    with ui.element("div").classes("premium-card").style(
        "padding: 24px; margin-bottom: 20px;"
    ):
        with ui.row().classes("items-center").style("gap: 10px; margin-bottom: 16px;"):
            ui.icon("downloading", size="sm", color="primary")
            ui.label("Active Downloads").style(
                "font-size: 15px; font-weight: 600; color: var(--text-primary);"
            )

        progress_container = ui.column().style(
            "width: 100%; gap: 8px; max-height: 320px; overflow-y: auto; padding-right: 4px;"
        )
        ui.html(
            '<div style="padding: 12px 0; text-align: center; color: var(--text-tertiary); font-size: 13px;" id="empty-state">No active downloads</div>'
        )

    # ── Terminal Logs (collapsible) ──
    with ui.element("div").classes("premium-card").style(
        "padding: 0; margin-bottom: 20px; overflow: hidden;"
    ):
        with ui.expansion("Terminal Output", icon="terminal", value=False).style(
            "width: 100%; font-size: 15px; font-weight: 600;"
        ).props("dense"):
            log_area = (
                ui.log(max_lines=300)
                .classes("terminal-log")
                .style(
                    "width: 100%; height: 420px; padding: 16px; font-size: 13px; line-height: 1.7;"
                )
            )

    # Custom logging handler
    class UILogHandler(logging.Handler):
        def emit(self, record):
            try:
                msg = self.format(record)
                log_area.push(msg)
            except Exception:
                pass

    ui_logger = UILogHandler()
    ui_logger.setFormatter(logging.Formatter("%(message)s"))

    is_running = {"value": False}
    active_downloads = {}

    def update_status(text, style_class):
        dot = '<span style="width:6px;height:6px;border-radius:50%;background:currentColor;display:inline-block;"></span>'
        status_label.content = (
            f'<span class="status-badge {style_class}">{dot} {text}</span>'
        )

    def ui_progress_hook(desc, current, total, file_path=None, media_type=None):
        if desc not in active_downloads:
            with progress_container:
                row = (
                    ui.row()
                    .classes("dl-row")
                    .style("width: 100%; align-items: center; gap: 12px;")
                )
                with row:
                    name_label = ui.label(desc).style(
                        "font-size: 13px; font-weight: 500; color: var(--text-secondary); "
                        "white-space: nowrap; overflow: hidden; text-overflow: ellipsis; width: 35%;"
                    )
                    bar = (
                        ui.linear_progress(value=0, show_value=False)
                        .props("instant-feedback color=primary size=6px rounded")
                        .style("width: 30%; border-radius: 3px;")
                    )
                    pct_label = ui.label("0%").style(
                        "font-size: 12px; font-weight: 500; color: var(--text-tertiary); "
                        "text-align: center; width: 20%; font-variant-numeric: tabular-nums;"
                    )
                    action_col = ui.column().style(
                        "width: 10%; min-width: 50px; align-items: flex-end;"
                    )
                active_downloads[desc] = (row, name_label, bar, pct_label, action_col)

        row, name_label, bar, pct_label, action_col = active_downloads[desc]
        if total > 0:
            fraction = current / total
            bar.set_value(fraction)
            pct_label.set_text(
                f"{current / 1024 / 1024:.1f}M / {total / 1024 / 1024:.1f}M ({fraction * 100:.1f}%)"
            )
            if current >= total:
                name_label.style(
                    "font-size: 13px; font-weight: 600; color: var(--positive); "
                    "white-space: nowrap; overflow: hidden; text-overflow: ellipsis; width: 35%;"
                )
                if desc.startswith("Downloading "):
                    name_label.set_text(desc.replace("Downloading ", "✓ ", 1))

                if file_path and not getattr(row, "has_open_btn", False):
                    row.has_open_btn = True
                    global_download_dir = config.get("download_directory", "")
                    file_url = ""
                    try:
                        abs_fpath = os.path.abspath(file_path)
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
                    if file_url:
                        with action_col:
                            fname = os.path.basename(file_path)
                            ui.button(
                                "Open",
                                on_click=lambda u=file_url, n=fname: open_media_fn(
                                    u, n
                                ),
                            ).props('flat dense color="primary" size="sm"').style(
                                "font-size: 12px;"
                            )
        else:
            bar.set_value(0)
            pct_label.set_text(f"{current} bytes")

    async def run_downloader():
        if is_running["value"]:
            ui.notify("Downloader is already running!", type="warning")
            return
        is_running["value"] = True
        main_logger = logging.getLogger("media_downloader")
        main_logger.addHandler(ui_logger)
        try:
            log_area.clear()
            progress_container.clear()
            active_downloads.clear()
            update_status("Running", "status-running")
            ui.notify("Initializing Telegram Client...", type="info")
            media_downloader.UI_PROGRESS_HOOK = ui_progress_hook
            fresh_config = load_config_fn()
            updated_config = await media_downloader.begin_import(
                fresh_config, pagination_limit=100
            )
            media_downloader.update_config(updated_config)
            updated_chats = updated_config.get("chats", [])
            for i, c in enumerate(updated_chats):
                if i < len(chat_inputs):
                    chat_inputs[i]["last_read"].value = c.get("last_read_message_id", 0)
            total_failures = sum(
                len(set(flist)) for flist in media_downloader.FAILED_IDS.values()
            )
            if total_failures > 0:
                update_status(f"Done · {total_failures} errors", "status-warning")
                log_area.push(
                    f"Warning: {total_failures} files failed. Check config.yaml ids_to_retry."
                )
                ui.notify(
                    f"Finished, but {total_failures} files failed.",
                    type="warning",
                    position="top",
                )
            else:
                update_status("Complete", "status-success")
                ui.notify(
                    "Download complete!",
                    type="positive",
                    position="top",
                )
        except Exception as e:
            update_status("Error", "status-error")
            log_area.push(f"Error: {str(e)}")
            ui.notify(f"Error: {str(e)}", type="negative", position="top")
        finally:
            media_downloader.UI_PROGRESS_HOOK = None
            is_running["value"] = False
            main_logger.removeHandler(ui_logger)

    ui.button("Start Download", on_click=run_downloader, icon="play_arrow").props(
        'unelevated color="primary"'
    ).style("width: 100%; height: 48px; font-size: 14px; font-weight: 600;")
