P='/workspace/app-apuntes/tools/'
h=open(P+'stage2.html').read()
def rep(old,new,count=1):
    global h
    n=h.count(old); assert n==count,(n,old[:160]); h=h.replace(old,new)

# A. storage
rep('''        function safeSetItem(key, value) {
            try {
                localStorage.setItem(key, value);
            } catch (e) {
                memoryStorage[key] = value;
            }
        }''','''        // REVISIÓN: antes, si localStorage fallaba (memoria llena / modo privado) los datos se perdían sin avisar.
        let storageWarned = false;
        function safeSetItem(key, value) {
            try {
                localStorage.setItem(key, value);
                return true;
            } catch (e) {
                memoryStorage[key] = value;
                if (!storageWarned) {
                    storageWarned = true;
                    setTimeout(() => showToast('No se pudo guardar en este navegador (memoria llena o modo privado). Exporta tu temario para no perderlo.', true), 0);
                }
                return false;
            }
        }

        function safeRemoveItem(key) {
            try { localStorage.removeItem(key); } catch (e) { /* sin acceso */ }
            delete memoryStorage[key];
        }''')

# B. progress system after session arrays
rep('''        let masteredCards = [];
        let completedDefs = [];
        let completedOpen = [];
''','''        let masteredCards = [];
        let completedDefs = [];
        let completedOpen = [];

        // REVISIÓN: progreso persistente por temario + repetición espaciada + historial de exámenes
        let selfValidatedOpen = [];   // preguntas abiertas dadas por válidas por el propio alumno (se distinguen en informes)
        let leitnerState = {};        // conceptId -> { box: 1..5, due: timestamp }
        let examHistory = [];         // [{ date, score, correct, total, retry, byBlock: { [bloque]: { c, t } }, wrong: [conceptos] }]
        let seqGameDone = [];         // secuencias ya resueltas (evita sumar XP infinito)
        const LEITNER_DAYS = [0, 0, 1, 3, 7, 16]; // días hasta el siguiente repaso según la caja

        function hashString(str) {
            let h = 2166136261;
            for (let i = 0; i < str.length; i++) {
                h ^= str.charCodeAt(i);
                h = Math.imul(h, 16777619);
            }
            return (h >>> 0).toString(36);
        }

        function computeDeckId(state) {
            const base = state.rawText && state.rawText.trim()
                ? state.rawText
                : (state.concepts || []).map(c => c.term).join('|');
            return 'd_' + hashString((state.subjectTitle || '') + '\\n' + base);
        }

        function getAllProgress() {
            try {
                const parsed = JSON.parse(safeGetItem('sm_progress', '{}'));
                return parsed && typeof parsed === 'object' ? parsed : {};
            } catch (e) {
                return {};
            }
        }

        function persistProgress() {
            if (!studyState.hasContent || !studyState.deckId) return;
            const all = getAllProgress();
            all[studyState.deckId] = {
                subjectTitle: studyState.subjectTitle,
                updatedAt: new Date().toISOString(),
                masteredCards, completedDefs, completedOpen, selfValidatedOpen,
                leitnerState, seqGameDone,
                examHistory: examHistory.slice(-50)
            };
            safeSetItem('sm_progress', JSON.stringify(all));
        }

        function loadProgressForDeck(deckId) {
            const p = getAllProgress()[deckId] || {};
            const nums = v => Array.isArray(v) ? v.filter(x => typeof x === 'number' && isFinite(x)) : [];
            masteredCards = nums(p.masteredCards);
            completedDefs = nums(p.completedDefs);
            completedOpen = nums(p.completedOpen);
            selfValidatedOpen = nums(p.selfValidatedOpen);
            seqGameDone = nums(p.seqGameDone);
            leitnerState = (p.leitnerState && typeof p.leitnerState === 'object') ? p.leitnerState : {};
            examHistory = Array.isArray(p.examHistory) ? p.examHistory.filter(a => a && typeof a.score === 'number') : [];
            pruneProgressToExistingItems();
        }

        function pruneProgressToExistingItems() {
            const cIds = new Set(studyState.concepts.map(c => c.id));
            const dIds = new Set(studyState.definitions.map(d => d.id));
            const oIds = new Set(studyState.openQuestions.map(q => q.id));
            const sIds = new Set(studyState.sequences.map(s => s.id));
            masteredCards = masteredCards.filter(id => cIds.has(id));
            completedDefs = completedDefs.filter(id => dIds.has(id));
            completedOpen = completedOpen.filter(id => oIds.has(id));
            selfValidatedOpen = selfValidatedOpen.filter(id => oIds.has(id));
            seqGameDone = seqGameDone.filter(id => sIds.has(id));
            Object.keys(leitnerState).forEach(k => { if (!cIds.has(Number(k))) delete leitnerState[k]; });
        }

        function persistCurrentDeck() {
            if (studyState.hasContent) safeSetItem('sm_current_deck', JSON.stringify(studyState));
        }
''')

