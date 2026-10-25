"""Fill the remaining translation gaps in the complete catalogues.

Run after :mod:`tools.build_translations` ``extract``:

    python tools/fill_translations.py

It has two tables:

* ``TRANSLATIONS`` - ``{source string: {language: translation}}``.  Applied to
  every context that uses the source string, so a term is translated the same
  way everywhere in a given language.
* ``IDENTITY`` - sources that are technical names, protocols, codec options or
  brand names.  They are written identically in every language on purpose
  (translating "DirectSound" or "1080p" would be wrong), and are registered so
  the catalogue explicitly states they are *not* missing.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_translations as B  # noqa: E402

NL = "\n"

# ----------------------------------------------------------------------
# Strings that must stay as they are, in every language.
# ----------------------------------------------------------------------
IDENTITY = [
    # video resolutions
    "1080p", "720p", "480p",
    # VLC / Windows audio & video output back-ends and options
    "DirectSound", "WASAPI", "WaveOut", "Direct3D11", "Direct3D9", "OpenGL",
    "Yadif", "Yadif2x", "IVTC", "Bob", "X",
    # streaming protocols
    "HTTP/HTTPS", "RTSP", "RTMP", "MMS", "RTP",
    "HLS (.m3u8)", "DASH (.mpd)",
    # network / HTTP terms that are international
    "URL:", "Referer", "Referer:", "User Agent:", "Cookies", "Cookies:",
    "Host", "Software",
    # music genres (international loan words)
    "Club", "Dance", "Live", "Party", "Pop", "Reggae", "Rock", "Ska", "Techno",
    # brand name
    "YouTube",
    # millisecond unit symbol - the same in every language
    " ms",
]

# Words that are *correct* in these languages exactly as they are written in
# English (Italian "Audio"/"Video"/"Volume", Spanish "General"/"Error",
# Portuguese "Linear"/"Volume", Turkish "Video", and the minute abbreviation).
# They must not be reported as translation gaps.
IDENTITY_WORDS = {
    "langs": {"it", "es", "pt", "tr"},
    "sources": [
        "Audio", "Video", "Playlist", "Volume", "File", "Password", "Password:",
        "Zoom", "Linear", "General", "Error",
        "&File", "&Playlist...", "&Audio", "&Video",
        "Playlist (Ctrl+L)", "Volume: {0}%",
        "1 min", "5 min", "10 min", "30 min",
    ],
}

# ----------------------------------------------------------------------
# Translations.  One entry per source string, applied to every context.
# ----------------------------------------------------------------------
TRANSLATIONS: dict = {
    # ---------------- About / contact -------------------------------
    "Copy Number": {
        "ar": "نسخ الرقم", "it": "Copia numero", "es": "Copiar número",
        "pt": "Copiar número", "tr": "Numarayı kopyala",
    },
    "Number copied": {
        "ar": "تم نسخ الرقم", "it": "Numero copiato", "es": "Número copiado",
        "pt": "Número copiado", "tr": "Numara kopyalandı",
    },
    "Contact number": {
        "ar": "رقم التواصل", "it": "Numero di contatto",
        "es": "Número de contacto", "pt": "Número de contato",
        "tr": "İletişim numarası",
    },

    # ---------------- Startup setting -------------------------------
    "Empty (open with nothing)": {
        "ar": "فارغ (فتح دون أي ملف)", "it": "Vuoto (apri senza nulla)",
        "es": "Vacío (abrir sin nada)", "pt": "Vazio (abrir sem nada)",
        "tr": "Boş (hiçbir şey açma)",
    },

    # ---------------- Control panel ---------------------------------
    "No media loaded": {
        "it": "Nessun file caricato",
        "es": "No hay archivos cargados",
        "pt": "Nenhum arquivo carregado",
        "tr": "Dosya yüklenmedi",
    },
    "One": {
        "it": "Uno", "es": "Uno", "pt": "Um", "tr": "Bir",
    },
    "All": {
        "it": "Tutti", "es": "Todos", "pt": "Todos", "tr": "Tümü",
    },
    "Repeat ({0}) (R)": {
        "it": "Ripeti ({0}) (R)", "es": "Repetir ({0}) (R)",
        "pt": "Repetir ({0}) (R)", "tr": "Tekrarla ({0}) (R)",
    },
    "5 sec": {"it": "5 s", "es": "5 s", "pt": "5 s", "tr": "5 sn"},
    "10 sec": {"it": "10 s", "es": "10 s", "pt": "10 s", "tr": "10 sn"},
    "30 sec": {"it": "30 s", "es": "30 s", "pt": "30 s", "tr": "30 sn"},
    "1 min": {"it": "1 min", "es": "1 min", "pt": "1 min", "tr": "1 dk"},
    "5 min": {"it": "5 min", "es": "5 min", "pt": "5 min", "tr": "5 dk"},
    "10 min": {"it": "10 min", "es": "10 min", "pt": "10 min", "tr": "10 dk"},
    "30 min": {"it": "30 min", "es": "30 min", "pt": "30 min", "tr": "30 dk"},
    "Volume": {
        "it": "Volume", "es": "Volumen", "pt": "Volume", "tr": "Ses",
    },
    "Volume: {0}%": {
        "ar": "الصوت: {0}%", "it": "Volume: {0}%", "es": "Volumen: {0}%",
        "pt": "Volume: {0}%", "tr": "Ses: {0}%",
    },
    "Playlist (Ctrl+L)": {
        "it": "Playlist (Ctrl+L)", "es": "Lista de reproducción (Ctrl+L)",
        "pt": "Lista de reprodução (Ctrl+L)", "tr": "Çalma listesi (Ctrl+L)",
    },

    # ---------------- Menus -----------------------------------------
    "&File": {
        "it": "&File", "es": "&Archivo", "pt": "&Arquivo", "tr": "&Dosya",
    },
    "&Playlist...": {
        "it": "&Playlist...", "es": "&Lista...", "pt": "&Lista...", "tr": "&Çalma listesi...",
    },
    "&Audio": {
        "it": "&Audio", "es": "&Audio", "pt": "&Áudio", "tr": "&Ses",
    },
    "&Video": {
        "it": "&Video", "es": "&Vídeo", "pt": "&Vídeo", "tr": "&Video",
    },
    "File": {
        "it": "File", "es": "Archivo", "pt": "Arquivo", "tr": "Dosya",
    },
    "Playlist": {
        "it": "Playlist", "es": "Lista de reproducción",
        "pt": "Lista de reprodução", "tr": "Çalma listesi",
    },
    "Audio": {
        "it": "Audio", "es": "Audio", "pt": "Áudio", "tr": "Ses",
    },
    "Video": {
        "it": "Video", "es": "Vídeo", "pt": "Vídeo", "tr": "Video",
    },
    "General": {
        "it": "Generale", "es": "General", "pt": "Geral", "tr": "Genel",
    },
    "Buffering...": {
        "es": "Almacenando en búfer...",
        "pt": "Armazenando em buffer...",
        "tr": "Arabelleğe alınıyor...",
    },
    "Error": {
        "it": "Errore", "es": "Error", "pt": "Erro", "tr": "Hata",
    },
    "Zoom": {
        "it": "Zoom", "es": "Zoom", "pt": "Zoom", "tr": "Yakınlaştırma",
    },
    "Password": {
        "it": "Password", "es": "Contraseña", "pt": "Senha", "tr": "Şifre",
    },
    "Password:": {
        "it": "Password:", "es": "Contraseña:", "pt": "Senha:", "tr": "Şifre:",
    },
    "Linear": {
        "it": "Lineare", "es": "Lineal", "pt": "Linear", "tr": "Doğrusal",
    },

    # ---------------- Units -----------------------------------------
    " sec": {
        "ar": " ث", "it": " s", "es": " s", "pt": " s", "tr": " sn",
    },
    " ms": {
        "ar": " م.ث", "it": " ms", "es": " ms", "pt": " ms", "tr": " ms",
    },

    # ---------------- Bookmarks -------------------------------------
    "Bookmarks": {
        "it": "Segnalibri", "es": "Marcadores", "pt": "Favoritos",
        "tr": "Yer imleri",
    },
    "No bookmarks yet. Click 'Add Bookmark' to create one.": {
        "ar": "لا توجد علامات مرجعية بعد. اضغط على 'إضافة علامة' لإنشائها.",
        "it": "Nessun segnalibro. Clicca 'Aggiungi segnalibro' per crearne uno.",
        "es": "Aún no hay marcadores. Pulsa 'Añadir marcador' para crear uno.",
        "pt": "Ainda não há favoritos. Clique em 'Adicionar favorito'.",
        "tr": "Henüz yer imi yok. 'Yer imi ekle'ye tıklayın.",
    },
    "Bookmark {0}": {
        "it": "Segnalibro {0}", "es": "Marcador {0}", "pt": "Favorito {0}",
        "tr": "Yer imi {0}",
    },
    "Bookmark name:": {
        "it": "Nome segnalibro:", "es": "Nombre del marcador:",
        "pt": "Nome do favorito:", "tr": "Yer imi adı:",
    },
    "Bookmark '{0}' added": {
        "it": "Segnalibro '{0}' aggiunto", "es": "Marcador '{0}' añadido",
        "pt": "Favorito '{0}' adicionado", "tr": "Yer imi '{0}' eklendi",
    },
    "Bookmark '{0}' added at {1}": {
        "it": "Segnalibro '{0}' aggiunto a {1}",
        "es": "Marcador '{0}' añadido en {1}",
        "pt": "Favorito '{0}' adicionado em {1}",
        "tr": "Yer imi '{0}' {1} konumuna eklendi",
    },
    "Rename Bookmark": {
        "it": "Rinomina segnalibro", "es": "Renombrar marcador",
        "pt": "Renomear favorito", "tr": "Yer imini yeniden adlandır",
    },
    "New name:": {
        "it": "Nuovo nome:", "es": "Nuevo nombre:", "pt": "Novo nome:",
        "tr": "Yeni ad:",
    },
    "Bookmark renamed to '{0}'": {
        "it": "Segnalibro rinominato in '{0}'",
        "es": "Marcador renombrado a '{0}'",
        "pt": "Favorito renomeado para '{0}'",
        "tr": "Yer imi '{0}' olarak adlandırıldı",
    },
    "Delete Bookmark": {
        "it": "Elimina segnalibro", "es": "Eliminar marcador",
        "pt": "Excluir favorito", "tr": "Yer imini sil",
    },
    "Delete bookmark '{0}'?": {
        "it": "Eliminare il segnalibro '{0}'?",
        "es": "¿Eliminar el marcador '{0}'?",
        "pt": "Excluir o favorito '{0}'?",
        "tr": "Yer imi '{0}' silinsin mi?",
    },
    "Bookmark '{0}' deleted": {
        "it": "Segnalibro '{0}' eliminato", "es": "Marcador '{0}' eliminado",
        "pt": "Favorito '{0}' excluído", "tr": "Yer imi '{0}' silindi",
    },
    "Jumped to bookmark at {0}": {
        "it": "Saltato al segnalibro a {0}",
        "es": "Saltado al marcador en {0}",
        "pt": "Saltou para o favorito em {0}",
        "tr": "{0} konumundaki yer imine geçildi",
    },

    # ---------------- Playlist manager ------------------------------
    "Custom Playlists": {
        "it": "Playlist personalizzate", "es": "Listas personalizadas",
        "pt": "Listas personalizadas", "tr": "Özel çalma listeleri",
    },
    "New...": {
        "it": "Nuovo...", "es": "Nueva...", "pt": "Nova...", "tr": "Yeni...",
    },
    "Save Current As...": {
        "it": "Salva corrente come...", "es": "Guardar la actual como...",
        "pt": "Salvar a atual como...", "tr": "Geçerliyi farklı kaydet...",
    },
    "Rename...": {
        "it": "Rinomina...", "es": "Renombrar...", "pt": "Renomear...",
        "tr": "Yeniden adlandır...",
    },
    "Add Files...": {
        "it": "Aggiungi file...", "es": "Añadir archivos...",
        "pt": "Adicionar arquivos...", "tr": "Dosya ekle...",
    },
    "Remove Item": {
        "it": "Rimuovi elemento", "es": "Quitar elemento",
        "pt": "Remover item", "tr": "Öğeyi kaldır",
    },
    "Load Into Player": {
        "it": "Carica nel lettore", "es": "Cargar en el reproductor",
        "pt": "Carregar no reprodutor", "tr": "Oynatıcıya yükle",
    },
    "Playlist Contents": {
        "it": "Contenuti della playlist", "es": "Contenido de la lista",
        "pt": "Conteúdo da lista", "tr": "Çalma listesi içeriği",
    },
    "{0} ({1} items)": {
        "it": "{0} ({1} elementi)", "es": "{0} ({1} elementos)",
        "pt": "{0} ({1} itens)", "tr": "{0} ({1} öğe)",
    },
    "New Custom Playlist": {
        "it": "Nuova playlist personalizzata",
        "es": "Nueva lista personalizada", "pt": "Nova lista personalizada",
        "tr": "Yeni özel çalma listesi",
    },
    "A playlist named '{0}' already exists.": {
        "it": "Esiste già una playlist chiamata '{0}'.",
        "es": "Ya existe una lista llamada '{0}'.",
        "pt": "Já existe uma lista chamada '{0}'.",
        "tr": "'{0}' adında bir çalma listesi zaten var.",
    },
    "A playlist named '{0}' already exists. Replace its contents?": {
        "it": "Esiste già una playlist chiamata '{0}'. Sostituirne il contenuto?",
        "es": "Ya existe una lista llamada '{0}'. ¿Reemplazar su contenido?",
        "pt": "Já existe uma lista chamada '{0}'. Substituir o conteúdo?",
        "tr": "'{0}' adında bir çalma listesi zaten var. İçeriği değiştirilsin mi?",
    },
    "Select or create a custom playlist first.": {
        "it": "Seleziona o crea prima una playlist personalizzata.",
        "es": "Selecciona o crea primero una lista personalizada.",
        "pt": "Selecione ou crie primeiro uma lista personalizada.",
        "tr": "Önce bir özel çalma listesi seçin veya oluşturun.",
    },
    "Rename Custom Playlist": {
        "it": "Rinomina playlist personalizzata",
        "es": "Renombrar lista personalizada",
        "pt": "Renomear lista personalizada",
        "tr": "Özel çalma listesini yeniden adlandır",
    },
    "Delete Custom Playlist": {
        "it": "Elimina playlist personalizzata",
        "es": "Eliminar lista personalizada",
        "pt": "Excluir lista personalizada",
        "tr": "Özel çalma listesini sil",
    },
    "Delete the custom playlist '{0}'?": {
        "it": "Eliminare la playlist personalizzata '{0}'?",
        "es": "¿Eliminar la lista personalizada '{0}'?",
        "pt": "Excluir a lista personalizada '{0}'?",
        "tr": "Özel çalma listesi '{0}' silinsin mi?",
    },

    # ---------------- Shortcuts dialog ------------------------------
    "Subtitle: {0} entries" + NL + "Duration: {1}": {
        "ar": "الترجمة: {0} مقطع" + NL + "المدة: {1}",
        "it": "Sottotitoli: {0} voci" + NL + "Durata: {1}",
        "es": "Subtítulos: {0} entradas" + NL + "Duración: {1}",
        "pt": "Legendas: {0} entradas" + NL + "Duração: {1}",
        "tr": "Altyazı: {0} kayıt" + NL + "Süre: {1}",
    },
    "Found: {0}" + NL + "Format: {1}" + NL + "Entries: {2}": {
        "ar": "تم العثور على: {0}" + NL + "الصيغة: {1}" + NL + "المقاطع: {2}",
        "it": "Trovato: {0}" + NL + "Formato: {1}" + NL + "Voci: {2}",
        "es": "Encontrado: {0}" + NL + "Formato: {1}" + NL + "Entradas: {2}",
        "pt": "Encontrado: {0}" + NL + "Formato: {1}" + NL + "Entradas: {2}",
        "tr": "Bulundu: {0}" + NL + "Biçim: {1}" + NL + "Kayıt: {2}",
    },
    "Subtitle Files (*{0});;All Files (*.*)": {
        "it": "File sottotitoli (*{0});;Tutti i file (*.*)",
        "es": "Archivos de subtítulos (*{0});;Todos los archivos (*.*)",
        "pt": "Arquivos de legendas (*{0});;Todos os arquivos (*.*)",
        "tr": "Altyazı dosyaları (*{0});;Tüm dosyalar (*.*)",
    },
}


def main() -> int:
    pairs = B.collect_pairs()
    # source -> set of contexts that use it
    contexts: dict = {}
    for ctx, src in pairs:
        contexts.setdefault(src, set()).add(ctx)

    changed = 0
    for lang in ("ar", "it", "es", "pt", "tr"):
        data = B.load_catalogue(lang)
        added = 0

        # 1) technical / international terms stay identical
        for src in IDENTITY:
            for ctx in contexts.get(src, ()):
                bucket = data.setdefault(ctx, {})
                if bucket.get(src) is None:
                    bucket[src] = src
                    added += 1

        # 1b) words that are already correct in this language
        if lang in IDENTITY_WORDS["langs"]:
            for src in IDENTITY_WORDS["sources"]:
                for ctx in contexts.get(src, ()):
                    bucket = data.setdefault(ctx, {})
                    if bucket.get(src) is None:
                        bucket[src] = src
                        added += 1

        # 2) explicit translations
        for src, per_lang in TRANSLATIONS.items():
            value = per_lang.get(lang)
            if value is None:
                continue
            for ctx in contexts.get(src, ()):
                bucket = data.setdefault(ctx, {})
                if bucket.get(src) != value:
                    bucket[src] = value
                    added += 1

        B.save_catalogue(lang, data)
        changed += added
        print(f"{lang}: {added} entries filled")

    print(f"total: {changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
