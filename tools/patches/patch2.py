P='/workspace/app-apuntes/tools/'
h=open(P+'stage1.html').read()
def rep(old,new,count=1):
    global h
    n=h.count(old); assert n==count,(n,old[:120]); h=h.replace(old,new)

NEW_TABS = '''
        <!-- ================================================================= -->
        <!-- PESTAÑA 8 (NUEVA): MI PROGRESO                                     -->
        <!-- ================================================================= -->
        <section id="tab-progreso" class="tab-content hidden space-y-6" role="tabpanel">
            <div id="progreso-empty-state" class="bg-white p-8 sm:p-12 rounded-3xl border border-slate-200 shadow-sm text-center max-w-xl mx-auto space-y-4">
                <div class="w-16 h-16 bg-sky-100 text-sky-700 rounded-2xl flex items-center justify-center mx-auto text-2xl">
                    <i class="fa-solid fa-chart-line"></i>
                </div>
                <h2 class="text-xl font-extrabold text-slate-800">Todavía no hay progreso que mostrar</h2>
                <p class="text-xs sm:text-sm text-slate-500 leading-relaxed">Carga unos apuntes y practica: aquí verás tu dominio por tema, tus notas de examen y qué conviene repasar.</p>
                <button type="button" onclick="switchTab('cargar')" class="bg-bio-600 hover:bg-bio-700 text-white font-bold py-3 px-6 rounded-2xl text-xs sm:text-sm shadow-sm transition-all inline-flex items-center gap-2">
                    <i class="fa-solid fa-file-import"></i> Ir a 📥 Cargar Apuntes
                </button>
            </div>

            <div id="progreso-active-content" class="hidden space-y-6">
                <div class="bg-white p-5 rounded-2xl shadow-sm border border-slate-200 space-y-1">
                    <h2 class="text-xl font-extrabold text-slate-800 flex items-center gap-2"><i class="fa-solid fa-chart-line text-sky-600"></i> Mi progreso en <span id="progress-deck-title" class="text-bio-700"></span></h2>
                    <p class="text-xs text-slate-500">Se guarda automáticamente en este navegador. Si cambias de ordenador o borras los datos del navegador, se pierde (puedes descargar el informe).</p>
                </div>

                <div id="progress-summary-cards" class="grid grid-cols-2 lg:grid-cols-4 gap-4"></div>

                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div class="bg-white p-5 rounded-2xl shadow-sm border border-slate-200 space-y-3">
                        <h3 class="font-bold text-slate-800 text-sm flex items-center gap-2"><i class="fa-solid fa-layer-group text-bio-600"></i> Dominio por bloque / tema</h3>
                        <div id="progress-blocks-table" class="space-y-3 text-xs"></div>
                    </div>
                    <div class="bg-white p-5 rounded-2xl shadow-sm border border-slate-200 space-y-3">
                        <h3 class="font-bold text-slate-800 text-sm flex items-center gap-2"><i class="fa-solid fa-graduation-cap text-emerald-600"></i> Historial de simulacros</h3>
                        <div id="progress-exam-history" class="space-y-2 text-xs"></div>
                    </div>
                </div>

                <div class="bg-white p-5 rounded-2xl shadow-sm border border-slate-200 space-y-3">
                    <h3 class="font-bold text-slate-800 text-sm flex items-center gap-2"><i class="fa-solid fa-triangle-exclamation text-amber-500"></i> Conceptos que conviene repasar</h3>
                    <div id="progress-weak-list" class="flex flex-wrap gap-2 text-xs"></div>
                </div>

                <div class="bg-white p-5 rounded-2xl shadow-sm border border-slate-200 space-y-3">
                    <h3 class="font-bold text-slate-800 text-sm flex items-center gap-2"><i class="fa-solid fa-paper-plane text-science-600"></i> Enviar mi progreso al profesor</h3>
                    <p class="text-xs text-slate-500">Descarga un informe (archivo .json) y entrégaselo a tu profesor por el canal que use la clase (aula virtual, correo del centro…). <strong>El informe no incluye tus apuntes</strong>, solo las estadísticas. Usa tu nombre de pila, iniciales o el código que te dé el profesor; no hace falta tu nombre completo.</p>
                    <div class="flex flex-wrap items-center gap-2">
                        <input type="text" id="student-alias-input" maxlength="40" placeholder="Nombre o código de alumno (p. ej. 2ºB-07)" oninput="saveStudentAlias()" class="flex-1 min-w-[200px] px-3 py-2 text-xs font-semibold bg-slate-50 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-bio-500" />
                        <button type="button" onclick="downloadProgressReport()" class="bg-science-600 hover:bg-science-700 text-white font-bold px-4 py-2 rounded-xl text-xs shadow-sm flex items-center gap-1.5"><i class="fa-solid fa-download"></i> Descargar informe</button>
                    </div>
                </div>
            </div>
        </section>

        <!-- ================================================================= -->
        <!-- PESTAÑA 9 (NUEVA): VISTA PROFESOR (sin servidor)                   -->
        <!-- ================================================================= -->
        <section id="tab-profesor" class="tab-content hidden space-y-6" role="tabpanel">
            <div class="bg-white p-5 rounded-2xl shadow-sm border border-slate-200 space-y-3">
                <h2 class="text-xl font-extrabold text-slate-800 flex items-center gap-2"><i class="fa-solid fa-chalkboard-user text-orange-500"></i> Vista del profesor</h2>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs text-slate-600">
                    <div class="p-4 rounded-xl bg-orange-50 border border-orange-200 space-y-1.5">
                        <div class="font-bold text-orange-800">1. Preparar material para la clase</div>
                        <p>Pega tus apuntes en «Cargar Apuntes», genera, revisa con «🛠️ Revisar y Editar Ítems» y pulsa <strong>Exportar .JSON</strong>. Comparte ese archivo con tus alumnos: al subirlo tendrán exactamente las mismas tarjetas y preguntas que has revisado.</p>
                    </div>
                    <div class="p-4 rounded-xl bg-orange-50 border border-orange-200 space-y-1.5">
                        <div class="font-bold text-orange-800">2. Ver el progreso de la clase</div>
                        <p>Pide a cada alumno su informe (pestaña «Mi Progreso» → «Descargar informe») y cárgalos aquí todos a la vez. Los datos solo se muestran en tu navegador y no se guardan.</p>
                    </div>
                </div>
                <div class="flex flex-wrap items-center gap-2 pt-1">
                    <input type="file" id="teacher-reports-input" multiple accept=".json,application/json" class="hidden" onchange="handleTeacherReports(event)" />
                    <button type="button" onclick="document.getElementById('teacher-reports-input').click()" class="bg-orange-500 hover:bg-orange-600 text-white font-bold px-4 py-2.5 rounded-xl text-xs shadow-sm flex items-center gap-1.5"><i class="fa-solid fa-folder-open"></i> Cargar informes de alumnos</button>
                    <button type="button" onclick="exportTeacherCSV()" class="bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold px-4 py-2.5 rounded-xl text-xs border border-slate-200 flex items-center gap-1.5"><i class="fa-solid fa-file-csv"></i> Exportar tabla (.csv)</button>
                    <button type="button" onclick="clearTeacherReports()" class="text-xs font-semibold text-slate-500 hover:text-red-600 px-2">Vaciar</button>
                </div>
                <p class="text-[11px] text-amber-700 bg-amber-50 border border-amber-200 rounded-xl p-2.5"><i class="fa-solid fa-circle-info"></i> Aviso: sin servidor ni inicio de sesión, un informe podría editarse a mano. Úsalo como seguimiento formativo, no como nota oficial.</p>
            </div>
            <div class="bg-white p-5 rounded-2xl shadow-sm border border-slate-200 space-y-3 overflow-x-auto">
                <h3 class="font-bold text-slate-800 text-sm">Resumen por alumno</h3>
                <div id="teacher-table-container" class="text-xs text-slate-500">Aún no has cargado informes.</div>
            </div>
            <div class="bg-white p-5 rounded-2xl shadow-sm border border-slate-200 space-y-3">
                <h3 class="font-bold text-slate-800 text-sm">Bloques con más dificultad (media de la clase en simulacros)</h3>
                <div id="teacher-blocks-container" class="text-xs text-slate-500">—</div>
            </div>
        </section>

    </main>'''
