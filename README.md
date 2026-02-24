
<h1 align="center">Telegram Media Downloader</h1>

<p align="center">
<a href="https://github.com/Dineshkarthik/telegram_media_downloader/actions"><img alt="Unittest" src="https://github.com/Dineshkarthik/telegram_media_downloader/workflows/Unittest/badge.svg"></a>
<a href="https://codecov.io/gh/Dineshkarthik/telegram_media_downloader"><img alt="Coverage Status" src="https://codecov.io/gh/Dineshkarthik/telegram_media_downloader/branch/master/graph/badge.svg"></a>
<a href="https://github.com/Dineshkarthik/telegram_media_downloader/blob/master/LICENSE"><img alt="License: MIT" src="https://black.readthedocs.io/en/stable/_static/license.svg"></a>
<a href="https://github.com/python/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
</p>

<h3 align="center">
  <a href="https://github.com/Dineshkarthik/telegram_media_downloader/discussions/categories/ideas">Feature request</a>
  <span> · </span>
  <a href="https://github.com/Dineshkarthik/telegram_media_downloader/issues">Report a bug</a>
  <span> · </span>
  Support: <a href="https://github.com/Dineshkarthik/telegram_media_downloader/discussions">Discussions</a>
  <span> & </span>
  <a href="https://t.me/tgmdnews">Telegram Community</a>
</h3>

### Overview:
Download all media files from a conversation or a channel that you are a part of from telegram.
A meta of last read/downloaded message is stored in the config file so that in such a way it won't download the same media file again.

### Support:
| Category | Support |
|--|--|
|Language | `Python 3.8 ` and above|
|Download media types|  audio, document, photo, video, video_note, voice|

### ToDo:
- Add GUI/Web interface.

## 🎉 Version 3.3.0 - Anti-Ban Rate Limiting

### What's New:
- **Rate Limiting**: Added `max_concurrent_downloads` to limit simultaneous downloads and prevent Telegram bans.
- **Download Delay**: Added `download_delay` with support for fixed or random delays between downloading files.
- **Improved Gentle Exit**: The script safely remembers the last downloaded file when stopping.

## 🎉 Version 3.2.0 - Multi-Chat & Parallel Processing

### What's New:
- **Multiple Chats Support**: Configure and download from multiple chats at once using a new `chats` list in `config.yaml`.
- **Parallel Downloading**: Added `parallel_chats` option to download from multiple chats concurrently using `asyncio.gather`.
- **Per-Chat Configurations**: Customize `media_types`, `download_directory`, `start_date`, and other filters locally for each specific chat without losing the ability to use global defaults.
- **Dynamic Directories**: Downloaded media is automatically organized into subdirectories by `chat_id` when relying on the default structure.
- **State Separation**: Maintains tracking (`last_read_message_id` and retry states) completely separated for each chat.

## ⚠️ Version 3.0.0 - Breaking Changes

**This version (3.0.0) contains breaking changes** due to migration from **Pyrogram** to **Telethon**.

### What's Changed:
- **Backend Migration**: Complete migration from Pyrogram to Telethon library
- **API Changes**: Some configuration options may have changed
- **Dependencies**: Updated to use Telethon-specific dependencies
- **Python Requirement**: Now requires Python 3.8 or higher (previously 3.7+)

### Migration Guide:
If you're upgrading from a previous version:
1. **Backup your `config.yaml`** and downloaded media
2. **Use `make install`** to ensure all dependencies are properly installed
3. **Review your configuration** as some options may have changed
4. **Test with a small channel first** to verify everything works

### Installation

> **⚠️ Important**: For version 3.0.0, we strongly recommend using `make install` to ensure all dependencies are properly installed with correct Python version compatibility.

#### For *nix OS distributions with `make` availability (Recommended):
```sh
git clone https://github.com/Dineshkarthik/telegram_media_downloader.git
cd telegram_media_downloader
make install
```

#### For Windows or systems without `make`:
```sh
git clone https://github.com/Dineshkarthik/telegram_media_downloader.git
cd telegram_media_downloader
pip3 install -r requirements.txt
```

> **Note**: The `make install` command automatically detects your Python version and installs the appropriate dependencies for optimal compatibility.

### Development Installation

For contributors and developers who need additional development tools:

