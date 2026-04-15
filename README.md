<div align="center">

# J.A.R.V.I.S.
### Just A Rather Very Intelligent System

<img src="https://img.shields.io/badge/Python-3.9+-blue?style=for-the-badge&logo=python&logoColor=white" />
<img src="https://img.shields.io/badge/Gemini_Live-API-orange?style=for-the-badge&logo=google&logoColor=white" />
<img src="https://img.shields.io/badge/ElevenLabs-TTS-purple?style=for-the-badge" />
<img src="https://img.shields.io/badge/PySide6-GUI-green?style=for-the-badge&logo=qt&logoColor=white" />

---

*An advanced AI desktop assistant inspired by Tony Stark's legendary AI from the Iron Man universe.*
*Built with real-time voice interaction, visual analysis, and system control capabilities.*

</div>

---

## Overview

**J.A.R.V.I.S.** is a sophisticated AI desktop assistant that combines the power of Google's Gemini Live API with ElevenLabs text-to-speech to create a truly interactive experience. Featuring an Iron Man-inspired interface with an animated Arc Reactor, JARVIS can see through your webcam, analyze your screen, execute code, search the web, manage files, launch applications, and much more — all through natural voice or text commands.

> FOR FULL VIDEO TUTORIAL: https://www.youtube.com/watch?v=aooylKf-PeA

## Key Features

