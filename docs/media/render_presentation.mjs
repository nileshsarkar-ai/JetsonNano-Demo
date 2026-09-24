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
text(s,'Local AI on\nJetson Nano',70,190,650,190,66,ink,true);
s.images.add({blob:new Uint8Array(await fs.readFile(new URL('./nano-product.jpeg',import.meta.url))),contentType:'image/jpeg',fit:'contain',alt:'NVIDIA Jetson Nano Developer Kit',position:{left:640,top:191,width:580,height:360}});
text(s,'Jetson Nano 4GB\nUbuntu 18.04.6 / JetPack 4\nPython 3.11',77,444,530,140,26,muted);
s.speakerNotes.textFrame.setText('Board configuration supplied by the user: L4T R32.7.6, CUDA 10.2, Python 3.11.3 and system Python 3.6.9. Camera bindings may use system Python. Image source: https://www.nvidia.com/en-us/autonomous-machines/embedded-systems/jetson-nano/product-development/ . Product reference photograph, not a photo of the user’s board.');
}
{
const s=page('Setup','Run in a terminal on the Nano.','');
const lines=['git clone https://github.com/nileshsarkar-ai/JetsonNano-Demo.git','cd JetsonNano-Demo','bash scripts/run_demo.sh --storage','bash scripts/run_demo.sh --check','bash scripts/run_demo.sh --setup-only','bash scripts/run_demo.sh'];
lines.forEach((line,i)=>text(s,line,76,235+i*62,1135,50,i===0?24:28,i===5?green:ink,i===5,'Courier New'));
}
{
const s=page('Text Conversation','Menu 3','');
text(s,'“Why does a steel ship float?”',78,225,1110,100,49,ink,true);
text(s,'Follow-up prompts',80,370,1060,45,24,green,true);
text(s,'“Explain it using an everyday analogy.”\n“Now explain it in two sentences.”',80,425,1090,130,34,ink);
text(s,'SmolLM2-360M Instruct uses the preceding conversation.',80,576,1090,45,25,muted);
text(s,'/reset clears history.  /quit returns to the menu.',80,627,1090,38,23,muted);
}
{
const s=page('Camera Object Detection','Menu 4','');
text(s,'SSD-Mobilenet-v2',75,230,490,65,34,ink,true);
text(s,'Place everyday objects\nin the camera’s view.',78,328,490,95,31,muted);
text(s,'Move one object.\nTurn the book sideways.\nPartly hide the cup.',78,469,490,130,30,ink);
s.images.add({blob:new Uint8Array(await fs.readFile(new URL('./tabletop-scene.png',import.meta.url))),contentType:'image/png',fit:'contain',alt:'Illustrative tabletop with cup, bottle and book',position:{left:575,top:220,width:650,height:430}});
text(s,'Illustrative scene',815,647,390,32,19,muted);
s.speakerNotes.textFrame.setText('AI-generated illustrative scene, not a camera capture or measured detection result. Detection labels and bounding boxes come from labs/vision.py during live execution. Ask students which objects remain detectable after rotation or partial occlusion; no accuracy outcome is predetermined.');
}
{
const s=page('Camera-Guided Object Hunt','Menu 5','');
text(s,'1   The language model proposes objects to find.',78,235,1100,85,31,ink);
text(s,'2   Arrange the objects in view and press Enter to scan.',78,355,1100,85,31,ink);
text(s,'3   Camera detections update the found and remaining lists.',78,475,1100,100,31,ink);
text(s,'The hunt shares the conversation model and object detector.',78,610,1100,45,24,muted);
s.speakerNotes.textFrame.setText('Implementation: labs/camera_tasks.py and CompactMenu in scripts/demo_menu.py. Quest targets come from a constrained COCO-label list. Code validates generated plans and scores detector observations. At most three scans. Detector and LLM run sequentially. This is a detector-plus-language-model application, not a trained vision-language-action robot policy. Physical Nano execution still needs rehearsal.');
}
{
const s=page('Models and Execution','','');
text(s,'Text',75,230,300,55,32,ink,true);
text(s,'SmolLM2-360M Q4\n258 MiB model file\nCPU inference',420,230,740,160,30,muted);
text(s,'Camera',75,460,300,55,32,ink,true);
text(s,'SSD-Mobilenet-v2\nTensorRT on the Nano GPU\nCamera and text stages run sequentially',420,460,760,165,30,muted);
}
{
const s=page('Menu Controls','','');
const rows=[['1','Prepare models and dependencies'],['2','Check board status'],['3 / 4 / 5','Run a demonstration'],['6','Inspect storage usage'],['7','Open this presentation'],['0','Exit']];
rows.forEach((row,i)=>{text(s,row[0],80,205+i*67,225,50,29,green,true);text(s,row[1],350,205+i*67,830,50,29,ink);});
text(s,'Ctrl+C cancels a demo and returns to the menu.',80,625,1090,42,24,muted);
}
const draft=root+'/candidate.pptx';await(await PresentationFile.exportPptx(p)).save(draft);
const result=await finalizePresentation({workspaceDir:root,candidatePath:draft,finalPath:root+'/output/Jetson_Nano_Visual_Demos.pptx',pythonExecutable:process.env.RUNTIME_PYTHON,integrityValidatorPath:skill+'/container_tools/inspect_presentation_package_integrity.py',layoutValidatorPath:skill+'/container_tools/inspect_presentation_layout_geometry.py',layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit'],requiredNativeTableOwnerSlides:[],fontPolicy:{basis:'design',families:[font,'Courier New']},explicitTotalSlideCount:7,verifyArtifactToolImport:true,receiptPath:root+'/validation.json'});
console.log(JSON.stringify(result));
