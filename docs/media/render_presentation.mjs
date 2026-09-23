import fs from 'node:fs/promises';
import {Presentation, PresentationFile} from '@oai/artifact-tool';
import {pathToFileURL} from 'node:url';
import path from 'node:path';
const skill=process.env.PRESENTATION_SKILL_DIR;
if (!skill || !process.argv[2]) throw new Error('Set PRESENTATION_SKILL_DIR and pass an output workspace directory. Use the bundled Node runtime and RUNTIME_NODE_MODULES.');
const {resolvePresentationFont, finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
const root=path.resolve(process.argv[2]);
await fs.mkdir(path.join(root,'presentation-build'),{recursive:true});
await fs.mkdir(path.join(root,'presentation-output'),{recursive:true});
const font=resolvePresentationFont({fontFamily:'Arial'});
const p=Presentation.create({slideSize:{width:1280,height:720}});
const pages=[
 ['Local AI on Jetson Nano','25 named experiments for a classroom\nOriginal Nano 4GB, JetPack 4, Python 3.6', ['Language models, evidence and memory','Interactive camera projects','One Bash launcher'], 'Nano and optional camera only. No external GPU, training, microphone or speaker.'],
 ['One command, named experiments','Run these commands in a terminal on the Nano', ['git clone https://github.com/nileshsarkar-ai/JetsonNano-Demo.git','cd JetsonNano-Demo','bash scripts/run_demo.sh','Setup: 1 prepares dependencies; 2 checks board resources'], 'Preparation needs Internet. Prepared inference is local. Select a numbered experiment after setup.'],
 ['Assistants with inspectable evidence','Students can inspect the information behind the answer', ['15  Mission Control: Tool-Planning Assistant','16  Document Detective: Answers with Evidence','9    Persistent Memory Assistant','8    Class Notes Retrieval and Grounded Answers','3    Offline Conversation Assistant'], 'Tools are read-only and validated. Memory stores explicit local facts. Retrieval uses lexical BM25.'],
 ['Language under the microscope','Change one input and compare the actual model outputs', ['4    Ask the Local Language Model','5    Tokenization Microscope','6    Structured Information Extraction','14  Sampling Playground','22  Prompt Design Studio','23  Few-Shot Pattern Learner'], 'Small models make mistakes. Outputs demonstrate behavior; they are not evidence of general accuracy.'],
 ['Creativity and useful text tasks','The audience controls the input', ['17  Story Director: Audience-Controlled Fiction','10  TinyStories Generator','24  Message Triage Desk: Validated JSON Routing','25  Summary Fact Checker','7    Calculator Tool Assistant'], 'The summary critique is another model response, not a factual guarantee. Triage sends no messages.'],
 ['Memory, uncertainty and trust','A wrong answer can become the most useful teaching moment', ['26  Prompt Injection Defense Lab','27  Answer or Abstain: Hallucination Challenge','28  Context Memory Challenge','Compare unprotected and separated instructions','Check recalled facts and missing-evidence responses'], 'Prompt separation is a demonstration, not a security guarantee. Reference facts are visible.'],
 ['Camera projects beyond detection','Keep the camera fixed; move ordinary objects in the scene', ['18  Scene Memory Detective','19  AI Visual Scavenger Hunt','20  Camera Change Journal','13  Camera Perception Lab and Installation','Perception modes: detection, classification, pose, segmentation'], 'Vision exits before the language model starts. These projects use detections, not a vision-language model.'],
 ['Performance and evaluation','Measure the actual workload on the actual board', ['11  Language Model Performance Benchmark','12  Reproducible Prompt Evaluation','Use your own JSONL questions and reference answers','Inspect model output, latency and saved logs'], 'No Nano performance or accuracy results are claimed. Software tests use mocks and dummy processes.'],
 ['Presentation flow and recovery','Prepare and rehearse before the audience arrives', ['Start with 15 Mission Control or 17 Story Director','Try 18 Scene Memory with the camera prepared','Choose any named experiment directly','Ctrl+C returns from a supervised demo; 0 exits','21 runs the optional prepared sequence'], 'RAM, disk, heat and timeout checks reduce risk. Physical-board rehearsal remains required.'],
];
for(let i=0;i<pages.length;i++){
 const [title,subtitle,lines,footer]=pages[i]; const slide=p.slides.add();slide.background.fill='#0C1825';
 const text=(value,x,y,w,h,size,color,bold=false)=>{const q=slide.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});q.text=value;q.text.style={typeface:font,fontSize:size,color,bold,autoFit:'none'};return q;};
 text(title,64,46,1148,90,50,'#F2F7FB',true);
 text(subtitle,68,143,1130,90,28,'#76DAC7');
 const step=lines.length>5?61:70;
 lines.forEach((line,j)=>text(line.replace(/^(\d+)\s+/, 'Experiment $1: '),72,244+j*step,1135,60,i===1?25:28,'#F2F7FB'));
 text(footer,68,654,1110,45,19,'#B6C6D5');
 slide.speakerNotes.textFrame.setText('Implementation source: https://github.com/nileshsarkar-ai/JetsonNano-Demo\nCurrent named routes: scripts/demo_menu.py. Full scope: docs/EXPERIMENTS.md. Software prepared; physical Nano execution unverified. The original 72-topic catalogue is a historical ideas reference. This deck covers only implemented local menu entries, with optional camera.');
}
const draft=root+'/presentation-build/candidate.pptx';await(await PresentationFile.exportPptx(p)).save(draft);
for(let i=0;i<p.slides.items.length;i++){const blob=await p.export({slide:p.slides.items[i],format:'png',scale:1});await fs.writeFile(root+'/presentation-build/slide-'+(i+1)+'.png',new Uint8Array(await blob.arrayBuffer()));}
const result=await finalizePresentation({workspaceDir:root,candidatePath:draft,finalPath:root+'/presentation-output/Jetson_Nano_Local_AI_Experiments-v4.pptx',pythonExecutable:process.env.RUNTIME_PYTHON,integrityValidatorPath:skill+'/container_tools/inspect_presentation_package_integrity.py',layoutValidatorPath:skill+'/container_tools/inspect_presentation_layout_geometry.py',layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit'],fontPolicy:{basis:'design',families:[font]},explicitTotalSlideCount:9,verifyArtifactToolImport:true,receiptPath:root+'/presentation-build/validation-v4.json'});
console.log(JSON.stringify(result));
