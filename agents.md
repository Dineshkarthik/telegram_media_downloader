# Telegram Media Downloader - Agent Context

This file provides architectural context, coding guidelines, and project conventions for AI coding agents (Gemini, Copilot, Cursor, etc.) working on this repository.

## Project Overview
A Python-based utility script using [Telethon](https://docs.telethon.dev/) to download media files (audio, document, photo, video, voice, video_note) from Telegram chats and channels without storing files that already exist in the target directory.

## Core Architecture
- **Entry Point**: `media_downloader.py`. 
- **Configuration**: Managed via `config.yaml` (see `config.yaml.example` for the schema). The configuration heavily utilizes a global/local fallback system where chat-specific settings inherit from global settings if not explicitly overridden.
- **State Management**: The application tracks downloaded messages and failed downloads to avoid duplicates.
  - **In-memory state**: `DOWNLOADED_IDS` and `FAILED_IDS` (dictionaries mapping `chat_id` -> `List[int]`).
  - **Persistent state**: Saved directly back into the `config.yaml` file after every batch via `update_config()`.
- **Concurrency**: 
  - **Chats**: Iterated sequentially by default, or in parallel using `asyncio.gather` if `parallel_chats` is set to `true` in config.
  - **Downloads**: Handled concurrently within a chat batch via `asyncio.gather` wrapped in an `asyncio.Semaphore(max_concurrent_downloads)` to prevent Telegram rate-limit bans constraints.

## Key Principles & Conventions
1. **Async & Telethon**: The core logic is highly asynchronous. Always use `async`/`await` patterns natively with `asyncio`.
2. **Rate Limiting (Anti-Ban)**: Operations against the Telegram API must respect rate limits. `max_concurrent_downloads` limits simultaneous file streams, and `download_delay` inserts `asyncio.sleep` pauses between downloads natively through `random.uniform` and `float` casts.
3. **Graceful Exits**: The script listens to `KeyboardInterrupt`. When triggered, it stops fetching new batches, finishes the current processing boundary, calculates the maximum contiguous successful `message_id`, and flushes state to the YAML config before exiting gracefully.
4. **Memory Safety**: Global state lists (`PROCESSED_IDS`, `CURRENT_BATCH_IDS`) are purged between pagination loops/batches to prevent severe memory leaks on channels with huge media populations.

## Development & Testing
- **Formatting and Linting**: Python code uses `black`, `isort`, `mypy`, and `pylint`. These are strictly enforced via `pre-commit`. **Always run `pre-commit run --all-files` before finalizing changes.**
- **Testing**: Uses `pytest`. The test suite is located in `tests/test_media_downloader.py` and extensively mocks Telethon client calls, file I/O operations (`yaml.dump`, `open`), and delays (`asyncio.sleep`) using `unittest.mock`. 
  - **Run tests locally after every change:** `pytest tests/ -v`.
  - Ensure any new code has its edge cases, mock configurations, and bounds covered in tests.

## Dependencies
- Main runtime packages: `telethon`, `pyyaml`, `tqdm`, `rich`, `cryptg` (for speed enhancements).
- Check `poetry.lock`/`pyproject.toml` and `Makefile` for dependency setup and configurations.
