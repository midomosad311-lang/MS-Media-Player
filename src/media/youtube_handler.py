"""
YouTube Handler - Handles YouTube URL streaming using yt-dlp
"""

import re
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
from PySide6.QtCore import QObject, Signal, QThread


class StreamQuality(Enum):
    """Available stream quality options"""
    BEST = "best"
    WORST = "worst"
    HD1080 = "1080p"
    HD720 = "720p"
    HD480 = "480p"
    AUDIO_ONLY = "audio"


@dataclass
class YouTubeVideoInfo:
    """Information about a YouTube video"""
    id: str
    title: str
    duration: float
    uploader: str
    view_count: int
    thumbnail: str
    formats: List[Dict[str, Any]]
    subtitles: Dict[str, Any]
    description: str
    upload_date: str


class YouTubeExtractor(QObject):
    """Extracts video info and streams from YouTube using yt-dlp"""
    
    # Signals
    info_extracted = Signal(dict)  # YouTubeVideoInfo as dict
    extraction_error = Signal(str)
    progress_update = Signal(str, float)  # message, progress (0-1)
    
    def __init__(self):
        super().__init__()
        self._cancelled = False
        
    def extract_info(self, url: str, quality: StreamQuality = StreamQuality.BEST) -> Optional[YouTubeVideoInfo]:
        """Extract video information from YouTube URL"""
        self._cancelled = False
        
        try:
            import yt_dlp
            
            # Configure yt-dlp
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'skip_download': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if self._cancelled:
                    return None
                    
                # Extract relevant information
                video_info = YouTubeVideoInfo(
                    id=info.get('id', ''),
                    title=info.get('title', ''),
                    duration=info.get('duration', 0),
                    uploader=info.get('uploader', ''),
                    view_count=info.get('view_count', 0),
                    thumbnail=info.get('thumbnail', ''),
                    formats=info.get('formats', []),
                    subtitles=info.get('subtitles', {}),
                    description=info.get('description', ''),
                    upload_date=info.get('upload_date', '')
                )
                
                self.info_extracted.emit(self._to_dict(video_info))
                return video_info
                
        except Exception as e:
            self.extraction_error.emit(str(e))
            return None
    
    def get_stream_info(self, url: str, quality: StreamQuality = StreamQuality.BEST) -> Optional[Dict[str, Any]]:
        """Resolve a playable stream URL together with the HTTP headers.

        YouTube serves most high-quality streams as separate video-only and
        audio-only DASH tracks.  VLC cannot play those merged from a single
        URL (merging requires downloading), so we prefer *progressive*
        formats that already contain both audio and video.
        """
        self._cancelled = False

        try:
            import yt_dlp

            format_selector = self._get_format_selector(quality)

            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'format': format_selector,
                'skip_download': True,
                'nocheckcertificate': True,
                # Do not try to merge (we are streaming, not downloading)
                'prefer_free_formats': False,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                if self._cancelled or not info:
                    return None

                stream_url = info.get('url')
                headers = dict(info.get('http_headers') or {})
                if not stream_url and info.get('formats'):
                    fmt = info['formats'][-1]
                    stream_url = fmt.get('url')
                    headers = dict(fmt.get('http_headers') or headers)

                if not stream_url:
                    return None

                return {
                    'url': stream_url,
                    'headers': headers,
                    'title': info.get('title', ''),
                    'uploader': info.get('uploader', ''),
                    'duration': info.get('duration', 0) or 0,
                    'is_live': bool(info.get('is_live')),
                }

        except Exception as e:
            self.extraction_error.emit(str(e))
            return None

    def get_stream_url(self, url: str, quality: StreamQuality = StreamQuality.BEST) -> Optional[str]:
        """Get direct stream URL for playback (playback URL only)."""
        info = self.get_stream_info(url, quality)
        return info['url'] if info else None
    
    def get_subtitle_tracks(self, url: str) -> Dict[str, Any]:
        """Get available subtitle tracks for a video"""
        try:
            import yt_dlp
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
                'writesubtitles': True,
                'writeautomaticsub': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info.get('subtitles', {}), info.get('automatic_captions', {})
                
        except Exception as e:
            print(f"Failed to get subtitles: {e}")
            return {}, {}
    
    def download_subtitles(self, url: str, lang: str = 'en', output_dir: str = None) -> Optional[str]:
        """Download subtitles for a video and return the created file path."""
        try:
            import yt_dlp

            if output_dir is None:
                out_dir = Path(tempfile.gettempdir()) / "MSMediaPlayer" / "youtube"
            else:
                out_dir = Path(output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)

            before = set(out_dir.glob("*.srt"))

            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
                'writesubtitles': True,
                'writeautomaticsub': True,
                'subtitleslangs': [lang],
                'subtitlesformat': 'srt',
                'outtmpl': str(out_dir / '%(id)s.%(ext)s'),
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            # Only return files that this download actually created.
            created = set(out_dir.glob("*.srt")) - before
            if created:
                return str(max(created, key=lambda p: p.stat().st_mtime))

            # Fall back to a language-matching file if one exists.
            matches = list(out_dir.glob(f"*{lang}*.srt"))
            if matches:
                return str(matches[0])

            return None
                
        except Exception as e:
            print(f"Failed to download subtitles: {e}")
            return None
    
    def _get_format_selector(self, quality: StreamQuality) -> str:
        """Get a yt-dlp format selector that yields a single progressive file.

        Progressive formats (audio + video in one file) can be streamed
        directly by VLC without merging.  Ordering: prefer MP4 progressive at
        (or below) the requested height, then any progressive, then the best
        progressive available so audio is always present.
        """

        def progressive(height: str = "") -> str:
            h = f"[height<={height}]" if height else ""
            return (
                f"best{h}[ext=mp4][vcodec!=none][acodec!=none]"
                f"/best{h}[vcodec!=none][acodec!=none]"
                f"/best[ext=mp4][vcodec!=none][acodec!=none]"
                f"/best[vcodec!=none][acodec!=none]"
            )

        selectors = {
            StreamQuality.BEST: progressive(),
            StreamQuality.WORST: "worst[ext=mp4][vcodec!=none][acodec!=none]/worst[vcodec!=none][acodec!=none]/worst",
            StreamQuality.HD1080: progressive("1080"),
            StreamQuality.HD720: progressive("720"),
            StreamQuality.HD480: progressive("480"),
            StreamQuality.AUDIO_ONLY: "bestaudio[ext=m4a]/bestaudio/best",
        }
        return selectors.get(quality, selectors[StreamQuality.BEST])
    
    def _to_dict(self, info: YouTubeVideoInfo) -> dict:
        """Convert YouTubeVideoInfo to dictionary"""
        return {
            'id': info.id,
            'title': info.title,
            'duration': info.duration,
            'uploader': info.uploader,
            'view_count': info.view_count,
            'thumbnail': info.thumbnail,
            'formats': info.formats,
            'subtitles': info.subtitles,
            'description': info.description,
            'upload_date': info.upload_date
        }
    
    def cancel(self):
        """Cancel ongoing operation"""
        self._cancelled = True