```sh
git clone https://github.com/Dineshkarthik/telegram_media_downloader.git
cd telegram_media_downloader
make dev_install  # Installs both runtime and development dependencies
```

> **Note**: `make dev_install` also automatically detects your Python version and installs version-specific development dependencies.

## Configuration

All the configurations are passed to the Telegram Media Downloader via `config.yaml` file.

### Setup Configuration

1. Copy `config.yaml.example` to `config.yaml`:
   ```sh
   cp config.yaml.example config.yaml
   ```
2. Update the values in `config.yaml` with your specific details (API keys, chat ID, etc.).

> **Note**: `config.yaml` is ignored by git to prevent accidental commits of sensitive information. Always use `config.yaml.example` as the template.

**Getting your API Keys:**
The very first step requires you to obtain a valid Telegram API key (API id/hash pair):
1.  Visit  [https://my.telegram.org/apps](https://my.telegram.org/apps)  and log in with your Telegram Account.
2.  Fill out the form to register a new Telegram application.
3.  Done! The API key consists of two parts:  **api_id**  and  **api_hash**.


**Getting chat id:**

**1. Using web telegram:**
1. Open https://web.telegram.org/?legacy=1#/im
2. Now go to the chat/channel and you will see the URL as something like
	- `https://web.telegram.org/?legacy=1#/im?p=u853521067_2449618633394` here `853521067` is the chat id.
	- `https://web.telegram.org/?legacy=1#/im?p=@somename` here `somename` is the chat id.
	- `https://web.telegram.org/?legacy=1#/im?p=s1301254321_6925449697188775560` here take `1301254321` and add `-100` to the start of the id => `-1001301254321`.
	- `https://web.telegram.org/?legacy=1#/im?p=c1301254321_6925449697188775560` here take `1301254321` and add `-100` to the start of the id => `-1001301254321`.


**2. Using bot:**
1. Use [@username_to_id_bot](https://t.me/username_to_id_bot) to get the chat_id of
    - almost any telegram user: send username to the bot or just forward their message to the bot
    - any chat: send chat username or copy and send its joinchat link to the bot
    - public or private channel: same as chats, just copy and send to the bot
    - id of any telegram bot


### config.yaml
```yaml
api_hash: your_api_hash
api_id: your_api_id

# The downloader can process multiple chats (either sequentially or in parallel).
# The 'chats' list is highly customizable per chat. If an option is not provided
# in a chat dictionary, it will fall back to the global option defined above.
parallel_chats: false
chats:
  - chat_id: telegram_chat_id_1
    last_read_message_id: 0
    ids_to_retry: []
    # Local chat options map exactly as the globals (media_types, file_formats, etc.)
  - chat_id: telegram_chat_id_2
    last_read_message_id: 0

# GLOBAL SETTINGS (act as fallback for local chats)
chat_id: telegram_chat_id
last_read_message_id: 0
ids_to_retry: []
media_types:
- audio
- document
- photo
- video
- voice
- video_note
file_formats:
  audio:
  - all
  document:
  - all
  video:
  - all

# Optional filters (Can also be set in individual chats)
download_directory: null  # Custom directory path for downloads (absolute or relative path)
start_date: null  # Filter messages after this date (ISO format, e.g., '2023-01-01' or '2023-01-01T00:00:00')
end_date: null    # Filter messages before this date (ISO format)
max_messages: null  # Limit the number of media items to download (integer)

# Anti-ban / rate limiting (optional, can also be set per-chat)
max_concurrent_downloads: 4   # Max files downloading at once per batch (1 = fully sequential)
download_delay: null          # Delay between files: fixed (2) or random range ([1, 5])
```

- api_hash  - The api_hash you got from telegram apps
- api_id - The api_id you got from telegram apps
- parallel_chats - If `true`, downloads chats inside the `chats` list concurrently.
- chats: A list of discrete chats/channels to download from. Setting `media_types`, `download_directory`, etc., locally inside here overrides global options.
- chat_id -  The id of the chat/channel you want to download media for. Can be set globally or locally.
- last_read_message_id - If it is the first time you are going to read the channel let it be `0` or if you have already used this script it will have auto-updated.
- ids_to_retry - `Leave it as it is.` This keeps track of all skipped downloads to retry.
- media_types - Type of media to download.
- file_formats - File types to download. Default is `all`.
- download_directory - Optional: Custom directory path where media files will be downloaded. Can be absolute or relative path. If `null`, uses default directory structure.
- start_date - Optional: Filter messages to download only those sent after this date (ISO format). Leave `null` to disable.
- end_date - Optional: Filter messages to download only those sent before this date (ISO format). Leave `null` to disable.
- max_messages - Optional: Limit the number of media items to download (integer). Leave `null` for unlimited.
- max_concurrent_downloads - Optional: Maximum number of files downloading simultaneously per batch. Lower values reduce ban risk. `1` = fully sequential. Default: `4`.
- download_delay - Optional: Pause between starting each file download (seconds). Use a number for a fixed delay (`2`) or a list for a random range (`[1, 5]`). Leave `null` for no delay.

### Rate Limiting (Anti-Ban)

To reduce the risk of Telegram rate-limiting or banning your account, you can slow down the downloader with two optional settings:

| Option | Type | Default | Description |
|---|---|---|---|
| `max_concurrent_downloads` | int | `4` | Max files downloading simultaneously per batch. Set to `1` for fully sequential. |
| `download_delay` | float \| [float, float] \| null | `null` | Pause between files. Fixed seconds (`2`) or random range (`[1, 5]`). |

Both options can be set **globally** or **overridden per-chat**:

```yaml
# Global (applies to all chats unless overridden)
max_concurrent_downloads: 2
download_delay: [1, 5]   # random 1–5 second pause between files

chats:
  - chat_id: 123456789
    # This chat downloads faster since it's a trusted source
    max_concurrent_downloads: 8
    download_delay: null
  - chat_id: 987654321
    # Falls back to global settings (2 concurrent, random 1–5 s delay)
```

## Execution

### CLI Execution
```sh
python3 media_downloader.py
```

### Web UI Execution
> **Note**: The Web UI relies on NiceGUI and requires **Python 3.10** or higher.

For an interactive experience that lets you configure downloads and track progress visually, you can start the built-in Web UI (powered by NiceGUI).

```sh
python3 webui.py
```
This will start a local web server (usually at `http://127.0.0.1:8080`). Open that URL in your browser to interact with the downloader.


### Download Directories

By default, all downloaded media will be stored in respective directories named after the media type and scoped to their specific `chat_id` in the same path as the python script.

| Media type | Default Download directory |
|--|--|
| audio | path/to/project/<chat_id>/audio |
| document | path/to/project/<chat_id>/document |
| photo | path/to/project/<chat_id>/photo |
| video | path/to/project/<chat_id>/video |
| voice | path/to/project/<chat_id>/voice |
| voice_note | path/to/project/<chat_id>/voice_note |

#### Custom Download Directory

You can specify a custom download directory by setting the `download_directory` option in your `config.yaml`. This allows you to organize all downloads in a single custom location while maintaining the media type subdirectories.

**Examples:**
- `download_directory: "/home/user/downloads/telegram"` (absolute path)
- `download_directory: "downloads/telegram"` (relative path)
- `download_directory: null` (use default directory structure)

If the specified directory doesn't exist, it will be automatically created. The media type subdirectories (audio/, photo/, etc.) will still be created within your custom directory.

## Proxy
`socks4, socks5, http` proxies are supported in this project currently. To use it, add the following to the bottom of your `config.yaml` file

```yaml
proxy:
  scheme: socks5
  hostname: 11.22.33.44
  port: 1234
  username: your_username
  password: your_password
```
If your proxy doesn’t require authorization you can omit username and password. Then the proxy will automatically be enabled.

## Contributing
### Contributing Guidelines
Read through our [contributing guidelines](https://github.com/Dineshkarthik/telegram_media_downloader/blob/master/CONTRIBUTING.md) to learn about our submission process, coding rules and more.

### Want to Help?
Want to file a bug, contribute some code, or improve documentation? Excellent! Read up on our guidelines for [contributing](https://github.com/Dineshkarthik/telegram_media_downloader/blob/master/CONTRIBUTING.md).

### Code of Conduct
Help us keep Telegram Media Downloader open and inclusive. Please read and follow our [Code of Conduct](https://github.com/Dineshkarthik/telegram_media_downloader/blob/master/CODE_OF_CONDUCT.md).
