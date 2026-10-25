"""
About content - a detailed, localized "A to Z" usage guide for the About dialog.

The text is kept here (rather than in the .qm catalogues) because it is a long
document that must always be available in every language the app ships with.
"""

from core.app_meta import APP_NAME, CONTACT_NUMBER_DISPLAY

# Each language maps to an HTML document shown in the About dialog.
ABOUT_TEXT = {
    "en": """
<h2>{APP_NAME}</h2>
<p><b>Version 1.0</b> &mdash; a professional media player with full accessibility support.</p>

<h3>1. Getting started</h3>
<p>When the player starts it opens without loading any file, so it never re-associates itself with a
previous session. You can choose to reopen the last file, the last playlist or resume the last position
from <b>Settings &rarr; On Startup</b>. Everything can be controlled from the menu bar at the top or with
the keyboard shortcuts below.</p>

<h3>2. Opening media</h3>
<ul>
<li><b>File &rarr; Open File (Ctrl+O):</b> pick one or more media files with the standard Windows dialog.</li>
<li><b>File &rarr; Open URL (Ctrl+U):</b> play a network stream (HTTP/HTTPS, HLS, DASH, RTSP, RTMP, MMS&hellip;).</li>
<li><b>File &rarr; Open YouTube (Ctrl+Y):</b> paste any YouTube link. Both <b>recorded videos</b> and <b>live streams</b> are supported; choose the quality and optional subtitles.</li>
<li>You can also open files by double-clicking them in Windows Explorer when file associations are set up.</li>
</ul>

<h3>3. Playback</h3>
<ul>
<li><b>Space</b> play / pause &middot; <b>S</b> stop</li>
<li><b>Ctrl+Right</b> or <b>N</b> next track &middot; <b>Ctrl+Left</b> or <b>P</b> previous track</li>
<li><b>Right</b> / <b>Left</b> seek by the current seek interval &middot; <b>Shift+Right</b> / <b>Shift+Left</b> seek 60&nbsp;seconds</li>
<li><b>Q</b> faster &middot; <b>A</b> slower &middot; <b>\\</b> normal speed</li>
</ul>

<h3>4. Volume and audio</h3>
<p><b>+</b> / <b>-</b> raise or lower the volume, <b>M</b> mutes. The Audio menu lets you choose an audio track,
adjust audio delay and open the equalizer.</p>

<h3>5. Subtitles</h3>
<p>Subtitles are detected automatically when a matching <i>.srt/.ass/.ssa/.vtt</i> file sits next to the video.
The <b>Subtitles</b> menu opens the options dialog, export, delay adjustment and manual loading.
Export formats: <b>TXT</b>, <b>DOCX</b>, <b>PDF</b>.</p>

<h3>6. Playlist</h3>
<p><b>File &rarr; Playlist (Ctrl+L)</b>. Add, reorder and sort items, and save/load M3U playlists.
Repeat and shuffle are in the control panel. When a file finishes the next one plays automatically.</p>

<h3>7. Bookmarks</h3>
<p>Add a bookmark at the current position with <b>Ctrl+Shift+B</b>, then jump back to it later from the
<b>Bookmarks</b> menu.</p>

<h3>8. Video</h3>
<p>Aspect ratio, crop, zoom, snapshots and fullscreen (<b>F</b>).</p>

<h3>9. Appearance</h3>
<p>The <b>View</b> menu offers a dark theme, a light theme and a high-contrast mode.</p>

<h3>10. Settings (Ctrl+P)</h3>
<p>Language, theme, hardware acceleration, network buffer, default seek interval, equalizer and accessibility options.</p>

<h3>11. Accessibility</h3>
<p>Screen-reader announcements, enhanced keyboard navigation, high contrast and a full shortcut list
(<b>Help &rarr; Keyboard Shortcuts</b>). Press <b>Ctrl+B</b> to announce the elapsed, total and remaining time.</p>

<h3>12. Supported formats</h3>
<p>MP4, AVI, MKV, MOV, MP3, WAV, FLAC, OGG, M4A, WMA, WebM, TS, WMV, MPG, VOB, OGV and many more &mdash; plus network streams.</p>

<p>Built with Python, PySide6 and VLC.</p>
""",

    "ar": """
<h2>{APP_NAME}</h2>
<p><b>الإصدار 1.0</b> &mdash; مشغّل وسائط احترافي بدعم كامل لإمكانية الوصول.</p>

<h3>١. بدء الاستخدام</h3>
<p>عند فتح المشغّل يبدأ دون تحميل أي ملف، فلا يرتبط تلقائياً بأي جلسة سابقة. يمكنك اختيار إعادة فتح آخر ملف
أو آخر قائمة تشغيل أو استئناف آخر موضع من <b>الإعدادات &rarr; عند البدء</b>. يمكنك التحكم في كل شيء من شريط
القوائم في الأعلى أو عبر اختصارات لوحة المفاتيح المذكورة أدناه.</p>

<h3>٢. فتح الوسائط</h3>
<ul>
<li><b>ملف &rarr; فتح ملف (Ctrl+O):</b> اختر ملفاً واحداً أو أكثر عبر نافذة الويندوز القياسية.</li>
<li><b>ملف &rarr; فتح رابط (Ctrl+U):</b> تشغيل بثّ شبكي (HTTP/HTTPS و HLS و DASH و RTSP و RTMP و MMS&hellip;).</li>
<li><b>ملف &rarr; فتح يوتيوب (Ctrl+Y):</b> الصق أي رابط يوتيوب؛ يدعم المشغّل <b>الفيديوهات المسجّلة</b> و<b>البثّ المباشر</b>،
مع اختيار الجودة والترجمات الاختيارية.</li>
<li>يمكنك أيضاً فتح الملفات بالنقر المزدوج عليها في مستكشف ويندوز عند تفعيل اقتران أنواع الملفات.</li>
</ul>

<h3>٣. التشغيل</h3>
<ul>
<li><b>مسافة</b> تشغيل/إيقاف مؤقت &middot; <b>S</b> إيقاف</li>
<li><b>Ctrl+يمين</b> أو <b>N</b> الملف التالي &middot; <b>Ctrl+يسار</b> أو <b>P</b> الملف السابق</li>
<li><b>يمين</b> / <b>يسار</b> تقديم/ترجيع بمقدار الفاصل الزمني المحدّد &middot; <b>Shift+يمين</b> / <b>Shift+يسار</b> تقديم/ترجيع ٦٠ ثانية</li>
<li><b>Q</b> أسرع &middot; <b>A</b> أبطأ &middot; <b>\\</b> السرعة الطبيعية</li>
</ul>

<h3>٤. الصوت ومستوى الصوت</h3>
<p><b>+</b> / <b>-</b> رفع أو خفض مستوى الصوت، و<b>M</b> لكتم الصوت. تتيح قائمة الصوت اختيار مسار صوتي،
وضبط تأخير الصوت، وفتح المُعدّل (الإيكولايزر).</p>

<h3>٥. الترجمات</h3>
<p>تُكتشف الترجمات تلقائياً عند وجود ملف مطابق بامتداد <i>.srt/.ass/.ssa/.vtt</i> بجوار الفيديو.
تفتح قائمة <b>الترجمات</b> نافذة الخيارات والتصدير وضبط التأخير والتحميل اليدوي.
صيغ التصدير: <b>TXT</b> و<b>DOCX</b> و<b>PDF</b>.</p>

<h3>٦. قائمة التشغيل</h3>
<p><b>ملف &rarr; قائمة التشغيل (Ctrl+L)</b>. أضف العناصر وأعد ترتيبها وفرزها، واحفظ/حمّل قوائم M3U.
الزرّان «تكرار» و«عشوائي» في لوحة التحكم. عند انتهاء الملف ينتقل المشغّل تلقائياً إلى التالي.</p>

<h3>٧. العلامات المرجعية</h3>
<p>أضف علامة مرجعية عند الموضع الحالي بالضغط على <b>Ctrl+Shift+B</b>، ثم انتقل إليها لاحقاً من قائمة
<b>العلامات المرجعية</b>.</p>

<h3>٨. الفيديو</h3>
<p>نسبة العرض، والقصّ، والتكبير، ولقطات الشاشة، وملء الشاشة (<b>F</b>).</p>

<h3>٩. المظهر</h3>
<p>توفّر قائمة <b>العرض</b> سمة داكنة وسمة فاتحة ووضعاً عالي التباين.</p>

<h3>١٠. الإعدادات (Ctrl+P)</h3>
<p>اللغة، والسمة، وتسريع العتاد، وحجم ذاكرة التخزين المؤقت للشبكة، والفاصل الزمني الافتراضي للتقديم/الترجيع،
والمُعدّل، وخيارات إمكانية الوصول.</p>

<h3>١١. إمكانية الوصول</h3>
<p>إعلانات قارئ الشاشة، والتنقّل الموسّع بلوحة المفاتيح، والوضع عالي التباين، وقائمة كاملة بالاختصارات
(<b>مساعدة &rarr; اختصارات لوحة المفاتيح</b>). اضغط <b>Ctrl+B</b> للإعلان عن الوقت المنقضي والكلي والمتبقّي.</p>

<h3>١٢. الصيغ المدعومة</h3>
<p>MP4 و AVI و MKV و MOV و MP3 و WAV و FLAC و OGG و M4A و WMA و WebM و TS و WMV و MPG و VOB و OGV وغيرها &mdash; إضافةً إلى بثوث الشبكة.</p>

<p>مبنيّ باستخدام Python و PySide6 و VLC.</p>
""",

    "it": """
<h2>{APP_NAME}</h2>
<p><b>Versione 1.0</b> &mdash; un lettore multimediale professionale con pieno supporto all'accessibilit&agrave;.</p>

<h3>1. Per iniziare</h3>
<p>All'avvio il lettore si apre senza caricare alcun file, quindi non si ricollega mai a una sessione
precedente. Puoi scegliere di riaprire l'ultimo file, l'ultima playlist o riprendere l'ultima posizione
da <b>Impostazioni &rarr; All'avvio</b>. Tutto si controlla dalla barra dei menu in alto o con le
scorciatoie da tastiera indicate sotto.</p>

<h3>2. Aprire i contenuti</h3>
<ul>
<li><b>File &rarr; Apri file (Ctrl+O):</b> scegli uno o pi&ugrave; file con la finestra standard di Windows.</li>
<li><b>File &rarr; Apri URL (Ctrl+U):</b> riproduci uno stream di rete (HTTP/HTTPS, HLS, DASH, RTSP, RTMP, MMS&hellip;).</li>
<li><b>File &rarr; Apri YouTube (Ctrl+Y):</b> incolla un link YouTube. Sono supportati sia i <b>video registrati</b> sia le
<b>dirette</b>, con scelta della qualit&agrave; e dei sottotitoli opzionali.</li>
<li>Puoi anche aprire i file con un doppio clic in Esplora file di Windows, se le associazioni sono configurate.</li>
</ul>

<h3>3. Riproduzione</h3>
<ul>
<li><b>Spazio</b> riproduci / pausa &middot; <b>S</b> ferma</li>
<li><b>Ctrl+Destra</b> o <b>N</b> brano successivo &middot; <b>Ctrl+Sinistra</b> o <b>P</b> brano precedente</li>
<li><b>Destra</b> / <b>Sinistra</b> sposta dell'intervallo impostato &middot; <b>Shift+Destra</b> / <b>Shift+Sinistra</b> sposta di 60&nbsp;secondi</li>
<li><b>Q</b> pi&ugrave; veloce &middot; <b>A</b> pi&ugrave; lento &middot; <b>\\</b> velocit&agrave; normale</li>
</ul>

<h3>4. Volume e audio</h3>
<p><b>+</b> / <b>-</b> alza o abbassa il volume, <b>M</b> disattiva l'audio. Il menu Audio permette di scegliere la traccia,
regolare il ritardo audio e aprire l'equalizzatore.</p>

<h3>5. Sottotitoli</h3>
<p>I sottotitoli vengono rilevati automaticamente se accanto al video esiste un file <i>.srt/.ass/.ssa/.vtt</i> corrispondente.
Il menu <b>Sottotitoli</b> apre le opzioni, l'esportazione, la regolazione del ritardo e il caricamento manuale.
Formati di esportazione: <b>TXT</b>, <b>DOCX</b>, <b>PDF</b>.</p>

<h3>6. Playlist</h3>
<p><b>File &rarr; Playlist (Ctrl+L)</b>. Aggiungi, riordina e ordina gli elementi e salva/carica playlist M3U.
Ripeti e casuale sono nel pannello di controllo. Al termine di un file parte automaticamente il successivo.</p>

<h3>7. Segnalibri</h3>
<p>Aggiungi un segnalibro nella posizione corrente con <b>Ctrl+Shift+B</b> e torna ad esso dal menu
<b>Segnalibri</b>.</p>

<h3>8. Video</h3>
<p>Proporzioni, ritaglio, zoom, istantanee e schermo intero (<b>F</b>).</p>

<h3>9. Aspetto</h3>
<p>Il menu <b>Visualizza</b> offre tema scuro, tema chiaro e modalit&agrave; ad alto contrasto.</p>

<h3>10. Impostazioni (Ctrl+P)</h3>
<p>Lingua, tema, accelerazione hardware, buffer di rete, intervallo di spostamento predefinito, equalizzatore e opzioni di accessibilit&agrave;.</p>

<h3>11. Accessibilit&agrave;</h3>
<p>Annunci per screen reader, navigazione da tastiera avanzata, alto contrasto ed elenco completo delle scorciatoie
(<b>Aiuto &rarr; Scorciatoie da tastiera</b>). Premi <b>Ctrl+B</b> per annunciare tempo trascorso, totale e rimanente.</p>

<h3>12. Formati supportati</h3>
<p>MP4, AVI, MKV, MOV, MP3, WAV, FLAC, OGG, M4A, WMA, WebM, TS, WMV, MPG, VOB, OGV e molti altri &mdash; oltre agli stream di rete.</p>

<p>Realizzato con Python, PySide6 e VLC.</p>
""",

    "es": """
<h2>{APP_NAME}</h2>
<p><b>Versi&oacute;n 1.0</b> &mdash; un reproductor multimedia profesional con plena compatibilidad de accesibilidad.</p>

<h3>1. Primeros pasos</h3>
<p>Al iniciarse, el reproductor se abre sin cargar ning&uacute;n archivo, por lo que nunca se reasocia con una
sesi&oacute;n anterior. Puedes elegir reabrir el &uacute;ltimo archivo, la &uacute;ltima lista de reproducci&oacute;n
o reanudar la &uacute;ltima posici&oacute;n desde <b>Configuraci&oacute;n &rarr; Al iniciar</b>. Todo se controla desde la
barra de men&uacute;s superior o con los atajos de teclado indicados abajo.</p>

<h3>2. Abrir contenido multimedia</h3>
<ul>
<li><b>Archivo &rarr; Abrir archivo (Ctrl+O):</b> elige uno o varios archivos con el di&aacute;logo est&aacute;ndar de Windows.</li>
<li><b>Archivo &rarr; Abrir URL (Ctrl+U):</b> reproduce una transmisi&oacute;n de red (HTTP/HTTPS, HLS, DASH, RTSP, RTMP, MMS&hellip;).</li>
<li><b>Archivo &rarr; Abrir YouTube (Ctrl+Y):</b> pega cualquier enlace de YouTube. Se admiten tanto los
<b>v&iacute;deos grabados</b> como las <b>transmisiones en directo</b>, con selecci&oacute;n de calidad y subt&iacute;tulos opcionales.</li>
<li>Tambi&eacute;n puedes abrir archivos con doble clic en el Explorador de Windows si las asociaciones est&aacute;n configuradas.</li>
</ul>

<h3>3. Reproducci&oacute;n</h3>
<ul>
<li><b>Espacio</b> reproducir / pausar &middot; <b>S</b> detener</li>
<li><b>Ctrl+Derecha</b> o <b>N</b> pista siguiente &middot; <b>Ctrl+Izquierda</b> o <b>P</b> pista anterior</li>
<li><b>Derecha</b> / <b>Izquierda</b> avanzar/retroceder el intervalo actual &middot; <b>Shift+Derecha</b> / <b>Shift+Izquierda</b> avanzar/retroceder 60&nbsp;segundos</li>
<li><b>Q</b> m&aacute;s r&aacute;pido &middot; <b>A</b> m&aacute;s lento &middot; <b>\\</b> velocidad normal</li>
</ul>

<h3>4. Volumen y audio</h3>
<p><b>+</b> / <b>-</b> subir o bajar el volumen, <b>M</b> silenciar. El men&uacute; Audio permite elegir la pista,
ajustar el retardo de audio y abrir el ecualizador.</p>

<h3>5. Subt&iacute;tulos</h3>
<p>Los subt&iacute;tulos se detectan autom&aacute;ticamente cuando hay un archivo <i>.srt/.ass/.ssa/.vtt</i> junto al v&iacute;deo.
El men&uacute; <b>Subt&iacute;tulos</b> abre las opciones, la exportaci&oacute;n, el ajuste de retardo y la carga manual.
Formatos de exportaci&oacute;n: <b>TXT</b>, <b>DOCX</b>, <b>PDF</b>.</p>

<h3>6. Lista de reproducci&oacute;n</h3>
<p><b>Archivo &rarr; Lista de reproducci&oacute;n (Ctrl+L)</b>. A&ntilde;ade, reordena y ordena elementos, y guarda/carga listas M3U.
Repetir y aleatorio est&aacute;n en el panel de control. Cuando un archivo termina, el siguiente se reproduce autom&aacute;ticamente.</p>

<h3>7. Marcadores</h3>
<p>A&ntilde;ade un marcador en la posici&oacute;n actual con <b>Ctrl+Shift+B</b> y vuelve a &eacute;l desde el men&uacute;
<b>Marcadores</b>.</p>

<h3>8. V&iacute;deo</h3>
<p>Relaci&oacute;n de aspecto, recorte, zoom, capturas y pantalla completa (<b>F</b>).</p>

<h3>9. Apariencia</h3>
<p>El men&uacute; <b>Ver</b> ofrece tema oscuro, tema claro y modo de alto contraste.</p>

<h3>10. Configuraci&oacute;n (Ctrl+P)</h3>
<p>Idioma, tema, aceleraci&oacute;n por hardware, b&uacute;fer de red, intervalo de avance predeterminado, ecualizador y opciones de accesibilidad.</p>

<h3>11. Accesibilidad</h3>
<p>Anuncios para lectores de pantalla, navegaci&oacute;n avanzada por teclado, alto contraste y una lista completa de atajos
(<b>Ayuda &rarr; Atajos de teclado</b>). Pulsa <b>Ctrl+B</b> para anunciar el tiempo transcurrido, total y restante.</p>

<h3>12. Formatos compatibles</h3>
<p>MP4, AVI, MKV, MOV, MP3, WAV, FLAC, OGG, M4A, WMA, WebM, TS, WMV, MPG, VOB, OGV y muchos m&aacute;s &mdash; adem&aacute;s de transmisiones de red.</p>

<p>Creado con Python, PySide6 y VLC.</p>
""",

    "pt": """
<h2>{APP_NAME}</h2>
<p><b>Vers&atilde;o 1.0</b> &mdash; um reprodutor de m&iacute;dia profissional com suporte completo de acessibilidade.</p>

<h3>1. Primeiros passos</h3>
<p>Ao iniciar, o reprodutor abre sem carregar nenhum arquivo, portanto nunca se reassocia a uma sess&atilde;o
anterior. Voc&ecirc; pode optar por reabrir o &uacute;ltimo arquivo, a &uacute;ltima playlist ou retomar a
&uacute;ltima posi&ccedil;&atilde;o em <b>Configura&ccedil;&otilde;es &rarr; Ao iniciar</b>. Tudo pode ser controlado
pela barra de menus no topo ou pelos atalhos de teclado abaixo.</p>

<h3>2. Abrir m&iacute;dia</h3>
<ul>
<li><b>Arquivo &rarr; Abrir arquivo (Ctrl+O):</b> escolha um ou mais arquivos com a janela padr&atilde;o do Windows.</li>
<li><b>Arquivo &rarr; Abrir URL (Ctrl+U):</b> reproduza um fluxo de rede (HTTP/HTTPS, HLS, DASH, RTSP, RTMP, MMS&hellip;).</li>
<li><b>Arquivo &rarr; Abrir YouTube (Ctrl+Y):</b> cole qualquer link do YouTube. S&atilde;o suportados tanto
<b>v&iacute;deos gravados</b> quanto <b>transmiss&otilde;es ao vivo</b>, com escolha de qualidade e legendas opcionais.</li>
<li>Voc&ecirc; tamb&eacute;m pode abrir arquivos com um duplo clique no Explorador de Arquivos do Windows, se as associa&ccedil;&otilde;es estiverem configuradas.</li>
</ul>

<h3>3. Reprodu&ccedil;&atilde;o</h3>
<ul>
<li><b>Espa&ccedil;o</b> reproduzir / pausar &middot; <b>S</b> parar</li>
<li><b>Ctrl+Direita</b> ou <b>N</b> faixa seguinte &middot; <b>Ctrl+Esquerda</b> ou <b>P</b> faixa anterior</li>
<li><b>Direita</b> / <b>Esquerda</b> avan&ccedil;ar/retroceder o intervalo atual &middot; <b>Shift+Direita</b> / <b>Shift+Esquerda</b> avan&ccedil;ar/retroceder 60&nbsp;segundos</li>
<li><b>Q</b> mais r&aacute;pido &middot; <b>A</b> mais lento &middot; <b>\\</b> velocidade normal</li>
</ul>

<h3>4. Volume e &aacute;udio</h3>
<p><b>+</b> / <b>-</b> aumentar ou diminuir o volume, <b>M</b> silenciar. O menu &Aacute;udio permite escolher a faixa,
ajustar o atraso de &aacute;udio e abrir o equalizador.</p>

<h3>5. Legendas</h3>
<p>As legendas s&atilde;o detectadas automaticamente quando h&aacute; um arquivo <i>.srt/.ass/.ssa/.vtt</i> junto do v&iacute;deo.
O menu <b>Legendas</b> abre as op&ccedil;&otilde;es, a exporta&ccedil;&atilde;o, o ajuste de atraso e o carregamento manual.
Formatos de exporta&ccedil;&atilde;o: <b>TXT</b>, <b>DOCX</b>, <b>PDF</b>.</p>

<h3>6. Lista de reprodu&ccedil;&atilde;o</h3>
<p><b>Arquivo &rarr; Lista de reprodu&ccedil;&atilde;o (Ctrl+L)</b>. Adicione, reordene e classifique itens e salve/carregue listas M3U.
Repetir e aleat&oacute;rio ficam no painel de controle. Ao terminar um arquivo, o pr&oacute;ximo &eacute; reproduzido automaticamente.</p>

<h3>7. Favoritos</h3>
<p>Adicione um favorito na posi&ccedil;&atilde;o atual com <b>Ctrl+Shift+B</b> e volte a ele depois pelo menu
<b>Favoritos</b>.</p>

<h3>8. V&iacute;deo</h3>
<p>Propor&ccedil;&atilde;o, corte, zoom, capturas de tela e tela cheia (<b>F</b>).</p>

<h3>9. Apar&ecirc;ncia</h3>
<p>O menu <b>Exibir</b> oferece tema escuro, tema claro e modo de alto contraste.</p>

<h3>10. Configura&ccedil;&otilde;es (Ctrl+P)</h3>
<p>Idioma, tema, acelera&ccedil;&atilde;o de hardware, buffer de rede, intervalo padr&atilde;o de avan&ccedil;o, equalizador e op&ccedil;&otilde;es de acessibilidade.</p>

<h3>11. Acessibilidade</h3>
<p>An&uacute;ncios para leitores de tela, navega&ccedil;&atilde;o avan&ccedil;ada por teclado, alto contraste e uma lista completa de atalhos
(<b>Ajuda &rarr; Atalhos de teclado</b>). Pressione <b>Ctrl+B</b> para anunciar o tempo decorrido, total e restante.</p>

<h3>12. Formatos suportados</h3>
<p>MP4, AVI, MKV, MOV, MP3, WAV, FLAC, OGG, M4A, WMA, WebM, TS, WMV, MPG, VOB, OGV e muitos outros &mdash; al&eacute;m de fluxos de rede.</p>

<p>Feito com Python, PySide6 e VLC.</p>
""",

    "tr": """
<h2>{APP_NAME}</h2>
<p><b>S&uuml;r&uuml;m 1.0</b> &mdash; tam eri&scedil;ilebilirlik deste&scedil;ine sahip profesyonel bir medya oynatıcı.</p>

<h3>1. Başlarken</h3>
<p>Oynatıcı a&ccedil;ıldığında hi&ccedil;bir dosya y&uuml;klenmez, bu nedenle &ouml;nceki oturuma asla otomatik
olarak bağlanmaz. <b>Ayarlar &rarr; Başlangı&ccedil;ta</b> b&ouml;l&uuml;m&uuml;nden son dosyayı, son &ccedil;alma
listesini yeniden a&ccedil;mayı veya son konumu s&uuml;rd&uuml;rmeyi se&ccedil;ebilirsiniz. Her şey &uuml;stteki
men&uuml; &ccedil;ubuğundan veya aşağıdaki klavye kısayollarıyla kontrol edilir.</p>

<h3>2. Medya a&ccedil;ma</h3>
<ul>
<li><b>Dosya &rarr; Dosya A&ccedil; (Ctrl+O):</b> standart Windows penceresiyle bir veya daha fazla medya dosyası se&ccedil;in.</li>
<li><b>Dosya &rarr; URL A&ccedil; (Ctrl+U):</b> bir ağ akışını oynatın (HTTP/HTTPS, HLS, DASH, RTSP, RTMP, MMS&hellip;).</li>
<li><b>Dosya &rarr; YouTube A&ccedil; (Ctrl+Y):</b> herhangi bir YouTube bağlantısı yapıştırın. Hem
<b>kayıtlı videolar</b> hem de <b>canlı yayınlar</b> desteklenir; kalite ve isteğe bağlı altyazı se&ccedil;ilebilir.</li>
<li>Dosya ilişkilendirmeleri ayarlıysa Windows Gezgini'nde &ccedil;ift tıklayarak da a&ccedil;abilirsiniz.</li>
</ul>

<h3>3. Oynatma</h3>
<ul>
<li><b>Boşluk</b> oynat / duraklat &middot; <b>S</b> durdur</li>
<li><b>Ctrl+Sağ</b> veya <b>N</b> sonraki par&ccedil;a &middot; <b>Ctrl+Sol</b> veya <b>P</b> &ouml;nceki par&ccedil;a</li>
<li><b>Sağ</b> / <b>Sol</b> ge&ccedil;erli atlama aralığı kadar ileri/geri &middot; <b>Shift+Sağ</b> / <b>Shift+Sol</b> 60&nbsp;saniye ileri/geri</li>
<li><b>Q</b> daha hızlı &middot; <b>A</b> daha yavaş &middot; <b>\\</b> normal hız</li>
</ul>

<h3>4. Ses ve ses d&uuml;zeyi</h3>
<p><b>+</b> / <b>-</b> sesi a&ccedil;ar veya kısar, <b>M</b> sesi kapatır. Ses men&uuml;s&uuml; par&ccedil;a se&ccedil;meyi,
ses gecikmesini ayarlamayı ve ekolayzeri a&ccedil;mayı sağlar.</p>

<h3>5. Altyazılar</h3>
<p>Videonun yanında eşleşen bir <i>.srt/.ass/.ssa/.vtt</i> dosyası varsa altyazılar otomatik algılanır.
<b>Altyazılar</b> men&uuml;s&uuml; se&ccedil;enekleri, dışa aktarmayı, gecikme ayarını ve elle y&uuml;klemeyi a&ccedil;ar.
Dışa aktarma bi&ccedil;imleri: <b>TXT</b>, <b>DOCX</b>, <b>PDF</b>.</p>

<h3>6. &Ccedil;alma listesi</h3>
<p><b>Dosya &rarr; &Ccedil;alma Listesi (Ctrl+L)</b>. &Ouml;ğe ekleyin, yeniden sıralayın ve sıralayın; M3U listelerini kaydedin/y&uuml;kleyin.
Tekrar ve karıştırma kontrol panelindedir. Bir dosya bittiğinde sıradaki otomatik oynatılır.</p>

<h3>7. Yer imleri</h3>
<p>Ge&ccedil;erli konuma <b>Ctrl+Shift+B</b> ile yer imi ekleyin, sonra <b>Yer İmleri</b> men&uuml;s&uuml;nden geri d&ouml;n&uuml;n.</p>

<h3>8. Video</h3>
<p>En-boy oranı, kırpma, yakınlaştırma, ekran g&ouml;r&uuml;nt&uuml;s&uuml; ve tam ekran (<b>F</b>).</p>

<h3>9. G&ouml;r&uuml;n&uuml;m</h3>
<p><b>G&ouml;r&uuml;n&uuml;m</b> men&uuml;s&uuml; koyu tema, a&ccedil;ık tema ve y&uuml;ksek kontrast modu sunar.</p>

<h3>10. Ayarlar (Ctrl+P)</h3>
<p>Dil, tema, donanım hızlandırma, ağ arabelleği, varsayılan atlama aralığı, ekolayzer ve erişilebilirlik se&ccedil;enekleri.</p>

<h3>11. Erişilebilirlik</h3>
<p>Ekran okuyucu bildirimleri, gelişmiş klavye gezinmesi, y&uuml;ksek kontrast ve tam kısayol listesi
(<b>Yardım &rarr; Klavye Kısayolları</b>). Ge&ccedil;en, toplam ve kalan s&uuml;reyi duyurmak i&ccedil;in <b>Ctrl+B</b>'ye basın.</p>

<h3>12. Desteklenen bi&ccedil;imler</h3>
<p>MP4, AVI, MKV, MOV, MP3, WAV, FLAC, OGG, M4A, WMA, WebM, TS, WMV, MPG, VOB, OGV ve daha fazlası &mdash; ayrıca ağ akışları.</p>

<p>Python, PySide6 ve VLC ile geliştirilmiştir.</p>
""",
}