rep('\n    </main>', NEW_TABS)

rep('''        <div class="max-w-7xl mx-auto px-4 text-center text-xs text-slate-400 font-medium">
            StudyMaster Studio • Generador Interactivo de Estudio 100% Adaptable a tus Apuntes
        </div>''',
'''        <div class="max-w-7xl mx-auto px-4 text-center text-xs text-slate-400 font-medium space-y-1.5">
            <div>StudyMaster Studio • Generador Interactivo de Estudio 100% Adaptable a tus Apuntes</div>
            <div>
                <i class="fa-solid fa-lock"></i> Tus apuntes y tu progreso se guardan solo en este navegador.
                <button type="button" id="wipe-data-btn" onclick="handleWipeAllData()" class="underline underline-offset-2 hover:text-red-600 ml-1">Borrar todos mis datos de este dispositivo</button>
            </div>
        </div>''')

# exam: per-attempt question count note & unanswered warning area
rep('''                        <span><i class="fa-solid fa-award text-purple-600"></i> Nota sobre 10</span>''',
    '''                        <span><i class="fa-solid fa-award text-purple-600"></i> Nota sobre 10</span>
                        <span><i class="fa-solid fa-shuffle text-amber-600"></i> Opciones barajadas en cada intento</span>''')
rep('''<div id="exam-results-screen" class="hidden max-w-3xl mx-auto space-y-6">''','''<div id="exam-results-screen" class="hidden max-w-3xl mx-auto space-y-6" aria-live="polite">''')
open(P+'stage2.html','w').write(h); print('ok stage2')
