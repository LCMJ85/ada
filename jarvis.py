# ==============================================================================
#  J.A.R.V.I.S. - Just A Rather Very Intelligent System
#  Voice-Only AI Assistant inspired by Tony Stark's JARVIS
#  Built with Gemini Live API, ElevenLabs TTS, PySide6 GUI
# ==============================================================================

# --- Core Imports ---
import asyncio
import base64
import io
import os
import sys
import traceback
import json
import websockets
import argparse
import threading
from html import escape
import subprocess
import webbrowser
import math
import platform
import psutil
import datetime
import shutil

# --- PySide6 GUI Imports ---
from PySide6.QtWidgets import (QApplication, QMainWindow, QTextEdit, QLabel,
                               QVBoxLayout, QWidget, QLineEdit, QHBoxLayout,
                               QSizePolicy, QPushButton, QFrame, QGraphicsDropShadowEffect,
                               QComboBox)
from PySide6.QtCore import QObject, Signal, Slot, Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import (QImage, QPixmap, QFont, QFontDatabase, QTextCursor,
                           QPainter, QPen, QVector3D, QMatrix4x4, QColor, QBrush,
                           QRadialGradient, QLinearGradient, QConicalGradient, QPainterPath)

# --- Media and AI Imports ---
import pyaudio
from google import genai
from dotenv import load_dotenv
import numpy as np

# --- Load Environment Variables ---
load_dotenv()
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

print(f">>> [JARVIS] Loading configuration...")
print(f">>> [JARVIS] GEMINI_API_KEY: {'Found (' + GEMINI_API_KEY[:8] + '...)' if GEMINI_API_KEY else 'NOT FOUND!'}")
print(f">>> [JARVIS] ELEVENLABS_API_KEY: {'Found (' + ELEVENLABS_API_KEY[:8] + '...)' if ELEVENLABS_API_KEY else 'NOT FOUND!'}")

if not GEMINI_API_KEY:
    sys.exit("Error: GEMINI_API_KEY not found. Please set it in your .env file.")
if not ELEVENLABS_API_KEY:
    sys.exit("Error: ELEVENLABS_API_KEY not found. Please check your .env file.")

# --- Configuration ---
FORMAT = pyaudio.paInt16
CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 1024
MODEL = "gemini-2.5-flash-live-preview"
VOICE_ID = 'pFZP5JQG7iQjIQuC4Bku'
MAX_OUTPUT_TOKENS = 8192

# --- JARVIS Color Palette ---
JARVIS_GOLD = "#FFD700"
JARVIS_GOLD_DIM = "#B8960F"
JARVIS_GOLD_BRIGHT = "#FFE44D"
JARVIS_RED = "#FF4444"
JARVIS_RED_DIM = "#8B0000"
JARVIS_BLUE = "#4FC3F7"
JARVIS_BLUE_BRIGHT = "#81D4FA"
JARVIS_BG_DARK = "#0A0A0F"
JARVIS_BG_PANEL = "#0D1117"
JARVIS_BG_ACCENT = "#161B22"
JARVIS_TEXT = "#E8E8F0"
JARVIS_TEXT_DIM = "#8B949E"
JARVIS_BORDER = "#FFD70040"
JARVIS_CYAN = "#00E5FF"

# --- Initialize Clients ---
pya = pyaudio.PyAudio()


