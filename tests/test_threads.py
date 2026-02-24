import asyncio
import unittest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from media_downloader import process_chat


class MockMessage:
    def __init__(self, id, date):
        self.id = id
        self.date = date
        self.media = None


class MockClientWithThreads:
    def __init__(self):
        self.iter_messages_calls = []
        self.get_messages_calls = []

    async def get_messages(self, *args, **kwargs):
        self.get_messages_calls.append(kwargs)
        return []

    async def iter_messages(self, *args, **kwargs):
        self.iter_messages_calls.append(kwargs)
        # Yield one dummy message so loop runs once
        msg = MockMessage(1, datetime.now())
        yield msg


class TestThreadsDownloading(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.loop = asyncio.get_event_loop()

    def setUp(self):
        self.client = MockClientWithThreads()

    def test_process_chat_with_threads(self):
        chat_conf = {"chat_id": 12345, "threads": [11, 22]}
        global_config = {}
        config_write_lock = asyncio.Lock()

        async def run_test():
            with patch(
                "media_downloader.process_messages", new_callable=AsyncMock
            ) as process_messages_mock, patch(
                "asyncio.sleep", new_callable=AsyncMock
            ), patch(
                "media_downloader.CURRENT_BATCH_IDS", {}
            ), patch(
                "media_downloader.PROCESSED_IDS", {}
            ), patch(
                "media_downloader.DOWNLOADED_IDS", {}
            ), patch(
                "media_downloader.FAILED_IDS", {}
            ), patch(
                "media_downloader.db.record_download"
            ):

                # The test will hang if we don't return 0 here at some point
                process_messages_mock.side_effect = [
                    1,
                    2,
                    0,
                ]  # Returns 0 on 3rd call to break the loop

                await process_chat(
                    self.client, global_config, chat_conf, 100, config_write_lock
                )

            self.assertGreaterEqual(len(self.client.iter_messages_calls), 2)

            # Verify call arguments
            calls = [c.get("reply_to") for c in self.client.iter_messages_calls]
            self.assertIn(11, calls)
            self.assertIn(22, calls)

        self.loop.run_until_complete(run_test())

    def test_process_chat_without_threads(self):
        chat_conf = {"chat_id": 12345, "threads": []}
        global_config = {}
        config_write_lock = asyncio.Lock()

        async def run_test():
            with patch(
                "media_downloader.process_messages", new_callable=AsyncMock
            ) as process_messages_mock, patch(
                "asyncio.sleep", new_callable=AsyncMock
            ), patch(
                "media_downloader.CURRENT_BATCH_IDS", {}
            ), patch(
                "media_downloader.PROCESSED_IDS", {}
            ), patch(
                "media_downloader.DOWNLOADED_IDS", {}
            ), patch(
                "media_downloader.FAILED_IDS", {}
            ), patch(
                "media_downloader.db.record_download"
            ):

                process_messages_mock.return_value = 0  # Break loop immediately
                await process_chat(
                    self.client, global_config, chat_conf, 100, config_write_lock
                )

            self.assertGreaterEqual(len(self.client.iter_messages_calls), 1)
            self.assertNotIn("reply_to", self.client.iter_messages_calls[0])

        self.loop.run_until_complete(run_test())

    def test_process_chat_with_single_thread(self):
        chat_conf = {"chat_id": 12345, "threads": 33}
        global_config = {}
        config_write_lock = asyncio.Lock()

        async def run_test():
            with patch(
                "media_downloader.process_messages", new_callable=AsyncMock
            ) as process_messages_mock, patch(
                "asyncio.sleep", new_callable=AsyncMock
            ), patch(
                "media_downloader.CURRENT_BATCH_IDS", {}
            ), patch(
                "media_downloader.PROCESSED_IDS", {}
            ), patch(
                "media_downloader.DOWNLOADED_IDS", {}
            ), patch(
                "media_downloader.FAILED_IDS", {}
            ), patch(
                "media_downloader.db.record_download"
            ):

                process_messages_mock.return_value = 0  # Break loop immediately
                await process_chat(
                    self.client, global_config, chat_conf, 100, config_write_lock
                )

            self.assertGreaterEqual(len(self.client.iter_messages_calls), 1)
            self.assertEqual(self.client.iter_messages_calls[0].get("reply_to"), 33)

        self.loop.run_until_complete(run_test())


if __name__ == "__main__":
    unittest.main()
