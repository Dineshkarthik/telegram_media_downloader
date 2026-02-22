"""Downloads media from telegram."""

import asyncio
import logging
import os
import random
import re
from datetime import date, datetime, timezone
from typing import List, Optional, Tuple, Union

import yaml
from rich.logging import RichHandler
from telethon import TelegramClient
from telethon.errors import FileReferenceExpiredError
from telethon.tl.types import (
    Document,
    Message,
    MessageMediaDocument,
    MessageMediaPhoto,
    Photo,
)
from tqdm import tqdm

from utils.file_management import get_next_name, manage_duplicate_file
from utils.log import LogFilter
from utils.meta import APP_VERSION, DEVICE_MODEL, LANG_CODE, SYSTEM_VERSION, print_meta
from utils.updates import check_for_updates

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler()],
)
logging.getLogger("telethon.client.downloads").addFilter(LogFilter())
logging.getLogger("telethon.network").addFilter(LogFilter())
logger = logging.getLogger("media_downloader")

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
FAILED_IDS: dict = {}
DOWNLOADED_IDS: dict = {}
PROCESSED_IDS: dict = {}
CURRENT_BATCH_IDS: dict = {}


def update_config(config: dict):
    """
    Update existing configuration file.

    Parameters
    ----------
    config: dict
        Configuration to be written into config file.
    """
    chats_config = config.get("chats", [])
    if chats_config:
        for chat_conf in chats_config:
            chat_id = chat_conf.get("chat_id")
            if chat_id and chat_id in DOWNLOADED_IDS and chat_id in FAILED_IDS:
                chat_conf["ids_to_retry"] = (
                    list(
                        set(chat_conf.get("ids_to_retry", []))
                        - set(DOWNLOADED_IDS[chat_id])
                    )
                    + FAILED_IDS[chat_id]
                )
    else:
        chat_id = config.get("chat_id")
        if chat_id and chat_id in DOWNLOADED_IDS and chat_id in FAILED_IDS:
            config["ids_to_retry"] = (
                list(set(config.get("ids_to_retry", [])) - set(DOWNLOADED_IDS[chat_id]))
                + FAILED_IDS[chat_id]
            )

    with open("config.yaml", "w") as yaml_file:
        yaml.dump(config, yaml_file, sort_keys=False, default_flow_style=False)
    logger.info("Updated last read message_id to config file")


def _can_download(_type: str, file_formats: dict, file_format: Optional[str]) -> bool:
    """
    Check if the given file format can be downloaded.

    Parameters
    ----------
    _type: str
        Type of media object.
    file_formats: dict
        Dictionary containing the list of file_formats
        to be downloaded for `audio`, `document` & `video`
        media types
    file_format: str
        Format of the current file to be downloaded.

    Returns
    -------
    bool
        True if the file format can be downloaded else False.
    """
    if _type in ["audio", "document", "video"]:
        allowed_formats: list = file_formats[_type]
        if not file_format in allowed_formats and allowed_formats[0] != "all":
            return False
    return True


def _is_exist(file_path: str) -> bool:
    """
    Check if a file exists and it is not a directory.

    Parameters
    ----------
    file_path: str
        Absolute path of the file to be checked.

    Returns
    -------
    bool
        True if the file exists else False.
    """
    return not os.path.isdir(file_path) and os.path.exists(file_path)


def _progress_callback(current: int, total: int, pbar: tqdm) -> None:
    """
    Update progress bar for file downloads.

    Parameters
    ----------
    current: int
        Current number of bytes downloaded.
    total: int
        Total number of bytes to download.
    pbar: tqdm
        Progress bar instance to update.
    """
    if pbar.total != total:
        pbar.total = total
        pbar.reset()
    pbar.update(current - pbar.n)