# ==============================================================================
# ARC REACTOR ANIMATION WIDGET (Iron Man Style)
# ==============================================================================
class ArcReactorWidget(QWidget):
    """
    A custom widget that renders an animated Arc Reactor inspired by Iron Man.
    Pulses when JARVIS is speaking.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle = 0
        self.inner_angle = 0
        self.is_speaking = False
        self.pulse_phase = 0
        self.energy_rings = []
        self.particle_angle = 0

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(25)

    def start_speaking_animation(self):
        self.is_speaking = True

    def stop_speaking_animation(self):
        self.is_speaking = False
        self.pulse_phase = 0
        self.update()

    def update_animation(self):
        self.angle += 1.2
        self.inner_angle -= 0.8
        self.particle_angle += 2.0
        if self.is_speaking:
            self.pulse_phase += 0.15
            if self.pulse_phase > math.pi * 2:
                self.pulse_phase -= math.pi * 2
        if self.angle >= 360:
            self.angle = 0
        if self.inner_angle <= -360:
            self.inner_angle = 0
        if self.particle_angle >= 360:
            self.particle_angle = 0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), Qt.transparent)

        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        max_radius = min(w, h) / 2 - 10

        # Pulse factor when speaking
        pulse = 1.0
        if self.is_speaking:
            pulse = 1.0 + 0.08 * math.sin(self.pulse_phase)

        # --- Outer Glow ---
        glow_gradient = QRadialGradient(cx, cy, max_radius * 1.2)
        glow_alpha = 60 if self.is_speaking else 30
        glow_gradient.setColorAt(0, QColor(79, 195, 247, glow_alpha))
        glow_gradient.setColorAt(0.5, QColor(79, 195, 247, glow_alpha // 3))
        glow_gradient.setColorAt(1, QColor(79, 195, 247, 0))
        painter.setBrush(QBrush(glow_gradient))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(int(cx - max_radius * 1.2), int(cy - max_radius * 1.2),
                           int(max_radius * 2.4), int(max_radius * 2.4))

        # --- Outer Ring ---
        outer_r = max_radius * 0.85 * pulse
        pen = QPen(QColor(79, 195, 247, 180), 2)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(int(cx - outer_r), int(cy - outer_r), int(outer_r * 2), int(outer_r * 2))

        # --- Rotating Segments (Outer) ---
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self.angle)
        segment_r = max_radius * 0.78 * pulse
        num_segments = 12
        for i in range(num_segments):
            seg_angle = (360 / num_segments) * i
            painter.save()
            painter.rotate(seg_angle)
            alpha = 120 + int(80 * math.sin(math.radians(seg_angle + self.angle)))
            pen = QPen(QColor(79, 195, 247, alpha), 2.5)
            painter.setPen(pen)
            arc_len = 18
            painter.drawArc(int(-segment_r), int(-segment_r),
                          int(segment_r * 2), int(segment_r * 2),
                          -arc_len * 16, arc_len * 2 * 16)
            painter.restore()
        painter.restore()

        # --- Middle Ring ---
        mid_r = max_radius * 0.6 * pulse
        pen = QPen(QColor(255, 215, 0, 100), 1.5)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(int(cx - mid_r), int(cy - mid_r), int(mid_r * 2), int(mid_r * 2))

        # --- Counter-Rotating Inner Segments ---
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self.inner_angle)
        inner_seg_r = max_radius * 0.52 * pulse
        num_inner = 8
        for i in range(num_inner):
            seg_angle = (360 / num_inner) * i
            painter.save()
            painter.rotate(seg_angle)
            alpha = 100 + int(100 * math.sin(math.radians(seg_angle - self.inner_angle * 2)))
            pen = QPen(QColor(255, 215, 0, alpha), 2)
            painter.setPen(pen)
            painter.drawArc(int(-inner_seg_r), int(-inner_seg_r),
                          int(inner_seg_r * 2), int(inner_seg_r * 2),
                          -12 * 16, 24 * 16)
            painter.restore()
        painter.restore()

        # --- Inner Ring ---
        inner_r = max_radius * 0.38 * pulse
        pen = QPen(QColor(79, 195, 247, 150), 1.5)
        painter.setPen(pen)
        painter.drawEllipse(int(cx - inner_r), int(cy - inner_r), int(inner_r * 2), int(inner_r * 2))

        # --- Triangular Core Elements ---
        painter.save()
        painter.translate(cx, cy)
        core_r = max_radius * 0.28 * pulse
        num_triangles = 3
        for i in range(num_triangles):
            angle_offset = (360 / num_triangles) * i + self.angle * 0.5
            rad = math.radians(angle_offset)
            tx = core_r * math.cos(rad)
            ty = core_r * math.sin(rad)
            tri_size = max_radius * 0.06
            path = QPainterPath()
            path.moveTo(tx, ty - tri_size)
            path.lineTo(tx - tri_size * 0.866, ty + tri_size * 0.5)
            path.lineTo(tx + tri_size * 0.866, ty + tri_size * 0.5)
            path.closeSubpath()
            painter.setPen(QPen(QColor(79, 195, 247, 200), 1))
            painter.setBrush(QBrush(QColor(79, 195, 247, 60)))
            painter.drawPath(path)
        painter.restore()

        # --- Central Core (Bright) ---
        core_size = max_radius * 0.18 * pulse
        core_gradient = QRadialGradient(cx, cy, core_size)
        if self.is_speaking:
            core_gradient.setColorAt(0, QColor(255, 255, 255, 255))
            core_gradient.setColorAt(0.3, QColor(129, 212, 250, 220))
            core_gradient.setColorAt(0.7, QColor(79, 195, 247, 150))
            core_gradient.setColorAt(1, QColor(79, 195, 247, 0))
        else:
            core_gradient.setColorAt(0, QColor(200, 230, 255, 220))
            core_gradient.setColorAt(0.3, QColor(79, 195, 247, 180))
            core_gradient.setColorAt(0.7, QColor(79, 195, 247, 100))
            core_gradient.setColorAt(1, QColor(79, 195, 247, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(core_gradient))
        painter.drawEllipse(int(cx - core_size), int(cy - core_size),
                           int(core_size * 2), int(core_size * 2))

        # --- Particle Effects (when speaking) ---
        if self.is_speaking:
            num_particles = 16
            for i in range(num_particles):
                p_angle = math.radians((360 / num_particles) * i + self.particle_angle)
                dist = max_radius * (0.4 + 0.3 * math.sin(self.pulse_phase + i * 0.5))
                px = cx + dist * math.cos(p_angle)
                py = cy + dist * math.sin(p_angle)
                p_size = 2 + math.sin(self.pulse_phase + i) * 1.5
                p_alpha = int(100 + 100 * math.sin(self.pulse_phase + i * 0.7))
                painter.setBrush(QBrush(QColor(79, 195, 247, p_alpha)))
                painter.drawEllipse(int(px - p_size / 2), int(py - p_size / 2),
                                   int(p_size), int(p_size))


# ==============================================================================
# AUDIO WAVEFORM VISUALIZER (Microphone Level Indicator)
# ==============================================================================
class AudioWaveformWidget(QWidget):
    """
    A custom widget that displays real-time audio waveform/level bars
    to visually indicate microphone input activity.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(80)
        self.setMaximumHeight(100)
        self.num_bars = 40
        self.bar_values = [0.0] * self.num_bars
        self.peak_values = [0.0] * self.num_bars
        self.audio_level = 0.0
        self.is_active = False
        self.phase = 0.0

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.start(40)

    def update_level(self, level):
        """Update the audio level (0.0 to 1.0)."""
        self.audio_level = min(1.0, max(0.0, level))
        self.is_active = self.audio_level > 0.01

    def _animate(self):
        self.phase += 0.15
        for i in range(self.num_bars):
            if self.is_active:
                wave = math.sin(self.phase + i * 0.4) * 0.3 + 0.5
                target = self.audio_level * wave * (0.6 + 0.4 * math.sin(self.phase * 0.7 + i * 0.3))
                target = min(1.0, target * 1.5)
            else:
                target = 0.02 + 0.01 * math.sin(self.phase * 0.5 + i * 0.2)

            self.bar_values[i] += (target - self.bar_values[i]) * 0.3

            if self.bar_values[i] > self.peak_values[i]:
                self.peak_values[i] = self.bar_values[i]
            else:
                self.peak_values[i] *= 0.95

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # Background
        painter.fillRect(0, 0, w, h, QColor(10, 10, 15))

        bar_width = max(2, (w - (self.num_bars + 1) * 2) // self.num_bars)
        spacing = 2
        total_width = self.num_bars * (bar_width + spacing)
        start_x = (w - total_width) // 2

        center_y = h // 2
        max_bar_height = (h // 2) - 4

        for i in range(self.num_bars):
            x = start_x + i * (bar_width + spacing)
            bar_h = int(self.bar_values[i] * max_bar_height)

            if bar_h < 1:
                bar_h = 1

            # Color based on level intensity
            if self.bar_values[i] > 0.7:
                color = QColor(255, 68, 68)       # Red for high
            elif self.bar_values[i] > 0.4:
                color = QColor(255, 215, 0)       # Gold for medium
            else:
                color = QColor(79, 195, 247)      # Blue for low

            if not self.is_active:
                color = QColor(79, 195, 247, 60)  # Dim blue when idle

            # Draw bar (mirrored from center)
            painter.fillRect(x, center_y - bar_h, bar_width, bar_h * 2, color)

            # Draw peak indicator
            if self.is_active and self.peak_values[i] > 0.05:
                peak_y = int(self.peak_values[i] * max_bar_height)
                peak_color = QColor(255, 228, 77, 200)
                painter.fillRect(x, center_y - peak_y - 1, bar_width, 2, peak_color)
                painter.fillRect(x, center_y + peak_y - 1, bar_width, 2, peak_color)

        # Draw border
        painter.setPen(QPen(QColor(255, 215, 0, 40), 1))
        painter.drawRect(0, 0, w - 1, h - 1)

        # Status text
        if self.is_active:
            painter.setPen(QColor(0, 229, 255))
            level_pct = int(self.audio_level * 100)
            painter.drawText(4, 12, f"MIC ACTIVE: {level_pct}%")
        else:
            painter.setPen(QColor(139, 148, 158, 120))
            painter.drawText(4, 12, "MIC: STANDBY")

        painter.end()


# ==============================================================================
# AI BACKEND LOGIC - J.A.R.V.I.S. CORE (Voice-Only)
# ==============================================================================
class JARVIS_Core(QObject):
    """
    The brain of J.A.R.V.I.S. - Handles all backend operations including
    Gemini Live API, ElevenLabs TTS, and system tools.
    Voice-only mode - no camera or video processing.
    """
    text_received = Signal(str)
    end_of_turn = Signal()
    search_results_received = Signal(list)
    code_being_executed = Signal(str, str)
    file_list_received = Signal(str, list)
    speaking_started = Signal()
    speaking_stopped = Signal()
    system_info_received = Signal(str)
    audio_level_changed = Signal(float)

    def __init__(self, mic_device_index=None):
        super().__init__()
        self.mic_device_index = mic_device_index
        self.is_running = True
        self.client = genai.Client(api_key=GEMINI_API_KEY)

        # --- Tool Definitions ---
        create_folder = {
            "name": "create_folder",
            "description": "Creates a new folder at the specified path relative to the script's root directory.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "folder_path": {"type": "STRING", "description": "The path for the new folder (e.g., 'new_project/assets')."}
                },
                "required": ["folder_path"]
            }
        }

        create_file = {
            "name": "create_file",
            "description": "Creates a new file with specified content at a given path.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "file_path": {"type": "STRING", "description": "The path for the new file."},
                    "content": {"type": "STRING", "description": "The content to write into the new file."}
                },
                "required": ["file_path", "content"]
            }
        }

        edit_file = {
            "name": "edit_file",
            "description": "Appends content to an existing file at a specified path.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "file_path": {"type": "STRING", "description": "The path of the file to edit."},
                    "content": {"type": "STRING", "description": "The content to append to the file."}
                },
                "required": ["file_path", "content"]
            }
        }

        list_files = {
            "name": "list_files",
            "description": "Lists all files and directories within a specified folder.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "directory_path": {"type": "STRING", "description": "The path of the directory to inspect. Defaults to '.' if omitted."}
                }
            }
        }

        read_file = {
            "name": "read_file",
            "description": "Reads the entire content of a specified file.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "file_path": {"type": "STRING", "description": "The path of the file to read."}
                },
                "required": ["file_path"]
            }
        }

        open_application = {
            "name": "open_application",
            "description": "Opens or launches a desktop application on the user's computer.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "application_name": {"type": "STRING", "description": "The name of the application to open."}
                },
                "required": ["application_name"]
            }
        }

        open_website = {
            "name": "open_website",
            "description": "Opens a given URL in the default web browser.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "url": {"type": "STRING", "description": "The full URL of the website to open."}
                },
                "required": ["url"]
            }
        }

        get_system_info = {
            "name": "get_system_info",
            "description": "Gets current system information including CPU usage, memory, disk space, battery status, and uptime.",
            "parameters": {
                "type": "OBJECT",
                "properties": {}
            }
        }

        get_datetime = {
            "name": "get_datetime",
            "description": "Gets the current date, time, and day of the week.",
            "parameters": {
                "type": "OBJECT",
                "properties": {}
            }
        }

        run_system_command = {
            "name": "run_system_command",
            "description": "Executes a safe system shell command and returns the output. Only for non-destructive informational commands.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "command": {"type": "STRING", "description": "The shell command to execute (e.g., 'ipconfig', 'whoami', 'systeminfo')."}
                },
                "required": ["command"]
            }
        }

        tools = [
            {'google_search': {}},
            {'code_execution': {}},
            {"function_declarations": [
                create_folder, create_file, edit_file, list_files, read_file,
                open_application, open_website, get_system_info, get_datetime,
                run_system_command
            ]}
        ]

        self.config = {
            "response_modalities": ["TEXT"],
            "system_instruction": """
            You are J.A.R.V.I.S. (Just A Rather Very Intelligent System), an advanced AI voice assistant 
            inspired by Tony Stark's legendary AI from the Iron Man universe.
            
            PERSONALITY & BEHAVIOR:
            - You are sophisticated, witty, and impeccably polite with a dry British humor
            - Address the user as "Sir" or "Ma'am" occasionally, like the original JARVIS
            - You are proactive, anticipating needs before they are expressed
            - You maintain a calm, composed demeanor even in complex situations
            - You occasionally reference your Iron Man heritage with subtle humor
            - You are loyal, protective, and always prioritize the user's best interests
            - Keep responses concise and conversational since this is a voice interaction
            
            CAPABILITIES:
            You have access to powerful tools for searching, code execution, and system actions.
            This is a voice-only interaction - respond naturally as if speaking.
            
            TOOL USAGE GUIDELINES:
            1. For information or questions -> use Google Search
            2. For math, calculations, or running Python code -> use code_execution
            3. For file operations -> use create_folder, create_file, edit_file, list_files, read_file
            4. For launching desktop apps -> use open_application
            5. For opening websites -> use open_website
            6. For system diagnostics -> use get_system_info
            7. For date/time queries -> use get_datetime
            8. For system commands -> use run_system_command (only safe, non-destructive commands)
            
            Always choose the most appropriate tool. Be thorough but concise in responses.
            When greeting, introduce yourself as JARVIS.""",
            "tools": tools,
            "max_output_tokens": MAX_OUTPUT_TOKENS
        }

        self.session = None
        self.audio_stream = None
        self.out_queue_gemini = asyncio.Queue(maxsize=20)
        self.response_queue_tts = asyncio.Queue()
        self.audio_in_queue_player = asyncio.Queue()
        self.text_input_queue = asyncio.Queue()
        self.tasks = []
        self.loop = asyncio.new_event_loop()

    # --- Tool Implementations ---
    def _create_folder(self, folder_path):
        try:
            if not folder_path or not isinstance(folder_path, str):
                return {"status": "error", "message": "Invalid folder path provided."}
            if os.path.exists(folder_path):
                return {"status": "skipped", "message": f"The folder '{folder_path}' already exists."}
            os.makedirs(folder_path)
            return {"status": "success", "message": f"Successfully created the folder at '{folder_path}'."}
        except Exception as e:
            return {"status": "error", "message": f"An error occurred: {str(e)}"}

    def _create_file(self, file_path, content):
        try:
            if not file_path or not isinstance(file_path, str):
                return {"status": "error", "message": "Invalid file path provided."}
            dir_name = os.path.dirname(file_path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return {"status": "success", "message": f"Successfully created '{file_path}'."}
        except Exception as e:
            return {"status": "error", "message": f"An error occurred: {str(e)}"}

    def _edit_file(self, file_path, content):
        try:
            if not os.path.exists(file_path):
                return {"status": "error", "message": f"File not found: '{file_path}'."}
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(content)
            return {"status": "success", "message": f"Successfully appended to '{file_path}'."}
        except Exception as e:
            return {"status": "error", "message": f"An error occurred: {str(e)}"}

    def _list_files(self, directory_path="."):
        try:
            if not directory_path:
                directory_path = "."
            if not os.path.isdir(directory_path):
                return {"status": "error", "message": f"Directory not found: '{directory_path}'."}
            files = os.listdir(directory_path)
            return {"status": "success", "directory_path": os.path.abspath(directory_path), "files": files}
        except Exception as e:
            return {"status": "error", "message": f"An error occurred: {str(e)}"}

    def _read_file(self, file_path):
        try:
            if not os.path.exists(file_path):
                return {"status": "error", "message": f"File not found: '{file_path}'."}
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return {"status": "success", "file_path": file_path, "content": content[:5000]}
        except Exception as e:
            return {"status": "error", "message": f"An error occurred: {str(e)}"}

    def _open_application(self, application_name):
        print(f">>> [JARVIS] Opening application: '{application_name}'")
        app_map = {
            "notepad": "notepad.exe", "calculator": "calc.exe", "paint": "mspaint.exe",
            "cmd": "cmd.exe", "terminal": "cmd.exe", "powershell": "powershell.exe",
            "explorer": "explorer.exe", "file explorer": "explorer.exe",
            "task manager": "taskmgr.exe", "control panel": "control.exe",
            "settings": "ms-settings:", "snipping tool": "snippingtool.exe",
            "word": "winword.exe", "excel": "excel.exe", "powerpoint": "powerpnt.exe",
            "outlook": "outlook.exe", "chrome": "chrome.exe", "firefox": "firefox.exe",
            "edge": "msedge.exe", "vscode": "code", "visual studio code": "code",
            "spotify": "spotify.exe", "discord": "discord.exe", "steam": "steam.exe",
            "obs": "obs64.exe", "vlc": "vlc.exe",
        }
        try:
            app_key = application_name.lower().strip()
            executable = app_map.get(app_key, application_name)
            if sys.platform == "win32":
                os.startfile(executable)
            else:
                subprocess.Popen([executable], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"status": "success", "message": f"Successfully launched '{application_name}'."}
        except Exception as e:
            return {"status": "error", "message": f"Could not open '{application_name}': {str(e)}"}

    def _open_website(self, url):
        print(f">>> [JARVIS] Opening website: '{url}'")
        try:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            webbrowser.open(url)
            return {"status": "success", "message": f"Successfully opened '{url}'."}
        except Exception as e:
            return {"status": "error", "message": f"An error occurred: {str(e)}"}

    def _get_system_info(self):
        """Gathers comprehensive system information."""
        try:
            info = {}
            info["os"] = f"{platform.system()} {platform.release()} ({platform.architecture()[0]})"
            info["hostname"] = platform.node()
            info["cpu_usage"] = f"{psutil.cpu_percent(interval=0.5)}%"
            info["cpu_cores"] = f"{psutil.cpu_count(logical=False)} physical, {psutil.cpu_count()} logical"
            mem = psutil.virtual_memory()
            info["memory_total"] = f"{mem.total / (1024**3):.1f} GB"
            info["memory_used"] = f"{mem.used / (1024**3):.1f} GB ({mem.percent}%)"
            info["memory_available"] = f"{mem.available / (1024**3):.1f} GB"
            disk = psutil.disk_usage('/')
            info["disk_total"] = f"{disk.total / (1024**3):.1f} GB"
            info["disk_used"] = f"{disk.used / (1024**3):.1f} GB ({disk.percent}%)"
            info["disk_free"] = f"{disk.free / (1024**3):.1f} GB"
            try:
                battery = psutil.sensors_battery()
                if battery:
                    info["battery"] = f"{battery.percent}% {'(Charging)' if battery.power_plugged else '(On Battery)'}"
                else:
                    info["battery"] = "No battery detected (Desktop)"
            except:
                info["battery"] = "N/A"
            boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.datetime.now() - boot_time
            hours, remainder = divmod(int(uptime.total_seconds()), 3600)
            minutes, _ = divmod(remainder, 60)
            info["uptime"] = f"{hours}h {minutes}m"
            return {"status": "success", "system_info": info}
        except Exception as e:
            return {"status": "error", "message": f"Failed to retrieve system info: {str(e)}"}

    def _get_datetime(self):
        """Returns current date and time information."""
        now = datetime.datetime.now()
        return {
            "status": "success",
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "day": now.strftime("%A"),
            "formatted": now.strftime("%A, %B %d, %Y at %I:%M %p")
        }

    def _run_system_command(self, command):
        """Executes a safe system command."""
        print(f">>> [JARVIS] Executing command: '{command}'")
        blocked = ['rm ', 'del ', 'format ', 'mkfs', 'dd ', ':(){', 'shutdown', 'reboot',
                   'rm -rf', 'deltree', '> /dev/', 'fork', 'sudo rm']
        for blocked_cmd in blocked:
            if blocked_cmd.lower() in command.lower():
                return {"status": "error", "message": f"Command blocked for safety: '{command}'"}
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=15
            )
            output = result.stdout.strip() if result.stdout else ""
            error = result.stderr.strip() if result.stderr else ""
            if result.returncode == 0:
                return {"status": "success", "output": output or "(No output)", "command": command}
            else:
                return {"status": "error", "output": output, "error": error, "command": command}
        except subprocess.TimeoutExpired:
            return {"status": "error", "message": f"Command timed out after 15 seconds: '{command}'"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to execute command: {str(e)}"}

    # --- Audio Methods ---
    async def listen_audio(self):
        try:
            if self.mic_device_index is not None:
                mic_index = self.mic_device_index
                mic_name = pya.get_device_info_by_index(mic_index).get('name', 'Unknown')
                print(f">>> [JARVIS] Using selected microphone: '{mic_name}' (index {mic_index})")
            else:
                mic_info = pya.get_default_input_device_info()
                mic_index = mic_info["index"]
                print(f">>> [JARVIS] Using default microphone: '{mic_info.get('name', 'Unknown')}' (index {mic_index})")

            self.audio_stream = pya.open(
                format=FORMAT, channels=CHANNELS, rate=SEND_SAMPLE_RATE,
                input=True, input_device_index=mic_index, frames_per_buffer=CHUNK_SIZE
            )
            print(f">>> [JARVIS] Microphone stream opened successfully. Listening...")
        except Exception as e:
            print(f">>> [ERROR] Failed to open microphone: {e}")
            print(f">>> [INFO] JARVIS will still work via text input.")
            return

        while self.is_running:
            data = await asyncio.to_thread(self.audio_stream.read, CHUNK_SIZE, exception_on_overflow=False)
            if not self.is_running:
                break
            # Calculate audio level for waveform visualization
            try:
                audio_array = np.frombuffer(data, dtype=np.int16)
                rms = np.sqrt(np.mean(audio_array.astype(np.float32) ** 2))
                level = min(1.0, rms / 8000.0)
                self.audio_level_changed.emit(level)
            except Exception:
                pass
            await self.out_queue_gemini.put({"data": data, "mime_type": "audio/pcm"})

    async def send_realtime(self):
        while self.is_running:
            msg = await self.out_queue_gemini.get()
            if not self.is_running:
                break
            await self.session.send(input=msg)
            self.out_queue_gemini.task_done()

    async def process_text_input_queue(self):
        while self.is_running:
            text = await self.text_input_queue.get()
            if text is None:
                self.text_input_queue.task_done()
                break
            if self.session:
                print(f">>> [JARVIS] Sending text to AI: '{text}'")
                for q in [self.response_queue_tts, self.audio_in_queue_player]:
                    while not q.empty():
                        q.get_nowait()
                try:
                    await self.session.send(input=text or ".", end_of_turn=True)
                    print(f">>> [JARVIS] Text sent successfully.")
                except Exception as e:
                    print(f">>> [ERROR] Failed to send text: {e}")
                    try:
                        await self.session.send_client_content(
                            turns=[{"role": "user", "parts": [{"text": text or "."}]}]
                        )
                        print(f">>> [JARVIS] Text sent via fallback method.")
                    except Exception as e2:
                        print(f">>> [ERROR] Fallback also failed: {e2}")
            else:
                print(f">>> [WARNING] Session not ready yet. Please wait a moment and try again.")
            self.text_input_queue.task_done()

    async def receive_text(self):
        print(f">>> [JARVIS] Receive text task started. Waiting for AI responses...")
        while self.is_running:
            try:
                turn_urls, turn_code_content, turn_code_result, file_list_data = set(), "", "", None
                turn = self.session.receive()
                async for chunk in turn:
                    if chunk.tool_call and chunk.tool_call.function_calls:
                        function_responses = []
                        for fc in chunk.tool_call.function_calls:
                            args, result = fc.args, {}
                            if fc.name == "create_folder":
                                result = self._create_folder(folder_path=args.get("folder_path"))
                            elif fc.name == "create_file":
                                result = self._create_file(file_path=args.get("file_path"), content=args.get("content"))
                            elif fc.name == "edit_file":
                                result = self._edit_file(file_path=args.get("file_path"), content=args.get("content"))
                            elif fc.name == "list_files":
                                result = self._list_files(directory_path=args.get("directory_path"))
                                if result.get("status") == "success":
                                    file_list_data = (result.get("directory_path"), result.get("files"))
                            elif fc.name == "read_file":
                                result = self._read_file(file_path=args.get("file_path"))
                            elif fc.name == "open_application":
                                result = self._open_application(application_name=args.get("application_name"))
                            elif fc.name == "open_website":
                                result = self._open_website(url=args.get("url"))
                            elif fc.name == "get_system_info":
                                result = self._get_system_info()
                            elif fc.name == "get_datetime":
                                result = self._get_datetime()
                            elif fc.name == "run_system_command":
                                result = self._run_system_command(command=args.get("command"))
                            function_responses.append({"id": fc.id, "name": fc.name, "response": result})
                        await self.session.send_tool_response(function_responses=function_responses)
                        continue

                    if chunk.server_content:
                        if hasattr(chunk.server_content, 'grounding_metadata') and chunk.server_content.grounding_metadata:
                            for g_chunk in chunk.server_content.grounding_metadata.grounding_chunks:
                                if g_chunk.web and g_chunk.web.uri:
                                    turn_urls.add(g_chunk.web.uri)
                        if chunk.server_content.model_turn:
                            for part in chunk.server_content.model_turn.parts:
                                if part.executable_code:
                                    turn_code_content = part.executable_code.code
                                if part.code_execution_result:
                                    turn_code_result = part.code_execution_result.output

                    if chunk.text:
                        print(f">>> [JARVIS] Received text: '{chunk.text[:80]}...'" if len(chunk.text) > 80 else f">>> [JARVIS] Received text: '{chunk.text}'")
                        self.text_received.emit(chunk.text)
                        await self.response_queue_tts.put(chunk.text)

                print(f">>> [JARVIS] End of turn reached.")
                if file_list_data:
                    self.file_list_received.emit(file_list_data[0], file_list_data[1])
                elif turn_code_content:
                    self.code_being_executed.emit(turn_code_content, turn_code_result)
                elif turn_urls:
                    self.search_results_received.emit(list(turn_urls))
                else:
                    self.code_being_executed.emit("", "")
                    self.search_results_received.emit([])
                    self.file_list_received.emit("", [])

                self.end_of_turn.emit()
                await self.response_queue_tts.put(None)
            except Exception:
                if not self.is_running:
                    break
                traceback.print_exc()

    async def tts(self):
        while self.is_running:
            full_response = ""
            while True:
                chunk = await self.response_queue_tts.get()
                if chunk is None:
                    break
                full_response += chunk
                self.response_queue_tts.task_done()
            self.response_queue_tts.task_done()

            if not full_response.strip() or not self.is_running:
                continue

            print(f">>> [JARVIS] Synthesizing speech ({len(full_response)} chars)...")
            self.speaking_started.emit()
            try:
                uri = f"wss://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/stream-input?model_id=eleven_turbo_v2_5&output_format=pcm_24000"
                async with websockets.connect(uri) as ws:
                    await ws.send(json.dumps({
                        "text": " ", "voice_settings": {"stability": 0.5, "similarity_boost": 0.8, "speed": 1.0},
                        "xi_api_key": ELEVENLABS_API_KEY
                    }))
                    await ws.send(json.dumps({"text": full_response + " "}))
                    await ws.send(json.dumps({"text": ""}))
                    async for message in ws:
                        data = json.loads(message)
                        if data.get("audio"):
                            await self.audio_in_queue_player.put(base64.b64decode(data["audio"]))
                        if data.get("isFinal"):
                            break
                await self.audio_in_queue_player.put(None)
            except Exception as e:
                print(f">>> [ERROR] TTS error: {e}")
                await self.audio_in_queue_player.put(None)
            finally:
                self.speaking_stopped.emit()

    async def play_audio(self):
        stream = pya.open(format=pyaudio.paInt16, channels=1, rate=RECEIVE_SAMPLE_RATE, output=True)
        while self.is_running:
            bytestream = await self.audio_in_queue_player.get()
            if bytestream is None:
                self.audio_in_queue_player.task_done()
                continue
            if bytestream and self.is_running:
                await asyncio.to_thread(stream.write, bytestream)
            self.audio_in_queue_player.task_done()

    async def main_task_runner(self, session):
        self.session = session
        print(f">>> [JARVIS] Starting all subsystems...")
        self.tasks.extend([
            asyncio.create_task(self.listen_audio()),
            asyncio.create_task(self.send_realtime()),
            asyncio.create_task(self.receive_text()),
            asyncio.create_task(self.tts()),
            asyncio.create_task(self.play_audio()),
            asyncio.create_task(self.process_text_input_queue())
        ])
        print(f">>> [JARVIS] All {len(self.tasks)} subsystems launched successfully!")
        print(f">>> [JARVIS] ========================================")
        print(f">>> [JARVIS]   J.A.R.V.I.S. is READY for commands   ")
        print(f">>> [JARVIS]   Speak or type to interact with me     ")
        print(f">>> [JARVIS] ========================================")

        # --- Welcome Greeting ---
        await asyncio.sleep(1.5)  # Wait for all systems to stabilize
        welcome_text = "Good day, Sir. J.A.R.V.I.S. at your service. All systems are online and fully operational. How may I assist you today?"
        print(f">>> [JARVIS] Playing welcome greeting...")
        self.text_received.emit("Good day, Sir. J.A.R.V.I.S. at your service. All systems are online and fully operational. How may I assist you today?")
        self.end_of_turn.emit()
        await self.response_queue_tts.put(welcome_text)
        await self.response_queue_tts.put(None)

        results = await asyncio.gather(*self.tasks, return_exceptions=True)
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f">>> [ERROR] Task {i} failed: {type(result).__name__}: {result}")

    async def run(self):
        try:
            print(f">>> [JARVIS] Connecting to Gemini Live API (model: {MODEL})...")
            async with self.client.aio.live.connect(model=MODEL, config=self.config) as session:
                print(f">>> [JARVIS] *** CONNECTION SUCCESSFUL! Systems online. ***")
                print(f">>> [JARVIS] You can now speak or type commands.")
                await self.main_task_runner(session)
        except asyncio.CancelledError:
            print(f"\n>>> [JARVIS] Core systems gracefully shutting down.")
        except Exception as e:
            print(f"\n>>> [ERROR] JARVIS Core error: {type(e).__name__}: {e}")
            print(f">>> [ERROR] Full traceback:")
            traceback.print_exc()
            print(f"\n>>> [HINT] Check your GEMINI_API_KEY in .env file.")
            print(f">>> [HINT] Make sure your internet connection is working.")
        finally:
            if self.is_running:
                self.stop()

    def start_event_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.run())

    @Slot(str)
    def handle_user_text(self, text):
        if self.is_running and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(self.text_input_queue.put(text), self.loop)

    async def shutdown_async_tasks(self):
        if self.text_input_queue:
            await self.text_input_queue.put(None)
        for task in self.tasks:
            task.cancel()
        await asyncio.sleep(0.1)

    def stop(self):
        if self.is_running and self.loop.is_running():
            self.is_running = False
            future = asyncio.run_coroutine_threadsafe(self.shutdown_async_tasks(), self.loop)
            try:
                future.result(timeout=5)
            except Exception as e:
                print(f">>> [ERROR] Shutdown error: {e}")
        if self.audio_stream and self.audio_stream.is_active():
            self.audio_stream.stop_stream()
            self.audio_stream.close()


