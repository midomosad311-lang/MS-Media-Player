"""
Subtitle Manager - Handles subtitle parsing, synchronization, and export
"""

import re
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass, field
from enum import Enum
from PySide6.QtCore import QObject, Signal

try:
    import pysrt
    HAS_PYSRT = True
except ImportError:
    HAS_PYSRT = False

try:
    import pysubs2
    HAS_PYSUBS2 = True
except ImportError:
    HAS_PYSUBS2 = False


class SyncMode(Enum):
    """Subtitle synchronization mode"""
    REAL_TIME = "real_time"          # Direct sync with speech
    PARAGRAPH_BY_PARAGRAPH = "paragraph"  # Paragraph by paragraph reading


@dataclass
class SubtitleEntry:
    """Represents a single subtitle entry"""
    index: int
    start_time: float  # seconds
    end_time: float    # seconds
    text: str
    
    def duration(self) -> float:
        return self.end_time - self.start_time
    
    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "text": self.text
        }


@dataclass
class SubtitleFile:
    """Represents a complete subtitle file"""
    path: str
    entries: List[SubtitleEntry] = field(default_factory=list)
    encoding: str = "utf-8"
    format: str = "srt"  # srt, ass, vtt
    
    def get_entry_at_time(self, time_seconds: float) -> Optional[SubtitleEntry]:
        """Get the subtitle entry active at given time"""
        for entry in self.entries:
            if entry.start_time <= time_seconds <= entry.end_time:
                return entry
        return None
    
    def get_entries_up_to_time(self, time_seconds: float) -> List[SubtitleEntry]:
        """Get all subtitle entries up to given time"""
        return [e for e in self.entries if e.end_time <= time_seconds]
    
    def get_entries_in_range(self, start: float, end: float) -> List[SubtitleEntry]:
        """Get subtitle entries within time range"""
        return [e for e in self.entries 
                if e.start_time >= start and e.end_time <= end]
    
    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "format": self.format,
            "encoding": self.encoding,
            "entries": [e.to_dict() for e in self.entries]
        }


