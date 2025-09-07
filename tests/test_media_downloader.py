"""Unittest module for media downloader."""

import asyncio
import copy
import os
import platform
import unittest
from datetime import datetime
from unittest import mock
from unittest.mock import patch

from telethon import TelegramClient
from telethon.errors import FileReferenceExpiredError
from telethon.tl.types import (
    DocumentAttributeAudio,
    DocumentAttributeFilename,
    DocumentAttributeVideo,
    MessageMediaDocument,
    MessageMediaPhoto,
)

from media_downloader import (
    _can_download,
    _get_media_meta,
    _is_exist,
    _progress_callback,
    begin_import,
    download_media,
    get_media_type,
    main,
    process_messages,
    update_config,
)

MOCK_DIR: str = "/root/project"
if platform.system() == "Windows":
    MOCK_DIR = "\\root\\project"
MOCK_CONF = {
    "api_id": 123,
    "api_hash": "hasw5Tgawsuj67",
    "last_read_message_id": 0,
    "chat_id": 8654123,
    "ids_to_retry": [1],
    "media_types": ["audio", "voice"],
    "file_formats": {"audio": ["all"], "voice": ["all"]},
}


def platform_generic_path(_path: str) -> str:
    platform_specific_path: str = _path
    if platform.system() == "Windows":
        platform_specific_path = platform_specific_path.replace("/", "\\")
    return platform_specific_path


def mock_manage_duplicate_file(file_path: str) -> str:
    return file_path


class Chat:
    def __init__(self, chat_id):
        self.id = chat_id


class MockMessage:
    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.media = kwargs.get("media")
        self.audio = kwargs.get("audio", None)
        self.document = kwargs.get("document", None)
        self.photo = kwargs.get("photo", None)
        self.video = kwargs.get("video", None)
        self.voice = kwargs.get("voice", None)
        self.video_note = kwargs.get("video_note", None)
        self.chat = Chat(kwargs.get("chat_id", None))
        # Set media based on type
        if self.photo:
            self.media = mock.Mock(spec=MessageMediaPhoto, photo=self.photo)
        elif self.document or self.audio or self.video or self.voice or self.video_note:
            # Set the appropriate document attribute based on what's provided
            media_obj = (
                self.document
                or self.audio
                or self.video
                or self.voice
                or self.video_note
            )
            self.media = mock.Mock(
                spec=MessageMediaDocument,
                document=media_obj,
            )
            # Also set the individual attribute for consistency
            if self.video:
                self.document = self.video
            elif self.audio:
                self.document = self.audio
            elif self.voice:
                self.document = self.voice
            elif self.video_note:
                self.document = self.video_note
        else:
            self.media = None


class MockAudio:
    def __init__(self, **kwargs):
        self.file_name = kwargs.get("file_name", "test.mp3")
        self.mime_type = kwargs["mime_type"]
        self.id = 123
        self.attributes = kwargs.get(
            "attributes", [mock.Mock(file_name=self.file_name)]
        )


class MockDocument:
    def __init__(self, **kwargs):
        self.file_name = kwargs.get("file_name", "test.pdf")
        self.mime_type = kwargs["mime_type"]
        self.id = 123
        self.attributes = kwargs.get(
            "attributes", [mock.Mock(file_name=self.file_name)]
        )


class MockPhoto:
    def __init__(self, **kwargs):
        self.date = kwargs["date"]
        self.id = 123


class MockVoice:
    def __init__(self, **kwargs):
        self.mime_type = kwargs["mime_type"]
        self.date = kwargs["date"]
        self.id = 123
        self.attributes = []


class MockVideo:
    def __init__(self, **kwargs):
        self.file_name = kwargs.get("file_name", "test.mp4")
        self.mime_type = kwargs["mime_type"]
        self.id = 123
        self.size = kwargs.get("size", 1024)  # Add size attribute for progress bar
        # Add video attribute for media type detection
        # Create a simple object instead of Mock to avoid file_name interference
        class VideoAttr:
            def __init__(self):
                self.voice = None
                self.round_message = False
        self.attributes = [VideoAttr()]


