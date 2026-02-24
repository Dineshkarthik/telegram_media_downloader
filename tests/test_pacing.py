"""Unit tests for download pacing features (delays and concurrency)."""

import asyncio
import unittest
from datetime import datetime, timezone
from unittest import mock

from media_downloader import process_messages


class MockMessage:
    def __init__(self, message_id):
        self.id = message_id
        self.date = datetime.now(timezone.utc)


class TestPacing(unittest.IsolatedAsyncioTestCase):
    """Tests for download_delay and max_concurrent_downloads in process_messages."""

    def setUp(self):
        self.client = mock.AsyncMock()
        self.media_types = ["photo"]
        self.file_formats = {"photo": ["all"]}
        self.chat_id = "test_chat"
        self.messages = [MockMessage(i) for i in range(1, 4)]

    @mock.patch("media_downloader.download_media")
    @mock.patch("asyncio.sleep", new_callable=mock.AsyncMock)
    async def test_process_messages_fixed_delay(self, mock_sleep, mock_download):
        """Verify that a fixed download_delay calls asyncio.sleep correctly."""
        mock_download.side_effect = lambda *args, **kwargs: args[1].id

        delay = 1.5
        await process_messages(
            self.client,
            self.messages,
            self.media_types,
            self.file_formats,
            self.chat_id,
            download_delay=delay,
        )

        # sleep should be called for each message
        self.assertEqual(mock_sleep.call_count, len(self.messages))
        mock_sleep.assert_called_with(delay)

    @mock.patch("media_downloader.download_media")
    @mock.patch("random.uniform", return_value=2.5)
    @mock.patch("asyncio.sleep", new_callable=mock.AsyncMock)
    async def test_process_messages_random_delay(
        self, mock_sleep, mock_random, mock_download
    ):
        """Verify that a range download_delay calls random.uniform and asyncio.sleep."""
        mock_download.side_effect = lambda *args, **kwargs: args[1].id

        delay_range = [1.0, 5.0]
        await process_messages(
            self.client,
            self.messages,
            self.media_types,
            self.file_formats,
            self.chat_id,
            download_delay=delay_range,
        )

        self.assertEqual(mock_random.call_count, len(self.messages))
        mock_random.assert_called_with(1.0, 5.0)
        self.assertEqual(mock_sleep.call_count, len(self.messages))
        mock_sleep.assert_called_with(2.5)

    @mock.patch("media_downloader.download_media")
    @mock.patch("asyncio.Semaphore")
    async def test_process_messages_concurrency_limit(
        self, mock_semaphore_class, mock_download
    ):
        """Verify that max_concurrent_downloads initializes Semaphore correctly."""
        mock_download.side_effect = lambda *args, **kwargs: args[1].id

        # Create a mock instance that behaves like an async context manager
        mock_semaphore = mock.MagicMock()
        mock_semaphore.__aenter__ = mock.AsyncMock(return_value=mock_semaphore)
        mock_semaphore.__aexit__ = mock.AsyncMock(return_value=None)
        mock_semaphore_class.return_value = mock_semaphore

        limit = 2
        await process_messages(
            self.client,
            self.messages,
            self.media_types,
            self.file_formats,
            self.chat_id,
            max_concurrent_downloads=limit,
        )

        mock_semaphore_class.assert_called_once_with(limit)
        # __aenter__ should be called once per message
        self.assertEqual(mock_semaphore.__aenter__.call_count, len(self.messages))

    @mock.patch("media_downloader.download_media")
    @mock.patch("media_downloader.logger")
    @mock.patch("asyncio.sleep", new_callable=mock.AsyncMock)
    async def test_process_messages_invalid_delay_warning(
        self, mock_sleep, mock_logger, mock_download
    ):
        """Verify that invalid delay lists trigger a warning and skip sleep."""
        mock_download.side_effect = lambda *args, **kwargs: args[1].id

        invalid_delay = [1.0, 2.0, 3.0]  # Too many elements
        await process_messages(
            self.client,
            self.messages,
            self.media_types,
            self.file_formats,
            self.chat_id,
            download_delay=invalid_delay,
        )

        self.assertTrue(mock_logger.warning.called)
        self.assertEqual(mock_sleep.call_count, 0)


if __name__ == "__main__":
    unittest.main()
