P='/workspace/app-apuntes/tools/'
h=open(P+'stage5.html').read()
def rep(old,new,count=1):
    global h
    n=h.count(old); assert n==count,(n,old[:160]); h=h.replace(old,new)

# ---- Flashcards / Leitner ----
rep('''        function updateMasteredCounter() {
            const masteredInCat = filteredCards.filter(c => masteredCards.includes(c.id)).length;''','''        function dueOf(conceptId) {
            const st = leitnerState[conceptId];
            return st && typeof st.due === 'number' ? st.due : 0;
        }

        function updateMasteredCounter() {
            const now = Date.now();
            const dueEl = document.getElementById('fc-due-count');
            if (dueEl) dueEl.innerText = filteredCards.filter(c => dueOf(c.id) <= now).length;
            const masteredInCat = filteredCards.filter(c => masteredCards.includes(c.id)).length;''')
rep('''            filteredCards = selectedCat === 'all'
                ? studyState.concepts
                : studyState.concepts.filter(c => String(c.blockId) === selectedCat);''','''            const base = selectedCat === 'all'
                ? studyState.concepts
                : studyState.concepts.filter(c => String(c.blockId) === selectedCat);
            // REVISIÓN: repetición espaciada. Primero las tarjetas cuyo repaso toca (o nuevas), en orden de urgencia.
            filteredCards = [...base].sort((a, b) => dueOf(a.id) - dueOf(b.id));''')
rep('''        function showCurrentCard() {
            if (filteredCards.length === 0) return;''','''        function showCurrentCard() {
            if (filteredCards.length === 0) {
                document.getElementById('fc-tag').innerText = '';
                document.getElementById('fc-question').innerText = 'No hay tarjetas en este filtro.';
                document.getElementById('fc-answer').innerText = '';
                const info = document.getElementById('fc-box-info');
                if (info) info.innerText = '';
                updateMasteredCounter();
                return;
            }''')
rep('''            const badge = document.getElementById('fc-mastered-badge');
            if (masteredCards.includes(card.id)) {''','''            const info = document.getElementById('fc-box-info');
            if (info) {
                const st = leitnerState[card.id];
                if (!st) info.innerText = 'Tarjeta nueva';
                else {
                    const due = dueOf(card.id);
                    const when = due <= Date.now() ? 'hoy' : new Date(due).toLocaleDateString('es-ES', { day: 'numeric', month: 'short' });
                    info.innerText = `Caja ${st.box}/5 · próximo repaso: ${when}`;
                }
            }

            const badge = document.getElementById('fc-mastered-badge');
            if (masteredCards.includes(card.id)) {''')
rep('''            const card = filteredCards[currentFCIndex];
            if (known) {
                if (!masteredCards.includes(card.id)) {
                    masteredCards.push(card.id);
                    updateXP(20);
                    showToast('¡Tarjeta dominada! +20 XP');
                }
            } else {
                masteredCards = masteredCards.filter(id => id !== card.id);
            }
            updateMasteredCounter();''','''            const card = filteredCards[currentFCIndex];
            const st = leitnerState[card.id] || { box: 0, due: 0 };
            st.box = known ? Math.min(5, (st.box || 0) + 1) : 1;
            st.due = Date.now() + LEITNER_DAYS[st.box] * 86400000;
            leitnerState[card.id] = st;
            if (known) {
                if (!masteredCards.includes(card.id)) {
                    masteredCards.push(card.id);
                    updateXP(20);
                    showToast('¡Tarjeta dominada! +20 XP');
                }
            } else {
                masteredCards = masteredCards.filter(id => id !== card.id);
            }
            persistProgress();
            updateMasteredCounter();''')

# ---- Definitions robustness ----
rep('''                    parts[0] = parts[0].replace(`{${bIdx}}`, inputHtml);''','''                    // REVISIÓN: si al editar se borró el marcador {n}, el hueco se añade al final en vez de desaparecer
                    if (parts[0].includes(`{${bIdx}}`)) parts[0] = parts[0].replace(`{${bIdx}}`, inputHtml);
                    else parts[0] += ' ' + inputHtml;''')
rep('''                const input = document.getElementById(`def-input-${defId}-${bIdx}`);
                const userVal = normalizeText(input.value);''','''                const input = document.getElementById(`def-input-${defId}-${bIdx}`);
                if (!input) { allCorrect = false; return; }
                const userVal = normalizeText(input.value);''')
rep('''                    completedDefs.push(defId);
                    updateXP(25);''','''                    completedDefs.push(defId);
                    persistProgress();
                    updateXP(25);''')

