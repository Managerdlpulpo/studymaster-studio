P='/workspace/app-apuntes/tools/'
h=open(P+'stage3.html').read()
def rep(old,new,count=1):
    global h
    n=h.count(old); assert n==count,(n,old[:160]); h=h.replace(old,new)

start = h.index('        // =========================================================\n        // EQUILIBRADOR DE LONGITUD')
endmark = '            return questions.slice(0, 20);\n        }\n'
end = h.index(endmark, start) + len(endmark)
NEW = r'''        // =========================================================
        // EQUILIBRADOR DE LONGITUD PARA OPCIONES DEL EXAMEN TIPO TEST
        // =========================================================
        // REVISIÓN: barajado Fisher-Yates (sort(() => Math.random() - 0.5) está sesgado)
        function shuffleArray(arr) {
            const a = [...arr];
            for (let i = a.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [a[i], a[j]] = [a[j], a[i]];
            }
            return a;
        }

        function escapeRegex(s) {
            return String(s).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        }

        // REVISIÓN: oculta el propio término dentro de su definición. Antes la respuesta correcta repetía la palabra
        // de la pregunta (p. ej. «¿Qué describe a "150 millones de km"?» -> "...a 150 millones de km del Sol").
        function maskTerm(text, term) {
            let out = String(text || '');
            const t = stripMarkdownBold(term || '').trim();
            if (!t) return out;
            out = out.replace(new RegExp('^\\s*' + escapeRegex(t) + '\\s*[:=–—-]\\s*', 'i'), '');
            const variants = [t];
            t.split(/\s+/).forEach(w => {
                const nw = normalizeText(w);
                if (nw.length >= 5 && !SPANISH_STOPWORDS.has(nw)) variants.push(w.replace(/[.,;:()]/g, ''));
            });
            variants.sort((a, b) => b.length - a.length).forEach(v => {
                if (!v) return;
                out = out.replace(new RegExp('(?<![\\p{L}\\p{N}])' + escapeRegex(v) + '(?![\\p{L}\\p{N}])', 'giu'), '_____');
            });
            return out.replace(/_____(?:\s+_____)+/g, '_____').trim();
        }

        // Garantiza que la respuesta correcta NO sea sistemáticamente la frase más larga
        function balanceOptionLengths(correctText, distractorPool) {
            const cleanCorrect = correctText.trim();
            const targetLen = cleanCorrect.length;
            const seen = new Set([normalizeText(cleanCorrect)]);
            const unique = [];
            distractorPool.forEach(d => {
                const n = normalizeText(d);
                if (n && !seen.has(n)) { seen.add(n); unique.push(d.trim()); }
            });

            // Seleccionar los 3 distractores cuya longitud natural sea más cercana a la correcta
            const chosen = unique
                .sort((a, b) => Math.abs(a.length - targetLen) - Math.abs(b.length - targetLen))
                .slice(0, 3);

            // Recortar en una pausa natural si algún distractor es mucho más largo que la correcta.
            // REVISIÓN: se elimina la mezcla "X; además, Y", que fabricaba opciones híbridas raras.
            const adjustedDistractors = chosen.map(dist => {
                let text = dist;
                if (text.length > targetLen * 1.45 && targetLen >= 25) {
                    const cutLimit = Math.min(text.length, Math.round(targetLen * 1.2));
                    const slice = text.slice(0, cutLimit);
                    const lastSpace = slice.lastIndexOf(' ');
                    text = (lastSpace > 15 ? slice.slice(0, lastSpace) : slice).replace(/[,;:\-]+$/, '') + '.';
                }
                return text;
            });

            return { correctOption: cleanCorrect, distractors: adjustedDistractors };
        }

        function makeMCQ(qText, correctText, distractors, explain, blockTitle, conceptTerm) {
            const opts = shuffleArray([
                { text: correctText, isCorrect: true },
                ...distractors.map(d => ({ text: d, isCorrect: false }))
            ]);
            return {
                q: qText,
                options: opts.map(o => o.text),
                correct: opts.findIndex(o => o.isCorrect),
                explain,
                blockTitle: blockTitle || '',
                concept: conceptTerm || ''
            };
        }

        // Vuelve a barajar las opciones de una pregunta conservando cuál es la correcta
        function reshuffleQuestion(q) {
            const correctText = q.options[q.correct];
            const options = shuffleArray(q.options);
            return { ...q, options, correct: options.indexOf(correctText) };
        }

        // Genera hasta 20 preguntas tipo test basadas exclusivamente en los apuntes cargados
        function buildBalancedExamQuestions(concepts, sequences, blocks) {
            if (concepts.length < 2) return [];

            const questions = [];
            const maskedDefs = concepts.map(c => maskTerm(c.definition, c.term));
            const allTerms = concepts.map(c => c.term);

            // 1. Preguntas de definición / de término, alternando
            concepts.forEach((concept, idx) => {
                if (questions.length >= 20) return;
                const ownMasked = maskedDefs[idx];
                if (!ownMasked || ownMasked.replace(/_/g, '').trim().length < 10) return;

                if (idx % 2 === 0 && concepts.length >= 4) {
                    const pool = maskedDefs.filter((_, i) => i !== idx);
                    const balanced = balanceOptionLengths(ownMasked, pool);
                    if (balanced.distractors.length === 3) {
                        questions.push(makeMCQ(
                            `¿Qué afirmación describe correctamente a «${concept.term}»?`,
                            balanced.correctOption, balanced.distractors,
                            `Según tus apuntes (${concept.blockTitle}): ${concept.term} — ${concept.definition}`,
                            concept.blockTitle, concept.term));
                    }
                } else if (allTerms.length >= 4) {
                    const pool = allTerms.filter((_, i) => i !== idx);
                    const balanced = balanceOptionLengths(concept.term, pool);
                    if (balanced.distractors.length === 3) {
                        questions.push(makeMCQ(
                            `¿A qué concepto de tus apuntes corresponde esta descripción?: «${ownMasked}»`,
                            balanced.correctOption, balanced.distractors,
                            `La descripción corresponde a «${concept.term}» dentro del bloque «${concept.blockTitle}».`,
                            concept.blockTitle, concept.term));
                    }
                }
            });

            // 2. Preguntas sobre secuencias reales (>= 4 pasos), máximo 4 por secuencia
            sequences.forEach(seq => {
                if (questions.length >= 20 || seq.steps.length < 4) return;
                let perSeq = 0;
                for (let i = 0; i < seq.steps.length - 1 && questions.length < 20 && perSeq < 4; i++) {
                    const currentStep = seq.steps[i];
                    const nextStep = seq.steps[i + 1];
                    const otherSteps = seq.steps.filter((_, sIdx) => sIdx !== i + 1 && sIdx !== i);
                    if (otherSteps.length < 3) {
                        // con 4 pasos solo quedan 2 alternativas: se añade el paso actual como distractor
                        otherSteps.push(currentStep);
                    }
                    const balanced = balanceOptionLengths(nextStep, otherSteps);
                    if (balanced.distractors.length === 3) {
                        questions.push(makeMCQ(
                            `En «${seq.title}», ¿qué etapa ocurre inmediatamente después de «${currentStep}»?`,
                            balanced.correctOption, balanced.distractors,
                            `La secuencia completa es: ${seq.steps.join(' → ')}.`,
                            seq.blockTitle, nextStep));
                        perSeq++;
                    }
                }
            });

            // 3. Preguntas de clasificación por bloque (si hay >= 4 bloques distintos y aún faltan preguntas)
            if (blocks.length >= 4 && questions.length < 20) {
                const blockTitles = blocks.map(b => b.title);
                concepts.forEach(concept => {
                    if (questions.length >= 20) return;
                    const alreadyAsked = questions.some(q => q.q.includes(`«${concept.term}»`));
                    if (alreadyAsked) return;
                    const balanced = balanceOptionLengths(concept.blockTitle, blockTitles);
                    if (balanced.distractors.length === 3) {
                        questions.push(makeMCQ(
                            `¿En qué bloque o apartado de tus apuntes se estudia «${concept.term}»?`,
                            balanced.correctOption, balanced.distractors,
                            `«${concept.term}» forma parte del bloque «${concept.blockTitle}».`,
                            concept.blockTitle, concept.term));
                    }
                });
            }

            return questions.slice(0, 20);
        }
'''
h = h[:start] + NEW + h[end:]
open(P+'stage4.html','w').write(h); print('ok stage4')
