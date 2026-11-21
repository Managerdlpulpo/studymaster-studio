import re
P='/workspace/app-apuntes/tools/'
h=open(P+'original.html').read()
def rep(old,new,count=1):
    global h
    n=h.count(old)
    assert n==count, (n, old[:120])
    h=h.replace(old,new)

# ---------- HEAD ----------
rep('<title>StudyMaster Studio - Tu Entorno de Estudio Adaptativo</title>',
    '<meta name="referrer" content="no-referrer">\n    <title>StudyMaster Studio - Tu Entorno de Estudio Adaptativo</title>')
rep('''    <!-- FontAwesome CDN para iconos -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <!-- Google Font Inter -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">''',
'''    <!-- FontAwesome CDN para iconos (versión fijada + integridad SRI) -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" integrity="sha384-iw3OoTErCYJJB9mCa8LNS2hbsQ7M3C0EpIsO/H5+EGAkPGc6rk+V8i04oW/K5xq0" crossorigin="anonymous" referrerpolicy="no-referrer">
    <!-- REVISIÓN: se elimina Google Fonts (transfiere la IP del alumno a Google; problema RGPD). Se usa la fuente del sistema. -->''')
rep("""                        sans: ['Inter', 'sans-serif'],""",
    """                        sans: ['system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],""")
rep("""                        bio: {
                            50: '#f0fdf4',
                            100: '#dcfce7',
                            200: '#bbf7d0',
                            500: '#22c55e',
                            600: '#16a34a',
                            700: '#15803d',
                            800: '#166534',
                            900: '#14532d',
                        },
                        science: {
                            50: '#eff6ff',
                            100: '#dbeafe',
                            200: '#bfdbfe',
                            500: '#3b82f6',
                            600: '#2563eb',
                            700: '#1d4ed8',
                        }""",
"""                        // REVISIÓN: paletas completas (antes faltaban 300, 400, 950 en bio y 300, 800, 900 en science,
                        // por lo que varias clases no se aplicaban, p. ej. el reverso de las flashcards).
                        bio: {
                            50: '#f0fdf4', 100: '#dcfce7', 200: '#bbf7d0', 300: '#86efac', 400: '#4ade80',
                            500: '#22c55e', 600: '#16a34a', 700: '#15803d', 800: '#166534', 900: '#14532d', 950: '#052e16',
                        },
                        science: {
                            50: '#eff6ff', 100: '#dbeafe', 200: '#bfdbfe', 300: '#93c5fd', 400: '#60a5fa',
                            500: '#3b82f6', 600: '#2563eb', 700: '#1d4ed8', 800: '#1e40af', 900: '#1e3a8a', 950: '#172554',
                        }""")
rep("""            font-family: 'Inter', sans-serif;""", """            font-family: system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;""")

# ---------- NAV: tabs a11y + new tabs ----------
rep('id="nav-tabs">', 'id="nav-tabs" role="tablist" aria-label="Secciones de estudio">')
h=re.sub(r'<button type="button" onclick="switchTab\(\'(\w+)\'\)" id="tab-btn-\1"', lambda m: f'<button type="button" role="tab" aria-controls="tab-{m.group(1)}" onclick="switchTab(\'{m.group(1)}\')" id="tab-btn-{m.group(1)}"', h)
rep("""                    <i class="fa-solid fa-pen-to-square text-emerald-400"></i> 📝 Simulacro Nivel 10
                </button>""",
"""                    <i class="fa-solid fa-pen-to-square text-emerald-400"></i> 📝 Simulacro Nivel 10
                </button>
                <button type="button" role="tab" aria-controls="tab-progreso" onclick="switchTab('progreso')" id="tab-btn-progreso" class="tab-btn px-4 py-2 rounded-xl text-sm font-semibold transition-all whitespace-nowrap flex items-center gap-2 text-slate-200 hover:bg-white/5">
                    <i class="fa-solid fa-chart-line text-sky-300"></i> 📈 Mi Progreso
                </button>
                <button type="button" role="tab" aria-controls="tab-profesor" onclick="switchTab('profesor')" id="tab-btn-profesor" class="tab-btn px-4 py-2 rounded-xl text-sm font-semibold transition-all whitespace-nowrap flex items-center gap-2 text-slate-200 hover:bg-white/5">
                    <i class="fa-solid fa-chalkboard-user text-orange-300"></i> 👩‍🏫 Profesor
                </button>""")
