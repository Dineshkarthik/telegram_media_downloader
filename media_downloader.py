"""Downloads media from telegram."""
import os
import logging
import re
import sys
from typing import List, Tuple, Optional
from datetime import datetime as dt

import asyncio
import pyrogram
import yaml

from utils.file_management import get_next_name, manage_duplicate_file
from utils.log import LogFilter
from utils.meta import print_meta

logging.basicConfig(level=logging.INFO)
logging.getLogger("pyrogram.session.session").addFilter(LogFilter())
logging.getLogger("pyrogram.client").addFilter(LogFilter())
logger = logging.getLogger("media_downloader")
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(message)s"))
logger.addHandler(handler)

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
FAILED_IDS: list = []


def update_config(config: dict):
    """
    Update exisitng configuration file.

    Parameters
    ----------
    config: dict
        Configuraiton to be written into config file.
    """
    config["ids_to_retry"] = list(set(config["ids_to_retry"] + FAILED_IDS))
    with open("config.yaml", "w") as yaml_file:
        yaml.dump(config, yaml_file, default_flow_style=False)
    logger.info("Updated last read message_id to config file")


def _can_download(
        _type: str, file_formats: dict, file_format: Optional[str]
) -> bool:
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
        media_obj: pyrogram.types.messages_and_media, _type: str
) -> Tuple[str, Optional[str]]:
    """
    Extract file name and file id.

    Parameters
    ----------
    media_obj: pyrogram.types.messages_and_media
        Media object to be extracted.
    _type: str
        Type of media object.

    Returns
    -------
    tuple
        file_name, file_format
    """
    if _type in ["audio", "document", "video"]:
        file_format: Optional[str] = media_obj.mime_type.split("/")[-1]
    else:
        file_format = None

    if _type == "voice":
        file_format = media_obj.mime_type.split("/")[-1]
        file_name: str = os.path.join(
            THIS_DIR,
            _type,
            "voice_{}.{}".format(
                dt.utcfromtimestamp(media_obj.date).isoformat(), file_format
            ),
        )
    else:
        file_name = os.path.join(
            THIS_DIR, _type, getattr(media_obj, "file_name", None) or ""
        )
    return file_name, file_format


