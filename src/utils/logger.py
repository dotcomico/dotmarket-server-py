import os
from datetime import datetime
from pathlib import Path

LOG_DIR = Path(__file__).parent.parent.parent / 'logs'

if not LOG_DIR.exists():
    LOG_DIR.mkdir(parents=True, exist_ok=True)

def getTimestamp():
    return datetime.now().isoformat()

def getLogFile():
    return LOG_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.log"

def writeLog(level, message, data=None):
    entry = f"[{getTimestamp()}] [{level}] {message}"
    if data:
        import json
        entry += f" | {json.dumps(data)}"
    entry += "\n"
    
    with open(getLogFile(), 'a') as f:
        f.write(entry)

class Logger:
    @staticmethod
    def info(message, data=None):
        print(f"✅ {message}", data if data else '')
        writeLog('INFO', message, data)
    
    @staticmethod
    def warn(message, data=None):
        print(f"⚠️ {message}", data if data else '')
        writeLog('WARN', message, data)
    
    @staticmethod
    def error(message, data=None):
        print(f"❌ {message}", data if data else '')
        writeLog('ERROR', message, data)

logger = Logger()
