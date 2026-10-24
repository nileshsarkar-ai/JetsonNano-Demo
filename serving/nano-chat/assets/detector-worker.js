/* CPU worker keeps TensorFlow computation and allocations off the UI thread. */
importScripts('/assets/tf.min.js','/assets/coco-ssd.min.js');
let detector;
(async()=>{try{await tf.setBackend('cpu');await tf.ready();detector=await cocoSsd.load({base:'lite_mobilenet_v2',modelUrl:'/assets/detector/model.json'});postMessage({ready:true})}catch(e){postMessage({error:'Detector could not load'})}})();
onmessage=async e=>{if(!detector)return;const started=performance.now();try{const predictions=await detector.detect(e.data.image,10,.55);postMessage({id:e.data.id,predictions,ms:Math.round(performance.now()-started),tensors:tf.memory().numTensors})}catch(error){postMessage({id:e.data.id,error:'Detection failed'})}};
