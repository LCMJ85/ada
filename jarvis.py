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
import random
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
MODEL = "gemini-2.0-flash-live-001"
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
JARVIS_AMBER = "#FF8C00"
JARVIS_AMBER_BRIGHT = "#FFA500"

# --- Initialize Clients ---
pya = pyaudio.PyAudio()


# ==============================================================================
# HOLOGRAPHIC SPHERE WIDGET (Iron Man Golden Globe Style)
# ==============================================================================
class HolographicSphereWidget(QWidget):
    """
    A large golden holographic sphere inspired by Tony Stark's JARVIS hologram.
    Features rotating wireframe globe, energy particles, and radial energy lines.
    Pulses and intensifies when JARVIS is speaking.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(350)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Animation state
        self.angle_y = 0
        self.angle_x = 0
        self.angle_z = 0
        self.is_speaking = False
        self.pulse_phase = 0
        self.energy_phase = 0
        self.particle_phase = 0
        self.breath_phase = 0

        # Pre-generate sphere wireframe points
        self.sphere_points = []
        self.longitude_lines = []
        self.latitude_lines = []
        self._generate_sphere_geometry()

        # Floating particles
        self.particles = []
        for _ in range(60):
            self.particles.append({
                'angle': random.uniform(0, 360),
                'dist': random.uniform(0.5, 1.4),
                'speed': random.uniform(0.3, 1.5),
                'size': random.uniform(1, 3),
                'phase': random.uniform(0, math.pi * 2),
                'y_offset': random.uniform(-0.8, 0.8),
            })

        # Energy rays
        self.rays = []
        for i in range(24):
            self.rays.append({
                'angle': (360 / 24) * i,
                'length': random.uniform(0.3, 0.7),
                'speed': random.uniform(0.5, 2.0),
                'phase': random.uniform(0, math.pi * 2),
            })

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(20)

    def _generate_sphere_geometry(self):
        """Generate 3D sphere wireframe points."""
        # Longitude lines (vertical circles)
        num_lon = 16
        num_points = 30
        for i in range(num_lon):
            lon_angle = (360 / num_lon) * i
            line = []
            for j in range(num_points + 1):
                lat_angle = -90 + (180 / num_points) * j
                x = math.cos(math.radians(lat_angle)) * math.cos(math.radians(lon_angle))
                y = math.sin(math.radians(lat_angle))
                z = math.cos(math.radians(lat_angle)) * math.sin(math.radians(lon_angle))
                line.append((x, y, z))
            self.longitude_lines.append(line)

        # Latitude lines (horizontal circles)
        num_lat = 10
        for i in range(1, num_lat):
            lat_angle = -90 + (180 / num_lat) * i
            line = []
            for j in range(num_points + 1):
                lon_angle = (360 / num_points) * j
                x = math.cos(math.radians(lat_angle)) * math.cos(math.radians(lon_angle))
                y = math.sin(math.radians(lat_angle))
                z = math.cos(math.radians(lat_angle)) * math.sin(math.radians(lon_angle))
                line.append((x, y, z))
            self.latitude_lines.append(line)

    def start_speaking_animation(self):
        self.is_speaking = True

    def stop_speaking_animation(self):
        self.is_speaking = False

    def update_animation(self):
        speed = 1.5 if self.is_speaking else 0.6
        self.angle_y += 0.4 * speed
        self.angle_x += 0.15 * speed
        self.angle_z += 0.1 * speed
        self.energy_phase += 0.08 * speed
        self.particle_phase += 0.05 * speed
        self.breath_phase += 0.03

        if self.is_speaking:
            self.pulse_phase += 0.12
            if self.pulse_phase > math.pi * 2:
                self.pulse_phase -= math.pi * 2

        if self.angle_y >= 360:
            self.angle_y -= 360

        self.update()

    def _rotate_point(self, x, y, z):
        """Apply 3D rotation to a point."""
        # Rotate around Y axis
        ry = math.radians(self.angle_y)
        x2 = x * math.cos(ry) - z * math.sin(ry)
        z2 = x * math.sin(ry) + z * math.cos(ry)

        # Rotate around X axis (slight tilt)
        rx = math.radians(self.angle_x * 0.3)
        y2 = y * math.cos(rx) - z2 * math.sin(rx)
        z3 = y * math.sin(rx) + z2 * math.cos(rx)

        return x2, y2, z3

    def _project(self, x, y, z, cx, cy, radius):
        """Project 3D point to 2D screen coordinates."""
        perspective = 3.0
        scale = perspective / (perspective + z * 0.5)
        sx = cx + x * radius * scale
        sy = cy - y * radius * scale
        return sx, sy, scale

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(10, 10, 15, 0))

        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        base_radius = min(w, h) / 2 - 30

        # Pulse when speaking
        pulse = 1.0
        if self.is_speaking:
            pulse = 1.0 + 0.06 * math.sin(self.pulse_phase)
        breath = 1.0 + 0.015 * math.sin(self.breath_phase)
        radius = base_radius * pulse * breath

        # === OUTER GLOW ===
        glow_r = radius * 1.6
        glow_gradient = QRadialGradient(cx, cy, glow_r)
        glow_alpha = 80 if self.is_speaking else 35
        glow_gradient.setColorAt(0, QColor(255, 165, 0, glow_alpha))
        glow_gradient.setColorAt(0.3, QColor(255, 140, 0, glow_alpha // 2))
        glow_gradient.setColorAt(0.6, QColor(255, 100, 0, glow_alpha // 4))
        glow_gradient.setColorAt(1, QColor(255, 80, 0, 0))
        painter.setBrush(QBrush(glow_gradient))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(int(cx - glow_r), int(cy - glow_r), int(glow_r * 2), int(glow_r * 2))

        # === ENERGY RAYS (radial lines from center) ===
        for ray in self.rays:
            ray_angle = math.radians(ray['angle'] + self.angle_y * 0.5)
            ray_len = radius * (ray['length'] + 0.2 * math.sin(self.energy_phase * ray['speed'] + ray['phase']))
            if self.is_speaking:
                ray_len *= 1.4
            end_x = cx + math.cos(ray_angle) * (radius * 0.9 + ray_len)
            end_y = cy + math.sin(ray_angle) * (radius * 0.9 + ray_len)
            start_x = cx + math.cos(ray_angle) * radius * 0.85
            start_y = cy + math.sin(ray_angle) * radius * 0.85

            alpha = int(40 + 30 * math.sin(self.energy_phase * ray['speed'] + ray['phase']))
            if self.is_speaking:
                alpha = min(255, alpha + 40)
            pen = QPen(QColor(255, 180, 0, alpha), 1)
            painter.setPen(pen)
            painter.drawLine(int(start_x), int(start_y), int(end_x), int(end_y))

        # === WIREFRAME SPHERE - Longitude Lines ===
        for line in self.longitude_lines:
            for j in range(len(line) - 1):
                x1, y1, z1 = self._rotate_point(*line[j])
                x2, y2, z2 = self._rotate_point(*line[j + 1])
                sx1, sy1, s1 = self._project(x1, y1, z1, cx, cy, radius * 0.85)
                sx2, sy2, s2 = self._project(x2, y2, z2, cx, cy, radius * 0.85)

                # Depth-based alpha
                avg_z = (z1 + z2) / 2
                alpha = int(max(30, min(200, 120 + avg_z * 80)))
                if self.is_speaking:
                    alpha = min(255, alpha + 40)

                pen = QPen(QColor(255, 180, 40, alpha), max(0.5, 1.2 * ((s1 + s2) / 2)))
                painter.setPen(pen)
                painter.drawLine(int(sx1), int(sy1), int(sx2), int(sy2))

        # === WIREFRAME SPHERE - Latitude Lines ===
        for line in self.latitude_lines:
            for j in range(len(line) - 1):
                x1, y1, z1 = self._rotate_point(*line[j])
                x2, y2, z2 = self._rotate_point(*line[j + 1])
                sx1, sy1, s1 = self._project(x1, y1, z1, cx, cy, radius * 0.85)
                sx2, sy2, s2 = self._project(x2, y2, z2, cx, cy, radius * 0.85)

                avg_z = (z1 + z2) / 2
                alpha = int(max(20, min(160, 90 + avg_z * 70)))
                if self.is_speaking:
                    alpha = min(255, alpha + 30)

                pen = QPen(QColor(255, 200, 60, alpha), max(0.4, 1.0 * ((s1 + s2) / 2)))
                painter.setPen(pen)
                painter.drawLine(int(sx1), int(sy1), int(sx2), int(sy2))

        # === INNER SPHERE GLOW ===
        inner_r = radius * 0.4
        inner_gradient = QRadialGradient(cx, cy, inner_r)
        if self.is_speaking:
            inner_gradient.setColorAt(0, QColor(255, 220, 100, 180))
            inner_gradient.setColorAt(0.4, QColor(255, 165, 0, 100))
            inner_gradient.setColorAt(0.8, QColor(255, 120, 0, 40))
            inner_gradient.setColorAt(1, QColor(255, 100, 0, 0))
        else:
            inner_gradient.setColorAt(0, QColor(255, 200, 80, 120))
            inner_gradient.setColorAt(0.4, QColor(255, 150, 0, 60))
            inner_gradient.setColorAt(0.8, QColor(255, 120, 0, 20))
            inner_gradient.setColorAt(1, QColor(255, 100, 0, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(inner_gradient))
        painter.drawEllipse(int(cx - inner_r), int(cy - inner_r), int(inner_r * 2), int(inner_r * 2))

        # === BRIGHT CORE ===
        core_r = radius * 0.12 * pulse
        core_gradient = QRadialGradient(cx, cy, core_r)
        core_gradient.setColorAt(0, QColor(255, 255, 255, 255))
        core_gradient.setColorAt(0.3, QColor(255, 230, 150, 220))
        core_gradient.setColorAt(0.6, QColor(255, 180, 50, 150))
        core_gradient.setColorAt(1, QColor(255, 140, 0, 0))
        painter.setBrush(QBrush(core_gradient))
        painter.drawEllipse(int(cx - core_r), int(cy - core_r), int(core_r * 2), int(core_r * 2))

        # === FLOATING PARTICLES ===
        for p in self.particles:
            p_angle = math.radians(p['angle'] + self.particle_phase * p['speed'] * 60)
            dist = radius * p['dist'] + radius * 0.1 * math.sin(self.energy_phase * p['speed'] + p['phase'])
            if self.is_speaking:
                dist *= 1.15

            px = cx + math.cos(p_angle) * dist
            py = cy + math.sin(p_angle) * dist * 0.6 + p['y_offset'] * radius * 0.3

            alpha = int(80 + 60 * math.sin(self.energy_phase + p['phase']))
            if self.is_speaking:
                alpha = min(255, alpha + 60)
            size = p['size'] * pulse

            p_gradient = QRadialGradient(px, py, size * 2)
            p_gradient.setColorAt(0, QColor(255, 200, 50, alpha))
            p_gradient.setColorAt(0.5, QColor(255, 160, 0, alpha // 2))
            p_gradient.setColorAt(1, QColor(255, 120, 0, 0))
            painter.setBrush(QBrush(p_gradient))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(int(px - size * 2), int(py - size * 2), int(size * 4), int(size * 4))

        # === OUTER RING ===
        ring_r = radius * 0.92
        ring_alpha = 120 if self.is_speaking else 60
        pen = QPen(QColor(255, 180, 0, ring_alpha), 1.5)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(int(cx - ring_r), int(cy - ring_r), int(ring_r * 2), int(ring_r * 2))

        # === SECOND OUTER RING ===
        ring2_r = radius * 0.96
        pen2 = QPen(QColor(255, 200, 50, ring_alpha // 2), 0.8)
        painter.setPen(pen2)
        painter.drawEllipse(int(cx - ring2_r), int(cy - ring2_r), int(ring2_r * 2), int(ring2_r * 2))

        painter.end()


# ==============================================================================
# AUDIO WAVEFORM VISUALIZER (Microphone Level Indicator)
# ==============================================================================
class AudioWaveformWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(60)
        self.setMaximumHeight(70)
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
        w, h = self.width(), self.height()
        painter.fillRect(0, 0, w, h, QColor(10, 10, 15))

        bar_width = max(2, (w - (self.num_bars + 1) * 2) // self.num_bars)
        spacing = 2
        total_width = self.num_bars * (bar_width + spacing)
        start_x = (w - total_width) // 2
        center_y = h // 2
        max_bar_height = (h // 2) - 4

        for i in range(self.num_bars):
            x = start_x + i * (bar_width + spacing)
            bar_h = max(1, int(self.bar_values[i] * max_bar_height))

            if self.bar_values[i] > 0.7:
                color = QColor(255, 68, 68)
            elif self.bar_values[i] > 0.4:
                color = QColor(255, 215, 0)
            else:
                color = QColor(255, 165, 0)
            if not self.is_active:
                color = QColor(255, 165, 0, 40)

            painter.fillRect(x, center_y - bar_h, bar_width, bar_h * 2, color)

            if self.is_active and self.peak_values[i] > 0.05:
                peak_y = int(self.peak_values[i] * max_bar_height)
                painter.fillRect(x, center_y - peak_y - 1, bar_width, 2, QColor(255, 228, 77, 200))
                painter.fillRect(x, center_y + peak_y - 1, bar_width, 2, QColor(255, 228, 77, 200))

        painter.setPen(QPen(QColor(255, 165, 0, 40), 1))
        painter.drawRect(0, 0, w - 1, h - 1)

        if self.is_active:
            painter.setPen(QColor(255, 200, 50))
            painter.drawText(4, 12, f"MIC ACTIVE: {int(self.audio_level * 100)}%")
        else:
            painter.setPen(QColor(139, 148, 158, 120))
            painter.drawText(4, 12, "MIC: STANDBY")
        painter.end()


# ==============================================================================
# AI BACKEND LOGIC - J.A.R.V.I.S. CORE (Voice-Only)
# ==============================================================================
class JARVIS_Core(QObject):
    text_received = Signal(str)
    end_of_turn = Signal()
    search_results_received = Signal(list)
    code_being_executed = Signal(str, str)
    file_list_received = Signal(str, list)
    speaking_started = Signal()
    speaking_stopped = Signal()
    system_info_received = Signal(str)
    audio_level_changed = Signal(float)
    connection_status_changed = Signal(str)  # NEW: update connection status in GUI

    def __init__(self, mic_device_index=None):
        super().__init__()
        self.mic_device_index = mic_device_index
        self.is_running = True
        self.client = genai.Client(api_key=GEMINI_API_KEY)

        # --- Tool Definitions ---
        create_folder = {
            "name": "create_folder",
            "description": "Creates a new folder at the specified path.",
            "parameters": {"type": "OBJECT", "properties": {
                "folder_path": {"type": "STRING", "description": "The path for the new folder."}
            }, "required": ["folder_path"]}
        }
        create_file = {
            "name": "create_file",
            "description": "Creates a new file with specified content.",
            "parameters": {"type": "OBJECT", "properties": {
                "file_path": {"type": "STRING", "description": "The path for the new file."},
                "content": {"type": "STRING", "description": "The content to write."}
            }, "required": ["file_path", "content"]}
        }
        edit_file = {
            "name": "edit_file",
            "description": "Appends content to an existing file.",
            "parameters": {"type": "OBJECT", "properties": {
                "file_path": {"type": "STRING", "description": "The path of the file."},
                "content": {"type": "STRING", "description": "The content to append."}
            }, "required": ["file_path", "content"]}
        }
        list_files = {
            "name": "list_files",
            "description": "Lists all files and directories within a folder.",
            "parameters": {"type": "OBJECT", "properties": {
                "directory_path": {"type": "STRING", "description": "The directory path. Defaults to '.'."}
            }}
        }
        read_file = {
            "name": "read_file",
            "description": "Reads the content of a file.",
            "parameters": {"type": "OBJECT", "properties": {
                "file_path": {"type": "STRING", "description": "The path of the file."}
            }, "required": ["file_path"]}
        }
        open_application = {
            "name": "open_application",
            "description": "Opens a desktop application.",
            "parameters": {"type": "OBJECT", "properties": {
                "application_name": {"type": "STRING", "description": "The application name."}
            }, "required": ["application_name"]}
        }
        open_website = {
            "name": "open_website",
            "description": "Opens a URL in the browser.",
            "parameters": {"type": "OBJECT", "properties": {
                "url": {"type": "STRING", "description": "The URL to open."}
            }, "required": ["url"]}
        }
        get_system_info = {
            "name": "get_system_info",
            "description": "Gets system info: CPU, memory, disk, battery, uptime.",
            "parameters": {"type": "OBJECT", "properties": {}}
        }
        get_datetime = {
            "name": "get_datetime",
            "description": "Gets current date, time, and day.",
            "parameters": {"type": "OBJECT", "properties": {}}
        }
        run_system_command = {
            "name": "run_system_command",
            "description": "Executes a safe system command.",
            "parameters": {"type": "OBJECT", "properties": {
                "command": {"type": "STRING", "description": "The command to execute."}
            }, "required": ["command"]}
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
            if not folder_path: return {"status": "error", "message": "Invalid path."}
            if os.path.exists(folder_path): return {"status": "skipped", "message": f"'{folder_path}' already exists."}
            os.makedirs(folder_path)
            return {"status": "success", "message": f"Created '{folder_path}'."}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _create_file(self, file_path, content):
        try:
            if not file_path: return {"status": "error", "message": "Invalid path."}
            d = os.path.dirname(file_path)
            if d: os.makedirs(d, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f: f.write(content)
            return {"status": "success", "message": f"Created '{file_path}'."}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _edit_file(self, file_path, content):
        try:
            if not file_path or not os.path.exists(file_path):
                return {"status": "error", "message": f"'{file_path}' not found."}
            with open(file_path, 'a', encoding='utf-8') as f: f.write(content)
            return {"status": "success", "message": f"Appended to '{file_path}'."}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _list_files(self, directory_path="."):
        try:
            p = directory_path or "."
            if not os.path.isdir(p): return {"status": "error", "message": f"'{p}' is not a directory."}
            return {"status": "success", "directory_path": p, "files": os.listdir(p)}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _read_file(self, file_path):
        try:
            if not file_path or not os.path.exists(file_path):
                return {"status": "error", "message": f"'{file_path}' not found."}
            with open(file_path, 'r', encoding='utf-8') as f: content = f.read(10000)
            return {"status": "success", "content": content}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _open_application(self, application_name):
        app_map = {
            "notepad": "notepad.exe", "calculator": "calc.exe", "paint": "mspaint.exe",
            "cmd": "cmd.exe", "powershell": "powershell.exe", "explorer": "explorer.exe",
            "chrome": "chrome.exe", "firefox": "firefox.exe", "edge": "msedge.exe",
            "word": "winword.exe", "excel": "excel.exe", "powerpoint": "powerpnt.exe",
            "vscode": "code", "visual studio code": "code", "spotify": "spotify.exe",
            "discord": "discord.exe", "slack": "slack.exe", "teams": "teams.exe",
            "obs": "obs64.exe", "vlc": "vlc.exe", "steam": "steam.exe",
        }
        try:
            name = application_name.lower().strip()
            cmd = app_map.get(name, application_name)
            subprocess.Popen(cmd, shell=True)
            return {"status": "success", "message": f"Launched '{application_name}'."}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _open_website(self, url):
        try:
            if not url.startswith(('http://', 'https://')): url = 'https://' + url
            webbrowser.open(url)
            return {"status": "success", "message": f"Opened '{url}'."}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _get_system_info(self):
        try:
            cpu = psutil.cpu_percent(interval=0.5)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            info = {
                "cpu_percent": cpu, "ram_total_gb": round(mem.total / (1024**3), 1),
                "ram_used_percent": mem.percent,
                "disk_total_gb": round(disk.total / (1024**3), 1),
                "disk_used_percent": round(disk.used / disk.total * 100, 1),
                "os": f"{platform.system()} {platform.release()}",
                "hostname": platform.node(),
            }
            try:
                bat = psutil.sensors_battery()
                if bat: info["battery_percent"] = bat.percent; info["plugged_in"] = bat.power_plugged
            except: pass
            return {"status": "success", **info}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _get_datetime(self):
        now = datetime.datetime.now()
        return {"date": now.strftime("%Y-%m-%d"), "time": now.strftime("%H:%M:%S"), "day": now.strftime("%A")}

    def _run_system_command(self, command):
        blocked = ['rm ', 'del ', 'format ', 'mkfs', 'dd ', ':(){', 'shutdown', 'reboot',
                   'rmdir', 'rd ', '> /dev', 'fork', 'kill', 'taskkill']
        if any(b in command.lower() for b in blocked):
            return {"status": "blocked", "message": f"Command '{command}' is blocked for safety."}
        try:
            r = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=15)
            return {"status": "success", "stdout": r.stdout[:3000], "stderr": r.stderr[:1000]}
        except subprocess.TimeoutExpired:
            return {"status": "error", "message": "Command timed out."}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # --- Audio & Communication ---
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

            # Open mic stream in a thread to avoid blocking
            self.audio_stream = await asyncio.to_thread(
                pya.open,
                format=FORMAT, channels=CHANNELS, rate=SEND_SAMPLE_RATE,
                input=True, input_device_index=mic_index, frames_per_buffer=CHUNK_SIZE
            )
            print(f">>> [JARVIS] Microphone stream opened successfully! Listening...")
            self.connection_status_changed.emit("MIC_READY")
        except Exception as e:
            print(f">>> [ERROR] Failed to open microphone: {e}")
            print(f">>> [INFO] Try selecting a different microphone from the dropdown.")
            self.connection_status_changed.emit(f"MIC_ERROR: {e}")
            return

        while self.is_running:
            try:
                data = await asyncio.to_thread(self.audio_stream.read, CHUNK_SIZE, exception_on_overflow=False)
            except Exception as e:
                print(f">>> [ERROR] Mic read error: {e}")
                break
            if not self.is_running:
                break
            # Calculate audio level for waveform
            try:
                audio_array = np.frombuffer(data, dtype=np.int16)
                rms = np.sqrt(np.mean(audio_array.astype(np.float32) ** 2))
                level = min(1.0, rms / 8000.0)
                self.audio_level_changed.emit(level)
            except:
                pass
            await self.out_queue_gemini.put({"data": data, "mime_type": "audio/pcm"})

    async def send_realtime(self):
        while self.is_running:
            data = await self.out_queue_gemini.get()
            if not self.is_running: break
            try:
                if self.session:
                    try:
                        await self.session.send_realtime_input(audio=data)
                    except AttributeError:
                        await self.session.send(input=data)
            except Exception as e:
                if self.is_running:
                    print(f">>> [ERROR] Send realtime error: {e}")

    async def process_text_input_queue(self):
        while self.is_running:
            text = await self.text_input_queue.get()
            if text is None:
                break
            if self.session:
                print(f">>> [JARVIS] Sending text to AI: '{text}'")
                # Clear queues
                for q in [self.response_queue_tts, self.audio_in_queue_player]:
                    while not q.empty():
                        try: q.get_nowait()
                        except: break
                try:
                    await self.session.send_client_content(
                        turns=[{"role": "user", "parts": [{"text": text or "."}]}],
                        turn_complete=True
                    )
                    print(f">>> [JARVIS] Text sent successfully via send_client_content.")
                except Exception as e:
                    print(f">>> [ERROR] send_client_content failed: {e}")
                    try:
                        await self.session.send(input=text or ".", end_of_turn=True)
                        print(f">>> [JARVIS] Text sent via fallback send().")
                    except Exception as e2:
                        print(f">>> [ERROR] Fallback also failed: {e2}")
            else:
                print(f">>> [WARNING] Session not ready. Please wait and try again.")
            self.text_input_queue.task_done()

    async def receive_text(self):
        print(f">>> [JARVIS] Receive text task started.")
        while self.is_running:
            try:
                turn_urls, turn_code_content, turn_code_result, file_list_data = set(), "", "", None
                turn = self.session.receive()
                async for chunk in turn:
                    if chunk.tool_call and chunk.tool_call.function_calls:
                        function_responses = []
                        for fc in chunk.tool_call.function_calls:
                            args, result = fc.args, {}
                            if fc.name == "create_folder": result = self._create_folder(folder_path=args.get("folder_path"))
                            elif fc.name == "create_file": result = self._create_file(file_path=args.get("file_path"), content=args.get("content"))
                            elif fc.name == "edit_file": result = self._edit_file(file_path=args.get("file_path"), content=args.get("content"))
                            elif fc.name == "list_files":
                                result = self._list_files(directory_path=args.get("directory_path"))
                                if result.get("status") == "success": file_list_data = (result.get("directory_path"), result.get("files"))
                            elif fc.name == "read_file": result = self._read_file(file_path=args.get("file_path"))
                            elif fc.name == "open_application": result = self._open_application(application_name=args.get("application_name"))
                            elif fc.name == "open_website": result = self._open_website(url=args.get("url"))
                            elif fc.name == "get_system_info": result = self._get_system_info()
                            elif fc.name == "get_datetime": result = self._get_datetime()
                            elif fc.name == "run_system_command": result = self._run_system_command(command=args.get("command"))
                            function_responses.append({"id": fc.id, "name": fc.name, "response": result})
                        await self.session.send_tool_response(function_responses=function_responses)
                        continue

                    if chunk.server_content:
                        if hasattr(chunk.server_content, 'grounding_metadata') and chunk.server_content.grounding_metadata:
                            for g_chunk in chunk.server_content.grounding_metadata.grounding_chunks:
                                if g_chunk.web and g_chunk.web.uri: turn_urls.add(g_chunk.web.uri)
                        if chunk.server_content.model_turn:
                            for part in chunk.server_content.model_turn.parts:
                                if part.executable_code: turn_code_content = part.executable_code.code
                                if part.code_execution_result: turn_code_result = part.code_execution_result.output

                    if chunk.text:
                        print(f">>> [JARVIS] AI says: '{chunk.text[:80]}...'" if len(chunk.text) > 80 else f">>> [JARVIS] AI says: '{chunk.text}'")
                        self.text_received.emit(chunk.text)
                        await self.response_queue_tts.put(chunk.text)

                print(f">>> [JARVIS] End of turn.")
                if file_list_data: self.file_list_received.emit(file_list_data[0], file_list_data[1])
                elif turn_code_content: self.code_being_executed.emit(turn_code_content, turn_code_result)
                elif turn_urls: self.search_results_received.emit(list(turn_urls))
                else:
                    self.code_being_executed.emit("", "")
                    self.search_results_received.emit([])
                    self.file_list_received.emit("", [])

                self.end_of_turn.emit()
                await self.response_queue_tts.put(None)
            except Exception:
                if not self.is_running: break
                traceback.print_exc()

    async def tts(self):
        while self.is_running:
            full_response = ""
            while True:
                chunk = await self.response_queue_tts.get()
                if chunk is None: break
                full_response += chunk
                self.response_queue_tts.task_done()
            self.response_queue_tts.task_done()

            if not full_response.strip() or not self.is_running: continue

            print(f">>> [JARVIS] Speaking: '{full_response[:60]}...'")
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
                        if data.get("isFinal"): break
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
        self.connection_status_changed.emit("CONNECTED")

        self.tasks.extend([
            asyncio.create_task(self.listen_audio()),
            asyncio.create_task(self.send_realtime()),
            asyncio.create_task(self.receive_text()),
            asyncio.create_task(self.tts()),
            asyncio.create_task(self.play_audio()),
            asyncio.create_task(self.process_text_input_queue())
        ])
        print(f">>> [JARVIS] All {len(self.tasks)} subsystems launched!")
        print(f">>> [JARVIS] ========================================")
        print(f">>> [JARVIS]   J.A.R.V.I.S. is READY for commands   ")
        print(f">>> [JARVIS]   Speak or type to interact with me     ")
        print(f">>> [JARVIS] ========================================")

        # --- Welcome Greeting ---
        await asyncio.sleep(2)
        welcome = "Good day, Sir. J.A.R.V.I.S. at your service. All systems are online and fully operational. How may I assist you today?"
        print(f">>> [JARVIS] Playing welcome greeting...")
        self.text_received.emit(welcome)
        self.end_of_turn.emit()
        await self.response_queue_tts.put(welcome)
        await self.response_queue_tts.put(None)

        results = await asyncio.gather(*self.tasks, return_exceptions=True)
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f">>> [ERROR] Task {i} failed: {type(result).__name__}: {result}")

    async def run(self):
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                print(f">>> [JARVIS] Connecting to Gemini Live API (model: {MODEL})... (attempt {attempt}/{max_retries})")
                self.connection_status_changed.emit("CONNECTING")
                async with self.client.aio.live.connect(model=MODEL, config=self.config) as session:
                    print(f">>> [JARVIS] *** CONNECTION SUCCESSFUL! ***")
                    await self.main_task_runner(session)
                    return  # Normal exit
            except asyncio.CancelledError:
                print(f"\n>>> [JARVIS] Shutting down gracefully.")
                return
            except Exception as e:
                print(f"\n>>> [ERROR] Connection attempt {attempt} failed: {type(e).__name__}: {e}")
                self.connection_status_changed.emit(f"ERROR: {e}")
                if attempt < max_retries:
                    wait = attempt * 3
                    print(f">>> [JARVIS] Retrying in {wait} seconds...")
                    await asyncio.sleep(wait)
                else:
                    print(f">>> [ERROR] All {max_retries} connection attempts failed.")
                    print(f">>> [HINT] Check your GEMINI_API_KEY in .env file.")
                    print(f">>> [HINT] Make sure your internet connection is working.")
                    print(f">>> [HINT] Try model name: gemini-2.0-flash-live-001")
                    traceback.print_exc()

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
            try: future.result(timeout=5)
            except Exception as e: print(f">>> [ERROR] Shutdown error: {e}")
        if self.audio_stream and self.audio_stream.is_active():
            self.audio_stream.stop_stream()
            self.audio_stream.close()


# ==============================================================================
# GUI - J.A.R.V.I.S. MAIN WINDOW
# ==============================================================================
class JARVISWindow(QMainWindow):
    user_text_submitted = Signal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("J.A.R.V.I.S. - Just A Rather Very Intelligent System")
        self.setGeometry(50, 50, 1400, 900)
        self.setMinimumSize(1000, 700)

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
                font-size: 18pt;
                padding: 8px;
                letter-spacing: 5px;
            }}
            QLabel#status_label {{
                color: {JARVIS_AMBER};
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
                border: none; background: {JARVIS_BG_PANEL}; width: 8px; margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {JARVIS_GOLD_DIM}; min-height: 20px; border-radius: 4px;
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
        header_layout.setContentsMargins(0, 8, 0, 0)
        header_layout.setSpacing(2)
        header_layout.setAlignment(Qt.AlignCenter)

        self.jarvis_title = QLabel("J . A . R . V . I . S .")
        self.jarvis_title.setObjectName("jarvis_title")
        self.jarvis_title.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(self.jarvis_title)

        self.status_label = QLabel("INITIALIZING SYSTEMS...")
        self.status_label.setObjectName("status_label")
        self.status_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(self.status_label)

        self.middle_layout.addWidget(header_widget)

        # --- Holographic Sphere (LARGE) ---
        self.animation_widget = HolographicSphereWidget()
        self.middle_layout.addWidget(self.animation_widget, 5)

        # --- Audio Waveform ---
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
        self.middle_layout.addWidget(self.text_display, 3)

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

        # ===== RIGHT PANEL - Controls =====
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
                background-color: {JARVIS_BG_DARK}; color: {JARVIS_GOLD};
                border: 1px solid {JARVIS_BORDER}; border-radius: 4px;
                padding: 8px 12px; font-size: 9pt;
            }}
            QComboBox:hover {{ border: 1px solid {JARVIS_GOLD}; }}
            QComboBox::drop-down {{ border: none; width: 30px; }}
            QComboBox QAbstractItemView {{
                background-color: {JARVIS_BG_DARK}; color: {JARVIS_GOLD};
                border: 1px solid {JARVIS_GOLD_DIM};
                selection-background-color: {JARVIS_GOLD_DIM}; selection-color: {JARVIS_BG_DARK};
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
        self.connection_status.setText(f'<p style="color:{JARVIS_AMBER};">Initializing...</p>')
        self.right_layout.addWidget(self.connection_status)

        # --- System Info ---
        self.sys_info_label = QLabel()
        self.sys_info_label.setObjectName("tool_activity_display")
        self.sys_info_label.setWordWrap(True)
        self.sys_info_label.setMaximumHeight(80)
        self.sys_info_label.setAlignment(Qt.AlignTop)
        self.right_layout.addWidget(self.sys_info_label)

        self.right_layout.addStretch()

        # --- Add Panels ---
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
            self.sys_info_label.setText(
                f'<span style="color: {JARVIS_GOLD}; font-size: 8pt;">'
                f'CPU: {cpu}% | RAM: {mem.percent}% | {now}</span>'
            )
        except: pass

    def _populate_microphones(self):
        self.mic_combo.clear()
        try:
            import pyaudio
            p = pyaudio.PyAudio()
            default_index = -1
            try:
                default_info = p.get_default_input_device_info()
                default_index = default_info.get('index', -1)
            except: pass
            for i in range(p.get_device_count()):
                info = p.get_device_info_by_index(i)
                if info.get('maxInputChannels', 0) > 0:
                    name = info.get('name', f'Device {i}')
                    suffix = " (Default)" if i == default_index else ""
                    self.mic_combo.addItem(f"{name}{suffix}", i)
            p.terminate()
            print(f">>> [JARVIS] Found {self.mic_combo.count()} microphone(s).")
        except Exception as e:
            print(f">>> [ERROR] Failed to enumerate microphones: {e}")

    def _get_selected_mic_index(self):
        idx = self.mic_combo.currentData()
        if idx is not None and idx >= 0: return idx
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
        self.jarvis_core.connection_status_changed.connect(self.on_connection_status_changed)

        self.backend_thread = threading.Thread(target=self.jarvis_core.start_event_loop)
        self.backend_thread.daemon = True
        self.backend_thread.start()

    @Slot(str)
    def on_connection_status_changed(self, status):
        if status == "CONNECTING":
            self.connection_status.setText(
                f'<p style="color:{JARVIS_AMBER};">Connecting to Gemini API...</p>')
            self.status_label.setText("CONNECTING TO GEMINI...")
            self.status_label.setStyleSheet(f"color: {JARVIS_AMBER}; font-size: 9pt; padding: 4px 8px; letter-spacing: 1px;")
        elif status == "CONNECTED":
            self.connection_status.setText(
                f'<p style="color:#00FF88; font-weight:bold;">CONNECTED</p>'
                f'<p style="color:{JARVIS_TEXT_DIM}; font-size:8pt;">Gemini Live API: Online</p>'
                f'<p style="color:{JARVIS_TEXT_DIM}; font-size:8pt;">ElevenLabs TTS: Ready</p>')
            self.status_label.setText("SYSTEMS ONLINE  //  READY")
            self.status_label.setStyleSheet(f"color: {JARVIS_AMBER}; font-size: 9pt; padding: 4px 8px; letter-spacing: 1px;")
        elif status == "MIC_READY":
            cur = self.connection_status.text()
            self.connection_status.setText(
                cur + f'<p style="color:#00FF88; font-size:8pt;">Microphone: Active</p>')
        elif status.startswith("MIC_ERROR"):
            cur = self.connection_status.text()
            self.connection_status.setText(
                cur + f'<p style="color:{JARVIS_RED}; font-size:8pt;">Microphone: Error</p>')
        elif status.startswith("ERROR"):
            self.connection_status.setText(
                f'<p style="color:{JARVIS_RED}; font-weight:bold;">CONNECTION FAILED</p>'
                f'<p style="color:{JARVIS_TEXT_DIM}; font-size:8pt;">{escape(status)}</p>')
            self.status_label.setText("CONNECTION FAILED")
            self.status_label.setStyleSheet(f"color: {JARVIS_RED}; font-size: 9pt; padding: 4px 8px; letter-spacing: 1px;")

    @Slot()
    def on_speaking_started(self):
        self.animation_widget.start_speaking_animation()
        self.status_label.setText("SPEAKING  //  ACTIVE")
        self.status_label.setStyleSheet(f"color: {JARVIS_GOLD}; font-size: 9pt; padding: 4px 8px; letter-spacing: 1px;")

    @Slot()
    def on_speaking_stopped(self):
        self.animation_widget.stop_speaking_animation()
        self.status_label.setText("SYSTEMS ONLINE  //  READY")
        self.status_label.setStyleSheet(f"color: {JARVIS_AMBER}; font-size: 9pt; padding: 4px 8px; letter-spacing: 1px;")

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
                f"<p style='color:{JARVIS_AMBER}; font-weight:bold; margin-bottom:2px;'>"
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
        html = f'<p style="color:{JARVIS_GOLD}; margin-bottom:8px; font-size:9pt;">Search Results:</p>'
        for i, url in enumerate(urls):
            display_text = url.split('//')[1].split('/')[0] if '//' in url else url
            html += f'<p style="margin:2px 0;">{i+1}. <a href="{url}" style="color: {JARVIS_BLUE};">{display_text}</a></p>'
        self.tool_activity_display.setText(html)

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
        html = (f'<p style="color:{JARVIS_GOLD}; margin-bottom:5px;">Executing:</p>'
                f'<pre style="white-space:pre-wrap; color:{JARVIS_TEXT}; font-size:9pt;">{escape(code)}</pre>')
        if result:
            html += (f'<p style="color:{JARVIS_GOLD}; font-weight:bold; margin-top:10px;">&gt; OUTPUT:</p>'
                     f'<pre style="white-space:pre-wrap; color:#90EE90; font-size:9pt;">{escape(result.strip())}</pre>')
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
        html = f'<p style="color:{JARVIS_GOLD};">DIR &gt; <strong>{escape(directory_path)}</strong></p>'
        if not files:
            html += f'<p style="color:{JARVIS_TEXT_DIM};"><em>(Empty)</em></p>'
        else:
            folders = sorted([i for i in files if os.path.isdir(os.path.join(directory_path, i))])
            file_items = sorted([i for i in files if not os.path.isdir(os.path.join(directory_path, i))])
            html += '<ul style="list-style-type:none; padding-left:5px;">'
            for f in folders: html += f'<li style="color:{JARVIS_GOLD};">[+] {escape(f)}</li>'
            for f in file_items: html += f'<li style="color:{JARVIS_TEXT};">&#9679; {escape(f)}</li>'
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
        font = QFont("Segoe UI", 10)
        app.setFont(font)
        window = JARVISWindow()
        window.show()
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\n>>> [JARVIS] Shutting down. Goodbye, Sir.")
    finally:
        pya.terminate()
        print(">>> [JARVIS] All systems offline.")
