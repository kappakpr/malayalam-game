FROM python:3.11.17-trixie

RUN apt-get update && apt-get install -y --no-install-recommends \
    tigervnc-standalone-server \
    novnc \
    websockify \
    openbox \
    libegl1 \
    libgl1 \
    libglib2.0-0 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxkbcommon-x11-0 \
    libxcb-cursor0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libxcb-xfixes0 \
    libxcb-xinerama0 \
    libfontconfig1 \
    fonts-noto-core \
    fonts-noto-color-emoji \
    libpulse0 \
    libasound2t64 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir PySide6-Essentials PySide6-Addons edge-tts

CMD ["sh", "-c", "Xvnc :1 -geometry 1024x768 -depth 24 -rfbport 5900 -SecurityTypes None & sleep 1 && DISPLAY=:1 openbox & websockify --web=/usr/share/novnc/ 6080 localhost:5900 & DISPLAY=:1 python -u malayalam_game.py"]