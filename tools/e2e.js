const puppeteer=require('puppeteer-core');const path=require('path');const fs=require('fs');
const URL='http://127.0.0.1:8765/index.html';
const results=[];const ok=(c,m)=>{results.push((c?'PASS ':'FAIL ')+m);console.log((c?'PASS ':'FAIL ')+m);if(!c)process.exitCode=1;};
(async()=>{
 const browser=await puppeteer.launch({executablePath:'/usr/bin/google-chrome',headless:'new',args:['--no-sandbox']});
 // fixtures: pdf + png
 const fp=await browser.newPage();
 await fp.goto('file://'+path.resolve('fixtures/notes_pdf.html')); await fp.pdf({path:'fixtures/revolucion.pdf',format:'A4'});
 await fp.goto('file://'+path.resolve('fixtures/notes_img.html')); await fp.setViewport({width:960,height:420}); await fp.screenshot({path:'fixtures/foto_apuntes.png'});
 await fp.close();

 const page=await browser.newPage(); const errors=[];
 page.on('pageerror',e=>errors.push('pageerror: '+e.message));
 page.on('console',m=>{ if(m.type()==='error') errors.push('console: '+m.text()); });
 const cdp=await page.target().createCDPSession(); await cdp.send('Browser.setDownloadBehavior',{behavior:'allow',downloadPath:path.resolve('dl')}).catch(()=>{});
 await page.goto(URL,{waitUntil:'networkidle0'});
 const $t=(sel)=>page.$eval(sel,e=>e.innerText);
 const click=async(sel)=>{await page.$eval(sel,e=>e.click());};
 const ev=(fn,...a)=>page.evaluate(fn,...a);

 // 1 demo
 await ev(()=>loadDemoNotes());
 const stats=await $t('#generation-stats-text'); ok(/12 tarjetas/.test(stats),'demo genera: '+stats);
 // palette check: bio-950 exists
 const bg=await ev(()=>getComputedStyle(document.getElementById('flashcard-back')).backgroundImage); ok(/rgb\(5, 46, 22\)/.test(bg),'reverso flashcard con bio-950');
 // 2 flashcards
 await ev(()=>switchTab('flashcards'));
 await ev(()=>{answerFlashcard(true);answerFlashcard(false);answerFlashcard(true);});
 ok((await $t('#mastered-count'))==='2','2 tarjetas dominadas');
 // 3 definitions
 await ev(()=>switchTab('definiciones'));
 const defId=await ev(()=>studyState.definitions[0].id);
 await ev((id)=>{revealDefinitionSolution(id);checkDefinition(id);},defId);
 ok((await $t('#defs-completed-count'))==='1','definición completada');
 // 4 open questions exam mode: no self-validate, model hidden
 await ev(()=>switchTab('abiertas')); await ev(()=>setOpenMode('exam'));
 const q0=await ev(()=>studyState.openQuestions[0].id);
 ok(await ev((id)=>document.getElementById('open-modelbtn-'+id).classList.contains('hidden'),q0),'modo examen: respuesta modelo oculta');
 await ev((id)=>{document.getElementById('open-textarea-'+id).value='nada que ver';evaluateOpenQuestion(id);},q0);
 ok(!(await ev((id)=>document.getElementById('open-feedback-'+id).innerHTML.includes('Dar por válida'),q0)),'modo examen: sin autovalidar');
 ok(!(await ev((id)=>document.getElementById('open-modelbtn-'+id).classList.contains('hidden'),q0)),'modelo visible tras intentar');
 await ev(()=>setOpenMode('practice'));
 const ans=await ev(()=>studyState.openQuestions[0].modelAnswer);
 await ev((id,a)=>{document.getElementById('open-textarea-'+id).value=a;evaluateOpenQuestion(id);},q0,ans);
 ok((await $t('#open-completed-count'))==='1','pregunta abierta superada con respuesta modelo');
 // 5 games: XP anti-farming
 await ev(()=>switchTab('juegos'));
 const xp0=await ev(()=>userXP);
 await ev(()=>{const b=document.querySelector('#speed-buttons button');b.click();b.click();b.click();});
 const xp1=await ev(()=>userXP); ok(xp1-xp0<=10,'doble clic en clasificador no multiplica XP ('+(xp1-xp0)+')');
 await ev(()=>{const s=studyState.sequences[0]; userMethodSeq=s.steps.slice(); checkMethodOrder(); checkMethodOrder(); checkMethodOrder();});
 const xp2=await ev(()=>userXP); ok(xp2-xp1===50,'secuencia: +50 XP una sola vez ('+(xp2-xp1)+')');
 // 6 exam
 await ev(()=>switchTab('examen')); await ev(()=>startExam(false));
 const n=await ev(()=>studyState.examQuestions.length);
 await ev(()=>{ for(let i=0;i<studyState.examQuestions.length;i++){ currentExamIndex=i; selectExamAnswer(i<5?studyState.examQuestions[i].correct:(studyState.examQuestions[i].correct+1)%4);} currentExamIndex=studyState.examQuestions.length-1; nextExamQuestion();});
 const score=await $t('#final-score'); ok(Math.abs(parseFloat(score)-(5/n*10))<0.06,`nota correcta ${score} (5/${n})`);
 const xpE=await ev(()=>userXP);
 await ev(()=>{repeatMistakes(); for(let i=0;i<studyState.examQuestions.length;i++){ if(userExamAnswers[i]===null){currentExamIndex=i;selectExamAnswer(studyState.examQuestions[i].correct);} } currentExamIndex=studyState.examQuestions.length-1; nextExamQuestion();});
 ok((await ev(()=>userXP))===xpE,'repetir fallos no suma XP');
 // unanswered warning
 await ev(()=>{startExam(false); currentExamIndex=studyState.examQuestions.length-1; nextExamQuestion();});
 ok(await ev(()=>!document.getElementById('exam-active-screen').classList.contains('hidden')),'aviso de preguntas sin responder antes de corregir');
 // 7 progress
 await ev(()=>switchTab('progreso'));
 const cards=await $t('#progress-summary-cards'); ok(/2\/12/.test(cards)&&/Mejor 2\.8/.test(cards),'Mi progreso muestra datos');
 await ev(()=>{document.getElementById('student-alias-input').value='2B-07';saveStudentAlias();downloadProgressReport();});
 await new Promise(r=>setTimeout(r,1500));
 const rep=fs.readdirSync('dl').find(f=>f.startsWith('informe_'));
 ok(!!rep,'informe descargado: '+rep);
 // 8 reload persistence
 await page.reload({waitUntil:'networkidle0'});
 ok((await ev(()=>studyState.hasContent&&studyState.concepts.length))===12,'tras recargar se recupera el temario');
 ok((await ev(()=>masteredCards.length))===2 && (await ev(()=>examHistory.length))>=2,'tras recargar se recupera el progreso');
 // 9 teacher
 await ev(()=>switchTab('profesor'));
 const inp=await page.$('#teacher-reports-input'); await inp.uploadFile(path.resolve('dl',rep));
 await new Promise(r=>setTimeout(r,800));
 ok(/2B-07/.test(await $t('#teacher-table-container')),'vista profesor muestra el informe');
 ok(/%/.test(await $t('#teacher-blocks-container')),'vista profesor agrega bloques');
 // 10 editor robustness
 await ev(()=>{openEditorModal(); switchEditorSubtab('defs'); draftDefinitions[0].template='plantilla sin marcador'; saveEditorChanges(); switchTab('definiciones');});
 ok(await ev(()=>studyState.definitions[0].template.includes('{0}')),'editor: marcador de hueco restaurado');
 // 11 XSS via JSON import
 fs.writeFileSync('fixtures/evil.json',JSON.stringify({subjectTitle:'<img src=x onerror="window.__pwn=1">',rawText:'',concepts:[{id:1,blockId:1,blockTitle:'<b onmouseover=alert(1)>B</b>',term:'<img src=x onerror="window.__pwn=1">',definition:'definicion <script>window.__pwn=1</script> larga'},{id:2,blockId:1,term:'b2',definition:'otra definicion suficientemente larga'}],definitions:[{id:'1);window.__pwn=1;//',blanks:[{display:'x'}],template:'{0}'}]}));
 await ev(()=>switchTab('cargar'));
 const up=await page.$('#file-upload-input'); await up.uploadFile(path.resolve('fixtures/evil.json'));
 await new Promise(r=>setTimeout(r,800));
 for (const t of ['apuntes','flashcards','definiciones','abiertas','examen','progreso']) await ev((t)=>switchTab(t),t);
 ok(await ev(()=>studyState.subjectTitle.startsWith('<img'))&&!(await ev(()=>window.__pwn)),'JSON malicioso importado sin ejecutar código');
 // 12 DOCX
 await ev(()=>{document.getElementById('subject-title-input').value='';switchTab('cargar');});
 await up.uploadFile(path.resolve('fixtures/celula.docx'));
 await page.waitForFunction(()=>studyState.subjectTitle==='Celula'||studyState.concepts.some(c=>c.term==='Mitocondria'),{timeout:30000}).catch(()=>{});
 ok(await ev(()=>studyState.concepts.some(c=>c.term==='Mitocondria')),'DOCX importado: '+(await ev(()=>studyState.concepts.map(c=>c.term).join('|'))));
 // 13 PDF
 await ev(()=>{document.getElementById('subject-title-input').value='';});
 await up.uploadFile(path.resolve('fixtures/revolucion.pdf'));
 await page.waitForFunction(()=>studyState.concepts.some(c=>/Bastilla/.test(c.term)),{timeout:60000}).catch(()=>{});
 ok(await ev(()=>studyState.concepts.some(c=>/Bastilla/.test(c.term))),'PDF importado: '+(await ev(()=>studyState.concepts.map(c=>c.term).join('|'))));
 ok(await ev(()=>studyState.sequences.some(s=>s.steps.join('|')==='Monarquía constitucional|República jacobina|Directorio|Consulado') && studyState.blocks[0].title==='TEMA 3: LA REVOLUCIÓN FRANCESA'),'PDF: secuencia detectada '+(await ev(()=>JSON.stringify(studyState.sequences.map(s=>s.steps)))));
 // 14 OCR image
 await ev(()=>{document.getElementById('subject-title-input').value='';document.getElementById('notes-textarea').value='';});
 await up.uploadFile(path.resolve('fixtures/foto_apuntes.png'));
 await page.waitForFunction(()=>document.getElementById('notes-textarea').value.length>30,{timeout:180000}).catch(()=>{});
 const ocr=await ev(()=>document.getElementById('notes-textarea').value);
 ok(/Fotos[ií]ntesis/i.test(ocr)&&/Clorofila/i.test(ocr),'OCR de foto: '+JSON.stringify(ocr.slice(0,160)));
 await ev(()=>processNotesAndGenerate());
 ok(await ev(()=>studyState.concepts.length>=3),'OCR -> conceptos: '+(await ev(()=>studyState.concepts.map(c=>c.term).join('|'))));
 // 15 wipe data
 await ev(()=>{handleWipeAllData();}); await Promise.all([page.waitForNavigation({waitUntil:'networkidle0'}), ev(()=>handleWipeAllData())]);
 ok(await ev(()=>Object.keys(localStorage).filter(k=>k.startsWith('sm_')).length===0 && !studyState.hasContent && userXP===0),'borrar todos mis datos');
 const realErrors=errors.filter(e=>!/cdn\.tailwindcss\.com should not be used in production/.test(e));
 ok(realErrors.length===0,'sin errores JS en consola '+JSON.stringify(realErrors));
 await page.screenshot({path:'screenshot_final.png'});
 await browser.close();
})().catch(e=>{console.error('E2E CRASH',e);process.exit(2);});
