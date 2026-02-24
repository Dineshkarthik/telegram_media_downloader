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
            global_inputs["start_date"] = (
                ui.input("Start Date", value=config.get("start_date", ""))
                .classes("col")
                .props('outlined dense hint="YYYY-MM-DDTHH:MM:SS+00:00"')
            )
            global_inputs["end_date"] = (
                ui.input("End Date", value=config.get("end_date", ""))
                .classes("col")
                .props('outlined dense hint="YYYY-MM-DDTHH:MM:SS+00:00"')
            )
            global_inputs["max_messages"] = (
                ui.number(
                    "Max Messages",
                    value=config.get("max_messages", None),
                    format="%.0f",
                )
                .classes("col")
                .props("outlined dense")
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

        with ui.expansion("File Formats (Comma-separated)", icon="folder_zip").props(
            "dense"
        ).style("width: 100%; font-size: 13px; margin-top: 8px;"):
            with ui.row().style("gap: 16px; width: 100%; padding-top: 8px;"):
                file_formats = config.get("file_formats", {})
                global_inputs["format_audio"] = (
                    ui.input(
                        "Audio Formats",
                        value=",".join(file_formats.get("audio", ["all"])),
                    )
                    .classes("col")
                    .props('outlined dense hint="e.g. mp3,flac or all"')
                )
                global_inputs["format_video"] = (
                    ui.input(
                        "Video Formats",
                        value=",".join(file_formats.get("video", ["all"])),
                    )
                    .classes("col")
                    .props('outlined dense hint="e.g. mp4,mkv or all"')
                )
                global_inputs["format_photo"] = (
                    ui.input(
                        "Photo Formats",
                        value=",".join(file_formats.get("photo", ["all"])),
                    )
                    .classes("col")
                    .props('outlined dense hint="e.g. jpg,png or all"')
                )
                global_inputs["format_document"] = (
                    ui.input(
                        "Document Formats",
                        value=",".join(file_formats.get("document", ["all"])),
                    )
                    .classes("col")
                    .props('outlined dense hint="e.g. pdf,epub or all"')
                )

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
                        with ui.column().style(
                            "gap: 16px; padding: 12px; background: rgba(0,0,0,0.02); border-radius: 8px; border: 1px solid var(--border-color); margin-top: 8px; width: 100%;"
                        ):
                            # General & Pacing
                            with ui.column().style("gap: 4px; width: 100%;"):
                                ui.label("General & Pacing Limits").style(
                                    "font-size: 11px; font-weight: 600; color: var(--text-tertiary); text-transform: uppercase; letter-spacing: 0.05em;"
                                )
                                with ui.row().style("gap: 12px; width: 100%;"):
                                    c_inputs["download_dir"] = (
                                        ui.input(
                                            "Override Directory",
                                            value=chat_data.get(
                                                "download_directory", ""
                                            ),
                                        )
                                        .classes("col")
                                        .props("outlined dense")
                                    )
                                    c_inputs["max_concurrent"] = (
                                        ui.number(
                                            "Concurrent",
                                            value=chat_data.get(
                                                "max_concurrent_downloads", None
                                            ),
                                            format="%.0f",
                                        )
                                        .classes("col")
                                        .props('outlined dense hint="Max concurrent"')
                                    )
                                    c_delay_val = chat_data.get("download_delay")
                                    if isinstance(c_delay_val, list):
                                        c_delay_str = (
                                            f"{c_delay_val[0]}, {c_delay_val[1]}"
                                        )
                                    else:
                                        c_delay_str = (
                                            str(c_delay_val)
                                            if c_delay_val is not None
                                            else ""
                                        )
                                    c_inputs["download_delay"] = (
                                        ui.input("Delay (sec)", value=c_delay_str)
                                        .classes("col")
                                        .props('outlined dense hint="e.g. 2 or 1,5"')
                                    )

                            ui.separator().style("opacity: 0.5")

                            # Message Filters
                            with ui.column().style("gap: 4px; width: 100%;"):
                                ui.label("Message Filters").style(
                                    "font-size: 11px; font-weight: 600; color: var(--text-tertiary); text-transform: uppercase; letter-spacing: 0.05em;"
                                )
                                with ui.row().style("gap: 12px; width: 100%;"):
                                    c_inputs["start_date"] = (
                                        ui.input(
                                            "Override Start Date",
                                            value=chat_data.get("start_date", ""),
                                        )
                                        .classes("col")
                                        .props("outlined dense")
                                    )
                                    c_inputs["end_date"] = (
                                        ui.input(
                                            "Override End Date",
                                            value=chat_data.get("end_date", ""),
                                        )
                                        .classes("col")
                                        .props("outlined dense")
                                    )
                                    c_inputs["max_messages"] = (
                                        ui.number(
                                            "Override Max Messages",
                                            value=chat_data.get("max_messages", None),
                                            format="%.0f",
                                        )
                                        .classes("col")
                                        .props("outlined dense")
                                    )

                            ui.separator().style("opacity: 0.5")

                            # Media & Formats
                            with ui.column().style("gap: 4px; width: 100%;"):
                                ui.label("Media Types & Formats").style(
                                    "font-size: 11px; font-weight: 600; color: var(--text-tertiary); text-transform: uppercase; letter-spacing: 0.05em;"
                                )
                                with ui.row().style(
                                    "gap: 12px; width: 100%; align-items: start;"
                                ):
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

                                    c_formats = chat_data.get("file_formats", {})
                                    with ui.column().classes("col").style("gap: 4px;"):
                                        ui.label("Override Formats:").style(
                                            "font-size: 11px; color: var(--text-tertiary); margin-left: 4px; margin-bottom: -6px;"
                                        )
                                        with ui.row().style("gap: 8px; width: 100%;"):
                                            c_inputs["format_audio"] = (
                                                ui.input(
                                                    "Override Audio",
                                                    value=",".join(
                                                        c_formats.get("audio", [])
                                                    ),
                                                )
                                                .classes("col")
                                                .props(
                                                    'outlined dense placeholder="all"'
                                                )
                                            )
                                            c_inputs["format_video"] = (
                                                ui.input(
                                                    "Override Video",
                                                    value=",".join(
                                                        c_formats.get("video", [])
                                                    ),
                                                )
                                                .classes("col")
                                                .props(
                                                    'outlined dense placeholder="all"'
                                                )
                                            )
                                        with ui.row().style(
                                            "gap: 8px; width: 100%; align-items: start; margin-top: 4px;"
                                        ):
                                            c_inputs["format_photo"] = (
                                                ui.input(
                                                    "Override Photo",
                                                    value=",".join(
                                                        c_formats.get("photo", [])
                                                    ),
                                                )
                                                .classes("col")
                                                .props(
                                                    'outlined dense placeholder="all"'
                                                )
                                            )
                                            c_inputs["format_document"] = (
                                                ui.input(
                                                    "Override Doc",
                                                    value=",".join(
                                                        c_formats.get("document", [])
                                                    ),
                                                )
                                                .classes("col")
                                                .props(
                                                    'outlined dense placeholder="all"'
                                                )
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

        if global_inputs["start_date"].value.strip():
            config["start_date"] = global_inputs["start_date"].value.strip()
        elif "start_date" in config:
            del config["start_date"]

        if global_inputs["end_date"].value.strip():
            config["end_date"] = global_inputs["end_date"].value.strip()
        elif "end_date" in config:
            del config["end_date"]

        if global_inputs["max_messages"].value is not None:
            config["max_messages"] = int(global_inputs["max_messages"].value)
        elif "max_messages" in config:
            del config["max_messages"]

        # File Formats
        config["file_formats"] = {
            "audio": [
                x.strip()
                for x in global_inputs["format_audio"].value.split(",")
                if x.strip()
            ]
            or ["all"],
            "video": [
                x.strip()
                for x in global_inputs["format_video"].value.split(",")
                if x.strip()
            ]
            or ["all"],
            "photo": [
                x.strip()
                for x in global_inputs["format_photo"].value.split(",")
                if x.strip()
            ]
            or ["all"],
            "document": [
                x.strip()
                for x in global_inputs["format_document"].value.split(",")
                if x.strip()
            ]
            or ["all"],
        }

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

            if c_in["max_concurrent"].value is not None:
                chat_obj["max_concurrent_downloads"] = int(c_in["max_concurrent"].value)

            c_delay_str = c_in["download_delay"].value.strip()
            if c_delay_str:
                if "," in c_delay_str:
                    c_delay_parts = [
                        int(x.strip())
                        for x in c_delay_str.split(",")
                        if x.strip().isdigit()
                    ]
                    if len(c_delay_parts) == 2:
                        chat_obj["download_delay"] = c_delay_parts
                elif c_delay_str.isdigit():
                    chat_obj["download_delay"] = int(c_delay_str)

            if c_in["start_date"].value.strip():
                chat_obj["start_date"] = c_in["start_date"].value.strip()
            if c_in["end_date"].value.strip():
                chat_obj["end_date"] = c_in["end_date"].value.strip()
            if c_in["max_messages"].value is not None:
                chat_obj["max_messages"] = int(c_in["max_messages"].value)

            # Chat-specific file_formats
            chat_formats = {}
            if c_in["format_audio"].value.strip():
                chat_formats["audio"] = [
                    x.strip()
                    for x in c_in["format_audio"].value.split(",")
                    if x.strip()
                ]
            if c_in["format_video"].value.strip():
                chat_formats["video"] = [
                    x.strip()
                    for x in c_in["format_video"].value.split(",")
                    if x.strip()
                ]
            if c_in["format_photo"].value.strip():
                chat_formats["photo"] = [
                    x.strip()
                    for x in c_in["format_photo"].value.split(",")
                    if x.strip()
                ]
            if c_in["format_document"].value.strip():
                chat_formats["document"] = [
                    x.strip()
                    for x in c_in["format_document"].value.split(",")
                    if x.strip()
                ]
            if chat_formats:
                chat_obj["file_formats"] = chat_formats

            built_chats.append(chat_obj)
        config["chats"] = built_chats

        if "chat_id" in config:
            del config["chat_id"]
        if "last_read_message_id" in config:
            del config["last_read_message_id"]

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
