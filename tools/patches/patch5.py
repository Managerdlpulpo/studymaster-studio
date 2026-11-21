P='/workspace/app-apuntes/tools/'
h=open(P+'stage4.html').read()
def rep(old,new,count=1):
    global h
    n=h.count(old); assert n==count,(n,old[:160]); h=h.replace(old,new)

# processNotesAndGenerate
rep('''        function processNotesAndGenerate(customDataOverride = null) {
            if (customDataOverride) {''','''        function processNotesAndGenerate(customDataOverride = null, opts = {}) {
            if (customDataOverride) {''')
rep('''            // Reiniciar contadores de progreso de sesión para el nuevo temario
            masteredCards = [];
            completedDefs = [];
            completedOpen = [];
            streak = 0;

            syncEmptyOrActiveStates();
            refreshAllStudyViews();
            showToast(`⚡ ¡Listo! ${studyState.concepts.length} tarjetas y ${studyState.examQuestions.length} preguntas generadas.`);''','''            // REVISIÓN: el progreso ya no se pierde al recargar. Se identifica el temario por un hash de título + texto
            // y se recupera el progreso guardado para ese temario (si regeneras el mismo texto, lo conservas).
            if (!studyState.deckId) studyState.deckId = computeDeckId(studyState);
            loadProgressForDeck(studyState.deckId);
            streak = 0;
            persistCurrentDeck();
            persistProgress();

            syncEmptyOrActiveStates();
            refreshAllStudyViews();
            if (!opts.silent) {
                showToast(`⚡ ¡Listo! ${studyState.concepts.length} tarjetas y ${studyState.examQuestions.length} preguntas generadas.`);
            }''')
rep('''                masteredCards = [];
                completedDefs = [];
                completedOpen = [];
                syncEmptyOrActiveStates();
                showToast('Espacio de trabajo limpiado por completo.');''','''                masteredCards = [];
                completedDefs = [];
                completedOpen = [];
                selfValidatedOpen = [];
                leitnerState = {};
                examHistory = [];
                seqGameDone = [];
                streak = 0;
                safeRemoveItem('sm_current_deck');
                syncEmptyOrActiveStates();
                showToast('Espacio de trabajo limpiado (tus temarios guardados y su progreso se conservan).');''')