| Feature | Description |
|---------|-------------|
| **Real-Time Voice Chat** | Speak naturally with JARVIS using Gemini Live API for speech-to-text and ElevenLabs for lifelike voice responses |
| **Visual Analysis** | Switch between webcam and screen capture for JARVIS to analyze what you see |
| **Arc Reactor Animation** | Iron Man-inspired animated Arc Reactor that pulses when JARVIS speaks |
| **Google Search** | Integrated web search with source links displayed in the System Diagnostics panel |
| **Code Execution** | Run Python code on-the-fly with real-time output display |
| **File Management** | Create, read, edit files and folders, and browse directories |
| **App Launcher** | Open any desktop application by name (20+ pre-mapped apps) |
| **Website Opener** | Navigate to any URL through voice or text commands |
| **System Diagnostics** | Monitor CPU, RAM, disk usage, battery status, and uptime |
| **Date & Time** | Get current date, time, and day information |
| **System Commands** | Execute safe shell commands with output display |
| **JARVIS Personality** | Sophisticated, witty British AI with dry humor — just like the original |
| **Cross-Platform** | Designed to work on Windows, macOS, and Linux |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    J.A.R.V.I.S. Application                 │
├──────────────┬──────────────────────┬───────────────────────┤
│  System      │    Main Interface    │    Visual Feed        │
│  Diagnostics │                      │                       │
│              │  ┌──────────────┐    │  ┌─────────────────┐  │
│  • Search    │  │ J.A.R.V.I.S. │    │  │                 │  │
│  • Code Exec │  │    Title     │    │  │   Webcam /      │  │
│  • File Sys  │  ├──────────────┤    │  │   Screen Feed   │  │
│              │  │  Arc Reactor │    │  │                 │  │
│              │  │  Animation   │    │  └─────────────────┘  │
│              │  ├──────────────┤    │                       │
│              │  │              │    │  [WEBCAM] [SCREEN]    │
│              │  │  Chat Log    │    │       [OFFLINE]       │
│              │  │              │    │                       │
│              │  ├──────────────┤    │  CPU: 12% | RAM: 45% │
│              │  │ > Input Box  │    │                       │
└──────────────┴──┴──────────────┴────┴───────────────────────┘
```

## Setup

### 1. Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.9+** — [Download Python](https://www.python.org/downloads/)
- **Git** — [Download Git](https://git-scm.com/downloads)
- **Gemini API Key** — Get yours from [Google AI Studio](https://aistudio.google.com/app/apikey)
- **ElevenLabs API Key** — Get yours from [ElevenLabs](https://try.elevenlabs.io/6alaeznm5itg)

### 2. Clone the Repository

```bash
git clone https://github.com/nazirlouis/ada.git
cd ada
```

### 3. Create a Virtual Environment

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**On macOS/Linux:**
```bash
python -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install google-genai python-dotenv elevenlabs PySide6 opencv-python Pillow numpy websockets pyaudio psutil
```

> **Note:** On some systems, `PyAudio` may require system-level dependencies. See the [PyAudio documentation](https://pypi.org/project/PyAudio/) for platform-specific instructions.

### 5. Configure API Keys

Create a `.env` file in the project root:

```env
GEMINI_API_KEY="YOUR_GEMINI_API_KEY_HERE"
ELEVENLABS_API_KEY="YOUR_ELEVENLABS_API_KEY_HERE"
```

> **Important:** Never share or commit your `.env` file. It is already included in `.gitignore`.

## Usage

### Running JARVIS

```bash
python jarvis.py
```

### Command-Line Arguments

| Argument | Options | Description |
|----------|---------|-------------|
| `--mode` | `camera`, `screen`, `none` | Sets the initial video input mode (default: `none`) |

**Examples:**
```bash
python jarvis.py --mode camera    # Start with webcam active
python jarvis.py --mode screen    # Start with screen sharing
python jarvis.py --mode none      # Start without video (default)
```

### Interacting with JARVIS

- **Voice:** Simply speak — JARVIS listens in real-time through your microphone
- **Text:** Type commands in the input box and press Enter
- **Video Modes:** Use the WEBCAM, SCREEN, and OFFLINE buttons to switch visual input

### Example Commands

```
"JARVIS, what's the weather like today?"
"Search for the latest news about AI"
"Open Google Chrome"
"What time is it?"
"Show me my system information"
"Create a folder called 'my_project'"
"Read the file notes.txt"
"Calculate 2^10 * 3.14"
"Open youtube.com"
```

## Running the Original A.D.A.

The original A.D.A. assistant is still available:

```bash
python ada.py
```

## Tutorials

The `Tutorials/` directory contains step-by-step guides that build up to the full assistant:

| # | File | Topic |
|---|------|-------|
| 1 | `1-simpleReply.py` | Basic Gemini text generation |
| 2 | `2-simpleReplyWithSystemInstructions.py` | System instructions |
| 3 | `3-simpleReplyStreaming.py` | Streaming responses |
| 4 | `4-chatWithGemini.py` | Multi-turn chat |
| 5 | `5-speechToTextwithGemini.py` | Speech-to-text |
| 6 | `6-textToSpeechwithGemini.py` | Text-to-speech with ElevenLabs |
| 7 | `7-geminiLiveApi.py` | Gemini Live API (real-time) |
| 8 | `8-guiAda.py` | PySide6 GUI |
| 9 | `9-googleSearch.py` | Google Search integration |
| 10 | `10-codeExecution.py` | Code execution |
| 11 | `11-functionCalling.py` | Function calling & tools |

## Troubleshooting

### API Key Errors
- Ensure `.env` file is in the project root alongside `jarvis.py`
- Verify variable names are exactly `GEMINI_API_KEY` and `ELEVENLABS_API_KEY`
- Check for extra spaces or characters in your keys

### Microphone Not Working
- **Windows:** Settings > Privacy & Security > Microphone — enable for desktop apps
- **macOS:** System Settings > Privacy & Security > Microphone — allow your terminal
- Ensure the correct microphone is set as default in system sound settings

### Video Feed Not Displaying
- Check camera permissions in your OS privacy settings
- Ensure no other app is using the webcam
- For multiple cameras, adjust the `cv2.VideoCapture(0)` index in the code

### PyAudio Installation Issues
- **Windows:** `pip install pyaudio` (usually works directly)
- **macOS:** `brew install portaudio && pip install pyaudio`
- **Linux:** `sudo apt-get install portaudio19-dev && pip install pyaudio`

## What's New in JARVIS (vs A.D.A.)

| Feature | A.D.A. | J.A.R.V.I.S. |
|---------|--------|---------------|
| Personality | Generic assistant | Sophisticated British AI with wit |
| Animation | Rotating 3D sphere | Iron Man Arc Reactor with particles |
| UI Theme | Cyan/dark blue | Gold/blue Iron Man palette |
| System Info | Not available | CPU, RAM, disk, battery monitoring |
| Date/Time | Not available | Built-in date/time tool |
| System Commands | Not available | Safe shell command execution |
| App Launcher | Basic (6 apps) | Extended (20+ app mappings) |
| Status Display | None | Real-time system status bar |
| File Creation | Basic | Auto-creates parent directories |
| Status Indicator | None | Speaking/Ready status with color |

## Project Structure

```
ada/
├── jarvis.py              # Main JARVIS application (NEW)
├── ada.py                 # Original A.D.A. assistant
├── requirements.txt       # Python dependencies
├── .env                   # API keys (not committed)
├── .gitignore
├── README.md
└── Tutorials/
    ├── README.md
    ├── 1-simpleReply.py
    ├── ...
    └── 11-functionCalling.py
```

## License

This project is open source and available for personal and educational use.

---

<div align="center">

*"At your service, Sir."* — J.A.R.V.I.S.

</div>