async def _get_media_meta(
    media_obj: Union[Document, Photo],
    _type: str,
    chat_id: Union[int, str],
    download_directory: Optional[str] = None,
) -> Tuple[str, Optional[str]]:
    """Extract file name and file id from media object.

    Parameters
    ----------
    media_obj: Union[Document, Photo]
        Media object to be extracted.
    _type: str
        Type of media object.
    chat_id: Union[int, str]
        ID of the chat, used for folder structuring.
    download_directory: Optional[str]
        Custom directory path for downloads. If None, uses default structure.

    Returns
    -------
    Tuple[str, Optional[str]]
        file_name, file_format
    """
    file_format: Optional[str] = None
    if hasattr(media_obj, "mime_type") and media_obj.mime_type:
        file_format = media_obj.mime_type.split("/")[-1]
    elif _type == "photo":
        file_format = "jpg"

    # Determine base directory for downloads
    if download_directory:
        base_dir = download_directory
    else:
        base_dir = os.path.join(THIS_DIR, str(chat_id))

    if _type in ["voice", "video_note"]:
        file_name_base = f"{_type}_{media_obj.date.isoformat()}.{file_format}"
    else:
        file_name_base = ""
        if hasattr(media_obj, "attributes"):
            for attr in media_obj.attributes:
                if hasattr(attr, "file_name"):
                    file_name_base = attr.file_name
                    break
        if file_name_base == "":
            if hasattr(media_obj, "id"):
                file_name_base = f"{_type}_{media_obj.id}"

    # Sanitize the file name to remove invalid Windows characters
    file_name_base = re.sub(r'[<>:"/\\|?*]', "_", file_name_base)
    file_name = os.path.join(base_dir, _type, file_name_base)
    return file_name, file_format


def get_media_type(message: Message) -> Optional[str]:
    """
    Determine the media type from the message's media attributes.

    Parameters
    ----------
    message: Message
        The Telethon message object.

    Returns
    -------
    Optional[str]
        The media type ('photo', 'video', 'audio', 'voice', 'video_note', 'document')
        or None.
    """
    if not message.media:
        return None
    if isinstance(message.media, MessageMediaPhoto):
        return "photo"
    if isinstance(message.media, MessageMediaDocument):
        doc = message.media.document
        for attr in doc.attributes:
            if hasattr(attr, "voice") and isinstance(attr.voice, bool):
                return "voice" if attr.voice else "audio"
            if hasattr(attr, "round_message") and isinstance(attr.round_message, bool):
                return "video_note" if attr.round_message else "video"
        return "document"
    return None


async def download_media(  # pylint: disable=too-many-locals,too-many-branches,too-many-positional-arguments,too-many-statements
    client: TelegramClient,
    message: Message,
    media_types: List[str],
    file_formats: dict,
    chat_id: Union[int, str],
    download_directory: Optional[str] = None,
):
    """
    Download media from Telegram.

    Each of the files to download are retried 3 times with a
    delay of 5 seconds each.

    Parameters
    ----------
    client: TelegramClient
        Client to interact with Telegram APIs.
    message: Message
        Message object retrieved from telegram.
    media_types: list
        List of strings of media types to be downloaded.
        Ex : ["audio", "photo"]
    file_formats: dict
        Dictionary containing the list of file_formats
        to be downloaded.
    chat_id: Union[int, str]
        ID of the chat being processed.
    download_directory: Optional[str]
        Custom directory path for downloads. If None, uses default structure.

    Returns
    -------
    int
        Current message id.
    """
    for retry in range(3):
        if chat_id not in FAILED_IDS:
            FAILED_IDS[chat_id] = []
        if chat_id not in DOWNLOADED_IDS:
            DOWNLOADED_IDS[chat_id] = []
        if chat_id not in PROCESSED_IDS:
            PROCESSED_IDS[chat_id] = []
        try:
            _type = get_media_type(message)
            logger.debug("Processing message %s of type %s", message.id, _type)
            if not _type or _type not in media_types:
                PROCESSED_IDS[chat_id].append(message.id)
                return message.id
            media_obj = message.photo if _type == "photo" else message.document
            if not media_obj:
                PROCESSED_IDS[chat_id].append(message.id)
                return message.id
            file_name, file_format = await _get_media_meta(
                media_obj, _type, chat_id, download_directory
            )
            if _can_download(_type, file_formats, file_format):
                file_size = getattr(media_obj, "size", 0)
                display_name = getattr(
                    media_obj, "file_name", os.path.basename(file_name)
                )
                desc = f"Downloading {display_name}"
                logger.info(desc)

                if _is_exist(file_name):
                    file_name = get_next_name(file_name)
                    with tqdm(
                        total=file_size, unit="B", unit_scale=True, desc=desc
                    ) as pbar:
                        download_path = await client.download_media(
                            message,
                            file=file_name,
                            progress_callback=lambda c, t, pbar=pbar: _progress_callback(
                                c, t, pbar
                            ),
                        )
                        download_path = manage_duplicate_file(
                            download_path
                        )  # type: ignore
                else:
                    with tqdm(
                        total=file_size, unit="B", unit_scale=True, desc=desc
                    ) as pbar:
                        download_path = await client.download_media(
                            message,
                            file=file_name,
                            progress_callback=lambda c, t, pbar=pbar: _progress_callback(
                                c, t, pbar
                            ),
                        )
                if download_path:
                    logger.info("Media downloaded - %s", download_path)
                    logger.debug("Successfully downloaded message %s", message.id)
                DOWNLOADED_IDS[chat_id].append(message.id)

            PROCESSED_IDS[chat_id].append(message.id)
            break
        except FileReferenceExpiredError:
            logger.warning(
                "Message[%d]: file reference expired, refetching...", message.id
            )
            messages = await client.get_messages(message.chat.id, ids=message.id)
            message = messages[0] if messages else message
            if retry == 2:
                logger.error(
                    "Message[%d]: file reference expired, skipping download.",
                    message.id,
                )
                FAILED_IDS[chat_id].append(message.id)
        except TimeoutError:
            logger.warning(
                "Timeout Error occurred when downloading Message[%d], "
                "retrying after 5 seconds",
                message.id,
            )
            await asyncio.sleep(5)
            if retry == 2:
                logger.error(
                    "Message[%d]: Timing out after 3 retries, download skipped.",
                    message.id,
                )
                FAILED_IDS[chat_id].append(message.id)
        except Exception as e:
            logger.error(
                "Message[%d]: could not be downloaded due to following "
                "exception:\n[%s].",
                message.id,
                e,
                exc_info=True,
            )
            FAILED_IDS[chat_id].append(message.id)
            break
    return message.id


