"""Configuration tab UI for the Telegram Media Downloader Web UI."""

from nicegui import ui


def build_config_tab(config: dict, save_config_fn):
    """Build the Configuration tab panel contents.

    Parameters
    ----------
    config : dict
        Loaded configuration dictionary (mutated on save).
    save_config_fn : callable
        Function that persists ``config`` to disk.

    Returns
    -------
    tuple[dict, list]
        ``(global_inputs, chat_inputs)`` — references other tabs may need.
    """
    global_inputs = {}
    chat_inputs = []

    # Page Header
    with ui.column().style("gap: 2px; margin-bottom: 28px;"):
        ui.label("Configuration").classes("section-title")
        ui.label(
            "Manage your Telegram API credentials, download preferences, and target chats."
        ).classes("section-subtitle")

    # ── API Credentials Card ──
    with ui.element("div").classes("premium-card").style(
        "padding: 24px; margin-bottom: 20px;"
    ):
        with ui.row().classes("items-center").style("gap: 10px; margin-bottom: 20px;"):
            ui.icon("vpn_key", size="sm", color="primary")
            with ui.column().style("gap: 0;"):
                ui.label("API Credentials").style(
                    "font-size: 15px; font-weight: 600; color: var(--text-primary); letter-spacing: -0.01em;"
                )
                ui.label("Your Telegram API ID and hash from my.telegram.org").style(
                    "font-size: 12px; color: var(--text-tertiary);"
                )

        with ui.row().style("gap: 16px; width: 100%;"):
            api_id_val = config.get("api_id")
            global_inputs["api_id"] = (
                ui.number("API ID", value=api_id_val, format="%.0f")
                .classes("col")
                .props("outlined dense")
            )
            api_hash_val = config.get("api_hash", "")
            global_inputs["api_hash"] = (
                ui.input(
                    "API Hash",
                    value=api_hash_val,
                    password=True,
                    password_toggle_button=True,
                )
                .classes("col")
                .props("outlined dense")
            )

    # ── Download Settings Card ──
    with ui.element("div").classes("premium-card").style(
        "padding: 24px; margin-bottom: 20px;"
    ):
        with ui.row().classes("items-center").style("gap: 10px; margin-bottom: 20px;"):
            ui.icon("settings", size="sm", color="primary")
            with ui.column().style("gap: 0;"):
                ui.label("Download Settings").style(
                    "font-size: 15px; font-weight: 600; color: var(--text-primary); letter-spacing: -0.01em;"
                )
                ui.label("Configure download directory, concurrency, and pacing").style(
                    "font-size: 12px; color: var(--text-tertiary);"
                )

        with ui.row().style("gap: 16px; width: 100%; margin-bottom: 16px;"):
            global_inputs["download_dir"] = (
                ui.input(
                    "Download Directory",
                    value=config.get("download_directory", ""),
                )
                .classes("col")
                .props('outlined dense hint="Leave empty to use app directory"')
            )

        with ui.row().style("gap: 16px; width: 100%; margin-bottom: 16px;"):
            global_inputs["max_concurrent"] = (
                ui.number(
                    "Max Concurrent",
                    value=config.get("max_concurrent_downloads", 4),
                    format="%.0f",
                )
                .classes("col")
                .props("outlined dense")
            )
            delay_val = config.get("download_delay")
            if isinstance(delay_val, list):
                delay_str = f"{delay_val[0]}, {delay_val[1]}"
            else:
                delay_str = str(delay_val) if delay_val is not None else ""
            global_inputs["download_delay"] = (
                ui.input("Download Delay (sec)", value=delay_str)
                .classes("col")
                .props('outlined dense hint="e.g. 2 or 1,5 for range"')
            )

        with ui.row().style("gap: 16px; width: 100%; align-items: center;"):
            _media_types = config.get(
                "media_types",
                ["photo", "video", "document", "audio", "voice", "video_note"],
            )
            global_inputs["media_types"] = (
                ui.select(
                    options=[
                        "photo",
                        "video",
                        "document",
                        "audio",
                        "voice",
                        "video_note",
                    ],
                    value=_media_types,
                    multiple=True,
                    label="Media Types",
                )
                .classes("col")
                .props("outlined dense use-chips")
            )
            global_inputs["parallel_chats"] = ui.checkbox(
                "Parallel Chats",
                value=config.get("parallel_chats", False),
            ).style("color: var(--text-secondary);")

    # ── Target Chats Card ──
    with ui.element("div").classes("premium-card").style(
        "padding: 24px; margin-bottom: 20px;"
    ):
        with ui.row().classes("items-center justify-between").style(
            "width: 100%; margin-bottom: 20px;"
        ):
            with ui.row().classes("items-center").style("gap: 10px;"):
                ui.icon("forum", size="sm", color="primary")
                with ui.column().style("gap: 0;"):
                    ui.label("Target Chats").style(
                        "font-size: 15px; font-weight: 600; color: var(--text-primary); letter-spacing: -0.01em;"
                    )
                    ui.label("Add chats to download media from").style(
                        "font-size: 12px; color: var(--text-tertiary);"
                    )

        chats_container = ui.column().style("width: 100%; gap: 12px;")

        def add_chat_ui(chat_data=None):
            if chat_data is None:
                chat_data = {
                    "chat_id": "",
                    "last_read_message_id": 0,
                    "ids_to_retry": [],
                }
            with chats_container:
                with ui.element("div").classes("chat-card") as chat_card:
                    c_inputs = {}
                    c_inputs["card"] = chat_card
                    c_inputs["ids_to_retry"] = chat_data.get("ids_to_retry", [])

                    with ui.row().style("gap: 12px; width: 100%; align-items: center;"):
                        c_inputs["chat_id"] = (
                            ui.input(
                                "Chat ID / Username",
                                value=str(chat_data.get("chat_id", "")),
                            )
                            .classes("col")
                            .props("outlined dense")
                        )
                        c_inputs["last_read"] = (
                            ui.number(
                                "Last Read Msg ID",
                                value=chat_data.get("last_read_message_id", 0),
                                format="%.0f",
                            )
                            .style("max-width: 180px;")
                            .props("outlined dense")
                        )

                        def remove_me(card=chat_card, inputs=c_inputs):
                            chats_container.remove(card)
                            chat_inputs.remove(inputs)

                        ui.button(icon="close", on_click=remove_me).props(
                            "flat dense round size=sm color=grey"
                        )

                    with ui.expansion("Advanced Overrides", icon="tune").props(
                        "dense"
                    ).style("margin-top: 8px; font-size: 13px;"):
                        with ui.row().style(
                            "gap: 12px; width: 100%; padding-top: 8px;"
                        ):
                            c_inputs["download_dir"] = (
                                ui.input(
                                    "Override Directory",
                                    value=chat_data.get("download_directory", ""),
                                )
                                .classes("col")
                                .props("outlined dense")
                            )
                            _c_media = chat_data.get("media_types", [])
                            c_inputs["media_types"] = (
                                ui.select(
                                    options=[
                                        "photo",
                                        "video",
                                        "document",
                                        "audio",
                                        "voice",
                                        "video_note",
                                    ],
                                    value=_c_media,
                                    multiple=True,
                                    label="Override Media Types",
                                )
                                .classes("col")
                                .props("outlined dense use-chips")
                            )
                    chat_inputs.append(c_inputs)

        # Init existing chats
        existing_chats = config.get("chats", [])
        if not existing_chats and "chat_id" in config:
            existing_chats = [
                {
                    "chat_id": config.get("chat_id"),
                    "last_read_message_id": config.get("last_read_message_id", 0),
                }
            ]
        if not existing_chats:
            add_chat_ui()
        else:
            for c in existing_chats:
                add_chat_ui(c)

        ui.button("Add Chat", on_click=lambda: add_chat_ui(), icon="add").props(
            "flat dense color=primary"
        ).style("margin-top: 8px; font-size: 13px;")

    # ── Save / Reload Actions ──
    def do_save():
        try:
            config["api_id"] = (
                int(global_inputs["api_id"].value)
                if global_inputs["api_id"].value
                else None
            )
        except ValueError:
            config["api_id"] = None
        config["api_hash"] = global_inputs["api_hash"].value or ""
        config["parallel_chats"] = global_inputs["parallel_chats"].value
        if global_inputs["download_dir"].value.strip():
            config["download_directory"] = global_inputs["download_dir"].value.strip()
        elif "download_directory" in config:
            del config["download_directory"]
        config["max_concurrent_downloads"] = (
            int(global_inputs["max_concurrent"].value)
            if global_inputs["max_concurrent"].value
            else 4
        )
        delay_str = global_inputs["download_delay"].value.strip()
        if delay_str:
            if "," in delay_str:
                parts = [
                    int(x.strip()) for x in delay_str.split(",") if x.strip().isdigit()
                ]
                if len(parts) == 2:
                    config["download_delay"] = parts
            elif delay_str.isdigit():
                config["download_delay"] = int(delay_str)
        elif "download_delay" in config:
            del config["download_delay"]
        config["media_types"] = global_inputs["media_types"].value

        built_chats = []
        for c_in in chat_inputs:
            chat_val = c_in["chat_id"].value.strip()
            if not chat_val:
                continue
            try:
                chat_val = int(chat_val)
            except ValueError:
                pass
            chat_obj = {
                "chat_id": chat_val,
                "last_read_message_id": (
                    int(c_in["last_read"].value) if c_in["last_read"].value else 0
                ),
                "ids_to_retry": c_in["ids_to_retry"],
            }
            if c_in["download_dir"].value.strip():
                chat_obj["download_directory"] = c_in["download_dir"].value.strip()
            if c_in["media_types"].value:
                chat_obj["media_types"] = c_in["media_types"].value
            built_chats.append(chat_obj)
        config["chats"] = built_chats

        if "chat_id" in config:
            del config["chat_id"]
        if "last_read_message_id" in config:
            del config["last_read_message_id"]
        if "file_formats" not in config:
            config["file_formats"] = {
                "audio": ["all"],
                "document": ["all"],
                "video": ["all"],
            }

        save_config_fn(config)
        ui.notify(
            "Configuration saved!",
            type="positive",
            position="top",
            icon="check_circle",
        )

    with ui.row().style("gap: 12px; justify-content: flex-end; width: 100%;"):
        ui.button(
            "Reload from Disk",
            on_click=lambda: ui.navigate.to("/"),
            icon="refresh",
        ).props("flat color=grey-7").style("font-size: 13px;")
        ui.button("Save Configuration", on_click=do_save, icon="check").props(
            "unelevated color=primary"
        ).style("font-size: 13px; padding: 8px 24px;")

    return global_inputs, chat_inputs
