const fs=require('fs');
const html=fs.readFileSync(process.argv[2]||(__dirname+'/../index.html'),'utf8');let src=[...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].pop()[1];
// stub DOM
global.window={addEventListener(){}}; global.document={getElementById:()=>null,querySelectorAll:()=>[]};
global.localStorage={getItem:()=>null,setItem(){}};
const demo=src.match(/const demoText = `([\s\S]*?)`;/)[1];
eval(src+'\n;globalThis.__p=parseNotesEngine;');
const r=__p('Demo',demo);
console.log('blocks',r.blocks.map(b=>b.title));
console.log('concepts',r.concepts.map(c=>c.term+' | '+c.type));
console.log('sequences',r.sequences.map(s=>s.title+': '+s.steps.join(' > ')));
console.log('exam',r.examQuestions.length);
let leak=0;r.examQuestions.forEach(q=>{const m=q.q.match(/«(.+?)»/); if(m){const t=m[1].toLowerCase(); if(q.q.includes('describe correctamente')&&q.options[q.correct].toLowerCase().includes(t.split(' ')[0]))leak++; if(q.q.includes('corresponde esta descripción')&&m[1].toLowerCase().includes(q.options[q.correct].toLowerCase().split(' ')[0]))leak++;}});
console.log('leaks',leak);
r.examQuestions.slice(0,20).forEach(q=>console.log('-',q.q.slice(0,140),'\n   OK=',q.options[q.correct].slice(0,80)));
console.log('open seq q', r.openQuestions.filter(q=>q.question.includes('Enumera')).map(q=>q.id+' -> '+q.question.slice(0,30)));
