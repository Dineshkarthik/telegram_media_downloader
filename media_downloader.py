"""Downloads media from telegram."""

import asyncio
import logging
import os
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
FAILED_IDS: list = []
DOWNLOADED_IDS: list = []


def update_config(config: dict):
    """
    Update existing configuration file.

    Parameters
    ----------
    config: dict
        Configuration to be written into config file.
    """
    config["ids_to_retry"] = (
        list(set(config["ids_to_retry"]) - set(DOWNLOADED_IDS)) + FAILED_IDS
    )
    with open("config.yaml", "w") as yaml_file:
        yaml.dump(config, yaml_file, default_flow_style=False)
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


async def _get_media_meta(
    media_obj: Union[Document, Photo],
    _type: str,
) -> Tuple[str, Optional[str]]:
    """Extract file name and file id from media object.

    Parameters
    ----------
    media_obj: Union[Document, Photo]
        Media object to be extracted.
    _type: str
        Type of media object.

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

    if _type in ["voice", "video_note"]:
        file_name: str = os.path.join(
            THIS_DIR,
            _type,
            f"{_type}_{media_obj.date.isoformat()}.{file_format}",
        )
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
        file_name = os.path.join(THIS_DIR, _type, file_name_base)
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


async def download_media(
    client: TelegramClient,
    message: Message,
    media_types: List[str],
    file_formats: dict,
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
        Supported formats:
            * audio
            * document
            * photo
            * video
            * video_note
            * voice
    file_formats: dict
        Dictionary containing the list of file_formats
        to be downloaded for `audio`, `document` & `video`
        media types.

    Returns
    -------
    int
        Current message id.
    """
    for retry in range(3):
        try:
            _type = get_media_type(message)
            if not _type or _type not in media_types:
                return message.id
            media_obj = message.photo if _type == "photo" else message.document
            if not media_obj:
                return message.id
            file_name, file_format = await _get_media_meta(media_obj, _type)
            if _can_download(_type, file_formats, file_format):
                if _is_exist(file_name):
                    file_name = get_next_name(file_name)
                    download_path = await client.download_media(message, file=file_name)
                    download_path = manage_duplicate_file(download_path)  # type: ignore
                else:
                    download_path = await client.download_media(message, file=file_name)
                if download_path:
                    logger.info("Media downloaded - %s", download_path)
                DOWNLOADED_IDS.append(message.id)
            break
        except FileReferenceExpiredError:
            logger.warning(
                "Message[%d]: file reference expired, refetching...", message.id
            )
            messages = await client.get_messages(message.chat_id, ids=message.id)
            message = messages[0] if messages else message
            if retry == 2:
                logger.error(
                    "Message[%d]: file reference expired, skipping download.",
                    message.id,
                )
                FAILED_IDS.append(message.id)
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
                FAILED_IDS.append(message.id)
        except Exception as e:
            logger.error(
                "Message[%d]: could not be downloaded due to following "
                "exception:\n[%s].",
                message.id,
                e,
                exc_info=True,
            )
            FAILED_IDS.append(message.id)
            break
    return message.id


async def process_messages(
    client: TelegramClient,
    messages: List[Message],
    media_types: List[str],
    file_formats: dict,
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
        Ex : `["audio", "photo"]`
        Supported formats:
            * audio
            * document
            * photo
            * video
            * video_note
            * voice
    file_formats: dict
        Dictionary containing the list of file_formats
        to be downloaded for `audio`, `document` & `video`
        media types.

    Returns
    -------
    int
        Max value of list of message ids.
    """
    message_ids = await asyncio.gather(
        *[
            download_media(client, message, media_types, file_formats)
            for message in messages
        ]
    )

    last_message_id: int = max(message_ids)
    return last_message_id


async def begin_import(config: dict, pagination_limit: int) -> dict:
    """
    Create telethon client and initiate download.

    The telethon client is created using the ``api_id``, ``api_hash``
    from the config and iter through message offset on the
    ``last_message_id`` and the requested file_formats.

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
    last_read_message_id: int = config["last_read_message_id"]
    messages_iter = client.iter_messages(
        config["chat_id"], min_id=last_read_message_id + 1, reverse=True
    )
    messages_list: list = []
    pagination_count: int = 0
    if config["ids_to_retry"]:
        logger.info("Downloading files failed during last run...")
        skipped_messages: list = await client.get_messages(  # type: ignore
            config["chat_id"], ids=config["ids_to_retry"]
        )
        for message in skipped_messages:
            pagination_count += 1
            messages_list.append(message)

    async for message in messages_iter:  # type: ignore
        if pagination_count != pagination_limit:
            pagination_count += 1
            messages_list.append(message)
        else:
            last_read_message_id = await process_messages(
                client,
                messages_list,
                config["media_types"],
                config["file_formats"],
            )
            pagination_count = 0
            messages_list = []
            messages_list.append(message)
            config["last_read_message_id"] = last_read_message_id
            update_config(config)
    if messages_list:
        last_read_message_id = await process_messages(
            client,
            messages_list,
            config["media_types"],
            config["file_formats"],
        )

    await client.disconnect()
    config["last_read_message_id"] = last_read_message_id
    return config


def main():
    """Main function of the downloader."""
    with open(os.path.join(THIS_DIR, "config.yaml")) as f:
        config = yaml.safe_load(f)
    updated_config = asyncio.get_event_loop().run_until_complete(
        begin_import(config, pagination_limit=100)
    )
    if FAILED_IDS:
        logger.info(
            "Downloading of %d files failed. "
            "Failed message ids are added to config file.\n"
            "These files will be downloaded on the next run.",
            len(set(FAILED_IDS)),
        )
    update_config(updated_config)
    check_for_updates()


if __name__ == "__main__":
    print_meta(logger)
    main()
