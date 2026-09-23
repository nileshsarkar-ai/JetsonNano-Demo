import fs from 'node:fs/promises';
import {Presentation, PresentationFile} from '@oai/artifact-tool';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const skill=process.env.PRESENTATION_SKILL_DIR;
if (!skill || !process.argv[2]) throw new Error('Set PRESENTATION_SKILL_DIR and RUNTIME_PYTHON; pass a fresh output workspace directory.');
const {resolvePresentationFont,finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
const root=path.resolve(process.argv[2]);
const font=resolvePresentationFont({fontFamily:'Arial'});
await fs.mkdir(root+'/output',{recursive:true});
const p=Presentation.create({slideSize:{width:1280,height:720}});
const ink='#19332A',green='#397718',muted='#52635B';
function text(s,value,x,y,w,h,size=28,color=ink,bold=false,family=font){const q=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});q.text=value;q.text.style={typeface:family,fontSize:size,color,bold,autoFit:'none'};return q;}
function page(title,subtitle,footer){const s=p.slides.add();s.background.fill='#FFFFFF';text(s,title,66,48,1150,80,48,ink,true);text(s,subtitle,70,140,1140,65,26,muted);text(s,footer,70,650,1080,44,18,muted);text(s,String(p.slides.items.length).padStart(2,'0'),1174,651,55,35,18,green,true);s.speakerNotes.textFrame.setText('Code and menu: https://github.com/nileshsarkar-ai/JetsonNano-Demo/tree/master\nScope and names: docs/EXPERIMENTS.md. Presenter notes: Physical Nano execution unverified. Software tests use mocks. Models may hallucinate; prompt separation and self-critique are not security or accuracy guarantees. Check against visible source facts. Camera projects use object detections plus text generation, not a vision-language model. Default setup does not need audio or external training. Rehearse power, cooling, camera capture, latency and answer quality on the actual board. This is the current local programme, not the historical 72-topic idea catalogue.');return s;}
function table(s,rows,y=220,height=392){const values=[['MENU','EXPERIMENT','WHAT STUDENTS DO'],...rows];const t=s.tables.add({rows:values.length,columns:3,left:70,top:y,width:1140,height,columnWidths:[85,450,605],values});t.styleOptions={headerRow:false,bandedRows:false};t.borders.assign({fill:'#E0E8DC',width:.6});t.cells.block({row:0,column:0,rowCount:values.length,columnCount:3}).assign({margins:{top:4,bottom:4,left:10,right:10}});for(let r=0;r<values.length;r++){t.rows[r].height=r===0?42:(height-42)/rows.length;for(let c=0;c<3;c++){const cell=t.getCell(r,c);cell.fill=r===0?'#EFF6E9':'#FFFFFF';cell.text.style={typeface:font,fontSize:r===0?18:23,color:c===0?green:ink,bold:r===0||c===0,autoFit:'none'};}}return t;}
{
const s=p.slides.add();s.background.fill='#FFFFFF';
text(s,'LOCAL AI / CLASSROOM EXPERIMENTS',72,68,1120,40,21,green,true);
text(s,'Local AI on\nJetson Nano',70,172,630,190,76,ink,true);
text(s,'Explore language, memory and vision\nwith local models and a camera.',76,390,570,94,29,muted);
text(s,'27',72,522,150,100,80,green,true);text(s,'named experiments\none Bash launcher',228,544,360,80,28,ink);
s.images.add({blob:new Uint8Array(await fs.readFile(new URL('./nano-product.jpeg',import.meta.url))),contentType:'image/jpeg',fit:'contain',alt:'NVIDIA photograph of the original Jetson Nano Developer Kit',position:{left:640,top:191,width:580,height:360}});
text(s,'Original Nano 4GB, JetPack 4, Python 3.6',75,660,900,32,19,muted);
s.speakerNotes.textFrame.setText('Image: NVIDIA, https://www.nvidia.com/en-us/autonomous-machines/embedded-systems/jetson-nano/product-development/\nAsset: https://www.nvidia.com/content/nvidiaGDC/us/en_US/autonomous-machines/embedded-systems/jetson-nano/product-development/_jcr_content/root/responsivegrid/nv_container_1169488117/nv_container_copy/nv_image.coreimg.jpeg/1710770678070/jetson-nano-2560x1440.jpeg\nPhoto is a product reference, not this user’s board. Code scope: docs/EXPERIMENTS.md in https://github.com/nileshsarkar-ai/JetsonNano-Demo. No physical-board performance claim.');
}
{
const s=page('Setup and the experiment menu','Run these commands in a terminal on the Nano.','Prepare once, then choose a local AI experiment by its menu number.');
text(s,'git clone https://github.com/nileshsarkar-ai/JetsonNano-Demo.git',76,242,1130,55,25,ink,false,'Courier New');
text(s,'cd JetsonNano-Demo',76,308,1130,55,27,ink,false,'Courier New');
text(s,'bash scripts/run_demo.sh',76,374,1130,65,34,green,true,'Courier New');
text(s,'Prepare',78,500,270,50,29,ink,true);text(s,'Choose 1 before class.',78,551,300,54,24,muted);
text(s,'Check',453,500,270,50,29,ink,true);text(s,'Choose 2 for board status.',453,551,320,54,24,muted);
text(s,'Explore',844,500,330,50,29,ink,true);text(s,'Select any experiment number.',844,551,350,65,24,muted);
}
{
const s=page('Conversations that involve the class','Students take the next turn and shape what happens.','Type /quit to return to the menu. Each conversation uses the earlier turns.');
text(s,'Experiment 29',75,224,510,40,22,green,true);
text(s,'Socratic Study Partner',75,282,535,95,38,ink,true);
text(s,'Choose a topic. Answer one guiding\nquestion at a time and explain\nyour reasoning.',78,393,515,135,28,muted);
text(s,'Try: Why do objects float?',78,562,520,50,25,green,true);
text(s,'Experiment 30',696,224,510,40,22,green,true);
text(s,'Mystery Character\nInterview',696,282,510,100,38,ink,true);
text(s,'Interview a fictional character.\nCollect clues, then guess\ntheir profession.',699,409,510,127,28,muted);
text(s,'Use /guess followed by your answer.',699,562,500,60,25,green,true);
}
{
const s=page('Assistants with visible evidence','Inspect what the model knows, retrieves and calls.','Read-only tools. Explicit local memory. BM25 retrieval over your own documents.');
table(s,[['15','Mission Control: Tool-Planning Assistant','Give a mission, inspect its tool plan, then check the evidence.'],['16','Document Detective: Answers with Evidence','Ask the exhibit brief a question and inspect source passages.'],['9','Persistent Memory Assistant','Store a fictional preference and reuse it in a later session.'],['8','Class Notes Retrieval and Grounded Answers','Index notes, retrieve passages and question the answer.'],['3','Offline Conversation Assistant','Hold a short local conversation and inspect its memory.']],214,405);
}
{
const s=page('Language under the microscope','Change the input or decoding settings and compare the response.','Ask the class to predict how each change will affect the answer.');
table(s,[['4','Ask the Local Language Model','Test a short question with the configured small model.'],['5','Tokenization Microscope','Compare how words, code and symbols split into tokens.'],['6','Structured Information Extraction','Turn text into constrained JSON fields.'],['14','Sampling Playground','Compare greedy output with two seeded creative samples.'],['22','Prompt Design Studio','Compare a minimal prompt with explicit audience instructions.'],['23','Few-Shot Pattern Learner','Compare classification with zero examples and four examples.']],206,422);
}
{
const s=page('Creativity and practical text tasks','Let students supply a twist, a message or a passage.','Invite students to bring a story twist, a classroom message or a short passage.');
table(s,[['17','Story Director: Audience-Controlled Fiction','Choose a setting, then change the generated story with a twist.'],['10','TinyStories Generator','Continue a story with a small dedicated language model.'],['24','Message Triage Desk','Validate a model-proposed category before routing.'],['25','Summary Fact Checker','Read the source, summary and separate model critique.'],['7','Calculator Tool Assistant','Inspect how a tool performs arithmetic for a language model.']],214,405);
}
{
const s=page('Memory, uncertainty and trust','Explore how an assistant handles instructions, missing facts and memory.','Challenge the assistant, inspect its answer, and compare it with the source facts.');
text(s,'Experiment 26',74,224,260,35,21,green,true);text(s,'Prompt Injection Defense Lab',74,266,1095,49,34,ink,true);text(s,'Compare an injected document with and without instruction separation.',77,318,1120,50,25,muted);
text(s,'Experiment 27',74,393,260,35,21,green,true);text(s,'Answer or Abstain: Hallucination Challenge',74,433,1100,49,34,ink,true);text(s,'Ask one answerable question and one whose answer is deliberately missing.',77,484,1120,50,25,muted);
text(s,'Experiment 28: Context Memory Challenge',75,565,1100,48,28,ink,true);
text(s,'Recall the same fact as irrelevant context grows.',77,608,1050,35,23,muted);
}
{
const s=page('Camera projects beyond detection','Keep the camera fixed. Move ordinary objects in the scene.','Run 13 → install and rehearse detection first. Vision and the language model run sequentially.');
table(s,[['18','Scene Memory Detective','Observe the desk, change something, then explain the measured difference.'],['19','AI Visual Scavenger Hunt','Arrange objects for an AI-generated quest; detector evidence determines the score.'],['20','Camera Change Journal','Capture three observations and summarize the recorded changes.'],['13','Camera Perception Lab','Explore detection, classification, pose or segmentation.']],222,348);
text(s,'Try it with a cup, a book or a bottle.',76,587,1090,48,30,green,true);
}
{
const s=page('Model performance and evaluation','Inspect model responses and measure runtime.','Compare the saved outputs and timings from your chosen workload.');
text(s,'Experiment 11',75,233,340,35,22,green,true);text(s,'Language Model\nPerformance Benchmark',75,285,540,100,35,ink,true);text(s,'Run the upstream model benchmark\nand inspect its saved measurements.',77,424,510,100,27,muted);
text(s,'Experiment 12',690,233,390,35,22,green,true);text(s,'Reproducible\nPrompt Evaluation',690,285,510,100,35,ink,true);text(s,'Supply JSONL questions and reference\nanswers. Inspect exact matches,\nresponses and latency.',692,424,500,130,27,muted);
}
{
const s=page('A classroom sequence','Choose a few experiments and let the audience steer.','Start with a conversation, invite a plot twist, then bring the camera into the demonstration.');
text(s,'Start with an assistant',75,229,1080,50,34,ink,true);text(s,'15 Mission Control or 17 Story Director gives students a task to direct.',78,283,1120,50,26,muted);
text(s,'Introduce the camera',75,363,1080,50,34,ink,true);text(s,'18 Scene Memory turns a small change on the desk into evidence to discuss.',78,417,1120,50,26,muted);
text(s,'Recover and repeat',75,497,1080,50,34,ink,true);text(s,'Ctrl+C returns to the menu. 0 exits. 21 runs the prepared demonstration sequence.',78,551,1120,65,25,muted);
}
const draft=root+'/candidate.pptx';await(await PresentationFile.exportPptx(p)).save(draft);
const tables=[4,5,6,8];
const result=await finalizePresentation({workspaceDir:root,candidatePath:draft,finalPath:root+'/output/Jetson_Nano_Local_AI_Light-v4.pptx',pythonExecutable:process.env.RUNTIME_PYTHON,integrityValidatorPath:skill+'/container_tools/inspect_presentation_package_integrity.py',layoutValidatorPath:skill+'/container_tools/inspect_presentation_layout_geometry.py',layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit',...tables.flatMap(n=>['--require-native-table-slide',String(n)])],requiredNativeTableOwnerSlides:tables,fontPolicy:{basis:'design',families:[font,'Courier New']},explicitTotalSlideCount:10,verifyArtifactToolImport:true,receiptPath:root+'/validation-v4.json'});
console.log(JSON.stringify(result));