class SubtitleManager(QObject):
    """Manages subtitle loading, parsing, synchronization, and export"""
    
    # Signals
    subtitle_loaded = Signal(str)  # path
    subtitle_error = Signal(str)   # error message
    sync_mode_changed = Signal(str)  # mode
    current_subtitle_changed = Signal(str)  # current text
    
    # Supported formats
    SUPPORTED_FORMATS = {
        '.srt': 'srt',
        '.ass': 'ass',
        '.ssa': 'ssa',
        '.vtt': 'vtt',
        '.sub': 'sub'
    }
    
    def __init__(self, settings_manager=None):
        super().__init__()
        self.settings = settings_manager
        self.current_subtitle: Optional[SubtitleFile] = None
        self.sync_mode = SyncMode.REAL_TIME
        self.subtitle_offset = 0.0  # seconds
        self.enabled = True
        self._subtitle_visible = True
        
    def load_subtitle(self, path: str) -> bool:
        """Load subtitle file from path"""
        path = Path(path)
        if not path.exists():
            self.subtitle_error.emit(f"Subtitle file not found: {path}")
            return False
            
        ext = path.suffix.lower()
        if ext not in self.SUPPORTED_FORMATS:
            self.subtitle_error.emit(f"Unsupported subtitle format: {ext}")
            return False
            
        format_type = self.SUPPORTED_FORMATS[ext]
        
        try:
            if format_type == 'srt':
                self.current_subtitle = self._parse_srt(path)
            elif format_type in ('ass', 'ssa'):
                self.current_subtitle = self._parse_ass(path)
            elif format_type == 'vtt':
                self.current_subtitle = self._parse_vtt(path)
            else:
                self.subtitle_error.emit(f"Parser not implemented for {ext}")
                return False
                
            self.subtitle_loaded.emit(str(path))
            return True
            
        except Exception as e:
            self.subtitle_error.emit(f"Failed to load subtitle: {str(e)}")
            return False
    
    def _parse_srt(self, path: Path) -> SubtitleFile:
        """Parse SRT subtitle file"""
        entries = []
        
        if HAS_PYSRT:
            subs = pysrt.open(str(path), encoding='utf-8')
            for i, sub in enumerate(subs):
                start = sub.start.ordinal / 1000.0
                end = sub.end.ordinal / 1000.0
                text = sub.text.replace('\n', ' ').strip()
                entries.append(SubtitleEntry(i, start, end, text))
        else:
            # Fallback manual parsing
            content = path.read_text(encoding='utf-8')
            entries = self._parse_srt_manual(content)
            
        return SubtitleFile(str(path), entries, format='srt')
    
    def _parse_srt_manual(self, content: str) -> List[SubtitleEntry]:
        """Manual SRT parsing fallback"""
        entries = []
        blocks = re.split(r'\n\s*\n', content.strip())
        
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) < 3:
                continue
                
            try:
                index = int(lines[0].strip())
                time_line = lines[1].strip()
                text = ' '.join(lines[2:]).strip()
                
                # Parse time: 00:00:00,000 --> 00:00:00,000
                time_match = re.match(r'(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})', time_line)
                if not time_match:
                    continue
                    
                start = self._parse_srt_time(time_match.group(1))
                end = self._parse_srt_time(time_match.group(2))
                
                entries.append(SubtitleEntry(index, start, end, text))
            except (ValueError, IndexError):
                continue
                
        return entries
    
    def _parse_srt_time(self, time_str: str) -> float:
        """Parse SRT time format (HH:MM:SS,mmm) to seconds"""
        time_str = time_str.replace(',', '.')
        parts = time_str.split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])
        return hours * 3600 + minutes * 60 + seconds
    
    def _parse_ass(self, path: Path) -> SubtitleFile:
        """Parse ASS/SSA subtitle file"""
        entries = []
        
        if HAS_PYSUBS2:
            subs = pysubs2.load(str(path))
            for i, line in enumerate(subs):
                start = line.start / 1000.0
                end = line.end / 1000.0
                text = line.text.replace('\\N', ' ').replace('\\n', ' ').strip()
                # Remove ASS tags
                text = re.sub(r'\{[^}]*\}', '', text)
                entries.append(SubtitleEntry(i, start, end, text))
        else:
            # Fallback - basic parsing
            content = path.read_text(encoding='utf-8')
            # Simple Dialogue line parsing
            for i, line in enumerate(content.split('\n')):
                if line.startswith('Dialogue:'):
                    parts = line.split(',', 9)
                    if len(parts) >= 10:
                        start = self._parse_ass_time(parts[1])
                        end = self._parse_ass_time(parts[2])
                        text = parts[9].replace('\\N', ' ').replace('\\n', ' ')
                        text = re.sub(r'\{[^}]*\}', '', text)
                        entries.append(SubtitleEntry(i, start, end, text.strip()))
                        
        return SubtitleFile(str(path), entries, format='ass')
    
    def _parse_ass_time(self, time_str: str) -> float:
        """Parse ASS time format (H:MM:SS.cc) to seconds"""
        parts = time_str.split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])
        return hours * 3600 + minutes * 60 + seconds
    
    def _parse_vtt(self, path: Path) -> SubtitleFile:
        """Parse WebVTT subtitle file"""
        entries = []
        content = path.read_text(encoding='utf-8')
        
        # Remove WEBVTT header
        lines = content.split('\n')
        in_cue = False
        current_entry = {}
        
        for line in lines:
            line = line.strip()
            if not line or line == 'WEBVTT':
                continue
                
            if '-->' in line:
                if in_cue and 'text' in current_entry:
                    start = self._parse_vtt_time(current_entry['start'])
                    end = self._parse_vtt_time(current_entry['end'])
                    entries.append(SubtitleEntry(
                        len(entries), start, end, current_entry['text']
                    ))
                parts = line.split('-->')
                current_entry = {
                    'start': parts[0].strip(),
                    'end': parts[1].split()[0].strip() if len(parts) > 1 else '',
                    'text': ''
                }
                in_cue = True
            elif in_cue:
                if current_entry['text']:
                    current_entry['text'] += ' ' + line
                else:
                    current_entry['text'] = line
                    
        # Last entry
        if in_cue and 'text' in current_entry:
            start = self._parse_vtt_time(current_entry['start'])
            end = self._parse_vtt_time(current_entry['end'])
            entries.append(SubtitleEntry(len(entries), start, end, current_entry['text']))
            
        return SubtitleFile(str(path), entries, format='vtt')
    
    def _parse_vtt_time(self, time_str: str) -> float:
        """Parse VTT time format (HH:MM:SS.mmm) to seconds"""
        time_str = time_str.strip()
        time_part = time_str.split('.')[0]
        parts = time_part.split(':')
        hours = int(parts[0]) if len(parts) == 3 else 0
        minutes = int(parts[-2])
        seconds = float(parts[-1])
        return hours * 3600 + minutes * 60 + seconds
    
    def auto_detect_subtitle(self, video_path: str) -> Optional[str]:
        """Auto-detect subtitle file for video"""
        video_path = Path(video_path)
        subtitle_extensions = ['.srt', '.ass', '.ssa', '.vtt', '.sub']
        
        for ext in subtitle_extensions:
            sub_path = video_path.with_suffix(ext)
            if sub_path.exists():
                return str(sub_path)
        return None
    
    def get_current_text(self, current_time: float) -> str:
        """Get current subtitle text at given time"""
        if not self.current_subtitle or not self.enabled or not self._subtitle_visible:
            return ""
            
        adjusted_time = current_time + self.subtitle_offset
        entry = self.current_subtitle.get_entry_at_time(adjusted_time)
        if entry:
            return entry.text
        return ""
    
    def get_full_text(self) -> str:
        """Get full subtitle text"""
        if not self.current_subtitle:
            return ""
        return '\n'.join([e.text for e in self.current_subtitle.entries])
    
    def get_text_up_to_time(self, time_seconds: float) -> str:
        """Get subtitle text up to given time"""
        if not self.current_subtitle:
            return ""
        entries = self.current_subtitle.get_entries_up_to_time(time_seconds + self.subtitle_offset)
        return '\n'.join([e.text for e in entries])
    
    def get_text_in_range(self, start: float, end: float) -> str:
        """Get subtitle text in time range"""
        if not self.current_subtitle:
            return ""
        entries = self.current_subtitle.get_entries_in_range(start + self.subtitle_offset, end + self.subtitle_offset)
        return '\n'.join([e.text for e in entries])
    
    def set_sync_mode(self, mode: SyncMode):
        """Set synchronization mode"""
        self.sync_mode = mode
        self.sync_mode_changed.emit(mode.value)
    
    def set_offset(self, offset: float):
        """Set subtitle time offset in seconds"""
        self.subtitle_offset = offset
    
    def set_enabled(self, enabled: bool):
        """Enable/disable subtitle display"""
        self.enabled = enabled
    
    def set_visible(self, visible: bool):
        """Show/hide subtitle display"""
        self._subtitle_visible = visible
    
    def export_to_txt(self, path: str, range_start: float = 0, range_end: float = None) -> bool:
        """Export subtitles to plain text file"""
        if not self.current_subtitle:
            return False
            
        try:
            if range_end is None:
                entries = self.current_subtitle.entries
            else:
                entries = self.current_subtitle.get_entries_in_range(range_start, range_end or float('inf'))
                
            with open(path, 'w', encoding='utf-8') as f:
                for entry in entries:
                    f.write(f"{entry.text}\n")
            return True
        except Exception as e:
            print(f"Export to TXT failed: {e}")
            return False
    
    def export_to_docx(self, path: str, range_start: float = 0, range_end: float = None) -> bool:
        """Export subtitles to Word document"""
        if not self.current_subtitle:
            return False
            
        try:
            from docx import Document
            from docx.shared import Pt
            
            doc = Document()
            style = doc.styles['Normal']
            font = style.font
            font.name = 'Arial'
            font.size = Pt(12)
            
            if range_end is None:
                entries = self.current_subtitle.entries
            else:
                entries = self.current_subtitle.get_entries_in_range(range_start, range_end or float('inf'))
                
            for entry in entries:
                # Add timestamp
                p = doc.add_paragraph()
                run = p.add_run(f"[{self._format_time(entry.start_time)}] ")
                run.bold = True
                run.font.size = Pt(10)
                p.add_run(entry.text)
                
            doc.save(path)
            return True
        except Exception as e:
            print(f"Export to DOCX failed: {e}")
            return False
    
    def export_to_pdf(self, path: str, range_start: float = 0, range_end: float = None) -> bool:
        """Export subtitles to PDF"""
        if not self.current_subtitle:
            return False
            
        try:
            from fpdf import FPDF
            
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            
            if range_end is None:
                entries = self.current_subtitle.entries
            else:
                entries = self.current_subtitle.get_entries_in_range(range_start, range_end or float('inf'))
                
            for entry in entries:
                timestamp = self._format_time(entry.start_time)
                pdf.cell(0, 10, f"[{timestamp}] {entry.text}", ln=True)
                
            pdf.output(path)
            return True
        except Exception as e:
            print(f"Export to PDF failed: {e}")
            return False
    
    def _format_time(self, seconds: float) -> str:
        """Format seconds to HH:MM:SS"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def clear(self):
        """Clear current subtitle"""
        self.current_subtitle = None
        self.subtitle_offset = 0.0
        
    def has_subtitle(self) -> bool:
        return self.current_subtitle is not None
    
    def get_entries_count(self) -> int:
        return len(self.current_subtitle.entries) if self.current_subtitle else 0