async def download_media(
        client: pyrogram.client.Client,
        message: pyrogram.types.Message,
        media_types: List[str],
        file_formats: dict,
):
    """
    Download media from Telegram.

    Each of the files to download are retried 3 times with a
    delay of 5 seconds each.

    Parameters
    ----------
    client: pyrogram.client.Client
        Client to interact with Telegram APIs.
    message: pyrogram.types.Message
        Message object retrived from telegram.
    media_types: list
        List of strings of media types to be downloaded.
        Ex : `["audio", "photo"]`
        Supported formats:
            * audio
            * document
            * photo
            * video
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
            logger.debug(message)
            if message.media is None:
                return message.message_id
            for _type in media_types:
                _media = getattr(message, _type, None)
                if _media is None:
                    continue
                file_name, file_format = await _get_media_meta(_media, _type)

                f_name = message.sender_chat.username + "_" + str(message.message_id) + "-"  # 文件名
                if message.forward_from_chat:  # 是转发的
                    f_name += message.forward_from_chat.username + "_" + str(message.forward_from_message_id) + "-"
                if message.video:
                    root, ext = os.path.splitext(message.video.file_name)
                    f_name += root
                if message.caption and message.caption != "":
                    caption = re.sub(r"\s", "_", message.caption)
                    # 只保留中文，字母，数字 [\u4e00-\u9fa5a-zA-Z0-9]+
                    f_name += "-" + re.sub(u"([^\u4e00-\u9fa5\u0030-\u0039\u0041-\u005a\u0061-\u007a])", "", caption)
                head, tail = os.path.split(file_name)  # 拆分路径
                file_name = os.path.join(head, f_name)  # 拼接路径
                logger.debug(file_name)

                if _can_download(_type, file_formats, file_format):
                    if _is_exist(file_name):
                        file_name = get_next_name(file_name)
                        download_path = await client.download_media(
                            message, file_name=file_name
                        )
                        download_path = manage_duplicate_file(download_path)
                    else:
                        download_path = await client.download_media(
                            message, file_name=file_name
                        )
                    if download_path:
                        logger.info("Media downloaded - %s", download_path)
            break
        except pyrogram.errors.exceptions.bad_request_400.BadRequest:
            logger.warning(
                "Message[%d]: file reference expired, refetching...",
                message.message_id,
            )
            message = await client.get_messages(
                chat_id=message.chat.id,
                message_ids=message.message_id,
            )
            if retry == 2:
                # pylint: disable = C0301
                logger.error(
                    "Message[%d]: file reference expired for 3 retries, download skipped.",
                    message.message_id,
                )
                FAILED_IDS.append(message.message_id)
        except TypeError:
            # pylint: disable = C0301
            logger.warning(
                "Timeout Error occured when downloading Message[%d], retrying after 5 seconds",
                message.message_id,
            )
            await asyncio.sleep(5)
            if retry == 2:
                logger.error(
                    "Message[%d]: Timing out after 3 reties, download skipped.",
                    message.message_id,
                )
                FAILED_IDS.append(message.message_id)
        except Exception as e:
            # pylint: disable = C0301
            logger.error(
                "Message[%d]: could not be downloaded due to following exception:\n[%s].",
                message.message_id,
                e,
                exc_info=True,
            )
            FAILED_IDS.append(message.message_id)
            break
    return message.message_id


async def process_messages(
        client: pyrogram.client.Client,
        messages: List[pyrogram.types.Message],
        media_types: List[str],
        file_formats: dict,
) -> int:
    """
    Download media from Telegram.

    Parameters
    ----------
    client: pyrogram.client.Client
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
    logger.debug(messages)
    message_ids = await asyncio.gather(
        *[
            download_media(client, message, media_types, file_formats)
            for message in messages
        ]
    )

    last_message_id = max(message_ids)
    return last_message_id


async def begin_import(config: dict, pagination_limit: int) -> dict:
    """
    Create pyrogram client and initiate download.

    The pyrogram client is created using the ``api_id``, ``api_hash``
    from the config and iter throught message offset on the
    ``last_message_id`` and the requested file_formats.

    Parameters
    ----------
    config: dict
        Dict containing the config to create pyrogram client.
    pagination_limit: int
        Number of message to download asynchronously as a batch.

    Returns
    -------
    dict
        Updated configuraiton to be written into config file.
    """
    client = pyrogram.Client(
        "media_downloader",
        api_id=config["api_id"],
        api_hash=config["api_hash"],
    )
    pyrogram.session.Session.notice_displayed = True
    await client.start()
    last_read_message_id: int = config["last_read_message_id"]
    messages_iter = client.iter_history(
        config["chat_id"],
        offset_id=last_read_message_id,
        reverse=True,
    )
    pagination_count: int = 0
    messages_list: list = []

    async for message in messages_iter:
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

    await client.stop()
    config["last_read_message_id"] = last_read_message_id
    return config


def main():
    """Main function of the downloader."""
    f = open(os.path.join(THIS_DIR, "config.yaml"))
    config = yaml.safe_load(f)
    f.close()
    updated_config = asyncio.get_event_loop().run_until_complete(
        begin_import(config, pagination_limit=100)
    )
    if FAILED_IDS:
        logger.info(
            "Downloading of %d files failed. "
            "Failed message ids are added to config file.\n"
            "Functionality to re-download failed downloads will be added "
            "in the next version of `Telegram-media-downloader`",
            len(set(FAILED_IDS)),
        )
    update_config(updated_config)


if __name__ == "__main__":
    print_meta(logger)
    main()