# ---- Open questions ----
rep('''                            <button type="button" onclick="toggleModelAnswer(${item.id})" class="bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold py-2 px-3 rounded-xl text-xs border border-slate-200 transition-colors flex items-center gap-1.5">''',
    '''                            <button type="button" id="open-modelbtn-${item.id}" onclick="toggleModelAnswer(${item.id})" class="${currentOpenMode === 'exam' ? 'hidden ' : ''}bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold py-2 px-3 rounded-xl text-xs border border-slate-200 transition-colors flex items-center gap-1.5">''')
rep('''        function markOpenQuestionPassed(qId) {
            if (!completedOpen.includes(qId)) {
                completedOpen.push(qId);
                updateXP(30);
                updateOpenCounter();
                showToast('¡Pregunta abierta superada! +30 XP');
            }''','''        // REVISIÓN: corrección tolerante a variaciones (evaporar / evaporación) y con límites de palabra
        // (antes "sol" se daba por encontrado dentro de "solido").
        function stemOf(word) {
            return word.length <= 4 ? word : word.slice(0, Math.max(4, Math.min(word.length - 2, 7)));
        }

        function answerContainsKeyword(normAnswer, answerTokens, kw) {
            const nk = normalizeText(kw);
            if (!nk) return false;
            if ((' ' + normAnswer + ' ').includes(' ' + nk + ' ')) return true;
            const kwTokens = nk.split(' ').filter(t => t.length >= 3 && !SPANISH_STOPWORDS.has(t));
            if (kwTokens.length === 0) return false;
            return kwTokens.every(kt => {
                const st = stemOf(kt);
                return answerTokens.some(at => at === kt || (st.length >= 4 && at.startsWith(st)));
            });
        }

        function markOpenQuestionPassed(qId, selfValidated = false) {
            if (selfValidated && currentOpenMode === 'exam') return; // en modo examen no se permite autovalidar
            if (selfValidated) {
                if (!selfValidatedOpen.includes(qId) && !completedOpen.includes(qId)) selfValidatedOpen.push(qId);
            } else {
                selfValidatedOpen = selfValidatedOpen.filter(id => id !== qId);
            }
            if (!completedOpen.includes(qId)) {
                completedOpen.push(qId);
                updateXP(selfValidated ? 15 : 30);
                updateOpenCounter();
                showToast(selfValidated ? 'Marcada como válida por ti (+15 XP). Tu profesor la verá como autovalidada.' : '¡Pregunta abierta superada! +30 XP');
            }
            persistProgress();''')
rep('''            item.keyGroups.forEach(group => {
                const isMatched = group.keywords.some(kw => {
                    const normKw = normalizeText(kw);
                    return normKw && normText.includes(normKw);
                });''','''            const answerTokens = normText.split(' ');
            item.keyGroups.forEach(group => {
                const isMatched = group.keywords.some(kw => answerContainsKeyword(normText, answerTokens, kw));''')
rep('''            const fb = document.getElementById(`open-feedback-${qId}`);
            const modelEl = document.getElementById(`open-model-${qId}`);''','''            const fb = document.getElementById(`open-feedback-${qId}`);
            const modelEl = document.getElementById(`open-model-${qId}`);
            const modelBtn = document.getElementById(`open-modelbtn-${qId}`);
            if (modelBtn) modelBtn.classList.remove('hidden'); // en modo examen solo se ve tras intentar
            const selfValidateHtml = (style) => currentOpenMode === 'exam' ? '' : `
                    <div class="pt-1">
                        <button type="button" onclick="markOpenQuestionPassed(${qId}, true)" class="${style} text-white font-bold px-3 py-1.5 rounded-lg text-[11px] transition-colors">
                            <i class="fa-solid fa-check"></i> Dar por válida mi redacción (+15 XP, quedará como autovalidada)
                        </button>
                    </div>`;''')
rep('''                    <div class="flex flex-wrap gap-1.5">${matchedHtml}${missingHtml}</div>
                    <div class="pt-1">
                        <button type="button" onclick="markOpenQuestionPassed(${qId})" class="bg-bio-600 hover:bg-bio-700 text-white font-bold px-3 py-1.5 rounded-lg text-[11px] transition-colors">
                            <i class="fa-solid fa-check"></i> Dar por válida mi redacción (+30 XP)
                        </button>
                    </div>
                `;''','''                    <div class="flex flex-wrap gap-1.5">${matchedHtml}${missingHtml}</div>
                    ${selfValidateHtml('bg-bio-600 hover:bg-bio-700')}
                `;''')
