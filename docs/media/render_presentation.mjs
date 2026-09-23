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
function page(title,subtitle,footer){const s=p.slides.add();s.background.fill='#FFFFFF';text(s,title,66,48,1150,80,48,ink,true);if(subtitle) text(s,subtitle,70,140,1140,65,26,muted);text(s,String(p.slides.items.length).padStart(2,'0'),1174,651,55,35,18,green,true);s.speakerNotes.textFrame.setText('Code and menu: https://github.com/nileshsarkar-ai/JetsonNano-Demo/tree/master\nScope and names: docs/EXPERIMENTS.md. Presenter notes: Physical Nano execution unverified. Software tests use mocks. Models may hallucinate; prompt separation and self-critique are not security or accuracy guarantees. Check against visible source facts. Camera projects use object detections plus text generation, not a vision-language model. Default setup does not need audio or external training. Rehearse power, cooling, camera capture, latency and answer quality on the actual board. This is the current local programme, not the historical 72-topic idea catalogue.');return s;}
function table(s,rows,y=220,height=392){const values=[['MENU','EXPERIMENT','FUNCTION'],...rows];const t=s.tables.add({rows:values.length,columns:3,left:70,top:y,width:1140,height,columnWidths:[85,450,605],values});t.styleOptions={headerRow:false,bandedRows:false};t.borders.assign({fill:'#E0E8DC',width:.6});t.cells.block({row:0,column:0,rowCount:values.length,columnCount:3}).assign({margins:{top:4,bottom:4,left:10,right:10}});for(let r=0;r<values.length;r++){t.rows[r].height=r===0?42:(height-42)/rows.length;for(let c=0;c<3;c++){const cell=t.getCell(r,c);cell.fill=r===0?'#EFF6E9':'#FFFFFF';cell.text.style={typeface:font,fontSize:r===0?18:23,color:c===0?green:ink,bold:r===0||c===0,autoFit:'none'};}}return t;}
{
const s=p.slides.add();s.background.fill='#FFFFFF';
text(s,'Language Models\non Jetson Nano',70,190,650,190,66,ink,true);
s.images.add({blob:new Uint8Array(await fs.readFile(new URL('./nano-product.jpeg',import.meta.url))),contentType:'image/jpeg',fit:'contain',alt:'NVIDIA photograph of the original Jetson Nano Developer Kit',position:{left:640,top:191,width:580,height:360}});
text(s,'Jetson Nano 4GB\nJetPack 4 / Ubuntu 18.04\nPython 3.6',77,444,530,140,26,muted);
s.speakerNotes.textFrame.setText('Image: NVIDIA, https://www.nvidia.com/en-us/autonomous-machines/embedded-systems/jetson-nano/product-development/\nAsset: https://www.nvidia.com/content/nvidiaGDC/us/en_US/autonomous-machines/embedded-systems/jetson-nano/product-development/_jcr_content/root/responsivegrid/nv_container_1169488117/nv_container_copy/nv_image.coreimg.jpeg/1710770678070/jetson-nano-2560x1440.jpeg\nPhoto is a product reference, not this user’s board. Code scope: docs/EXPERIMENTS.md in https://github.com/nileshsarkar-ai/JetsonNano-Demo. No physical-board performance claim.');
}
{
const s=page('Setup','Run in a terminal on the Nano.','');
text(s,'git clone https://github.com/nileshsarkar-ai/JetsonNano-Demo.git',76,242,1130,55,25,ink,false,'Courier New');
text(s,'cd JetsonNano-Demo',76,308,1130,55,27,ink,false,'Courier New');
text(s,'bash scripts/run_demo.sh',76,374,1130,65,34,green,true,'Courier New');
text(s,'1  Install dependencies and models',78,500,1100,50,27,ink);
text(s,'2  Check board status',78,555,1100,50,27,ink);
}
{
const s=page('Text Conversations','','');
text(s,'Menu 29',75,224,510,40,22,green,true);
text(s,'Socratic Study Partner',75,282,535,95,38,ink,true);
text(s,'Discuss a topic through successive\nquestions. Each reply uses the\nprevious conversation.',78,393,515,135,28,muted);
text(s,'Example topic: Why do objects float?',78,562,520,50,25,green,true);
text(s,'Menu 30',696,224,510,40,22,green,true);
text(s,'Mystery Character\nInterview',696,282,510,100,38,ink,true);
text(s,'Ask a fictional character questions\nand use the answers to identify\ntheir profession.',699,409,510,127,28,muted);
text(s,'Use /guess followed by your answer.',699,562,500,60,25,green,true);
}
{
const s=page('Tools and Document Retrieval','','');
table(s,[['15','Mission Control: Tool-Planning Assistant','Select read-only tools and summarize the returned data.'],['16','Document Detective: Answers with Evidence','Answer questions from retrieved exhibit passages.'],['9','Persistent Memory Assistant','Save explicit facts and retrieve them in later sessions.'],['8','Class Notes Retrieval and Grounded Answers','Index text documents and generate answers from retrieved passages.'],['3','Offline Conversation Assistant','Generate responses using the preceding conversation.']],214,405);
}
{
const s=page('Tokenization and Generation','','');
table(s,[['4','Ask the Local Language Model','Generate a response to a single prompt.'],['5','Tokenization Microscope','Inspect token IDs for text, code and symbols.'],['6','Structured Information Extraction','Turn text into constrained JSON fields.'],['14','Sampling Playground','Compare greedy output with two seeded creative samples.'],['22','Prompt Design Studio','Compare a minimal prompt with explicit audience instructions.'],['23','Few-Shot Pattern Learner','Compare classification with zero examples and four examples.']],206,422);
}
{
const s=page('Text Generation and Processing','','');
table(s,[['17','Story Director: Audience-Controlled Fiction','Generate a story and continue it using a supplied plot change.'],['10','TinyStories Generator','Generate text with the TinyStories model.'],['24','Message Triage Desk','Validate a model-proposed category before routing.'],['25','Summary Fact Checker','Summarize a passage and compare it with a second model critique.'],['7','Calculator Tool Assistant','Evaluate a validated arithmetic expression using a calculator tool.']],214,405);
}
{
const s=page('Prompt Injection and Context','','');
text(s,'Menu 26',74,224,260,35,21,green,true);text(s,'Prompt Injection Defense Lab',74,266,1095,49,34,ink,true);text(s,'Compare an injected document with and without instruction separation.',77,318,1120,50,25,muted);
text(s,'Menu 27',74,393,260,35,21,green,true);text(s,'Answer or Abstain: Hallucination Challenge',74,433,1100,49,34,ink,true);text(s,'Ask one answerable question and one whose answer is deliberately missing.',77,484,1120,50,25,muted);
text(s,'Menu 28: Context Memory Challenge',75,565,1100,48,28,ink,true);
text(s,'Recall the same fact as irrelevant context grows.',77,608,1050,35,23,muted);
}
{
const s=page('Camera Applications','Keep the camera fixed between observations.','');
table(s,[['18','Scene Memory Detective','Compare object classes, counts and positions across two observations.'],['19','AI Visual Scavenger Hunt','Generate an object-finding task and score detections against its targets.'],['20','Camera Change Journal','Record three observations and summarize the detected changes.'],['13','Camera Perception Lab','Run detection, classification, pose estimation or segmentation.']],222,348);
text(s,'Camera setup: menu 13, then install.',76,594,1090,48,25,muted);
}
{
const s=page('Performance and Evaluation','','');
text(s,'Menu 11',75,233,340,35,22,green,true);text(s,'Language Model\nPerformance Benchmark',75,285,540,100,35,ink,true);text(s,'Run the upstream model benchmark\nand inspect its saved measurements.',77,424,510,100,27,muted);
text(s,'Menu 12',690,233,390,35,22,green,true);text(s,'Reproducible\nPrompt Evaluation',690,285,510,100,35,ink,true);text(s,'Supply JSONL questions and reference\nanswers. Inspect exact matches,\nresponses and latency.',692,424,500,130,27,muted);
}
{
const s=page('Menu Controls','','');
text(s,'Run',75,220,280,50,32,ink,true);text(s,'Enter the experiment number.',360,222,820,55,28,muted);
text(s,'Cancel',75,320,280,50,32,ink,true);text(s,'Ctrl+C stops the active demo and returns to the menu.',360,322,820,80,28,muted);
text(s,'Exit',75,440,280,50,32,ink,true);text(s,'Enter 0.',360,442,820,55,28,muted);
text(s,'Sequence',75,540,280,50,32,ink,true);text(s,'Enter 21 to run the prepared demonstrations.',360,542,820,80,28,muted);
}
const draft=root+'/candidate.pptx';await(await PresentationFile.exportPptx(p)).save(draft);
const tables=[4,5,6,8];
const result=await finalizePresentation({workspaceDir:root,candidatePath:draft,finalPath:root+'/output/Jetson_Nano_Local_AI_Clean.pptx',pythonExecutable:process.env.RUNTIME_PYTHON,integrityValidatorPath:skill+'/container_tools/inspect_presentation_package_integrity.py',layoutValidatorPath:skill+'/container_tools/inspect_presentation_layout_geometry.py',layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit',...tables.flatMap(n=>['--require-native-table-slide',String(n)])],requiredNativeTableOwnerSlides:tables,fontPolicy:{basis:'design',families:[font,'Courier New']},explicitTotalSlideCount:10,verifyArtifactToolImport:true,receiptPath:root+'/validation.json'});
console.log(JSON.stringify(result));