class MockVideoNote:
    def __init__(self, **kwargs):
        self.mime_type = kwargs["mime_type"]
        self.date = kwargs["date"]
        self.id = 123
        self.attributes = []


class MockEventLoop:
    def __init__(self):
        pass

    def run_until_complete(self, *args, **kwargs):
        return {"api_id": 1, "api_hash": "asdf", "ids_to_retry": [1, 2, 3]}


class MockAsync:
    def __init__(self):
        pass

    def get_event_loop(self):
        return MockEventLoop()


async def async_get_media_meta(message_media, _type):
    result = await _get_media_meta(message_media, _type)
    return result


async def async_download_media(client, message, media_types, file_formats):
    result = await download_media(client, message, media_types, file_formats)
    return result


async def async_begin_import(conf, pagination_limit):
    result = await begin_import(conf, pagination_limit)
    return result


async def mock_process_message(*args, **kwargs):
    return 5


async def async_process_messages(client, messages, media_types, file_formats):
    result = await process_messages(client, messages, media_types, file_formats)
    return result


class SimpleAttr:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class MockClient:
    def __init__(self, *args, **kwargs):
        pass

    async def start(self):
        pass

    async def disconnect(self):
        pass

    async def iter_messages(self, *args, **kwargs):
        items = [
            MockMessage(
                id=1213,
                media=True,
                voice=MockVoice(
                    mime_type="audio/ogg",
                    date=datetime(2019, 7, 25, 14, 53, 50),
                ),
            ),
            MockMessage(
                id=1214,
                media=False,
                text="test message 1",
            ),
            MockMessage(
                id=1215,
                media=False,
                text="test message 2",
            ),
            MockMessage(
                id=1216,
                media=False,
                text="test message 3",
            ),
        ]
        for item in items:
            yield item

    async def get_messages(self, *args, **kwargs):
        ids = kwargs.get("ids", kwargs.get("message_ids"))
        if ids == 7:
            message = MockMessage(
                id=7,
                media=True,
                chat_id=123456,
                video=MockVideo(
                    file_name="sample_video.mov",
                    mime_type="video/mov",
                ),
            )
        elif ids == 8:
            message = MockMessage(
                id=8,
                media=True,
                chat_id=234567,
                video=MockVideo(
                    file_name="sample_video.mov",
                    mime_type="video/mov",
                ),
            )
        elif ids == [1]:
            message = [
                MockMessage(
                    id=1,
                    media=True,
                    chat_id=234568,
                    video=MockVideo(
                        file_name="sample_video.mov",
                        mime_type="video/mov",
                    ),
                )
            ]
        return message

    async def download_media(self, message_or_media, file=None, **kwargs):
        mock_message = message_or_media
        if mock_message.id in [7, 8]:
            raise FileReferenceExpiredError
        elif mock_message.id == 9:
            raise Exception("Unauthorized")
        elif mock_message.id == 11:
            raise TimeoutError
        elif mock_message.id == 13:
            return None
        return file or "downloaded"


class MediaDownloaderTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.loop = asyncio.get_event_loop()

    @mock.patch("media_downloader.THIS_DIR", new=MOCK_DIR)
    def test_get_media_meta(self):
        # Test Voice notes
        message = MockMessage(
            id=1,
            media=True,
            voice=MockVoice(
                mime_type="audio/ogg",
                date=datetime(2019, 7, 25, 14, 53, 50),
            ),
        )
        result = self.loop.run_until_complete(
            async_get_media_meta(message.voice, "voice")
        )

        self.assertEqual(
            (
                platform_generic_path(
                    "/root/project/voice/voice_2019-07-25T14:53:50.ogg"
                ),
                "ogg",
            ),
            result,
        )

        # Test photos
        message = MockMessage(
            id=2,
            media=True,
            photo=MockPhoto(date=datetime(2019, 8, 5, 14, 35, 12)),
        )
        result = self.loop.run_until_complete(
            async_get_media_meta(message.photo, "photo")
        )
        self.assertEqual(
            (
                platform_generic_path("/root/project/photo/photo_123"),
                "jpg",
            ),
            result,
        )

        # Test Documents
        message = MockMessage(
            id=3,
            media=True,
            document=MockDocument(
                file_name="sample_document.pdf",
                mime_type="application/pdf",
            ),
        )
        result = self.loop.run_until_complete(
            async_get_media_meta(message.document, "document")
        )
        self.assertEqual(
            (
                platform_generic_path("/root/project/document/sample_document.pdf"),
                "pdf",
            ),
            result,
        )

        # Test audio
        message = MockMessage(
            id=4,
            media=True,
            audio=MockAudio(
                file_name="sample_audio.mp3",
                mime_type="audio/mp3",
            ),
        )
        result = self.loop.run_until_complete(
            async_get_media_meta(message.audio, "audio")
        )
        self.assertEqual(
            (
                platform_generic_path("/root/project/audio/sample_audio.mp3"),
                "mp3",
            ),
            result,
        )

        # Test Video
        message = MockMessage(
            id=5,
            media=True,
            video=MockVideo(
                mime_type="video/mp4",
            ),
        )
        result = self.loop.run_until_complete(
            async_get_media_meta(message.video, "video")
        )
        self.assertEqual(
            (
                platform_generic_path("/root/project/video/video_123"),
                "mp4",
            ),
            result,
        )

        # Test VideoNote
        message = MockMessage(
            id=6,
            media=True,
            video_note=MockVideoNote(
                mime_type="video/mp4",
                date=datetime(2019, 7, 25, 14, 53, 50),
            ),
        )
        result = self.loop.run_until_complete(
            async_get_media_meta(message.video_note, "video_note")
        )
        self.assertEqual(
            (
                platform_generic_path(
                    "/root/project/video_note/video_note_2019-07-25T14:53:50.mp4"
                ),
                "mp4",
            ),
            result,
        )

    @mock.patch("media_downloader.THIS_DIR", new=MOCK_DIR)
    def test_download_media(self):
        client = MockClient()
        message = MockMessage(
            id=5,
            media=True,
            video=MockVideo(
                file_name="sample_video.mp4",
                mime_type="video/mp4",
            ),
        )
        result = self.loop.run_until_complete(
            async_download_media(
                client, message, ["video", "photo"], {"video": ["mp4"]}
            )
        )
        self.assertEqual(5, result)

        message_1 = MockMessage(
            id=6,
            media=True,
            video=MockVideo(
                file_name="sample_video.mov",
                mime_type="video/mov",
            ),
        )
        result = self.loop.run_until_complete(
            async_download_media(
                client, message_1, ["video", "photo"], {"video": ["all"]}
            )
        )
        self.assertEqual(6, result)

        # Test re-fetch message success
        message_2 = MockMessage(
            id=7,
            media=True,
            video=MockVideo(
                file_name="sample_video.mov",
                mime_type="video/mov",
            ),
        )
        result = self.loop.run_until_complete(
            async_download_media(
                client, message_2, ["video", "photo"], {"video": ["all"]}
            )
        )
        self.assertEqual(7, result)

        # Test re-fetch message failure
        message_3 = MockMessage(
            id=8,
            media=True,
            video=MockVideo(
                file_name="sample_video.mov",
                mime_type="video/mov",
            ),
        )
        result = self.loop.run_until_complete(
            async_download_media(
                client, message_3, ["video", "photo"], {"video": ["all"]}
            )
        )
        self.assertEqual(8, result)

        # Test other exception
        message_4 = MockMessage(
            id=9,
            media=True,
            video=MockVideo(
                file_name="sample_video.mov",
                mime_type="video/mov",
            ),
        )
        result = self.loop.run_until_complete(
            async_download_media(
                client, message_4, ["video", "photo"], {"video": ["all"]}
            )
        )
        self.assertEqual(9, result)

        # Check no media
        message_5 = MockMessage(
            id=10,
            media=None,
        )
        result = self.loop.run_until_complete(
            async_download_media(
                client, message_5, ["video", "photo"], {"video": ["all"]}
            )
        )
        self.assertEqual(10, result)

        # Test timeout
        message_6 = MockMessage(
            id=11,
            media=True,
            video=MockVideo(
                file_name="sample_video.mov",
                mime_type="video/mov",
            ),
        )
        result = self.loop.run_until_complete(
            async_download_media(
                client, message_6, ["video", "photo"], {"video": ["all"]}
            )
        )
        self.assertEqual(11, result)

        # Test file format not allowed (should skip download)
        message_format_not_allowed = MockMessage(
            id=12,
            media=True,
            video=MockVideo(
                file_name="sample_video.mov",
                mime_type="video/mov",
            ),
        )
        result = self.loop.run_until_complete(
            async_download_media(
                client,
                message_format_not_allowed,
                ["video", "photo"],
                {"video": ["mp4"]},
            )
        )
        self.assertEqual(12, result)

        # Test download_path is None (should still add to DOWNLOADED_IDS)
        message_download_none = MockMessage(
            id=13,
            media=True,
            video=MockVideo(
                file_name="sample_video.mp4",
                mime_type="video/mp4",
            ),
        )
        result = self.loop.run_until_complete(
            async_download_media(
                client, message_download_none, ["video", "photo"], {"video": ["all"]}
            )
        )
        self.assertEqual(13, result)

        # Test FileReferenceExpiredError that persists until max retries (covers lines 282-292)
        message_persistent_error = MockMessage(
            id=14,  # Use ID 14 which isn't in the MockClient's special cases
            media=True,
            chat_id=345678,
            video=MockVideo(
                file_name="persistent_error.mp4",
                mime_type="video/mp4",
                size=1024,
            ),
        )

        # Create a custom mock client that always raises FileReferenceExpiredError for ID 14
        class PersistentErrorClient(MockClient):
            async def download_media(self, message_or_media, file=None, **kwargs):
                mock_message = message_or_media
                if mock_message.id == 14:
                    # Create a proper FileReferenceExpiredError with required parameters
                    raise FileReferenceExpiredError(request=None)
                return await super().download_media(message_or_media, file, **kwargs)

            async def get_messages(self, *args, **kwargs):
                ids = kwargs.get("ids", kwargs.get("message_ids"))
                if ids == 14:
                    # Return the same message that will fail again
                    return [MockMessage(
                        id=14,
                        media=True,
                        chat_id=345678,
                        video=MockVideo(
                            file_name="persistent_error.mp4",
                            mime_type="video/mp4",
                            size=1024,
                        ),
                    )]
                return await super().get_messages(*args, **kwargs)

        persistent_client = PersistentErrorClient()
        result = self.loop.run_until_complete(
            async_download_media(
                persistent_client, message_persistent_error, ["video"], {"video": ["all"]}
            )
        )
        self.assertEqual(14, result)

    @mock.patch("__main__.__builtins__.open", new_callable=mock.mock_open)
    @mock.patch("media_downloader.yaml", autospec=True)
    def test_update_config(self, mock_yaml, mock_open):
        conf = {
            "api_id": 123,
            "api_hash": "hasw5Tgawsuj67",
            "ids_to_retry": [],
        }
        update_config(conf)
        mock_open.assert_called_with("config.yaml", "w")
        mock_yaml.dump.assert_called_with(conf, mock.ANY, default_flow_style=False)

    def test_get_media_type(self):
        # Test photo
        message = MockMessage(
            id=1,
            media=True,
            photo=MockPhoto(date=datetime(2019, 8, 5, 14, 35, 12)),
        )
        result = get_media_type(message)
        self.assertEqual("photo", result)

        # Test document without special attributes
        doc_attr = mock.Mock()
        doc_attr.file_name = "test.pdf"
        doc_attr.voice = None
        doc_attr.round_message = None
        message = MockMessage(
            id=2,
            media=True,
            document=MockDocument(
                file_name="test.pdf",
                mime_type="application/pdf",
                attributes=[doc_attr],
            ),
        )
        result = get_media_type(message)
        self.assertEqual("document", result)

        # Test audio
        audio_attr = mock.Mock()
        audio_attr.voice = False
        audio_attr.round_message = None
        message = MockMessage(
            id=3,
            media=True,
            document=MockDocument(
                file_name="test.mp3",
                mime_type="audio/mp3",
                attributes=[audio_attr],
            ),
        )
        result = get_media_type(message)
        self.assertEqual("audio", result)

        # Test voice
        voice_attr = mock.Mock()
        voice_attr.voice = True
        voice_attr.round_message = None
        message = MockMessage(
            id=4,
            media=True,
            document=MockDocument(
                mime_type="audio/ogg",
                attributes=[voice_attr],
            ),
        )
        result = get_media_type(message)
        self.assertEqual("voice", result)

        # Test video
        video_attr = mock.Mock()
        video_attr.voice = None
        video_attr.round_message = False
        message = MockMessage(
            id=5,
            media=True,
            document=MockDocument(
                mime_type="video/mp4",
                attributes=[video_attr],
            ),
        )
        result = get_media_type(message)
        self.assertEqual("video", result)

        # Test video_note
        video_note_attr = mock.Mock()
        video_note_attr.voice = None
        video_note_attr.round_message = True
        message = MockMessage(
            id=6,
            media=True,
            document=MockDocument(
                mime_type="video/mp4",
                attributes=[video_note_attr],
            ),
        )
        result = get_media_type(message)
        self.assertEqual("video_note", result)

        # Test no media
        message = MockMessage(id=7, media=None)
        result = get_media_type(message)
        self.assertIsNone(result)

        # Test unsupported media type
        message = MockMessage(id=8, media=True)
        # Manually set media to an unsupported type (not MessageMediaPhoto or MessageMediaDocument)
        message.media = mock.Mock()
        result = get_media_type(message)
        self.assertIsNone(result)

    @mock.patch("media_downloader.THIS_DIR", new=MOCK_DIR)
    def test_download_media_no_media_obj(self):
        client = MockClient()
        # Mock message with media but no media_obj
        message = MockMessage(
            id=12,
            media=True,
            # No photo or document
        )
        result = self.loop.run_until_complete(
            async_download_media(
                client, message, ["video", "photo"], {"video": ["mp4"]}
            )
        )
        self.assertEqual(12, result)

        # Test media_obj is None for photo type
        message_photo_none = MockMessage(
            id=14,
            media=True,
            # Don't set photo attribute
        )
        # Manually set media to photo type
        message_photo_none.media = mock.Mock(spec=MessageMediaPhoto, photo=None)
        result = self.loop.run_until_complete(
            async_download_media(
                client, message_photo_none, ["photo"], {"photo": ["all"]}
            )
        )
        self.assertEqual(14, result)

    @mock.patch("media_downloader.update_config")
    @mock.patch("media_downloader.TelegramClient", new=MockClient)
    @mock.patch("media_downloader.process_messages", new=mock_process_message)
    def test_begin_import(self, mock_update_config):
        result = self.loop.run_until_complete(async_begin_import(MOCK_CONF, 3))
        conf = copy.deepcopy(MOCK_CONF)
        conf["last_read_message_id"] = 5
        self.assertDictEqual(result, conf)

    @mock.patch("media_downloader.update_config")
    @mock.patch("media_downloader.TelegramClient", new=MockClient)
    @mock.patch("media_downloader.process_messages", new=mock_process_message)
    def test_begin_import_with_proxy(self, mock_update_config):
        conf_with_proxy = copy.deepcopy(MOCK_CONF)
        conf_with_proxy["proxy"] = {
            "scheme": "socks5",
            "hostname": "127.0.0.1",
            "port": 1080,
            "username": "user",
            "password": "pass",
        }
        result = self.loop.run_until_complete(async_begin_import(conf_with_proxy, 3))
        expected_conf = copy.deepcopy(conf_with_proxy)
        expected_conf["last_read_message_id"] = 5
        self.assertDictEqual(result, expected_conf)

    def test_process_message(self):
        client = MockClient()
        result = self.loop.run_until_complete(
            async_process_messages(
                client,
                [
                    MockMessage(
                        id=1213,
                        media=True,
                        voice=MockVoice(
                            mime_type="audio/ogg",
                            date=datetime(2019, 7, 25, 14, 53, 50),
                        ),
                    ),
                    MockMessage(
                        id=1214,
                        media=False,
                        text="test message 1",
                    ),
                    MockMessage(
                        id=1215,
                        media=False,
                        text="test message 2",
                    ),
                    MockMessage(
                        id=1216,
                        media=False,
                        text="test message 3",
                    ),
                ],
                ["voice", "photo"],
                {"audio": ["all"], "voice": ["all"]},
            )
        )
        self.assertEqual(result, 1216)

    @mock.patch("media_downloader._is_exist", return_value=True)
    @mock.patch(
        "media_downloader.manage_duplicate_file",
        new=mock_manage_duplicate_file,
    )
    def test_process_message_when_file_exists(self, mock_is_exist):
        client = MockClient()
        result = self.loop.run_until_complete(
            async_process_messages(
                client,
                [
                    MockMessage(
                        id=1213,
                        media=True,
                        voice=MockVoice(
                            mime_type="audio/ogg",
                            date=datetime(2019, 7, 25, 14, 53, 50),
                        ),
                    ),
                    MockMessage(
                        id=1214,
                        media=False,
                        text="test message 1",
                    ),
                    MockMessage(
                        id=1215,
                        media=False,
                        text="test message 2",
                    ),
                    MockMessage(
                        id=1216,
                        media=False,
                        text="test message 3",
                    ),
                ],
                ["voice", "photo"],
                {"audio": ["all"], "voice": ["all"]},
            )
        )
        self.assertEqual(result, 1216)

    def test_can_download(self):
        file_formats = {
            "audio": ["mp3"],
            "video": ["mp4"],
            "document": ["all"],
        }
        result = _can_download("audio", file_formats, "mp3")
        self.assertEqual(result, True)

        result1 = _can_download("audio", file_formats, "ogg")
        self.assertEqual(result1, False)

        result2 = _can_download("document", file_formats, "pdf")
        self.assertEqual(result2, True)

        result3 = _can_download("document", file_formats, "epub")
        self.assertEqual(result3, True)

    def test_is_exist(self):
        this_dir = os.path.dirname(os.path.abspath(__file__))
        result = _is_exist(os.path.join(this_dir, "__init__.py"))
        self.assertEqual(result, True)

        result1 = _is_exist(os.path.join(this_dir, "init.py"))
        self.assertEqual(result1, False)

        result2 = _is_exist(this_dir)
        self.assertEqual(result2, False)

    @mock.patch("media_downloader.FAILED_IDS", [2, 3])
    @mock.patch("media_downloader.yaml.safe_load")
    @mock.patch("media_downloader.update_config", return_value=True)
    @mock.patch("media_downloader.begin_import")
    @mock.patch("media_downloader.asyncio", new=MockAsync())
    def test_main(self, mock_import, mock_update, mock_yaml):
        conf = {
            "api_id": 1,
            "api_hash": "asdf",
            "ids_to_retry": [1, 2],
        }
        mock_yaml.return_value = conf
        main()
        mock_import.assert_called_with(conf, pagination_limit=100)
        conf["ids_to_retry"] = [1, 2, 3]
        mock_update.assert_called_with(conf)

    @mock.patch("media_downloader.print_meta")
    @mock.patch("media_downloader.main")
    def test_main_entry(self, mock_main, mock_print_meta):
        # To cover the if __name__ == "__main__" block, we mock the calls
        # and then call the functions to simulate the main entry point
        from media_downloader import main, print_meta

        print_meta(mock_print_meta)
        main()
        mock_print_meta.assert_called_once()
        mock_main.assert_called_once()

    def test_progress_callback_function(self):
        """Test the _progress_callback function works correctly."""
        from tqdm import tqdm

        # Test initial callback with total
        with tqdm(total=100, unit="B", unit_scale=True, desc="Test") as pbar:
            _progress_callback(0, 100, pbar)
            self.assertEqual(pbar.total, 100)
            self.assertEqual(pbar.n, 0)

            # Test progress update
            _progress_callback(50, 100, pbar)
            self.assertEqual(pbar.n, 50)

            # Test completion
            _progress_callback(100, 100, pbar)
            self.assertEqual(pbar.n, 100)

    @mock.patch("media_downloader.tqdm")
    def test_download_media_with_progress_bar(self, mock_tqdm):
        """Test that progress bar is created and used during downloads."""
        # Setup mocks
        mock_client = MockClient()
        mock_pbar = mock.Mock()
        mock_tqdm.return_value.__enter__ = mock.Mock(return_value=mock_pbar)
        mock_tqdm.return_value.__exit__ = mock.Mock(return_value=None)

        # Create test message with video that has size
        message = MockMessage(
            id=15,
            media=True,
            video=MockVideo(
                file_name="test_video.mp4",
                mime_type="video/mp4",
                size=1024,
            ),
        )

        # Run the download
        result = self.loop.run_until_complete(
            async_download_media(
                mock_client, message, ["video"], {"video": ["all"]}
            )
        )

        # Verify progress bar was created
        self.assertEqual(result, 15)
        mock_tqdm.assert_called_once()
        call_args = mock_tqdm.call_args
        self.assertEqual(call_args[1]["total"], 1024)
        self.assertEqual(call_args[1]["unit"], "B")
        self.assertEqual(call_args[1]["unit_scale"], True)
        self.assertIn("test_video.mp4", call_args[1]["desc"])

    @mock.patch("media_downloader.tqdm")
    @mock.patch("media_downloader._is_exist", return_value=True)
    def test_download_media_existing_file_with_progress_bar(self, mock_is_exist, mock_tqdm):
        """Test progress bar creation when file already exists."""
        # Setup mocks
        mock_client = MockClient()
        mock_pbar = mock.Mock()
        mock_tqdm.return_value.__enter__ = mock.Mock(return_value=mock_pbar)
        mock_tqdm.return_value.__exit__ = mock.Mock(return_value=None)

        # Create test message with video that has size
        message = MockMessage(
            id=16,
            media=True,
            video=MockVideo(
                file_name="existing_video.mp4",
                mime_type="video/mp4",
                size=2048,
            ),
        )

        # Run the download
        result = self.loop.run_until_complete(
            async_download_media(
                mock_client, message, ["video"], {"video": ["all"]}
            )
        )

        # Verify progress bar was created for existing file
        self.assertEqual(result, 16)
        mock_tqdm.assert_called_once()
        call_args = mock_tqdm.call_args
        self.assertEqual(call_args[1]["total"], 2048)
        self.assertIn("existing_video.mp4", call_args[1]["desc"])

    @mock.patch("media_downloader.tqdm")
    def test_progress_callback_called_during_download(self, mock_tqdm):
        """Test that progress callback is properly passed to download_media."""
        # Setup mocks
        mock_client = MockClient()
        mock_pbar = mock.Mock()
        mock_pbar.n = 0  # Set initial progress to 0
        mock_tqdm.return_value.__enter__ = mock.Mock(return_value=mock_pbar)
        mock_tqdm.return_value.__exit__ = mock.Mock(return_value=None)

        # Create test message with video that has size
        message = MockMessage(
            id=17,
            media=True,
            video=MockVideo(
                file_name="callback_test.mp4",
                mime_type="video/mp4",
                size=1024,
            ),
        )

        # Mock the client's download_media to capture the progress_callback
        captured_callback = None

        async def mock_download_media(*args, **kwargs):
            nonlocal captured_callback
            captured_callback = kwargs.get("progress_callback")
            return "downloaded"

        mock_client.download_media = mock_download_media

        # Run the download
        result = self.loop.run_until_complete(
            async_download_media(
                mock_client, message, ["video"], {"video": ["all"]}
            )
        )

        # Verify callback was passed and is callable
        self.assertEqual(result, 17)
        self.assertIsNotNone(captured_callback)
        self.assertTrue(callable(captured_callback))

        # Test the captured callback
        captured_callback(50, 100)
        mock_pbar.update.assert_called_with(50)

    @classmethod
    def tearDownClass(cls):
        cls.loop.close()
