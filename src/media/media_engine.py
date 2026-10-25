"""
Media Engine - Core media playback using VLC/MPV
"""

from pathlib import Path
from typing import Optional, Dict, Any, List
from enum import Enum
from PySide6.QtCore import QObject, Signal, QTimer
from core.app_meta import USER_AGENT
from settings.settings_manager import SettingsManager
import vlc


class PlaybackState(Enum):
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"
    BUFFERING = "buffering"
    ERROR = "error"
    ENDED = "ended"


class MediaEngine(QObject):
    """Core media playback engine"""

    # Signals
    state_changed = Signal(str)
    position_changed = Signal(float, float)  # current, total
    duration_changed = Signal(float)
    volume_changed = Signal(int)
    muted_changed = Signal(bool)
    speed_changed = Signal(float)
    error_occurred = Signal(str)
    media_loaded = Signal(str)
    media_ready = Signal()  # Media is parsed and ready to play
    media_ended = Signal()
    buffer_progress = Signal(int)
    subtitle_changed = Signal(int)
    audio_track_changed = Signal(int)
    video_track_changed = Signal(int)

    # The on-screen volume slider always runs from 0 % to 100 %.  That range is
    # mapped onto a larger internal libvlc range.  libvlc's audio_set_volume()
    # takes a *linear* gain where 100 == 0 dB, so any value above 100 amplifies
    # in software (VLC's software amplifier: output_factor * gain_factor).
    #
    # The user explicitly asked that the player at 100 % be LOUDER than the
    # device at 100 %, therefore 100 % on the slider maps to
    # VOLUME_GAIN * 100 (250 == about +8 dB / 2.5x amplitude).
    VOLUME_GAIN = 2.5

    def __init__(self, settings_manager: SettingsManager):
        super().__init__()
        self.settings = settings_manager
        self.instance = None
        self.player = None
        self.media = None
        self.video_widget = None
        
        self.current_file = ""
        self.current_url = ""
        self.duration = 0.0
        self.position = 0.0
        self.volume = 100
        self.muted = False
        self.speed = 1.0
        self.state = PlaybackState.STOPPED
        self.hardware_acceleration = True
        self.equalizer = None
        self._position_timer = QTimer()
        self._position_timer.timeout.connect(self._update_position)
        self._position_timer.setInterval(100)
        self._cleaned_up = False
        self._video_output_attached = False

        # VLC creates the audio output lazily when playback starts, and that
        # new output ignores a volume that was set before it existed (it falls
        # back to nominal 100 == 0 dB).  We therefore re-apply the volume for a
        # short while after playback starts so the loudness gain sticks.
        self._volume_reapply_ticks = 0

        # Guards used to keep end-of-media handling idempotent.  Without them a
        # stale/incorrect position could fire ``media_ended`` repeatedly and send
        # the auto-advance logic into a tight reload loop that freezes the UI.
        self._ended_emitted = False
        self._last_duration_check = 0.0

        # Lazy VLC initialization flag
        self._vlc_initialized = False

    def _ensure_vlc_initialized(self):
        """Lazy initialization of VLC"""
        if self._vlc_initialized:
            return True
            
        try:
            import vlc

            # VLC arguments for better performance and compatibility
            vlc_args = [
                '--no-video-title-show',
                '--no-osd',
                '--quiet',
                '--no-xlib',
            ]

            # Hardware acceleration
            if self.settings.get_hardware_acceleration():
                vlc_args.extend([
                    '--avcodec-hw=any',
                    '--vout=direct3d11',  # Windows hardware acceleration
                ])

            self.instance = vlc.Instance(vlc_args)
            self.player = self.instance.media_player_new()

            # Set initial volume (mapped through the loudness gain)
            self.player.audio_set_volume(self._vlc_volume(self.settings.get_volume()))

            # Polling timer for state/position updates.  It is connected once
            # in __init__; do not connect it again here.
            self._position_timer.setInterval(100)
            
            self._vlc_initialized = True
            return True

        except ImportError:
            self.error_occurred.emit("VLC not installed. Please install python-vlc.")
            return False
        except Exception as e:
            self.error_occurred.emit(f"Failed to initialize VLC: {str(e)}")
            return False

    def _ensure_player(self):
        """Ensure VLC player is initialized"""
        if not self._vlc_initialized:
            return self._ensure_vlc_initialized()
        return True

    def load_file(self, file_path: str, headers: Optional[Dict[str, str]] = None) -> bool:
        """Load media file or stream URL.

        ``headers`` (optional) are extra HTTP headers (e.g. User-Agent /
        Referer) applied when playing a network stream - required by many
        YouTube / googlevideo URLs.
        """
        if not self._ensure_player():
            return False

        try:
            # Stop current playback and forget the previous track's duration so
            # the seek bar / announcements never show stale values for the new
            # file (the real duration arrives once VLC has parsed it).
            self.duration = 0.0
            self.stop()

            # Create media
            path = Path(file_path)
            if path.exists():
                self.media = self.instance.media_new(str(path))
                self.current_file = str(path)
                self.current_url = ""
            else:
                # Treat as URL
                self.media = self.instance.media_new(file_path)
                self.current_file = ""
                self.current_url = file_path

            # Set media options
            self._apply_media_options(headers)

            # Set up media parsed event callback
            self._setup_media_parsed_callback()

            # Set media to player
            self.player.set_media(self.media)

            # Parse media to get duration and metadata (async)
            self.media.parse()

            # Apply settings
            self._apply_playback_settings()

            self.media_loaded.emit(self.current_file or self.current_url)
            
            # Check if media is already parsed (can happen with local files)
            if self.media.get_parsed_status() == vlc.MediaParsedStatus.done:
                self.media_ready.emit()
                
            return True

        except Exception as e:
            self.error_occurred.emit(f"Failed to load media: {str(e)}")
            return False

    def _setup_media_parsed_callback(self):
        """Set up callback for media parsed event"""
        if not self.media:
            return
            
        try:
            event_manager = self.media.event_manager()
            # Remove any existing callback to avoid duplicates
            try:
                event_manager.event_detach(vlc.EventType.MediaParsedChanged)
            except:
                pass
            # Attach new callback
            event_manager.event_attach(vlc.EventType.MediaParsedChanged, self._on_media_parsed)
        except Exception as e:
            print(f"Failed to setup media parsed callback: {e}")

    def _on_media_parsed(self, event):
        """Callback when media parsing is complete"""
        if self.media and self.media.get_parsed_status() == vlc.MediaParsedStatus.done:
            self.media_ready.emit()

    def load_url(self, url: str, headers: Optional[Dict[str, str]] = None) -> bool:
        """Load media from URL (with optional HTTP headers)."""
        return self.load_file(url, headers)

    def _apply_media_options(self, headers: Optional[Dict[str, str]] = None):
        """Apply media options"""
        if not self.media:
            return

        # Network settings
        net_settings = self.settings.get_network_settings()
        if self.current_url:
            self.media.add_option(f":network-caching={net_settings.get('buffer_size', 8192)}")
            self.media.add_option(f":http-timeout={net_settings.get('timeout', 30)}")
            self.media.add_option(f":http-user-agent={net_settings.get('user_agent', USER_AGENT)}")

        # Extra per-stream HTTP headers (YouTube etc.)
        if headers:
            def _get(*names):
                for n in names:
                    if n in headers and headers[n]:
                        return headers[n]
                return None

            user_agent = _get("User-Agent", "user-agent")
            referer = _get("Referer", "referer")
            origin = _get("Origin", "origin")
            if user_agent:
                self.media.add_option(f":http-user-agent={user_agent}")
            if referer:
                self.media.add_option(f":http-referrer={referer}")
            if origin:
                self.media.add_option(f":http-origin={origin}")

        # Hardware acceleration
        if self.hardware_acceleration:
            self.media.add_option(":avcodec-hw=any")

    def set_video_widget(self, video_widget):
        """Set video widget for video output"""
        self.video_widget = video_widget
        if self.player and video_widget:
            self._attach_video_output()

    def _attach_video_output(self):
        """Attach VLC video output to the video widget"""
        if not self.player or not self.video_widget:
            return

        try:
            # Ensure widget has a valid native window handle
            self.video_widget.winId()  # Force creation of native window
            
            import sys
            if sys.platform == "win32":
                # Windows: use HWND
                self.player.set_hwnd(int(self.video_widget.winId()))
            elif sys.platform == "darwin":
                # macOS: use NSView
                self.player.set_nsobject(int(self.video_widget.winId()))
            else:
                # Linux: use XWindow
                self.player.set_xwindow(int(self.video_widget.winId()))
            
            self._video_output_attached = True
        except Exception as e:
            print(f"Failed to attach video output: {e}")

    def _apply_playback_settings(self):
        """Apply current playback settings"""
        if not self.player:
            return

        # Volume
        self.player.audio_set_volume(self._vlc_volume(self.volume))
        self.player.audio_set_mute(self.muted)

        # Speed
        self.player.set_rate(self.speed)

        # Audio sync
        audio_sync = self.settings.get_audio_sync()
        if audio_sync != 0:
            self.player.audio_set_delay(audio_sync * 1000)  # ms

        # Attach video output if not already attached
        if not self._video_output_attached:
            self._attach_video_output()

    def play(self):
        """Start/resume playback"""
        if not self._ensure_player():
            return

        if self.state == PlaybackState.PAUSED:
            self.player.set_pause(False)
            self._set_state(PlaybackState.PLAYING)
        else:
            result = self.player.play()
            if result != 0:
                self.error_occurred.emit(f"Failed to start playback: VLC error code {result}")
                self._set_state(PlaybackState.ERROR)
            else:
                # Optimistically set state to playing - _update_position will correct if needed
                self._set_state(PlaybackState.PLAYING)
        
        # Start polling timer to track state/position
        self._position_timer.start()

        # Re-apply the (boosted) volume for the next ~2 s: the audio output is
        # created just after play() and would otherwise start at nominal 100.
        self._volume_reapply_ticks = 20

    def pause(self):
        """Pause playback"""
        if not self._ensure_player() or self.state != PlaybackState.PLAYING:
            return
        self.player.set_pause(True)

    def stop(self):
        """Stop playback"""
        if not self._ensure_player():
            return
        self.player.stop()
        self._position_timer.stop()
        self._set_state(PlaybackState.STOPPED)
        self.position = 0.0
        self.position_changed.emit(0.0, self.duration)

    def is_finished(self) -> bool:
        """True when the current media has played through to its end."""
        if self.state == PlaybackState.ENDED:
            return True
        if self.state == PlaybackState.PLAYING:
            return False
        return self.duration > 0 and self.position >= self.duration - 0.5

    def restart(self):
        """Restart the current media from the very beginning and play it.

        VLC keeps the input at EOF once a stream finishes, so a plain
        ``play()`` would report the end again immediately; stop + play rewinds
        it properly.
        """
        if not self._ensure_player():
            return
        try:
            self.player.stop()
        except Exception:
            pass
        self.position = 0.0
        result = self.player.play()
        try:
            self.player.set_time(0)
        except Exception:
            pass
        if result != 0:
            self.error_occurred.emit(f"Failed to restart playback: VLC error code {result}")
            self._set_state(PlaybackState.ERROR)
            return
        self._set_state(PlaybackState.PLAYING)
        self._position_timer.start()
        self._volume_reapply_ticks = 20
        self.position_changed.emit(0.0, self.duration)

    def toggle_play_pause(self):
        """Toggle play/pause.

        When the current media has already finished, Space must restart it from
        the beginning instead of doing nothing and re-reporting the end.
        """
        if self.state == PlaybackState.PLAYING:
            self.pause()
        elif self.is_finished():
            self.restart()
        else:
            self.play()

    def seek(self, position: float):
        """Seek to position (0.0 to 1.0)"""
        if not self._ensure_player() or self.duration <= 0:
            return
        time_ms = int(position * self.duration * 1000)
        self.player.set_time(time_ms)

    def seek_relative(self, seconds: float) -> float:
        """Seek relative to the current position.

        Works while playing *and* while paused or stopped (the tracked position
        is used as the base when the player reports no usable time) and returns
        the resulting position in seconds so callers can announce it.
        """
        if not self._ensure_player() or self.duration <= 0:
            return self.position
        base = self.position
        if self.state == PlaybackState.PLAYING:
            try:
                current_ms = self.player.get_time()
                if current_ms >= 0:
                    base = current_ms / 1000.0
            except Exception:
                pass
        new_time = max(0.0, min(base + float(seconds), self.duration))
        try:
            self.player.set_time(int(new_time * 1000))
        except Exception:
            pass
        self.position = new_time
        self.position_changed.emit(self.position, self.duration)
        return new_time

    def _vlc_volume(self, percent: int) -> int:
        """Map the UI volume (0-100) onto libvlc's volume scale.

        libvlc uses a linear gain where 100 == 0 dB.  Multiplying by
        ``VOLUME_GAIN`` (see above) makes 100 % on the slider amplify the
        audio so the player is clearly louder than the system at 100 %.
        """
        try:
            percent = max(0, min(100, int(percent)))
        except (TypeError, ValueError):
            percent = 0
        return int(round(percent * self.VOLUME_GAIN))

    def set_volume(self, volume: int):
        """Set volume (0-100)"""
        if not self._ensure_player():
            return
        self.volume = max(0, min(100, volume))
        self.player.audio_set_volume(self._vlc_volume(self.volume))
        self.volume_changed.emit(self.volume)
        self.settings.set_volume(self.volume)

    def set_muted(self, muted: bool):
        """Toggle mute"""
        if not self._ensure_player():
            return
        self.muted = muted
        self.player.audio_set_mute(muted)
        self.muted_changed.emit(muted)

    def toggle_mute(self):
        """Toggle mute state"""
        self.set_muted(not self.muted)

    def set_speed(self, speed: float):
        """Set playback speed"""
        if not self._ensure_player():
            return
        self.speed = max(0.25, min(4.0, speed))
        self.player.set_rate(self.speed)
        self.speed_changed.emit(self.speed)
        self.settings.set_speed(self.speed)

    def get_speed(self) -> float:
        return self.speed

    def get_volume(self) -> int:
        return self.volume

    def is_muted(self) -> bool:
        return self.muted

    def get_position(self) -> float:
        """Get position as 0.0-1.0"""
        if self.duration > 0:
            return self.position / self.duration
        return 0.0

    def get_time(self) -> float:
        """Get current time in seconds"""
        return self.position

    def get_duration(self) -> float:
        """Get total duration in seconds"""
        return self.duration

    def get_state(self) -> PlaybackState:
        return self.state

    def _set_state(self, state: PlaybackState):
        """Update playback state"""
        if self.state != state:
            self.state = state
            self.state_changed.emit(state.value)

    def _update_position(self):
        """Update position from player - also polls state changes"""
        if self._cleaned_up or not self._ensure_player():
            return
            
        try:
            # Get current VLC state
            vlc_state = self.player.get_state()
            
            # Map VLC state to our state
            new_state = self._vlc_state_to_playback_state(vlc_state)

            # Some backends report State.Stopped at EOF instead of State.Ended.
            # Treat "stopped at the very end" as finished so auto-advance and
            # replay-after-end still work - but never infer the end from the
            # position alone, because a provisional/short duration would then
            # end a long file early.
            if (new_state == PlaybackState.STOPPED and self.duration > 0
                    and self.position >= self.duration - 1.0):
                new_state = PlaybackState.ENDED

            if new_state != self.state:
                self._set_state(new_state)
                if new_state == PlaybackState.PLAYING:
                    self._position_timer.start()
                else:
                    self._position_timer.stop()
                if new_state == PlaybackState.ENDED:
                    self.media_ended.emit()

            # Re-apply the boosted volume for a short window after playback
            # starts: VLC's audio output is created just after play() and
            # otherwise ignores the volume that was set before it existed.
            if self._volume_reapply_ticks > 0 and self.state == PlaybackState.PLAYING:
                try:
                    self.player.audio_set_volume(self._vlc_volume(self.volume))
                    self.player.audio_set_mute(self.muted)
                except Exception:
                    pass
                self._volume_reapply_ticks -= 1

            # Keep the duration up to date: VLC can report a provisional (and
            # occasionally wrong) length right after load, then correct it once
            # the file is fully parsed.  A stale, too-small duration used to make
            # the player believe a long file had ended after a minute or two.
            try:
                dur_ms = self.player.get_length()
                if dur_ms <= 0 and self.media:
                    dur_ms = self.media.get_duration()
                if dur_ms and dur_ms > 0:
                    new_duration = dur_ms / 1000.0
                    if abs(new_duration - self.duration) > 1.0:
                        self.duration = new_duration
                        self.duration_changed.emit(self.duration)
            except Exception as e:
                print(f"get_duration ERROR: {e}")

            # Update position
            if self.state == PlaybackState.PLAYING:
                try:
                    time_ms = self.player.get_time()
                    if time_ms >= 0:
                        self.position = time_ms / 1000.0
                        self.position_changed.emit(self.position, self.duration)
                except Exception as e:
                    print(f"get_time ERROR: {e}")
        except Exception as e:
            print(f"_update_position ERROR: {e}")
            import traceback
            traceback.print_exc()

    def _vlc_state_to_playback_state(self, vlc_state) -> PlaybackState:
        """Convert VLC state to PlaybackState"""
        if vlc_state == vlc.State.Playing:
            return PlaybackState.PLAYING
        elif vlc_state == vlc.State.Paused:
            return PlaybackState.PAUSED
        elif vlc_state == vlc.State.Stopped:
            return PlaybackState.STOPPED
        elif vlc_state == vlc.State.Ended:
            return PlaybackState.ENDED
        elif vlc_state == vlc.State.Buffering:
            return PlaybackState.BUFFERING
        elif vlc_state == vlc.State.Error:
            return PlaybackState.ERROR
        return PlaybackState.STOPPED

    # Audio track management
    def get_audio_tracks(self) -> List[Dict[str, Any]]:
        """Get available audio tracks"""
        if not self.player:
            return []
        try:
            tracks = self.player.audio_get_track_description()
            return [{"id": tid, "name": name} for tid, name in tracks]
        except:
            return []

    def set_audio_track(self, track_id: int):
        """Set audio track"""
        if self.player:
            self.player.audio_set_track(track_id)
            self.audio_track_changed.emit(track_id)

    def get_current_audio_track(self) -> int:
        if self.player:
            return self.player.audio_get_track()
        return -1

    # Video track management
    def get_video_tracks(self) -> List[Dict[str, Any]]:
        """Get available video tracks"""
        if not self.player:
            return []
        try:
            tracks = self.player.video_get_track_description()
            return [{"id": tid, "name": name} for tid, name in tracks]
        except:
            return []

    def set_video_track(self, track_id: int):
        """Set video track"""
        if self.player:
            self.player.video_set_track(track_id)
            self.video_track_changed.emit(track_id)

    def get_current_video_track(self) -> int:
        if self.player:
            return self.player.video_get_track()
        return -1

    # Subtitle management
    def get_subtitle_tracks(self) -> List[Dict[str, Any]]:
        """Get available subtitle tracks"""
        if not self.player:
            return []
        try:
            tracks = self.player.video_get_spu_description()
            return [{"id": tid, "name": name} for tid, name in tracks]
        except:
            return []

    def set_subtitle_track(self, track_id: int):
        """Set subtitle track"""
        if self.player:
            self.player.video_set_spu(track_id)
            self.subtitle_changed.emit(track_id)

    def get_current_subtitle_track(self) -> int:
        if self.player:
            return self.player.video_get_spu()
        return -1

    def load_external_subtitle(self, subtitle_path: str) -> bool:
        """Load external subtitle file"""
        if not self.player or not self.media:
            return False
        try:
            self.player.video_set_subtitle_file(subtitle_path)
            return True
        except:
            return False

    def set_subtitle_delay(self, delay_ms: int):
        """Set subtitle delay in milliseconds"""
        self._subtitle_delay_ms = int(delay_ms)
        if self.player:
            self.player.video_set_spu_delay(self._subtitle_delay_ms)

    def get_subtitle_delay(self) -> int:
        """Return the current subtitle delay in milliseconds."""
        return int(getattr(self, "_subtitle_delay_ms", 0))

    def adjust_subtitle_delay(self, delta_ms: int) -> int:
        """Nudge the subtitle delay by *delta_ms* and return the new value."""
        self.set_subtitle_delay(self.get_subtitle_delay() + int(delta_ms))
        return self.get_subtitle_delay()

    def set_audio_sync(self, seconds: int):
        """Set the audio delay in *seconds* (may be negative) and remember it."""
        seconds = int(seconds)
        self.settings.set_audio_sync(seconds)
        if self.player:
            self.player.audio_set_delay(seconds * 1000)  # ms

    def get_audio_sync(self) -> int:
        """Return the current audio delay in seconds."""
        return int(self.settings.get_audio_sync())

    # Video adjustments
    def set_aspect_ratio(self, ratio: str):
        """Set aspect ratio (e.g., '16:9', '4:3')"""
        if self.player:
            self.player.video_set_aspect_ratio(ratio)

    def set_scale(self, scale: float):
        """Set video scale"""
        if self.player:
            self.player.video_set_scale(scale)

    def set_crop(self, crop: str):
        """Set video crop"""
        if self.player:
            self.player.video_set_crop(crop)

    def take_snapshot(self, file_path: str) -> bool:
        """Take video snapshot"""
        if self.player:
            try:
                return self.player.video_take_snapshot(0, file_path, 0, 0) == 0
            except:
                return False
        return False

    # Equalizer
    def setup_equalizer(self):
        """Setup equalizer"""
        try:
            import vlc
            self.equalizer = vlc.AudioEqualizer()
            self.player.set_equalizer(self.equalizer)
        except:
            pass

    def set_equalizer_band(self, band: int, value: float):
        """Set equalizer band value (-20 to 20)"""
        if self.equalizer:
            self.equalizer.set_amp_at_index(value, band)

    def get_equalizer_band(self, band: int) -> float:
        if self.equalizer:
            return self.equalizer.get_amp_at_index(band)
        return 0.0

    def set_equalizer_preset(self, preset_name: str):
        """Set equalizer preset"""
        try:
            import vlc
            presets = vlc.AudioEqualizer.get_preset_names()
            if preset_name in presets:
                self.equalizer = vlc.AudioEqualizer.new_from_preset(preset_name)
                self.player.set_equalizer(self.equalizer)
        except:
            pass

    def enable_equalizer(self, enabled: bool):
        """Enable/disable equalizer"""
        if self.player:
            if enabled and not self.equalizer:
                self.setup_equalizer()
            self.player.set_equalizer(self.equalizer if enabled else None)

    def cleanup(self):
        """Cleanup resources"""
        self._cleaned_up = True
        self._position_timer.stop()
        try:
            if self.player:
                self.player.stop()
                # Don't release player/instance to avoid Windows COM cleanup crashes
                # The OS will clean up on process exit
        except Exception:
            pass