# C. reset stats
rep('''                streak = 0;
                document.getElementById('streak-count').innerText = '0 🔥';
                updateXP(0);''','''                selfValidatedOpen = [];
                leitnerState = {};
                examHistory = [];
                seqGameDone = [];
                persistProgress();
                streak = 0;
                document.getElementById('streak-count').innerText = '0 🔥';
                updateXP(0);''')
rep("showToast('XP y progreso de esta sesión reiniciados a 0.');","showToast('XP y progreso de este temario reiniciados a 0.');")

# D. switchTab
rep('''            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.remove('bg-white/15', 'text-white', 'shadow-sm');
                btn.classList.add('text-slate-200');
            });''','''            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.remove('bg-white/15', 'text-white', 'shadow-sm');
                btn.classList.add('text-slate-200');
                btn.setAttribute('aria-selected', 'false');
            });''')
rep('''                activeBtn.classList.remove('text-slate-200');
            }
''','''                activeBtn.classList.remove('text-slate-200');
                activeBtn.setAttribute('aria-selected', 'true');
            }
''')
rep('''            if (tabId === 'juegos' && studyState.hasContent) initGames();
        }''','''            if (tabId === 'juegos' && studyState.hasContent) initGames();
            if (tabId === 'progreso' && studyState.hasContent) renderProgress();
            if (tabId === 'profesor') renderTeacherView();
        }''')
rep('''                { empty: 'examen-empty-state', active: 'examen-active-wrapper' }''','''                { empty: 'examen-empty-state', active: 'examen-active-wrapper' },
                { empty: 'progreso-empty-state', active: 'progreso-active-content' }''')

# E. parser
rep('''            const numFormulaRegex = /\\b(?:\\d+(?:[.,]\\d+)?\\s*(?:%|ºc|°c|km|m|cm|mm|millones|años|siglo)?|[A-Z]{1,3}\\d)\\b/g;''',
'''            // REVISIÓN: antes el \\b final impedía capturar "70%" o "15 ºC" (y "ºc" solo en minúsculas)
            const numFormulaRegex = /(?<![\\p{L}\\p{N}])(?:\\d+(?:[.,]\\d+)?(?:\\s*(?:%|[º°]\\s?[cC]|km|cm|mm|millones|años|siglos?))?|[A-Z]{1,3}\\d)(?![\\p{L}\\p{N}])/gu;''')

rep('''        // Motor principal de análisis de apuntes
        function parseNotesEngine(subjectTitle, rawText) {''','''        // REVISIÓN: utilidades para títulos y pasos de secuencias más limpios
        function prettifyHeading(title) {
            let t = String(title || '').replace(/^\\s*(?:\\d+|[IVXLC]+)[.)]\\s*/, '').trim();
            if (t && t === t.toUpperCase()) t = capitalizeFirst(t.toLowerCase());
            return t;
        }

        // "Evaporación: el calor del Sol..." -> etiqueta corta "Evaporación" (el detalle se conserva aparte)
        function stepLabel(stepText) {
            const clean = stripMarkdownBold(stepText).trim();
            const idx = clean.indexOf(':');
            if (idx > 0 && idx <= 45) return clean.slice(0, idx).trim();
            if (clean.length > 70) return clean.slice(0, 67).replace(/\\s+\\S*$/, '') + '…';
            return clean;
        }

        // Motor principal de análisis de apuntes
        function parseNotesEngine(subjectTitle, rawText) {''')