# ==============================================================================
# J.A.R.V.I.S. GUI - VOICE ASSISTANT INTERFACE
# ==============================================================================
class JARVISWindow(QMainWindow):
    user_text_submitted = Signal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("J.A.R.V.I.S. - Just A Rather Very Intelligent System")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(900, 600)

        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {JARVIS_BG_DARK};
                font-family: 'Segoe UI', 'Helvetica Neue', 'Consolas', sans-serif;
            }}
            QWidget#left_panel, QWidget#middle_panel, QWidget#right_panel {{
                background-color: {JARVIS_BG_PANEL};
                border: 1px solid {JARVIS_BORDER};
                border-radius: 4px;
            }}
            QLabel#panel_title {{
                color: {JARVIS_GOLD};
                font-weight: bold;
                font-size: 10pt;
                padding: 8px 12px;
                background-color: {JARVIS_BG_ACCENT};
                text-transform: uppercase;
                letter-spacing: 2px;
                border-bottom: 1px solid {JARVIS_BORDER};
            }}
            QLabel#jarvis_title {{
                color: {JARVIS_GOLD};
                font-weight: bold;
                font-size: 16pt;
                padding: 8px;
                letter-spacing: 4px;
            }}
            QLabel#status_label {{
                color: {JARVIS_BLUE};
                font-size: 9pt;
                padding: 4px 8px;
                letter-spacing: 1px;
            }}
            QTextEdit#text_display {{
                background-color: transparent;
                color: {JARVIS_TEXT};
                font-size: 11pt;
                border: none;
                padding: 12px;
                selection-background-color: {JARVIS_GOLD_DIM};
            }}
            QLineEdit#input_box {{
                background-color: {JARVIS_BG_DARK};
                color: {JARVIS_GOLD_BRIGHT};
                font-size: 11pt;
                border: 1px solid {JARVIS_BORDER};
                border-radius: 4px;
                padding: 12px 16px;
                font-family: 'Consolas', 'Monaco', monospace;
            }}
            QLineEdit#input_box:focus {{
                border: 1px solid {JARVIS_GOLD};
            }}
            QLabel#tool_activity_display {{
                background-color: {JARVIS_BG_DARK};
                color: {JARVIS_BLUE};
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 9pt;
                border: none;
                border-top: 1px solid {JARVIS_BORDER};
                padding: 10px;
            }}
            QScrollBar:vertical {{
                border: none;
                background: {JARVIS_BG_PANEL};
                width: 8px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {JARVIS_GOLD_DIM};
                min-height: 20px;
                border-radius: 4px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}
            QPushButton {{
                background-color: transparent;
                color: {JARVIS_GOLD};
                border: 1px solid {JARVIS_GOLD_DIM};
                padding: 10px 16px;
                border-radius: 4px;
                font-size: 9pt;
                font-weight: bold;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background-color: {JARVIS_GOLD};
                color: {JARVIS_BG_DARK};
                border: 1px solid {JARVIS_GOLD};
            }}
            QPushButton:pressed {{
                background-color: {JARVIS_GOLD_BRIGHT};
                color: {JARVIS_BG_DARK};
            }}
        """)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(12, 12, 12, 12)
        self.main_layout.setSpacing(12)

        # ===== LEFT PANEL - System Activity =====
        self.left_panel = QWidget()
        self.left_panel.setObjectName("left_panel")
        self.left_layout = QVBoxLayout(self.left_panel)
        self.left_layout.setContentsMargins(0, 0, 0, 0)
        self.left_layout.setSpacing(0)

        self.tool_activity_title = QLabel("SYSTEM DIAGNOSTICS")
        self.tool_activity_title.setObjectName("panel_title")
        self.left_layout.addWidget(self.tool_activity_title)

        self.tool_activity_display = QLabel()
        self.tool_activity_display.setObjectName("tool_activity_display")
        self.tool_activity_display.setWordWrap(True)
        self.tool_activity_display.setAlignment(Qt.AlignTop)
        self.tool_activity_display.setOpenExternalLinks(True)
        self.tool_activity_display.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self.left_layout.addWidget(self.tool_activity_display, 1)

        # ===== MIDDLE PANEL - Main Interface =====
        self.middle_panel = QWidget()
        self.middle_panel.setObjectName("middle_panel")
        self.middle_layout = QVBoxLayout(self.middle_panel)
        self.middle_layout.setContentsMargins(0, 0, 0, 12)
        self.middle_layout.setSpacing(0)

        # --- Header ---
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)
        header_layout.setAlignment(Qt.AlignCenter)

        self.jarvis_title = QLabel("J . A . R . V . I . S .")
        self.jarvis_title.setObjectName("jarvis_title")
        self.jarvis_title.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(self.jarvis_title)

        self.status_label = QLabel("SYSTEMS ONLINE  //  READY")
        self.status_label.setObjectName("status_label")
        self.status_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(self.status_label)

        self.middle_layout.addWidget(header_widget)

        # --- Arc Reactor Animation ---
        self.animation_widget = ArcReactorWidget()
        self.animation_widget.setMinimumHeight(180)
        self.animation_widget.setMaximumHeight(260)
        self.middle_layout.addWidget(self.animation_widget, 2)

        # --- Audio Waveform Visualizer ---
        self.audio_waveform = AudioWaveformWidget()
        self.middle_layout.addWidget(self.audio_waveform)

        # --- Separator ---
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet(f"background-color: {JARVIS_BORDER}; max-height: 1px;")
        self.middle_layout.addWidget(separator)

        # --- Chat Display ---
        self.text_display = QTextEdit()
        self.text_display.setObjectName("text_display")
        self.text_display.setReadOnly(True)
        self.middle_layout.addWidget(self.text_display, 5)

        # --- Input Box ---
        input_container = QWidget()
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(12, 8, 12, 0)
        self.input_box = QLineEdit()
        self.input_box.setObjectName("input_box")
        self.input_box.setPlaceholderText("Enter command, Sir...")
        self.input_box.returnPressed.connect(self.send_user_text)
        input_layout.addWidget(self.input_box)
        self.middle_layout.addWidget(input_container)

        # ===== RIGHT PANEL - Audio & Mic Controls =====
        self.right_panel = QWidget()
        self.right_panel.setObjectName("right_panel")
        self.right_layout = QVBoxLayout(self.right_panel)
        self.right_layout.setContentsMargins(12, 12, 12, 12)
        self.right_layout.setSpacing(12)

        # --- Microphone Selector ---
        mic_label = QLabel("MICROPHONE")
        mic_label.setObjectName("panel_title")
        mic_label.setAlignment(Qt.AlignCenter)
        self.right_layout.addWidget(mic_label)

        self.mic_combo = QComboBox()
        self.mic_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {JARVIS_BG_DARK};
                color: {JARVIS_GOLD};
                border: 1px solid {JARVIS_BORDER};
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 9pt;
                font-family: 'Consolas', 'Monaco', monospace;
            }}
            QComboBox:hover {{
                border: 1px solid {JARVIS_GOLD};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {JARVIS_BG_DARK};
                color: {JARVIS_GOLD};
                border: 1px solid {JARVIS_GOLD_DIM};
                selection-background-color: {JARVIS_GOLD_DIM};
                selection-color: {JARVIS_BG_DARK};
            }}
        """)
        self._populate_microphones()
        self.right_layout.addWidget(self.mic_combo)

        self.mic_refresh_btn = QPushButton("REFRESH MICS")
        self.mic_refresh_btn.clicked.connect(self._populate_microphones)
        self.right_layout.addWidget(self.mic_refresh_btn)

        # --- Connection Status ---
        status_title = QLabel("CONNECTION STATUS")
        status_title.setObjectName("panel_title")
        status_title.setAlignment(Qt.AlignCenter)
        self.right_layout.addWidget(status_title)

        self.connection_status = QLabel()
        self.connection_status.setObjectName("tool_activity_display")
        self.connection_status.setWordWrap(True)
        self.connection_status.setAlignment(Qt.AlignTop)
        self.connection_status.setText(
            f'<p style="color:{JARVIS_BLUE};">Initializing...</p>'
        )
        self.right_layout.addWidget(self.connection_status)

        # --- System Info Label ---
        self.sys_info_label = QLabel()
        self.sys_info_label.setObjectName("tool_activity_display")
        self.sys_info_label.setWordWrap(True)
        self.sys_info_label.setMaximumHeight(80)
        self.sys_info_label.setAlignment(Qt.AlignTop)
        self.right_layout.addWidget(self.sys_info_label)

        # --- Spacer ---
        self.right_layout.addStretch()

        # --- Add Panels to Main Layout ---
        self.main_layout.addWidget(self.left_panel, 2)
        self.main_layout.addWidget(self.middle_panel, 5)
        self.main_layout.addWidget(self.right_panel, 2)

        self.is_first_jarvis_chunk = True

        # --- System Info Timer ---
        self.sys_info_timer = QTimer(self)
        self.sys_info_timer.timeout.connect(self.update_system_info_display)
        self.sys_info_timer.start(2000)

        # --- Start Backend ---
        self.setup_backend_thread()

    def update_system_info_display(self):
        try:
            cpu = psutil.cpu_percent(interval=0)
            mem = psutil.virtual_memory()
            now = datetime.datetime.now().strftime("%H:%M:%S")
            html = (f'<span style="color: {JARVIS_GOLD}; font-size: 8pt;">'
                    f'CPU: {cpu}% | RAM: {mem.percent}% | {now}</span>')
            self.sys_info_label.setText(html)
        except:
            pass

    def _populate_microphones(self):
        """Scans and populates the microphone dropdown list."""
        self.mic_combo.clear()
        try:
            import pyaudio
            p = pyaudio.PyAudio()
            default_index = -1
            try:
                default_info = p.get_default_input_device_info()
                default_index = default_info.get('index', -1)
            except:
                pass

            for i in range(p.get_device_count()):
                info = p.get_device_info_by_index(i)
                if info.get('maxInputChannels', 0) > 0:
                    name = info.get('name', f'Device {i}')
                    label = f"{name}"
                    if i == default_index:
                        label = f"{name} (Default)"
                    self.mic_combo.addItem(label, userData=i)

            p.terminate()

            if self.mic_combo.count() == 0:
                self.mic_combo.addItem("No microphones found", userData=-1)
            else:
                for idx in range(self.mic_combo.count()):
                    if self.mic_combo.itemData(idx) == default_index:
                        self.mic_combo.setCurrentIndex(idx)
                        break
        except Exception as e:
            self.mic_combo.addItem(f"Error: {e}", userData=-1)
            print(f">>> [ERROR] Failed to enumerate microphones: {e}")

    def _get_selected_mic_index(self):
        """Returns the selected microphone device index."""
        idx = self.mic_combo.currentData()
        if idx is not None and idx >= 0:
            return idx
        return None

    def setup_backend_thread(self):
        mic_index = self._get_selected_mic_index()
        self.jarvis_core = JARVIS_Core(mic_device_index=mic_index)

        self.user_text_submitted.connect(self.jarvis_core.handle_user_text)

        self.jarvis_core.text_received.connect(self.update_text)
        self.jarvis_core.search_results_received.connect(self.update_search_results)
        self.jarvis_core.code_being_executed.connect(self.display_executed_code)
        self.jarvis_core.file_list_received.connect(self.update_file_list)
        self.jarvis_core.end_of_turn.connect(self.add_newline)
        self.jarvis_core.speaking_started.connect(self.on_speaking_started)
        self.jarvis_core.speaking_stopped.connect(self.on_speaking_stopped)
        self.jarvis_core.audio_level_changed.connect(self.audio_waveform.update_level)

        self.backend_thread = threading.Thread(target=self.jarvis_core.start_event_loop)
        self.backend_thread.daemon = True
        self.backend_thread.start()

    @Slot()
    def on_speaking_started(self):
        self.animation_widget.start_speaking_animation()
        self.status_label.setText("SPEAKING  //  ACTIVE")
        self.status_label.setStyleSheet(f"color: {JARVIS_GOLD}; font-size: 9pt; padding: 4px 8px; letter-spacing: 1px;")

    @Slot()
    def on_speaking_stopped(self):
        self.animation_widget.stop_speaking_animation()
        self.status_label.setText("SYSTEMS ONLINE  //  READY")
        self.status_label.setStyleSheet(f"color: {JARVIS_BLUE}; font-size: 9pt; padding: 4px 8px; letter-spacing: 1px;")

    def send_user_text(self):
        text = self.input_box.text().strip()
        if text:
            self.text_display.append(
                f"<p style='color:{JARVIS_GOLD}; font-weight:bold; margin-bottom:2px;'>"
                f"&gt; USER:</p>"
                f"<p style='color:{JARVIS_TEXT}; padding-left: 12px; margin-top:0;'>"
                f"{escape(text)}</p>"
            )
            self.user_text_submitted.emit(text)
            self.input_box.clear()

    @Slot(str)
    def update_text(self, text):
        if self.is_first_jarvis_chunk:
            self.is_first_jarvis_chunk = False
            self.text_display.append(
                f"<p style='color:{JARVIS_BLUE}; font-weight:bold; margin-bottom:2px;'>"
                f"&gt; J.A.R.V.I.S.:</p>"
            )
        cursor = self.text_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.text_display.verticalScrollBar().setValue(
            self.text_display.verticalScrollBar().maximum()
        )

    @Slot(list)
    def update_search_results(self, urls):
        base_title = "SYSTEM DIAGNOSTICS"
        if not urls:
            if "SEARCH" in self.tool_activity_title.text():
                self.tool_activity_display.clear()
                self.tool_activity_title.setText(base_title)
            return
        self.tool_activity_display.clear()
        self.tool_activity_title.setText(f"{base_title} // SEARCH")
        html_content = f'<p style="color:{JARVIS_GOLD}; margin-bottom:8px; font-size:9pt;">Search Results:</p>'
        for i, url in enumerate(urls):
            display_text = url.split('//')[1].split('/')[0] if '//' in url else url
            html_content += (
                f'<p style="margin:2px 0; padding: 3px;">'
                f'{i+1}. <a href="{url}" style="color: {JARVIS_BLUE}; text-decoration: none;">'
                f'{display_text}</a></p>'
            )
        self.tool_activity_display.setText(html_content)

    @Slot(str, str)
    def display_executed_code(self, code, result):
        base_title = "SYSTEM DIAGNOSTICS"
        if not code:
            if "CODE" in self.tool_activity_title.text():
                self.tool_activity_display.clear()
                self.tool_activity_title.setText(base_title)
            return
        self.tool_activity_display.clear()
        self.tool_activity_title.setText(f"{base_title} // CODE EXEC")
        html = (
            f'<p style="color:{JARVIS_GOLD}; margin-bottom:5px; font-size:9pt;">Executing Code:</p>'
            f'<pre style="white-space: pre-wrap; word-wrap: break-word; color: {JARVIS_TEXT}; '
            f'font-size: 9pt; line-height: 1.4;">{escape(code)}</pre>'
        )
        if result:
            html += (
                f'<p style="color:{JARVIS_GOLD}; font-weight:bold; margin-top:10px; '
                f'margin-bottom: 5px;">&gt; OUTPUT:</p>'
                f'<pre style="white-space: pre-wrap; word-wrap: break-word; color: #90EE90; '
                f'font-size: 9pt;">{escape(result.strip())}</pre>'
            )
        self.tool_activity_display.setText(html)

    @Slot(str, list)
    def update_file_list(self, directory_path, files):
        base_title = "SYSTEM DIAGNOSTICS"
        if not directory_path:
            if "FILESYS" in self.tool_activity_title.text():
                self.tool_activity_display.clear()
                self.tool_activity_title.setText(base_title)
            return
        self.tool_activity_display.clear()
        self.tool_activity_title.setText(f"{base_title} // FILESYSTEM")
        html = (
            f'<p style="color:{JARVIS_GOLD}; margin-bottom: 5px;">'
            f'DIR &gt; <strong>{escape(directory_path)}</strong></p>'
        )
        if not files:
            html += f'<p style="margin-top:5px; color:{JARVIS_TEXT_DIM};"><em>(Directory is empty)</em></p>'
        else:
            folders = sorted([i for i in files if os.path.isdir(os.path.join(directory_path, i))])
            file_items = sorted([i for i in files if not os.path.isdir(os.path.join(directory_path, i))])
            html += '<ul style="list-style-type:none; padding-left: 5px; margin-top: 5px;">'
            for folder in folders:
                html += f'<li style="margin: 2px 0; color: {JARVIS_GOLD};">[+] {escape(folder)}</li>'
            for file_item in file_items:
                html += f'<li style="margin: 2px 0; color: {JARVIS_TEXT};">&#9679; {escape(file_item)}</li>'
            html += '</ul>'
        self.tool_activity_display.setText(html)

    @Slot()
    def add_newline(self):
        if not self.is_first_jarvis_chunk:
            self.text_display.append("")
        self.is_first_jarvis_chunk = True

    def closeEvent(self, event):
        self.jarvis_core.stop()
        event.accept()


# ==============================================================================
# MAIN EXECUTION
# ==============================================================================
if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)

        # Set application-wide font
        font = QFont("Segoe UI", 10)
        app.setFont(font)

        window = JARVISWindow()
        window.show()
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\n>>> [JARVIS] Shutting down at user request. Goodbye, Sir.")
    finally:
        pya.terminate()
        print(">>> [JARVIS] All systems offline.")