class YouTubeExtractorThread(QThread):
    """Background thread for YouTube extraction"""
    
    def __init__(self, extractor: YouTubeExtractor, url: str, quality: StreamQuality = StreamQuality.BEST):
        super().__init__()
        self.extractor = extractor
        self.url = url
        self.quality = quality
        self.result = None
        
    def run(self):
        """Run extraction in background"""
        self.result = self.extractor.extract_info(self.url, self.quality)


def get_ffmpeg_path() -> Optional[str]:
    """Locate an ffmpeg executable.

    ``imageio-ffmpeg`` (a lightweight pip dependency) bundles a static ffmpeg
    binary, which is used to merge separate video and audio streams that
    YouTube serves for recorded videos.  Falls back to a system ``ffmpeg``.
    """
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and Path(exe).exists():
            return exe
    except Exception:
        pass
    from shutil import which
    return which("ffmpeg")


class _DownloadCancelled(Exception):
    """Raised from a yt-dlp progress hook to abort a download."""


class _YouTubeResolveThread(QThread):
    """Background worker that turns a YouTube URL into something playable.

    * audio-only requests stream a single audio URL directly;
    * when YouTube exposes a single combined (progressive) file it is streamed;
    * otherwise the best video + audio are downloaded and merged with ffmpeg
      (recorded videos only&nbsp;- live streams cannot be merged).
    """

    stream_ready = Signal(str, dict)   # playable URL, info
    file_ready = Signal(str, dict)     # local file path, info
    progress = Signal(float, str)      # percent (0-100 or -1), message
    failed = Signal(str)

    def __init__(self, url: str, quality: StreamQuality, workdir: Path):
        super().__init__()
        self.url = url
        self.quality = quality
        self.workdir = Path(workdir)
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def _max_height(self) -> Optional[int]:
        return {
            StreamQuality.BEST: None,
            StreamQuality.WORST: None,
            StreamQuality.HD1080: 1080,
            StreamQuality.HD720: 720,
            StreamQuality.HD480: 480,
        }.get(self.quality)

    def run(self):
        try:
            import yt_dlp

            base_opts = {
                "quiet": True,
                "no_warnings": True,
                "nocheckcertificate": True,
                "noplaylist": True,
                "noprogress": True,
            }

            # --- Probe (no download) ---
            with yt_dlp.YoutubeDL({**base_opts, "skip_download": True}) as ydl:
                info = ydl.extract_info(self.url, download=False)
            if self._cancel:
                return
            if not info:
                self.failed.emit("Failed to load YouTube video")
                return

            meta = self._meta(info)
            is_live = bool(info.get("is_live"))

            # --- Audio-only: a single audio URL can be streamed directly ---
            if self.quality == StreamQuality.AUDIO_ONLY:
                url = self._pick_combined(info, audio_only=True)
                if url:
                    self.stream_ready.emit(url, meta)
                    return

            # --- Any single combined (progressive) file: stream it ---
            url = self._pick_combined(info, max_height=self._max_height())
            if url:
                self.stream_ready.emit(url, meta)
                return

            # --- Live streams cannot be merged => stream the best single URL ---
            if is_live:
                url = self._pick_any(info)
                if url:
                    self.stream_ready.emit(url, meta)
                    return
                self.failed.emit("Cannot play this live stream")
                return

            # --- Recorded video: download + merge with ffmpeg ---
            self._download_and_merge(meta, base_opts)

        except Exception as e:
            if not self._cancel:
                self.failed.emit(str(e))

    def _download_and_merge(self, meta, base_opts):
        import yt_dlp

        height = self._max_height()
        h = f"[height<={height}]" if height else ""
        if self.quality == StreamQuality.WORST:
            fmt = "worstvideo+worstaudio/worst"
        else:
            fmt = (
                f"bestvideo{h}[ext=mp4]+bestaudio[ext=m4a]/"
                f"bestvideo{h}+bestaudio/best{h}/best"
            )

        self.workdir.mkdir(parents=True, exist_ok=True)
        outtmpl = str(self.workdir / "%(title).120B [%(id)s].%(ext)s")

        def hook(d):
            if self._cancel:
                raise _DownloadCancelled()
            status = d.get("status")
            if status == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                done = d.get("downloaded_bytes") or 0
                pct = (done / total * 100.0) if total else -1.0
                self.progress.emit(pct, "Downloading...")
            elif status == "finished":
                self.progress.emit(100.0, "Processing...")

        opts = {
            **base_opts,
            "format": fmt,
            "outtmpl": outtmpl,
            "merge_output_format": "mp4",
            "progress_hooks": [hook],
        }
        ffmpeg = get_ffmpeg_path()
        if ffmpeg:
            opts["ffmpeg_location"] = ffmpeg

        path = None
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                result = ydl.extract_info(self.url, download=True)
                path = self._merged_path(ydl, result)
        except _DownloadCancelled:
            return
        except Exception as e:
            # yt-dlp may wrap the cancellation; treat as a normal failure
            if self._cancel:
                return
            self.failed.emit(str(e))
            return

        if self._cancel:
            return
        if path and Path(path).exists():
            self.file_ready.emit(str(path), meta)
        else:
            self.failed.emit("Failed to load YouTube video")

    def _merged_path(self, ydl, result) -> Optional[Path]:
        try:
            cand = Path(ydl.prepare_filename(result))
            if cand.exists():
                return cand
            for ext in (".mp4", ".mkv", ".webm"):
                alt = cand.with_suffix(ext)
                if alt.exists():
                    return alt
        except Exception:
            pass
        for f in (result.get("requested_downloads") or []):
            fp = f.get("filepath")
            if fp and Path(fp).exists():
                return Path(fp)
        return None

    def _pick_combined(self, info, audio_only=False, max_height=None) -> Optional[str]:
        cands = []
        for f in (info.get("formats") or []):
            if not f.get("url"):
                continue
            v = f.get("vcodec")
            a = f.get("acodec")
            if audio_only:
                if a and a != "none" and (not v or v == "none"):
                    cands.append(f)
            else:
                if v and v != "none" and a and a != "none":
                    cands.append(f)
        if not cands:
            return None
        if max_height:
            filtered = [f for f in cands if (f.get("height") or 0) <= max_height]
            if filtered:
                cands = filtered
        if audio_only:
            cands.sort(key=lambda f: (f.get("abr") or f.get("tbr") or 0), reverse=True)
        else:
            cands.sort(key=lambda f: (f.get("ext") == "mp4", f.get("height") or 0, f.get("tbr") or 0), reverse=True)
        return cands[0].get("url")

    def _pick_any(self, info) -> Optional[str]:
        formats = info.get("formats") or []
        hls = [f for f in formats if str(f.get("protocol", "")).startswith("m3u8") and f.get("url")]
        if hls:
            hls.sort(key=lambda f: (f.get("height") or 0), reverse=True)
            return hls[0].get("url")
        return info.get("url")

    def _meta(self, info) -> dict:
        return {
            "title": info.get("title", ""),
            "uploader": info.get("uploader", ""),
            "duration": info.get("duration", 0) or 0,
            "is_live": bool(info.get("is_live")),
            "headers": dict(info.get("http_headers") or {}),
        }


