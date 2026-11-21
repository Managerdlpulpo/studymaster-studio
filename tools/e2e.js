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
 // 9 teacher: acceso oculto con PIN
 const PIN='t'+Math.random().toString(36).slice(2,10); const PIN2='n'+Math.random().toString(36).slice(2,10);
 const vis=(sel)=>ev((s)=>{const e=document.querySelector(s); return !!e && e.offsetParent!==null && !e.closest('.hidden');},sel);
 const modalOpen=()=>ev(()=>!document.getElementById('teacher-pin-modal').classList.contains('hidden'));
 const pinMsg=()=>ev(()=>document.getElementById('pin-message').innerText);
 const typePin=async(main,confirm,current)=>{ await ev((m,c,cu)=>{document.getElementById('pin-field-main').value=m||'';document.getElementById('pin-field-confirm').value=c||'';document.getElementById('pin-field-current').value=cu||'';},main,confirm,current); await click('#pin-submit-btn'); await new Promise(r=>setTimeout(r,900)); };
 ok(!(await page.$('#tab-btn-profesor')),'pestaña Profesor no está en la navegación');
 const navTxt=await $t('#nav-tabs'); ok(!/profesor/i.test(navTxt),'la navegación no menciona al profesor');
 const visibleText=await ev(()=>document.body.innerText); ok(!/pesta[ñn]a.{0,6}profesor|vista del profesor/i.test(visibleText),'ningún texto visible delata la vista del profesor');
 await ev(()=>switchTab('profesor')); ok(!(await vis('#tab-profesor')) && await modalOpen(),'switchTab(profesor) sin PIN no muestra la vista (pide PIN)');
 await click('#pin-title + button'); ok(!(await modalOpen()),'el cuadro se puede cerrar');
 for(let i=0;i<4;i++) await page.click('#app-brand h1'); ok(!(await modalOpen()),'4 toques en el logo no abren nada');
 await page.click('#app-brand h1'); ok(await modalOpen() && (await $t('#pin-title-text'))==='Crear PIN de acceso','5 toques en el logo abren el cuadro (primer uso: crear PIN)');
 await typePin('abc','abc'); ok(/al menos 6/.test(await pinMsg()),'PIN corto rechazado');
 await typePin(PIN,PIN+'x'); ok(/no coinciden/.test(await pinMsg()),'confirmación distinta rechazada');
 await typePin(PIN,PIN); ok(await vis('#tab-profesor') && !(await modalOpen()),'PIN creado: acceso a la vista profesor');
 const stored=await ev(()=>localStorage.getItem('sm_teacher_pin')); ok(stored && !stored.includes(PIN) && /PBKDF2-SHA256/.test(stored) && /"salt"/.test(stored),'solo se guarda hash PBKDF2 con sal');
 await click('#teacher-exit-btn'); ok(!(await vis('#tab-profesor')),'«Salir del modo profesor» oculta la vista');
 await page.keyboard.down('Control'); await page.keyboard.down('Shift'); await page.keyboard.press('KeyP'); await page.keyboard.up('Shift'); await page.keyboard.up('Control');
 ok(await modalOpen() && (await $t('#pin-title-text'))==='Acceso restringido','Ctrl+Shift+P abre el cuadro del PIN');
 await typePin('incorrecto1'); ok(/incorrecto/i.test(await pinMsg()) && !(await vis('#tab-profesor')),'PIN erróneo rechazado');
 await typePin(PIN); ok(await vis('#tab-profesor'),'PIN correcto da acceso');
 const inp=await page.$('#teacher-reports-input'); await inp.uploadFile(path.resolve('dl',rep));
 await new Promise(r=>setTimeout(r,800));
 ok(/2B-07/.test(await $t('#teacher-table-container')),'vista profesor muestra el informe');
 ok(/%/.test(await $t('#teacher-blocks-container')),'vista profesor agrega bloques');
 // cambiar PIN
 await click('#teacher-change-pin-btn'); await typePin(PIN2,PIN2,'malo123'); ok(/actual no es correcto/.test(await pinMsg()),'cambiar PIN: PIN actual erróneo rechazado');
 await typePin(PIN2,PIN2,PIN); ok(!(await modalOpen()),'PIN cambiado');
 await click('#teacher-exit-btn'); await ev(()=>openTeacherPinDialog()); await typePin(PIN); ok(!(await vis('#tab-profesor')),'el PIN antiguo ya no vale');
 await typePin(PIN2); ok(await vis('#tab-profesor'),'el PIN nuevo da acceso');
 // bloqueo tras 5 fallos
 await click('#teacher-exit-btn'); await ev(()=>openTeacherPinDialog());
 for(let i=0;i<5;i++) await typePin('fallo'+i+'xx');
 ok(/espera/i.test(await pinMsg()),'tras 5 fallos se impone una espera: '+(await pinMsg()));
 await typePin(PIN2); ok(!(await vis('#tab-profesor')) && /Demasiados intentos/.test(await pinMsg()),'durante la espera ni el PIN correcto entra');
 const lock=await ev(()=>JSON.parse(localStorage.getItem('sm_teacher_lock'))); ok(lock.fails===5 && lock.until-Date.now()>20000,'espera de ~30 s registrada');
 await ev(()=>localStorage.setItem('sm_teacher_lock',JSON.stringify({fails:5,until:Date.now()-1}))); // simula que pasó el tiempo
 await typePin(PIN2); ok(await vis('#tab-profesor'),'pasada la espera, el PIN correcto entra');
 // recarga vuelve a ocultar
 await page.reload({waitUntil:'networkidle0'});
 ok(!(await vis('#tab-profesor')) && !(await modalOpen()) && !(await page.$('#tab-btn-profesor')) && !(await ev(()=>teacherUnlocked)),'tras recargar, el modo profesor vuelve a estar oculto y bloqueado');
 ok(!(await ev(()=>{switchTab('profesor'); return !document.getElementById('tab-profesor').classList.contains('hidden');})),'tras recargar, switchTab(profesor) no entra sin PIN');
 // olvidé el PIN: restablecer borra solo datos de profesor
 await click('#pin-forgot-btn'); ok((await $t('#pin-title-text'))==='Acceso restringido','un clic en «olvidé el PIN» solo pide confirmación');
 await click('#pin-forgot-btn'); ok((await $t('#pin-title-text'))==='Restablecer acceso','segundo clic: cuadro de restablecer');
 await click('#pin-submit-btn'); await new Promise(r=>setTimeout(r,300));
 ok((await $t('#pin-title-text'))==='Crear PIN de acceso' && !(await ev(()=>localStorage.getItem('sm_teacher_pin'))) && !!(await ev(()=>localStorage.getItem('sm_current_deck'))),'restablecer borra solo el PIN (temario y progreso intactos)');
 await typePin(PIN,PIN); ok(await vis('#tab-profesor'),'se puede crear un PIN nuevo tras restablecer');
 await click('#teacher-exit-btn');
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