rep('''                    <div class="flex flex-wrap gap-1.5">${missingHtml}</div>
                    <div class="pt-1">
                        <button type="button" onclick="markOpenQuestionPassed(${qId})" class="bg-slate-700 hover:bg-slate-800 text-white font-bold px-3 py-1.5 rounded-lg text-[11px] transition-colors">
                            <i class="fa-solid fa-check"></i> Dar por válida mi redacción (+30 XP)
                        </button>
                    </div>
                `;''','''                    <div class="flex flex-wrap gap-1.5">${missingHtml}</div>
                    ${selfValidateHtml('bg-slate-700 hover:bg-slate-800')}
                `;''')
rep("showToast('Modo Examen Escrito activado: pistas ocultas.', true);","showToast('Modo Examen Escrito: sin pistas, sin autovalidar y la respuesta modelo solo tras intentarlo.', true);")

# ---- Games ----
rep('''            const seq = studyState.sequences[currentSequenceGameIdx];
            if (!seq || seq.steps.length === 0) return;

            document.getElementById('sequence-game-subtitle')''','''            const seq = studyState.sequences[currentSequenceGameIdx];
            if (!seq || seq.steps.length === 0) {
                document.getElementById('sequence-game-subtitle').innerText =
                    'Tus apuntes no tienen secuencias. Añade una lista numerada (1. 2. 3.) o una cadena con flechas (A → B → C) para jugar.';
                return;
            }

            document.getElementById('sequence-game-subtitle')''')
rep('''                fb.innerText = '🎉 ¡Perfecto! Has ordenado la secuencia correctamente. (+50 XP)';
                updateXP(50);''','''                // REVISIÓN: antes se podía pulsar «Comprobar» una y otra vez sumando +50 XP cada vez
                if (!seqGameDone.includes(seq.id)) {
                    seqGameDone.push(seq.id);
                    updateXP(50);
                    persistProgress();
                    fb.innerText = '🎉 ¡Perfecto! Has ordenado la secuencia correctamente. (+50 XP)';
                } else {
                    fb.innerText = '🎉 ¡Perfecto otra vez! (los XP de esta secuencia ya los sumaste)';
                }''')
rep('''        function answerSpeed(selectedKey, selectedLabel) {
            if (!currentSpeedItem) return;''','''        let speedLocked = false;
        function answerSpeed(selectedKey, selectedLabel) {
            if (!currentSpeedItem || speedLocked) return; // REVISIÓN: evita sumar XP con doble clic
            speedLocked = true;''')
rep('''            setTimeout(nextSpeedQuestion, 750);''','''            setTimeout(() => { speedLocked = false; nextSpeedQuestion(); }, 750);''')

# ---- Exam ----
rep('''            isRetryMistakesMode = keepCorrect;
            const retryBadge = document.getElementById('exam-retry-badge');''','''            isRetryMistakesMode = keepCorrect;
            finishConfirmPending = false;
            const retryBadge = document.getElementById('exam-retry-badge');
            // REVISIÓN: en cada intento nuevo se barajan preguntas y opciones (antes siempre salían igual)
            if (!keepCorrect) {
                studyState.examQuestions = shuffleArray(studyState.examQuestions).map(reshuffleQuestion);
            }''')
rep('''        function finishExam() {
            let correctCount = 0;''','''        let finishConfirmPending = false;
        function finishExam() {
            const unanswered = userExamAnswers.filter(a => a === null).length;
            if (unanswered > 0 && !finishConfirmPending) {
                finishConfirmPending = true;
                showToast(`Te quedan ${unanswered} pregunta(s) sin responder. Pulsa otra vez «Finalizar» para corregir igualmente.`, true);
                setTimeout(() => { finishConfirmPending = false; }, 5000);
                return;
            }
            finishConfirmPending = false;
            let correctCount = 0;''')