class _SubtitleThread(QThread):
    """Background thread that downloads subtitles."""

    finished_with_path = Signal(str)

    def __init__(self, handler, url: str, lang: str):
        super().__init__()
        self.handler = handler
        self.url = url
        self.lang = lang

    def run(self):
        try:
            path = self.handler.download_subtitles(self.url, self.lang)
        except Exception:
            path = None
        self.finished_with_path.emit(path or "")


class YouTubeStreamHandler(QObject):
    """High-level YouTube stream handler for media engine integration"""
    
    # Signals
    stream_ready = Signal(str, dict)  # playable URL, video_info
    file_ready = Signal(str, dict)    # downloaded+merged file path, video_info
    download_progress = Signal(float, str)  # percent (0-100 or -1), message
    stream_error = Signal(str)
    info_ready = Signal(dict)  # video_info
    subtitles_ready = Signal(str)  # path to subtitle file ("" on failure)
    
    def __init__(self):
        super().__init__()
        self.extractor = YouTubeExtractor()
        self.current_info: Optional[YouTubeVideoInfo] = None
        self._resolve_thread = None
        self._subtitle_thread = None
        self._workdir = Path(tempfile.gettempdir()) / "MSMediaPlayer" / "youtube"
        
        # Connect signals
        self.extractor.info_extracted.connect(self._on_info_extracted)
        self.extractor.extraction_error.connect(self.stream_error.emit)

    def resolve_stream(self, url: str, quality: StreamQuality = StreamQuality.BEST):
        """Resolve a YouTube URL in the background (keeps the UI responsive).

        Emits either ``stream_ready`` (a directly playable URL) or
        ``file_ready`` (a downloaded + merged local file), plus
        ``download_progress`` updates while downloading.
        """
        if not self._is_valid_youtube_url(url):
            self.stream_error.emit("Invalid YouTube URL")
            return

        self.cancel()
        # Drop the previous worker's connections so a late result from a
        # cancelled/superseded request can't reach the UI.
        old = self._resolve_thread
        if old is not None:
            for sig in (old.stream_ready, old.file_ready, old.progress, old.failed):
                try:
                    sig.disconnect()
                except Exception:
                    pass
        self._resolve_thread = _YouTubeResolveThread(url, quality, self._workdir)
        self._resolve_thread.stream_ready.connect(self.stream_ready.emit)
        self._resolve_thread.file_ready.connect(self.file_ready.emit)
        self._resolve_thread.progress.connect(self.download_progress.emit)
        self._resolve_thread.failed.connect(self.stream_error.emit)
        self._resolve_thread.start()

    def cancel(self):
        """Cancel an in-flight resolution/download."""
        if self._resolve_thread is not None and self._resolve_thread.isRunning():
            self._resolve_thread.cancel()

    def download_subtitles_async(self, url: str, lang: str):
        """Download subtitles in the background."""
        self._subtitle_thread = _SubtitleThread(self, url, lang)
        self._subtitle_thread.finished_with_path.connect(self.subtitles_ready.emit)
        self._subtitle_thread.start()
        
    def load_video(self, url: str, quality: StreamQuality = StreamQuality.BEST) -> bool:
        """Load YouTube video for playback"""
        # Validate URL
        if not self._is_valid_youtube_url(url):
            self.stream_error.emit("Invalid YouTube URL")
            return False
            
        # Extract info first
        self.extractor.extract_info(url, quality)
        return True
    
    def get_stream_url(self, url: str, quality: StreamQuality = StreamQuality.BEST) -> Optional[str]:
        """Get direct stream URL"""
        return self.extractor.get_stream_url(url, quality)
    
    def get_subtitles(self, url: str) -> tuple:
        """Get available subtitles"""
        return self.extractor.get_subtitle_tracks(url)
    
    def download_subtitles(self, url: str, lang: str = 'en') -> Optional[str]:
        """Download subtitles"""
        return self.extractor.download_subtitles(url, lang)
    
    def _is_valid_youtube_url(self, url: str) -> bool:
        """Validate YouTube URL"""
        youtube_patterns = [
            r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/',
            r'(https?://)?(www\.)?youtube\.com/(watch\?v=|embed/|v/|shorts/)',
            r'(https?://)?youtu\.be/',
        ]
        return any(re.match(pattern, url) for pattern in youtube_patterns)
    
    def _on_info_extracted(self, info: dict):
        """Handle extracted video info"""
        self.current_info = YouTubeVideoInfo(
            id=info.get('id', ''),
            title=info.get('title', ''),
            duration=info.get('duration', 0),
            uploader=info.get('uploader', ''),
            view_count=info.get('view_count', 0),
            thumbnail=info.get('thumbnail', ''),
            formats=info.get('formats', []),
            subtitles=info.get('subtitles', {}),
            description=info.get('description', ''),
            upload_date=info.get('upload_date', '')
        )
        self.info_ready.emit(info)