# Right-to-left languages need RTL layout in the dialog.
RTL_LANGUAGES = {"ar"}

# Contact / support details (CONTACT_NUMBER and CONTACT_NUMBER_DISPLAY) come
# from core.app_meta, the single source of truth, and are re-exported here so
# the About dialog can import them from this module.

# Localized credits block (application name, developer, contact).
CREDITS = {
    "ar": (
        "هذا التطبيق من تطوير: محمد مسعد",
        "للاقتراحات والدعم الفني (واتساب / تليجرام):",
    ),
    "en": (
        "This application is developed by: Mohamed Mosad",
        "For suggestions and technical support (WhatsApp / Telegram):",
    ),
    "it": (
        "Questa applicazione &egrave; sviluppata da: Mohamed Mosad",
        "Per suggerimenti e supporto tecnico (WhatsApp / Telegram):",
    ),
    "es": (
        "Esta aplicaci&oacute;n ha sido desarrollada por: Mohamed Mosad",
        "Para sugerencias y soporte t&eacute;cnico (WhatsApp / Telegram):",
    ),
    "pt": (
        "Este aplicativo foi desenvolvido por: Mohamed Mosad",
        "Para sugest&otilde;es e suporte t&eacute;cnico (WhatsApp / Telegram):",
    ),
    "tr": (
        "Bu uygulama &scedil;u ki&scedil;i tarafından geliştirilmiştir: Mohamed Mosad",
        "&Ouml;neriler ve teknik destek i&ccedil;in (WhatsApp / Telegram):",
    ),
}


def get_credits_html(language_code: str) -> str:
    """Return the localized credits/contact header for the About dialog."""
    developed_by, contact_label = CREDITS.get(language_code, CREDITS["en"])
    return (
        "<div style='text-align:center'>"
        f"<h1 style='margin-bottom:2px'>{APP_NAME}</h1>"
        f"<p style='margin:2px 0'><b>{developed_by}</b></p>"
        f"<p style='margin:2px 0'>{contact_label} "
        f"<b dir='ltr'>{CONTACT_NUMBER_DISPLAY}</b></p>"
        "<hr>"
        "</div>"
    )


def get_about_text(language_code: str) -> str:
    """Return the localized About document for a language code."""
    body = ABOUT_TEXT.get(language_code, ABOUT_TEXT["en"])
    # The document templates use ``{APP_NAME}`` so the product name is always
    # the same, untranslated brand in every language.
    body = body.replace("{APP_NAME}", APP_NAME)
    return get_credits_html(language_code) + body
