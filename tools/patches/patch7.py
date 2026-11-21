P='/workspace/app-apuntes/tools/'
h=open(P+'stage6.html').read()
def rep(old,new,count=1):
    global h
    n=h.count(old); assert n==count,(n,old[:160]); h=h.replace(old,new)

NEWFUNCS = r'''
        // =========================================================
        // 13. (NUEVO) MI PROGRESO
        // =========================================================
        function computeProgressStats() {
            const s = studyState;
            const fullAttempts = examHistory.filter(a => !a.retry);
            const blocks = s.blocks.map(b => {
                const cs = s.concepts.filter(c => c.blockId === b.id);
                const ds = s.definitions.filter(d => d.blockId === b.id);
                const os = s.openQuestions.filter(q => q.blockId === b.id);
                let exC = 0, exT = 0;
                fullAttempts.forEach(a => {
                    const bb = a.byBlock && a.byBlock[b.title];
                    if (bb) { exC += Number(bb.c) || 0; exT += Number(bb.t) || 0; }
                });
                return {
                    title: b.title,
                    cards: cs.length, mastered: cs.filter(c => masteredCards.includes(c.id)).length,
                    defs: ds.length, defsDone: ds.filter(d => completedDefs.includes(d.id)).length,
                    open: os.length, openDone: os.filter(q => completedOpen.includes(q.id)).length,
                    examCorrect: exC, examTotal: exT
                };
            });
            return {
                cards: s.concepts.length, mastered: masteredCards.length,
                defs: s.definitions.length, defsDone: completedDefs.length,
                open: s.openQuestions.length, openDone: completedOpen.length, openSelfValidated: selfValidatedOpen.length,
                examAttempts: fullAttempts.length,
                bestScore: fullAttempts.length ? Math.max(...fullAttempts.map(a => a.score)) : null,
                lastScore: fullAttempts.length ? fullAttempts[fullAttempts.length - 1].score : null,
                blocks
            };
        }

        function pct(a, b) { return b > 0 ? Math.round((a / b) * 100) : 0; }

        function progressBar(value, colorClass) {
            return `<div class="h-2 bg-slate-100 rounded-full overflow-hidden"><div class="h-full ${colorClass}" style="width:${Math.max(0, Math.min(100, value))}%"></div></div>`;
        }

        function renderProgress() {
            if (!studyState.hasContent) return;
            const st = computeProgressStats();
            document.getElementById('progress-deck-title').innerText = studyState.subjectTitle;
            const aliasInput = document.getElementById('student-alias-input');
            if (aliasInput && !aliasInput.value) aliasInput.value = safeGetItem('sm_student_alias', '');

            const card = (icon, label, value, sub) => `
                <div class="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm space-y-1">
                    <div class="text-[11px] font-bold text-slate-500 uppercase tracking-wider">${icon} ${label}</div>
                    <div class="text-2xl font-extrabold text-slate-800">${value}</div>
                    <div class="text-[11px] text-slate-500">${sub}</div>
                </div>`;
            document.getElementById('progress-summary-cards').innerHTML =
                card('🗂️', 'Tarjetas', `${st.mastered}/${st.cards}`, `${pct(st.mastered, st.cards)}% dominadas`) +
                card('✍️', 'Definiciones', `${st.defsDone}/${st.defs}`, `${pct(st.defsDone, st.defs)}% completadas`) +
                card('⌨️', 'Preguntas abiertas', `${st.openDone}/${st.open}`, `${st.openSelfValidated} autovalidadas por ti`) +
                card('📝', 'Simulacros', st.examAttempts, st.examAttempts ? `Mejor ${st.bestScore.toFixed(1)} · Última ${st.lastScore.toFixed(1)}` : 'Aún no has hecho ninguno');

            const blocksEl = document.getElementById('progress-blocks-table');
            blocksEl.innerHTML = st.blocks.map(b => `
                <div class="space-y-1.5 p-3 rounded-xl bg-slate-50 border border-slate-100">
                    <div class="font-bold text-slate-800">${escapeHtml(b.title)}</div>
                    <div class="grid grid-cols-3 gap-3 text-[11px] text-slate-500">
                        <div>Tarjetas ${pct(b.mastered, b.cards)}%${progressBar(pct(b.mastered, b.cards), 'bg-amber-400')}</div>
                        <div>Huecos ${pct(b.defsDone, b.defs)}%${progressBar(pct(b.defsDone, b.defs), 'bg-cyan-500')}</div>
                        <div>Examen ${b.examTotal ? pct(b.examCorrect, b.examTotal) + '%' : '—'}${progressBar(pct(b.examCorrect, b.examTotal), 'bg-emerald-500')}</div>
                    </div>
                </div>`).join('') || '<p class="text-slate-400">Sin bloques.</p>';

            const histEl = document.getElementById('progress-exam-history');
            const hist = examHistory.slice(-10).reverse();
            histEl.innerHTML = hist.length ? hist.map(a => `
                <div class="flex items-center gap-3">
                    <span class="w-28 text-slate-500">${escapeHtml(new Date(a.date).toLocaleString('es-ES', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }))}</span>
                    <div class="flex-1">${progressBar(a.score * 10, a.score >= 5 ? 'bg-emerald-500' : 'bg-red-400')}</div>
                    <span class="w-24 text-right font-bold ${a.score >= 5 ? 'text-emerald-700' : 'text-red-600'}">${Number(a.score).toFixed(1)}${a.retry ? ' <span class="font-normal text-slate-400">(repaso)</span>' : ''}</span>
                </div>`).join('') : '<p class="text-slate-400">Aún no has hecho ningún simulacro.</p>';

            const weak = new Set();
            studyState.concepts.forEach(c => { const s = leitnerState[c.id]; if (s && s.box === 1) weak.add(c.term); });
            const lastFull = examHistory.filter(a => !a.retry).slice(-1)[0];
            if (lastFull && Array.isArray(lastFull.wrong)) lastFull.wrong.forEach(t => weak.add(t));
            const weakEl = document.getElementById('progress-weak-list');
            weakEl.innerHTML = weak.size
                ? Array.from(weak).slice(0, 30).map(t => `<span class="px-2.5 py-1 rounded-lg bg-amber-50 border border-amber-200 text-amber-900 font-semibold">${escapeHtml(t)}</span>`).join('')
                : '<span class="text-slate-400">¡Nada pendiente! Las tarjetas que marques como «Repasar luego» y los fallos del último examen aparecerán aquí.</span>';
        }

        function saveStudentAlias() {
            const v = (document.getElementById('student-alias-input').value || '').slice(0, 40);
            safeSetItem('sm_student_alias', v);
        }

        function slugify(str) {
            return normalizeText(str).replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '').slice(0, 40) || 'x';
        }

        function downloadProgressReport() {
            if (!studyState.hasContent) {
                showToast('Primero carga unos apuntes y practica un poco.', true);
                return;
            }
            const aliasInput = document.getElementById('student-alias-input');
            const alias = (aliasInput.value || '').trim();
            if (!alias) {
                showToast('Escribe tu nombre o código de alumno antes de descargar el informe.', true);
                aliasInput.focus();
                return;
            }
            const report = {
                type: 'studymaster-progress-report',
                version: 1,
                generatedAt: new Date().toISOString(),
                student: alias,
                deckTitle: studyState.subjectTitle,
                deckId: studyState.deckId,
                xp: userXP,
                stats: computeProgressStats(),
                examHistory: examHistory.map(a => ({ date: a.date, score: a.score, correct: a.correct, total: a.total, retry: !!a.retry, byBlock: a.byBlock || {} }))
            };
            downloadFile(`informe_${slugify(alias)}_${slugify(studyState.subjectTitle)}.json`, JSON.stringify(report, null, 2), 'application/json');
            showToast('Informe descargado. Entrégaselo a tu profesor.');
        }

        // =========================================================
        // 14. (NUEVO) VISTA PROFESOR: agrega informes sin servidor
        // =========================================================
        let teacherReports = [];

        function sanitizeReport(r) {
            if (!r || r.type !== 'studymaster-progress-report' || !r.stats) return null;
            const S = (v, max = 200) => String(v == null ? '' : v).slice(0, max);
            const N = v => { const n = Number(v); return Number.isFinite(n) ? n : 0; };
            const st = r.stats;
            return {
                student: S(r.student, 60) || 'Sin nombre',
                deckTitle: S(r.deckTitle),
                deckId: S(r.deckId, 40),
                generatedAt: S(r.generatedAt, 40),
                cards: N(st.cards), mastered: N(st.mastered), defs: N(st.defs), defsDone: N(st.defsDone),
                open: N(st.open), openDone: N(st.openDone), openSelfValidated: N(st.openSelfValidated),
                examAttempts: N(st.examAttempts),
                bestScore: st.bestScore == null ? null : N(st.bestScore),
                lastScore: st.lastScore == null ? null : N(st.lastScore),
                blocks: (Array.isArray(st.blocks) ? st.blocks : []).slice(0, 100).map(b => ({
                    title: S(b && b.title), examCorrect: N(b && b.examCorrect), examTotal: N(b && b.examTotal)
                }))
            };
        }

        async function handleTeacherReports(event) {
            const files = Array.from(event.target.files || []);
            event.target.value = '';
            let added = 0, rejected = 0;
            for (const f of files) {
                try {
                    const rep = sanitizeReport(JSON.parse(await readFileAs(f, 'text')));
                    if (!rep) { rejected++; continue; }
                    // Si llega un informe más reciente del mismo alumno y tema, sustituye al anterior
                    const idx = teacherReports.findIndex(t => t.student.toLowerCase() === rep.student.toLowerCase() && t.deckId === rep.deckId);
                    if (idx !== -1) {
                        if (rep.generatedAt >= teacherReports[idx].generatedAt) teacherReports[idx] = rep;
                    } else {
                        teacherReports.push(rep);
                    }
                    added++;
                } catch (e) {
                    rejected++;
                }
            }
            renderTeacherView();
            showToast(`${added} informe(s) cargados${rejected ? `, ${rejected} archivo(s) no válidos` : ''}.`, rejected > 0);
        }

        function fmtScore(v) { return v == null ? '—' : Number(v).toFixed(1); }

        function renderTeacherView() {
            const tableEl = document.getElementById('teacher-table-container');
            const blocksEl = document.getElementById('teacher-blocks-container');
            if (!tableEl) return;
            if (teacherReports.length === 0) {
                tableEl.innerHTML = 'Aún no has cargado informes.';
                blocksEl.innerHTML = '—';
                return;
            }
            const rows = [...teacherReports].sort((a, b) => a.deckTitle.localeCompare(b.deckTitle) || a.student.localeCompare(b.student));
            tableEl.innerHTML = `
                <table class="min-w-full text-left text-xs">
                    <thead class="text-slate-500 border-b border-slate-200">
                        <tr>
                            <th class="py-2 pr-3">Alumno</th><th class="py-2 pr-3">Tema</th><th class="py-2 pr-3">Informe</th>
                            <th class="py-2 pr-3">Tarjetas</th><th class="py-2 pr-3">Huecos</th><th class="py-2 pr-3">Abiertas (autoval.)</th>
                            <th class="py-2 pr-3">Simulacros</th><th class="py-2 pr-3">Mejor</th><th class="py-2 pr-3">Última</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${rows.map(r => `
                            <tr class="border-b border-slate-100">
                                <td class="py-2 pr-3 font-bold text-slate-800">${escapeHtml(r.student)}</td>
                                <td class="py-2 pr-3">${escapeHtml(r.deckTitle)}</td>
                                <td class="py-2 pr-3 text-slate-400">${escapeHtml(r.generatedAt ? new Date(r.generatedAt).toLocaleDateString('es-ES') : '')}</td>
                                <td class="py-2 pr-3">${r.mastered}/${r.cards} (${pct(r.mastered, r.cards)}%)</td>
                                <td class="py-2 pr-3">${r.defsDone}/${r.defs}</td>
                                <td class="py-2 pr-3">${r.openDone}/${r.open} (${r.openSelfValidated})</td>
                                <td class="py-2 pr-3">${r.examAttempts}</td>
                                <td class="py-2 pr-3 font-bold ${r.bestScore != null && r.bestScore < 5 ? 'text-red-600' : 'text-emerald-700'}">${fmtScore(r.bestScore)}</td>
                                <td class="py-2 pr-3">${fmtScore(r.lastScore)}</td>
                            </tr>`).join('')}
                    </tbody>
                </table>`;

            const agg = {};
            teacherReports.forEach(r => r.blocks.forEach(b => {
                if (!b.examTotal) return;
                const key = r.deckTitle + ' › ' + b.title;
                agg[key] = agg[key] || { c: 0, t: 0, students: 0 };
                agg[key].c += b.examCorrect;
                agg[key].t += b.examTotal;
                agg[key].students++;
            }));
            const list = Object.entries(agg).map(([k, v]) => ({ k, p: pct(v.c, v.t), n: v.students })).sort((a, b) => a.p - b.p);
            blocksEl.innerHTML = list.length ? list.map(x => `
                <div class="flex items-center gap-3 py-1">
                    <span class="flex-1 text-slate-700">${escapeHtml(x.k)} <span class="text-slate-400">(${x.n} alumno/s)</span></span>
                    <div class="w-40">${progressBar(x.p, x.p < 50 ? 'bg-red-400' : (x.p < 75 ? 'bg-amber-400' : 'bg-emerald-500'))}</div>
                    <span class="w-10 text-right font-bold">${x.p}%</span>
                </div>`).join('') : 'Los informes cargados aún no tienen simulacros realizados.';
        }

        function exportTeacherCSV() {
            if (teacherReports.length === 0) {
                showToast('Carga primero algunos informes.', true);
                return;
            }
            // Evita inyección de fórmulas al abrir el CSV en Excel/Calc
            const cell = v => {
                let s = String(v == null ? '' : v);
                if (/^[=+\-@\t\r]/.test(s)) s = "'" + s;
                return '"' + s.replace(/"/g, '""') + '"';
            };
            const header = ['Alumno', 'Tema', 'Fecha informe', 'Tarjetas dominadas', 'Tarjetas', 'Huecos completados', 'Huecos', 'Abiertas superadas', 'Abiertas autovalidadas', 'Abiertas', 'Simulacros', 'Mejor nota', 'Última nota'];
            const lines = [header.map(cell).join(';')].concat(teacherReports.map(r => [
                r.student, r.deckTitle, r.generatedAt, r.mastered, r.cards, r.defsDone, r.defs, r.openDone, r.openSelfValidated, r.open,
                r.examAttempts, fmtScore(r.bestScore).replace('.', ','), fmtScore(r.lastScore).replace('.', ',')
            ].map(cell).join(';')));
            downloadFile('progreso_clase.csv', '\ufeff' + lines.join('\r\n'), 'text/csv;charset=utf-8');
        }

        function clearTeacherReports() {
            teacherReports = [];
            renderTeacherView();
        }

        // =========================================================
        // 15. (NUEVO) BORRAR TODOS LOS DATOS DEL DISPOSITIVO (derecho de supresión)
        // =========================================================
        let wipeConfirmPending = false;
        function handleWipeAllData() {
            const btn = document.getElementById('wipe-data-btn');
            if (!wipeConfirmPending) {
                wipeConfirmPending = true;
                btn.innerText = '¿Seguro? Se borrarán apuntes, temarios guardados, progreso y XP. Pulsa de nuevo.';
                btn.classList.add('text-red-600', 'font-bold');
                setTimeout(() => {
                    wipeConfirmPending = false;
                    btn.innerText = 'Borrar todos mis datos de este dispositivo';
                    btn.classList.remove('text-red-600', 'font-bold');
                }, 4000);
                return;
            }
            try {
                Object.keys(localStorage).filter(k => k.startsWith('sm_')).forEach(k => localStorage.removeItem(k));
            } catch (e) { /* sin acceso */ }
            Object.keys(memoryStorage).forEach(k => delete memoryStorage[k]);
            location.reload();
        }

        // =========================================================
        // 16. INICIALIZACIÓN AL CARGAR LA PÁGINA
        // =========================================================
        window.addEventListener('DOMContentLoaded', () => {
            updateXP(0);
            renderSavedDecksList();
            // REVISIÓN: se recupera el último temario abierto (antes, al recargar se perdía todo)
            try {
                const saved = safeGetItem('sm_current_deck', null);
                const deck = saved ? sanitizeDeck(JSON.parse(saved)) : null;
                if (deck && deck.hasContent) {
                    document.getElementById('subject-title-input').value = deck.subjectTitle;
                    document.getElementById('notes-textarea').value = deck.rawText || '';
                    updateCharCount();
                    processNotesAndGenerate(deck, { silent: true });
                }
            } catch (e) {
                console.warn('No se pudo recuperar el último temario', e);
            }
            syncEmptyOrActiveStates();
        });
    </script>'''
start = h.index('''        // =========================================================
        // 13. INICIALIZACIÓN AL CARGAR LA PÁGINA (ESTADO LIMPIO)''')
end = h.index('    </script>', start) + len('    </script>')
h = h[:start] + NEWFUNCS.lstrip('\n') + h[end:]
open('/workspace/app-apuntes/index.html','w').write(h); print('ok index', len(h))