rep('<div id="toast-banner" class="', '<div id="toast-banner" role="status" aria-live="polite" class="')

# ---------- Upload ----------
rep('''<input type="file" id="file-upload-input" accept=".txt,.md,.csv,.json" class="hidden" onchange="handleFileUpload(event)" />''',
    '''<input type="file" id="file-upload-input" multiple accept=".txt,.md,.csv,.json,.pdf,.docx,image/*,application/pdf" class="hidden" onchange="handleFileUpload(event)" />''')
rep('''<i class="fa-solid fa-upload text-slate-600"></i> Subir archivo (.txt, .md, .csv, .json)''',
    '''<i class="fa-solid fa-upload text-slate-600"></i> Subir apuntes (PDF, Word, foto, .txt, .md, .json)''')
rep('''                    <!-- Barra de Acciones Principales -->''',
'''                    <!-- Estado de extracción de archivos (PDF / Word / OCR) -->
                    <div id="extract-status" class="hidden p-3 rounded-xl bg-science-50 border border-science-200 text-xs text-science-900 flex items-center gap-2" role="status" aria-live="polite">
                        <i class="fa-solid fa-spinner fa-spin text-science-600"></i>
                        <span id="extract-status-text">Procesando archivo…</span>
                    </div>
                    <p class="text-[11px] text-slate-500 flex items-start gap-1.5">
                        <i class="fa-solid fa-shield-halved text-bio-600 mt-0.5"></i>
                        <span>Privacidad: tus apuntes se procesan <strong>en este navegador</strong> (también los PDF y las fotos, mediante OCR local). No se envían a ningún servidor ni a ninguna IA. Solo se descargan las librerías necesarias desde CDN públicos.</span>
                    </p>

                    <!-- Barra de Acciones Principales -->''')

# ---------- Flashcard a11y + leitner info ----------
rep('''<div class="max-w-lg mx-auto perspective cursor-pointer" onclick="flipCard()">''',
    '''<div class="max-w-lg mx-auto perspective cursor-pointer" onclick="flipCard()" role="button" tabindex="0" aria-label="Tarjeta: pulsa Intro o Espacio para darle la vuelta" onkeydown="if(event.key==='Enter'||event.key===' '){event.preventDefault();flipCard();}">''')
rep('''                        <span class="text-slate-400 font-normal ml-2">(Tarjeta <span id="fc-position-num">1</span>)</span>''',
    '''                        <span class="text-slate-400 font-normal ml-2">(Tarjeta <span id="fc-position-num">1</span>)</span>
                        <span class="ml-2 text-amber-600" title="Repetición espaciada (sistema Leitner): tarjetas cuyo repaso toca hoy">· Para repasar hoy: <span id="fc-due-count">0</span></span>''')
rep('''                            <div class="text-center text-xs text-slate-400 font-medium">
                                <i class="fa-solid fa-rotate text-amber-500"></i> Haz clic para ver la respuesta
                            </div>''',
    '''                            <div class="text-center text-xs text-slate-400 font-medium space-y-1">
                                <div><i class="fa-solid fa-rotate text-amber-500"></i> Haz clic para ver la respuesta</div>
                                <div id="fc-box-info" class="text-[10px] text-slate-400"></div>
                            </div>''')
rep('''<button type="button" onclick="nextCard()" class="bg-slate-200 hover:bg-slate-300 text-slate-700 p-3 rounded-xl text-xs transition-colors" title="Saltar tarjeta">''',
    '''<button type="button" onclick="nextCard()" class="bg-slate-200 hover:bg-slate-300 text-slate-700 p-3 rounded-xl text-xs transition-colors" title="Saltar tarjeta" aria-label="Saltar tarjeta">''')

open(P+'stage1.html','w').write(h)
print('ok stage1')