# upload rewrite
start=h.index('        // Subida de archivos (.txt, .md, .csv o .json de respaldo)')
end=h.index('        // Gestor de Temarios Guardados en localStorage')
UPLOAD=r'''        // =========================================================
        // REVISIÓN: SUBIDA DE APUNTES EN PDF, WORD, FOTO (OCR) Y TEXTO
        // Todo se procesa en el navegador; solo se descargan las librerías (versión fijada + SRI).
        // =========================================================
        const LIBS = {
            pdf: {
                src: 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js',
                integrity: 'sha384-/1qUCSGwTur9vjf/z9lmu/eCUYbpOTgSjmpbMQZ1/CtX2v/WcAIKqRv+U1DUCG6e',
                worker: 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js'
            },
            tesseract: {
                src: 'https://cdn.jsdelivr.net/npm/tesseract.js@5.1.1/dist/tesseract.min.js',
                integrity: 'sha384-GJqSu7vueQ9qN0E9yLPb3Wtpd7OrgK8KmYzC8T1IysG1bcvxvIO4qtYR/D3A991F'
            },
            mammoth: {
                src: 'https://cdn.jsdelivr.net/npm/mammoth@1.8.0/mammoth.browser.min.js',
                integrity: 'sha384-/cXAMbzovUIKbBERjPmR3SnPTh8siWr5lsvFYj1Uq4XP0yaJUZJmsh0YXyGv5P0y'
            }
        };
        const MAX_UPLOAD_BYTES = 40 * 1024 * 1024;
        const MAX_PDF_PAGES = 80;
        const MAX_OCR_PAGES = 15;
        const loadedScripts = {};

        function loadScriptOnce(lib) {
            if (loadedScripts[lib.src]) return loadedScripts[lib.src];
            loadedScripts[lib.src] = new Promise((resolve, reject) => {
                const s = document.createElement('script');
                s.src = lib.src;
                if (lib.integrity) { s.integrity = lib.integrity; s.crossOrigin = 'anonymous'; }
                s.referrerPolicy = 'no-referrer';
                s.onload = resolve;
                s.onerror = () => {
                    delete loadedScripts[lib.src];
                    reject(new Error('No se pudo descargar una librería necesaria. ¿Hay conexión a Internet?'));
                };
                document.head.appendChild(s);
            });
            return loadedScripts[lib.src];
        }

        function setExtractStatus(msg) {
            const box = document.getElementById('extract-status');
            if (!box) return;
            if (!msg) { box.classList.add('hidden'); return; }
            box.classList.remove('hidden');
            document.getElementById('extract-status-text').innerText = msg;
        }

        function readFileAs(file, mode) {
            return new Promise((resolve, reject) => {
                const r = new FileReader();
                r.onload = () => resolve(r.result);
                r.onerror = () => reject(r.error);
                if (mode === 'text') r.readAsText(file, 'UTF-8');
                else r.readAsArrayBuffer(file);
            });
        }

        // Une las líneas partidas típicas de PDF/OCR (una frase cortada en varias líneas) y las palabras con guion final
        function reflowExtractedText(text) {
            const lines = String(text || '').replace(/\r/g, '').replace(/-\n(?=\p{Ll})/gu, '').split('\n');
            const out = [];
            for (const raw of lines) {
                const line = raw.replace(/[ \t\u00a0]+/g, ' ').trim();
                if (!line) {
                    if (out.length && out[out.length - 1] !== '') out.push('');
                    continue;
                }
                const prev = out.length ? out[out.length - 1] : '';
                const prevEndsSentence = /[.:;!?»)\]]$/.test(prev);
                const startsNewItem = /^(?:[-•*▪▸►]|\d+[.)]|#|[IVXLC]+\.)\s/.test(line)
                    || /^\p{Lu}[^:]{1,60}:\s/u.test(line)
                    || /(?:→|->)/.test(line)
                    || !!detectHeading(line);
                if (prev && !prevEndsSentence && !startsNewItem && !detectHeading(prev) && /^[\p{Ll}0-9(«"]/u.test(line)) {
                    out[out.length - 1] = prev + ' ' + line;
                } else {
                    out.push(line);
                }
            }
            return out.join('\n').replace(/\n{3,}/g, '\n\n').trim();
        }

        let ocrWorker = null;
        async function getOcrWorker() {
            await loadScriptOnce(LIBS.tesseract);
            if (!ocrWorker) {
                setExtractStatus('Preparando el reconocimiento de texto (la primera vez descarga ~10 MB)…');
                ocrWorker = await Tesseract.createWorker('spa', 1, {
                    logger: m => {
                        if (m && m.status === 'recognizing text') {
                            setExtractStatus(`Reconociendo texto (OCR): ${Math.round((m.progress || 0) * 100)}%…`);
                        }
                    }
                });
            }
            return ocrWorker;
        }

        async function ocrImageSource(source) {
            const worker = await getOcrWorker();
            const { data } = await worker.recognize(source);
            return (data && data.text) || '';
        }

        async function extractTextFromPdf(file) {
            await loadScriptOnce(LIBS.pdf);
            const pdfjs = window.pdfjsLib;
            pdfjs.GlobalWorkerOptions.workerSrc = LIBS.pdf.worker;
            const data = await readFileAs(file, 'buffer');
            const pdf = await pdfjs.getDocument({ data, isEvalSupported: false }).promise;
            const pages = Math.min(pdf.numPages, MAX_PDF_PAGES);
            if (pdf.numPages > MAX_PDF_PAGES) showToast(`El PDF tiene ${pdf.numPages} páginas; se leen las ${MAX_PDF_PAGES} primeras.`, true);

            let text = '';
            for (let p = 1; p <= pages; p++) {
                setExtractStatus(`Leyendo «${file.name}»: página ${p} de ${pages}…`);
                const page = await pdf.getPage(p);
                const tc = await page.getTextContent();
                let pageText = '';
                let lastEnd = null, lastY = null;
                tc.items.forEach(it => {
                    if (!it || typeof it.str !== 'string') return;
                    const x = it.transform ? it.transform[4] : 0;
                    const y = it.transform ? it.transform[5] : 0;
                    if (lastY !== null && Math.abs(y - lastY) > 2 && !pageText.endsWith('\n')) pageText += '\n';
                    else if (lastEnd !== null && x - lastEnd > 1.5 && !/[\s]$/.test(pageText) && !it.str.startsWith(' ')) pageText += ' ';
                    pageText += it.str;
                    if (it.hasEOL) { pageText += '\n'; lastEnd = null; } else { lastEnd = x + (it.width || 0); }
                    lastY = y;
                });
                text += pageText + '\n\n';
            }

            // PDF escaneado (sin capa de texto): OCR de las primeras páginas
            let usedOcr = false;
            if (text.replace(/\s/g, '').length < 25 * pages) {
                usedOcr = true;
                const ocrPages = Math.min(pages, MAX_OCR_PAGES);
                if (pages > MAX_OCR_PAGES) showToast(`PDF escaneado: se aplica OCR a las ${MAX_OCR_PAGES} primeras páginas.`, true);
                let ocrText = '';
                for (let p = 1; p <= ocrPages; p++) {
                    setExtractStatus(`PDF escaneado: OCR de la página ${p} de ${ocrPages}…`);
                    const page = await pdf.getPage(p);
                    const viewport = page.getViewport({ scale: 2 });
                    const canvas = document.createElement('canvas');
                    canvas.width = viewport.width;
                    canvas.height = viewport.height;
                    await page.render({ canvasContext: canvas.getContext('2d'), viewport }).promise;
                    ocrText += (await ocrImageSource(canvas)) + '\n\n';
                }
                text = ocrText;
            }
            return { text: reflowExtractedText(text), usedOcr };
        }

        async function extractTextFromDocx(file) {
            await loadScriptOnce(LIBS.mammoth);
            setExtractStatus(`Leyendo «${file.name}»…`);
            const arrayBuffer = await readFileAs(file, 'buffer');
            const result = await mammoth.extractRawText({ arrayBuffer });
            return (result && result.value) || '';
        }

        // REVISIÓN: valida y normaliza cualquier temario importado (JSON de otra persona o datos antiguos del
        // navegador). Antes se cargaba tal cual: ids no numéricos acababan dentro de atributos onclick (riesgo XSS)
        // y un JSON manipulado podía traer respuestas "correctas" falsas.
        function sanitizeDeck(p) {
            if (!p || typeof p !== 'object' || !Array.isArray(p.concepts) || !p.subjectTitle) return null;
            const S = (v, max = 4000) => String(v == null ? '' : v).slice(0, max);
            const N = v => { const n = Number(v); return Number.isFinite(n) ? n : null; };
            const A = v => Array.isArray(v) ? v : [];
            const LIM = 2000;

            const concepts = p.concepts.slice(0, LIM).map(c => ({
                id: N(c && c.id), blockId: N(c && c.blockId), blockTitle: S(c && c.blockTitle, 200),
                term: S(c && c.term, 300), definition: S(c && c.definition), rawLine: S(c && c.rawLine),
                type: ['definition', 'fact', 'sequence'].includes(c && c.type) ? c.type : 'fact'
            })).filter(c => c.id !== null && c.term && c.definition);

            let blocks = A(p.blocks).slice(0, 200).map(b => ({ id: N(b && b.id), title: S(b && b.title, 200), items: [] }))
                .filter(b => b.id !== null);
            if (!blocks.length) {
                const seen = new Map();
                concepts.forEach(c => { if (!seen.has(c.blockId)) seen.set(c.blockId, c.blockTitle || 'General'); });
                blocks = Array.from(seen, ([id, title]) => ({ id: id === null ? 1 : id, title, items: [] }));
            }

            const sequences = A(p.sequences).slice(0, 100).map(s => ({
                id: N(s && s.id), blockId: N(s && s.blockId), blockTitle: S(s && s.blockTitle, 200), title: S(s && s.title, 300),
                steps: A(s && s.steps).slice(0, 30).map(x => S(x, 300)).filter(Boolean),
                details: A(s && s.details).slice(0, 30).map(x => S(x, 2000))
            })).filter(s => s.id !== null && s.steps.length >= 2);

            const definitions = A(p.definitions).slice(0, LIM).map(d => ({
                id: N(d && d.id), blockId: N(d && d.blockId), blockTitle: S(d && d.blockTitle, 200), title: S(d && d.title, 300),
                template: S(d && d.template), rawSentence: S(d && d.rawSentence),
                blanks: A(d && d.blanks).slice(0, 6).map(b => ({
                    display: S(b && b.display, 100),
                    accepted: A(b && b.accepted).slice(0, 10).map(a => S(a, 100)).filter(Boolean)
                })).filter(b => b.display),
                distractorWord: S(d && d.distractorWord, 100), explain: S(d && d.explain)
            })).filter(d => d.id !== null && d.blanks.length > 0);
            definitions.forEach(d => d.blanks.forEach(b => { if (!b.accepted.length) b.accepted = buildAcceptedVariants(b.display); }));

            const openQuestions = A(p.openQuestions).slice(0, LIM).map(q => ({
                id: N(q && q.id), conceptId: N(q && q.conceptId), blockId: N(q && q.blockId), blockTitle: S(q && q.blockTitle, 200),
                question: S(q && q.question, 1000), hint: S(q && q.hint, 1000), modelAnswer: S(q && q.modelAnswer),
                keyGroups: A(q && q.keyGroups).slice(0, 8).map(g => ({
                    label: S(g && g.label, 200),
                    keywords: A(g && g.keywords).slice(0, 10).map(k => S(k, 100)).filter(Boolean)
                })).filter(g => g.label)
            })).filter(q => q.id !== null && q.question && q.keyGroups.length > 0);
            openQuestions.forEach(q => q.keyGroups.forEach(g => { if (!g.keywords.length) g.keywords = buildAcceptedVariants(g.label); }));

            const deck = {
                hasContent: concepts.length > 0,
                subjectTitle: S(p.subjectTitle, 200),
                rawText: S(p.rawText, 500000),
                blocks, concepts, sequences, definitions, openQuestions,
                examQuestions: []
            };
            // Las preguntas tipo test se regeneran siempre: nunca se confía en índices "correctos" importados
            deck.examQuestions = buildBalancedExamQuestions(concepts, sequences, blocks);
            deck.deckId = (typeof p.deckId === 'string' && /^d_[a-z0-9]{1,16}$/.test(p.deckId)) ? p.deckId : computeDeckId(deck);
            return deck;
        }

        async function importDeckJsonFile(file) {
            try {
                const parsed = JSON.parse(await readFileAs(file, 'text'));
                if (parsed && parsed.type === 'studymaster-progress-report') {
                    showToast('Esto es un informe de progreso de un alumno: cárgalo en la pestaña 👩‍🏫 Profesor.', true);
                    return;
                }
                const deck = sanitizeDeck(parsed);
                if (!deck || !deck.hasContent) {
                    showToast('El archivo JSON no tiene un formato válido de StudyMaster.', true);
                    return;
                }
                document.getElementById('subject-title-input').value = deck.subjectTitle;
                document.getElementById('notes-textarea').value = deck.rawText || '';
                updateCharCount();
                processNotesAndGenerate(deck, { silent: true });
                showToast(`Temario JSON «${deck.subjectTitle}» importado.`);
            } catch (err) {
                showToast('Error al leer el archivo JSON.', true);
            }
        }

        async function handleFileUpload(event) {
            const input = event.target;
            const files = Array.from((input && input.files) || []);
            if (input) input.value = '';
            if (files.length === 0) return;

            if (files.length === 1 && /\.json$/i.test(files[0].name)) {
                await importDeckJsonFile(files[0]);
                return;
            }

            const texts = [];
            let usedOcr = false;
            try {
                for (const file of files) {
                    const name = (file.name || '').toLowerCase();
                    if (file.size > MAX_UPLOAD_BYTES) { showToast(`«${file.name}» supera 40 MB y se ha omitido.`, true); continue; }
                    let text = '';
                    if (name.endsWith('.json')) {
                        showToast('Los temarios .json se importan de uno en uno.', true);
                        continue;
                    } else if (file.type === 'application/pdf' || name.endsWith('.pdf')) {
                        const r = await extractTextFromPdf(file);
                        text = r.text;
                        usedOcr = usedOcr || r.usedOcr;
                    } else if (name.endsWith('.docx')) {
                        text = await extractTextFromDocx(file);
                    } else if ((file.type || '').startsWith('image/')) {
                        setExtractStatus(`Preparando OCR de «${file.name}»…`);
                        text = reflowExtractedText(await ocrImageSource(file));
                        usedOcr = true;
                    } else if (/\.(txt|md|markdown|csv)$/.test(name) || (file.type || '').startsWith('text/')) {
                        text = await readFileAs(file, 'text');
                    } else {
                        showToast(`Formato no admitido: «${file.name}» (usa PDF, .docx, imagen, .txt o .md).`, true);
                        continue;
                    }
                    if (text && text.trim()) texts.push(text.trim());
                    else showToast(`No se encontró texto en «${file.name}».`, true);
                }
            } catch (err) {
                console.error(err);
                showToast('Error al procesar el archivo: ' + (err && err.message ? err.message : String(err)), true);
            } finally {
                setExtractStatus(null);
            }

            if (texts.length === 0) return;
            const titleInput = document.getElementById('subject-title-input');
            if (!titleInput.value.trim()) {
                titleInput.value = capitalizeFirst(files[0].name.replace(/\.[^/.]+$/, '').replace(/[_-]+/g, ' '));
            }
            document.getElementById('notes-textarea').value = texts.join('\n\n');
            updateCharCount();

            if (usedOcr) {
                showToast('Texto reconocido por OCR: revísalo y corrige errores antes de pulsar «Generar».', true);
                document.getElementById('notes-textarea').focus();
            } else {
                processNotesAndGenerate();
            }
        }

'''
h=h[:start]+UPLOAD+h[end:]