rep('''            const msg = document.getElementById('exam-feedback-msg');
            if (parseFloat(score) >= 9) {
                msg.innerText = '🎉 ¡SOBRESALIENTE! Dominas estos apuntes a nivel de 10.';
                updateXP(150);
            } else if (parseFloat(score) >= 7) {
                msg.innerText = '👍 ¡Notable alto! Repasa los pequeños fallos para rozar la perfección.';
                updateXP(80);
            } else {
                msg.innerText = '📚 Buen intento. Repasa las tarjetas y definiciones y repite los fallos.';
                updateXP(30);
            }''','''            const msg = document.getElementById('exam-feedback-msg');
            const numScore = parseFloat(score);
            // REVISIÓN: XP sin trampas. Antes «Repetir solo fallos» daba otra vez +150 XP con las respuestas ya acertadas.
            const fullAttempts = examHistory.filter(a => !a.retry);
            const bestBefore = fullAttempts.length ? Math.max(...fullAttempts.map(a => a.score)) : -1;
            const tierXP = numScore >= 9 ? 150 : (numScore >= 7 ? 80 : 30);
            const xpGain = isRetryMistakesMode ? 0 : (numScore > bestBefore ? tierXP : 10);
            if (numScore >= 9) {
                msg.innerText = '🎉 ¡SOBRESALIENTE! Dominas estos apuntes a nivel de 10.';
            } else if (numScore >= 7) {
                msg.innerText = '👍 ¡Notable alto! Repasa los pequeños fallos para rozar la perfección.';
            } else if (numScore >= 5) {
                msg.innerText = '🙂 Aprobado. Repasa las tarjetas en las que fallas y repite los fallos.';
            } else {
                msg.innerText = '📚 Aún no. Repasa las tarjetas y definiciones y repite los fallos.';
            }
            msg.innerText += isRetryMistakesMode ? ' (Repaso de fallos: no cuenta como nota ni suma XP)' : ` (+${xpGain} XP)`;
            if (xpGain > 0) updateXP(xpGain);

            // Registrar intento en el historial (para «Mi Progreso» y el informe al profesor)
            const byBlock = {};
            const wrong = [];
            studyState.examQuestions.forEach((q, idx) => {
                const key = q.blockTitle || 'General';
                byBlock[key] = byBlock[key] || { c: 0, t: 0 };
                byBlock[key].t++;
                if (userExamAnswers[idx] === q.correct) byBlock[key].c++;
                else if (q.concept) wrong.push(q.concept);
            });
            examHistory.push({
                date: new Date().toISOString(), score: numScore, correct: correctCount,
                total: studyState.examQuestions.length, retry: isRetryMistakesMode, byBlock, wrong: wrong.slice(0, 30)
            });
            persistProgress();''')
rep('''                    <div class="font-bold text-slate-800 mb-1">${escapeHtml(q.q)}</div>''','''                    <div class="font-bold text-slate-800 mb-1">${idx + 1}. ${escapeHtml(q.q)}</div>''')

# ---- Editor ----
rep('''        function saveEditorChanges() {
            studyState.concepts = draftConcepts;
            studyState.definitions = draftDefinitions;
            studyState.openQuestions = draftOpenQuestions;
            studyState.examQuestions = buildBalancedExamQuestions(studyState.concepts, studyState.sequences, studyState.blocks);
''','''        function saveEditorChanges() {
            // REVISIÓN: se descartan ítems vacíos y se garantiza que cada hueco tenga su marcador {n}
            studyState.concepts = draftConcepts
                .map(c => ({ ...c, term: String(c.term || '').trim(), definition: String(c.definition || '').trim() }))
                .filter(c => c.term && c.definition);
            studyState.definitions = draftDefinitions.filter(d => String(d.template || '').trim() && d.blanks.length > 0);
            studyState.definitions.forEach(d => {
                d.blanks.forEach((_, i) => { if (!d.template.includes(`{${i}}`)) d.template += ` {${i}}`; });
            });
            studyState.openQuestions = draftOpenQuestions.filter(q => String(q.question || '').trim() && q.keyGroups.length > 0);
            studyState.examQuestions = buildBalancedExamQuestions(studyState.concepts, studyState.sequences, studyState.blocks);
            studyState.hasContent = studyState.concepts.length > 0;
            if (!studyState.hasContent) {
                showToast('Has eliminado todas las tarjetas: no queda material para estudiar.', true);
            }
            pruneProgressToExistingItems();
            persistCurrentDeck();
            persistProgress();
''')
rep('''            syncEmptyOrActiveStates();
            refreshAllStudyViews();
            closeEditorModal();''','''            syncEmptyOrActiveStates();
            if (studyState.hasContent) refreshAllStudyViews();
            closeEditorModal();''')
# unique ids for new editor items
h = h.replace("                    id: Date.now(),\n", "                    id: nextFreeId(),\n")
assert h.count('id: nextFreeId(),')==3
rep('''        function addNewItemInEditor() {''','''        let idSeq = 0;
        function nextFreeId() {
            idSeq++;
            return Date.now() * 10 + (idSeq % 10);
        }

        function addNewItemInEditor() {''')
open(P+'stage6.html','w').write(h); print('ok stage6')