async def process_messages(  # pylint: disable=too-many-positional-arguments
    client: TelegramClient,
    messages: List[Message],
    media_types: List[str],
    file_formats: dict,
    chat_id: Union[int, str],
    download_directory: Optional[str] = None,
    max_concurrent_downloads: int = 4,
    download_delay: Optional[Union[float, List[float]]] = None,
) -> int:
    """
    Download media from Telegram.

    Parameters
    ----------
    client: TelegramClient
        Client to interact with Telegram APIs.
    messages: list
        List of telegram messages.
    media_types: list
        List of strings of media types to be downloaded.
    file_formats: dict
        Dictionary containing the list of file_formats
        to be downloaded.
    chat_id: Union[int, str]
        ID of the chat.
    download_directory: Optional[str]
        Custom directory path for downloads. If None, uses default structure.
    max_concurrent_downloads: int
        Max number of files to download simultaneously. 1 = fully sequential.
        Default 4. Higher values speed up downloads but increase ban risk.
    download_delay: Optional[Union[float, List[float]]]
        Delay between starting each file download (seconds).
        Pass a float for a fixed delay, or [min, max] for a random range.
        None means no delay.

    Returns
    -------
    int
        Max value of list of message ids.
    """
    semaphore = asyncio.Semaphore(max(1, max_concurrent_downloads))

    async def _download_with_limit(message: Message) -> int:
        async with semaphore:
            if download_delay is not None:
                delay: Optional[float] = None
                if isinstance(download_delay, (list, tuple)):
                    if len(download_delay) != 2:
                        logger.warning(
                            "download_delay list must have exactly 2 elements "
                            "[min, max]; got %r. Skipping delay.",
                            download_delay,
                        )
                    else:
                        try:
                            lo, hi = float(download_delay[0]), float(download_delay[1])
                            delay = max(0.0, random.uniform(lo, hi))
                        except (TypeError, ValueError):
                            logger.warning(
                                "download_delay list %r contains non-numeric values; "
                                "skipping delay.",
                                download_delay,
                            )
                else:
                    try:
                        delay = max(0.0, float(download_delay))  # type: ignore[arg-type]
                    except (TypeError, ValueError):
                        logger.warning(
                            "Invalid download_delay value %r; skipping delay.",
                            download_delay,
                        )
                if delay is not None:
                    await asyncio.sleep(delay)
            return int(
                await download_media(
                    client,
                    message,
                    media_types,
                    file_formats,
                    chat_id,
                    download_directory,
                )
            )

    message_ids = await asyncio.gather(
        *[_download_with_limit(message) for message in messages]
    )
    logger.info("Processed batch of %d messages for chat %s", len(messages), chat_id)
    last_message_id: int = max(message_ids)
    return last_message_id