# saved decks
rep('''            const found = decks.find(d => d.id === deckId);
            if (!found) return;

            document.getElementById('subject-title-input').value = found.subjectTitle;
            document.getElementById('notes-textarea').value = found.rawText || '';
            updateCharCount();
            processNotesAndGenerate(found);''','''            const found = sanitizeDeck(decks.find(d => d.id === deckId));
            if (!found) {
                showToast('Este temario guardado está dañado y no se puede abrir.', true);
                return;
            }

            document.getElementById('subject-title-input').value = found.subjectTitle;
            document.getElementById('notes-textarea').value = found.rawText || '';
            updateCharCount();
            processNotesAndGenerate(found, { silent: true });
            showToast(`Temario «${found.subjectTitle}» abierto con tu progreso.`);''')
rep('''<div class="text-[10px] text-slate-400">${deck.concepts ? deck.concepts.length : 0} tarjetas · ${deck.savedAt || ''}</div>''',
    '''<div class="text-[10px] text-slate-400">${Array.isArray(deck.concepts) ? deck.concepts.length : 0} tarjetas · ${escapeHtml(deck.savedAt || '')}</div>''')
rep('''                .replace(/"/g, '&quot;');
        }''','''                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#39;');
        }''')
rep('''            const dataStr = JSON.stringify(studyState, null, 2);
            const blob = new Blob([dataStr], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            const safeFileName = normalizeText(studyState.subjectTitle).replace(/\\s+/g, '_') || 'temario_studymaster';
            a.href = url;
            a.download = `${safeFileName}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            showToast('📤 Archivo .JSON descargado correctamente.');''','''            const safeFileName = normalizeText(studyState.subjectTitle).replace(/\\s+/g, '_') || 'temario_studymaster';
            downloadFile(`${safeFileName}.json`, JSON.stringify(studyState, null, 2), 'application/json');
            showToast('📤 Archivo .JSON descargado correctamente.');
        }

        function downloadFile(fileName, content, mime) {
            const blob = new Blob([content], { type: mime });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = fileName;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            setTimeout(() => URL.revokeObjectURL(url), 1000);''')

# flowchart details
rep('''                    document.getElementById('flow-desc').innerText = stepText;''','''                    document.getElementById('flow-desc').innerText = (seq.details && seq.details[idx]) || stepText;''')

open(P+'stage5.html','w').write(h); print('ok stage5')