rep('''                if (numberedBuffer.length >= 3) {
                    rawSequences.push({
                        blockId: currentBlock.id,
                        blockTitle: currentBlock.title,
                        title: numberedContextTitle || `Secuencia en ${currentBlock.title}`,
                        steps: numberedBuffer.map(s => stripMarkdownBold(s))
                    });
                }''','''                if (numberedBuffer.length >= 3) {
                    rawSequences.push({
                        blockId: currentBlock.id,
                        blockTitle: currentBlock.title,
                        title: numberedContextTitle || `Secuencia: ${prettifyHeading(currentBlock.title)}`,
                        steps: numberedBuffer.map(s => stepLabel(s)),
                        details: numberedBuffer.map(s => stripMarkdownBold(s))
                    });
                }''')
rep('''                    let seqTitle = `Proceso en ${currentBlock.title}`;''','''                    let seqTitle = `Proceso: ${prettifyHeading(currentBlock.title)}`;''')
rep('''                        rawSequences.push({
                            blockId: currentBlock.id,
                            blockTitle: currentBlock.title,
                            title: seqTitle,
                            steps
                        });''','''                        rawSequences.push({
                            blockId: currentBlock.id,
                            blockTitle: currentBlock.title,
                            title: seqTitle,
                            steps,
                            details: steps.slice()
                        });''')
rep('''                        if (prevLine.endsWith(':') && prevLine.length <= 75) {
                            numberedContextTitle = stripMarkdownBold(prevLine.slice(0, -1));
                        } else {
                            numberedContextTitle = `Fases de ${currentBlock.title}`;
                        }''','''                        if (prevLine.endsWith(':') && prevLine.length <= 110) {
                            numberedContextTitle = stripMarkdownBold(prevLine.slice(0, -1));
                        } else {
                            numberedContextTitle = `Fases: ${prettifyHeading(currentBlock.title)}`;
                        }''')
rep('''                if (cleanBulletLine.endsWith(':') && cleanBulletLine.length <= 75) {''','''                if (cleanBulletLine.endsWith(':') && cleanBulletLine.length <= 110) {''')
rep('''            if (sequences.length === 0 && concepts.length >= 3) {
                sequences.push({
                    id: 1,
                    blockId: validBlocks[0].id,
                    blockTitle: validBlocks[0].title,
                    title: `Orden del temario: ${finalTitle}`,
                    steps: concepts.slice(0, 6).map(c => c.term)
                });
            }''','''            // REVISIÓN: se elimina la "secuencia" inventada con los primeros conceptos. No representaba un orden real
            // y generaba preguntas de examen falsas ("¿qué etapa va después de X?") y un juego sin sentido.''')
rep('''            const sepMatch = line.match(/^([^:=–—\\-]{2,65}?)\\s*(?::|=|–|—|\\s-\\s)\\s*(.{8,})$/);
            if (sepMatch) {
                const rawTerm = stripMarkdownBold(sepMatch[1]).replace(/^\\d+[\\.\\)]\\s+/, '').trim();''','''            // REVISIÓN: el término ahora admite guiones internos ("Distancia Tierra-Sol: ...") y se ignoran URLs
            const sepMatch = /https?:\\/\\//i.test(line) ? null
                : line.match(/^((?:[^:=–—\\-]|(?<=\\S)-(?=\\S)){2,65}?)\\s*(?::|=|–|—|\\s-\\s)\\s*(.{8,})$/);
            if (sepMatch) {
                const rawTerm = stripMarkdownBold(sepMatch[1]).replace(/^\\d+[\\.\\)]\\s+/, '').trim();''')

# F. open questions numbering
rep('''                openQs.push({
                    id: qId++,
                    blockId: concept.blockId,''','''                openQs.push({
                    id: qId++,
                    conceptId: concept.id,
                    blockId: concept.blockId,''')
rep('''                    openQs.push({
                        id: qId++,
                        blockId: seq.blockId,
                        blockTitle: seq.blockTitle,
                        question: `${qId}. Enumera y explica ordenadamente las fases de: «${seq.title}».`,''','''                    // REVISIÓN: antes se numeraba con qId ya incrementado (la pregunta 14 aparecía como "15.")
                    const thisId = qId++;
                    openQs.push({
                        id: thisId,
                        blockId: seq.blockId,
                        blockTitle: seq.blockTitle,
                        question: `${thisId}. Enumera y explica ordenadamente las fases de: «${seq.title}».`,''')
open(P+'stage3.html','w').write(h); print('ok stage3')