async def process_chat(  # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    client: TelegramClient,
    global_config: dict,
    chat_conf: dict,
    pagination_limit: int,
    config_write_lock: asyncio.Lock,
):
    """
    Process a single chat's media downloads.
    """
    chat_id = chat_conf["chat_id"]
    logger.info("Starting processing for chat_id: %s", chat_id)

    # Initialize state maps for this chat
    if chat_id not in FAILED_IDS:
        FAILED_IDS[chat_id] = []
    if chat_id not in DOWNLOADED_IDS:
        DOWNLOADED_IDS[chat_id] = []
    if chat_id not in PROCESSED_IDS:
        PROCESSED_IDS[chat_id] = []

    CURRENT_BATCH_IDS[chat_id] = []

    # Merge chat-specific config with global fallback
    media_types: List[str] = chat_conf.get(
        "media_types", global_config.get("media_types", [])
    )
    file_formats: dict = chat_conf.get(
        "file_formats", global_config.get("file_formats", {})
    )
    last_read_message_id = chat_conf.get(
        "last_read_message_id", global_config.get("last_read_message_id", 0)
    )
    _max_concurrent_raw = chat_conf.get(
        "max_concurrent_downloads", global_config.get("max_concurrent_downloads", 4)
    )
    try:
        max_concurrent_downloads = int(_max_concurrent_raw)  # type: ignore[arg-type]
        if max_concurrent_downloads <= 0:
            raise ValueError("must be a positive integer")
    except (TypeError, ValueError):
        logger.warning(
            "Invalid max_concurrent_downloads value %r; defaulting to 4.",
            _max_concurrent_raw,
        )
        max_concurrent_downloads = 4
    download_delay = chat_conf.get(
        "download_delay", global_config.get("download_delay")
    )

    start_date_val = chat_conf.get("start_date", global_config.get("start_date"))
    if isinstance(start_date_val, str) and start_date_val.strip():
        start_date = datetime.fromisoformat(start_date_val)
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=timezone.utc)
    elif isinstance(start_date_val, date):
        start_date = datetime.combine(
            start_date_val, datetime.min.time(), tzinfo=timezone.utc
        )
    else:
        start_date = None

    end_date_val = chat_conf.get("end_date", global_config.get("end_date"))
    if isinstance(end_date_val, str) and end_date_val.strip():
        end_date = datetime.fromisoformat(end_date_val)
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)
    elif isinstance(end_date_val, date):
        end_date = datetime.combine(
            end_date_val, datetime.min.time(), tzinfo=timezone.utc
        )
    else:
        end_date = None

    max_messages_val = chat_conf.get("max_messages", global_config.get("max_messages"))
    if isinstance(max_messages_val, int):
        max_messages = max_messages_val
    elif isinstance(max_messages_val, str) and max_messages_val.strip():
        max_messages = int(max_messages_val)
    else:
        max_messages = None

    download_directory_val = chat_conf.get(
        "download_directory", global_config.get("download_directory")
    )
    if isinstance(download_directory_val, str) and download_directory_val.strip():
        download_directory = download_directory_val.strip()
        if not os.path.isabs(download_directory):
            download_directory = os.path.abspath(download_directory)
        os.makedirs(download_directory, exist_ok=True)
    else:
        download_directory = None

    messages_iter = client.iter_messages(
        chat_id, min_id=last_read_message_id, reverse=True
    )
    messages_list: list = []
    pagination_count: int = 0
    ids_to_retry = chat_conf.get("ids_to_retry", global_config.get("ids_to_retry", []))

    if ids_to_retry:
        logger.info("Downloading files failed during last run for chat %s...", chat_id)
        skipped_messages: list = await client.get_messages(  # type: ignore
            chat_id, ids=ids_to_retry
        )
        for message in skipped_messages:
            pagination_count += 1
            messages_list.append(message)

    async for message in messages_iter:  # type: ignore
        if end_date and message.date > end_date:
            continue
        if start_date and message.date < start_date:
            break
        if pagination_count != pagination_limit:
            pagination_count += 1
            messages_list.append(message)
        else:
            CURRENT_BATCH_IDS[chat_id] = [m.id for m in messages_list]
            last_read_message_id = await process_messages(
                client,
                messages_list,
                media_types,
                file_formats,
                chat_id,
                download_directory,
                max_concurrent_downloads,
                download_delay,
            )
            # Memory cleanup for next batch
            CURRENT_BATCH_IDS[chat_id] = []
            PROCESSED_IDS[chat_id] = []

            if max_messages and len(DOWNLOADED_IDS[chat_id]) >= max_messages:
                break
            pagination_count = 0
            messages_list = []
            messages_list.append(message)
            chat_conf["last_read_message_id"] = last_read_message_id

            # Checkpoint: persist progress to disk after every batch so that
            # crashes or network failures don't lose progress.
            async with config_write_lock:
                update_config(global_config)

    if messages_list:
        CURRENT_BATCH_IDS[chat_id] = [m.id for m in messages_list]
        last_read_message_id = await process_messages(
            client,
            messages_list,
            media_types,
            file_formats,
            chat_id,
            download_directory,
            max_concurrent_downloads,
            download_delay,
        )
        CURRENT_BATCH_IDS[chat_id] = []
        PROCESSED_IDS[chat_id] = []

    chat_conf["last_read_message_id"] = last_read_message_id
    # Final checkpoint for this chat
    async with config_write_lock:
        update_config(global_config)


async def begin_import(  # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    config: dict, pagination_limit: int
) -> dict:
    """
    Create telethon client and initiate download.

    Parameters
    ----------
    config: dict
        Dict containing the config to create telethon client.
    pagination_limit: int
        Number of message to download asynchronously as a batch.

    Returns
    -------
    dict
        Updated configuration to be written into config file.
    """
    proxy = config.get("proxy")
    proxy_dict = None
    if proxy:
        proxy_dict = {
            "proxy_type": proxy["scheme"],
            "addr": proxy["hostname"],
            "port": proxy["port"],
            "username": proxy.get("username"),
            "password": proxy.get("password"),
        }
    client = TelegramClient(
        "media_downloader",
        api_id=config["api_id"],
        api_hash=config["api_hash"],
        proxy=proxy_dict,
        device_model=DEVICE_MODEL,
        system_version=SYSTEM_VERSION,
        app_version=APP_VERSION,
        lang_code=LANG_CODE,
    )
    await client.start()

    # Extract chats format configuration
    chats_config = config.get("chats", [])
    if not chats_config:
        # Backward compatibility for legacy config format
        logger.info("Using legacy single-chat configuration format.")
        if "chat_id" not in config:
            raise KeyError(
                "chat_id must be specified either in a chats list or globally."
            )

        # In legacy mode, processing directly on the global config might be safer, but
        # using the process_chat flow is strictly better for logic reuse.
        chats_to_process = [config]
    else:
        chats_to_process = chats_config

    parallel_chats = config.get("parallel_chats", False)
    config_write_lock = asyncio.Lock()

    if parallel_chats:
        logger.info("Processing chats in parallel...")
        tasks = [
            process_chat(client, config, chat_conf, pagination_limit, config_write_lock)
            for chat_conf in chats_to_process
        ]
        await asyncio.gather(*tasks)
    else:
        logger.info("Processing chats sequentially...")
        for chat_conf in chats_to_process:
            await process_chat(
                client, config, chat_conf, pagination_limit, config_write_lock
            )

    await client.disconnect()
    return config


def main():
    """Main function of the downloader."""
    with open(os.path.join(THIS_DIR, "config.yaml")) as f:
        config = yaml.safe_load(f)

    updated_config = config
    try:
        updated_config = asyncio.get_event_loop().run_until_complete(
            begin_import(config, pagination_limit=100)
        )
    except KeyboardInterrupt:
        logger.warning(
            "KeyboardInterrupt received. Gentle exit triggered! "
            "Saving the last read message IDs and exiting..."
        )

        # Accurately calculate the safe resumption point for each chat
        chats_config = updated_config.get("chats", [])
        if not chats_config:
            chats_to_process = [updated_config]
        else:
            chats_to_process = chats_config

        for chat_conf in chats_to_process:
            chat_id = chat_conf.get("chat_id")
            if chat_id and chat_id in CURRENT_BATCH_IDS:
                batch_ids = CURRENT_BATCH_IDS[chat_id]
                processed = PROCESSED_IDS.get(chat_id, [])
                unprocessed = [m_id for m_id in batch_ids if m_id not in processed]
                if unprocessed:
                    # Safe ID is just below the lowest unprocessed message.
                    # IDs between this boundary and min(unprocessed) that were
                    # already processed will be re-encountered on next run, but
                    # the file-existence check prevents actual re-downloads.
                    safe_id = min(unprocessed) - 1
                    chat_conf["last_read_message_id"] = max(0, safe_id)
                elif batch_ids:
                    # All messages in batch were processed: resume after the
                    # highest message so the next run starts beyond this batch.
                    chat_conf["last_read_message_id"] = max(batch_ids)

    total_failures = sum(len(set(fail_list)) for fail_list in FAILED_IDS.values())
    if total_failures > 0:
        logger.info(
            "Downloading of %d files failed. "
            "Failed message ids are added to config file.\n"
            "These files will be downloaded on the next run.",
            total_failures,
        )
    update_config(updated_config)
    check_for_updates()


if __name__ == "__main__":
    print_meta(logger)
    main()
