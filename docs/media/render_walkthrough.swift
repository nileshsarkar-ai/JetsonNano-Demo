import AppKit
import AVFoundation
import CoreVideo

struct Scene {
    let title: String
    let note: String
    let commands: [String]
    let footer: String
    let seconds: Int
}
let scenes = [
    Scene(title: "Named experiments / Nano and camera only", note: "No training, microphone, speaker or external GPU in this menu.", commands: ["# 9: Persistent Memory Assistant", "# 14: Sampling Playground", "# 22-25: Prompts, Few-Shot Learning, Triage, Summary", "# 26-28: Prompt Injection, Abstention, Context Recall", "# Every project has a numbered menu entry"], footer: "Use docs/EXPERIMENTS.md for the full current list.", seconds: 12),
    Scene(title: "Offline AI / Student showcase", note: "Original Nano 4GB. JetPack 4. Ubuntu 18.04. Python 3.6.", commands: ["# No cloud API or external GPU", "# No microphone or speaker required", "# Attached camera is optional", "# Prepare once, then run local projects from one menu"], footer: "Instructional walkthrough only — no Nano execution or desktop capture is shown.", seconds: 9),
    Scene(title: "1 / Clone or update", note: "In a terminal on the Nano:", commands: ["git clone https://github.com/nileshsarkar-ai/JetsonNano-Demo.git", "cd JetsonNano-Demo", "", "# If already cloned, enter that folder and run:", "git pull --ff-only"], footer: "Choose a fresh clone OR update your existing clone.", seconds: 11),
    Scene(title: "2 / One command opens everything", note: "The menu is the entry point for the student projects.", commands: ["bash scripts/run_demo.sh", "", "# 1 = Prepare core dependencies and models", "# 2 = Check board resources and dependencies"], footer: "Complete preparation before class. Internet, sudo and build time are needed initially.", seconds: 11),
    Scene(title: "3 / Named experiments", note: "Select an experiment by number and full name.", commands: ["# 15 = Mission Control: Tool-Planning Assistant", "# LLM mission control with real read-only tools", "# Document detective with visible local evidence", "# Story director with a printed plot twist", "# Optional prepared camera journal"], footer: "Small local models generate the answers. Quality and latency need a real-board rehearsal.", seconds: 12),
    Scene(title: "4 / Let the audience steer", note: "Choose 15, 16 or 17 directly from the main menu.", commands: ["# 15 Mission Control: give the assistant a task; inspect its tool plan", "# 16 Document Detective: ask a question about the local brief", "# 17 Story Director: choose a scene, then supply a plot twist", "", "# The bundled exhibit brief is fictional demo data"], footer: "Tool calls are validated. The model cannot execute arbitrary shell commands.", seconds: 12),
    Scene(title: "5 / Prepare the attached camera", note: "Optional camera preparation is inside the same launcher.", commands: ["# 13 -> install: prepare vision dependencies", "# Then choose experiment 18, 19 or 20", "# USB camera URI: v4l2:///dev/video0", "# CSI camera may need: csi://0"], footer: "Rehearse model download and TensorRT compilation before class. Camera may be skipped.", seconds: 12),
    Scene(title: "6 / Scene-memory detective", note: "Choose 18: Scene Memory Detective.", commands: ["# Capture five frames of the desk", "# Move, add or remove an ordinary object", "# Keep the camera fixed; press Enter to observe again", "# Compare stable objects, counts and positions", "# Local AI explains only the recorded changes"], footer: "Vision exits before loading the LLM. No observed change means no invented change story.", seconds: 12),
    Scene(title: "7 / AI scavenger hunt", note: "Choose 19: AI Visual Scavenger Hunt.", commands: ["# The LLM plans a quest with 2 or 3 supported targets", "# Arrange ordinary objects in view; press Enter to scan", "# The camera gathers multi-frame evidence", "# Code scores progress over up to three rounds", "# The model does not decide whether you succeeded"], footer: "Suggested props: cup, bottle, book or phone. Detection errors remain possible.", seconds: 12),
    Scene(title: "8 / Workspace-change journal", note: "Choose 20: Camera Change Journal.", commands: ["# Record three observations over time", "# Change the scene between observations", "# Build an ordered event history", "# Ask the local model to summarize the changes"], footer: "The automatic tour uses timed gaps. An unavailable camera is reported and skipped.", seconds: 11),
    Scene(title: "9 / Exit, recover and repeat", note: "The launcher supervises projects one at a time.", commands: ["# Ctrl+C cancels the active project", "# 0 exits the main menu", "# Logs and camera evidence are in runs/demo-*", "# Close other programs if memory is low", "", "bash scripts/run_demo.sh"], footer: "Earlier labs have direct entries 3 through 14. Rehearse the exact student sequence on the Nano before presenting.", seconds: 12),
]
let outdir = URL(fileURLWithPath: CommandLine.arguments[1], isDirectory: true)
let output = outdir.appendingPathComponent("jetson-nano-student-showcase.mp4")
let width = 1280, height = 720, fps = 10
let writer = try AVAssetWriter(outputURL: output, fileType: .mp4)
let input = AVAssetWriterInput(mediaType: .video, outputSettings: [AVVideoCodecKey: AVVideoCodecType.h264, AVVideoWidthKey: width, AVVideoHeightKey: height, AVVideoCompressionPropertiesKey: [AVVideoAverageBitRateKey: 1800000]])
input.expectsMediaDataInRealTime = false
let adaptor = AVAssetWriterInputPixelBufferAdaptor(assetWriterInput: input, sourcePixelBufferAttributes: [kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32ARGB, kCVPixelBufferWidthKey as String: width, kCVPixelBufferHeightKey as String: height, kCVPixelBufferCGImageCompatibilityKey as String: true, kCVPixelBufferCGBitmapContextCompatibilityKey as String: true])
writer.add(input)
guard writer.startWriting() else { fatalError("Writer start failed: \(String(describing: writer.error))") }
writer.startSession(atSourceTime: .zero)
func color(_ r: CGFloat, _ g: CGFloat, _ b: CGFloat) -> NSColor { NSColor(srgbRed:r,green:g,blue:b,alpha:1) }
func text(_ s: String, _ x: CGFloat, _ y: CGFloat, _ size: CGFloat, _ c: NSColor, mono: Bool = false) {
    let font = mono ? NSFont.monospacedSystemFont(ofSize: size, weight: .medium) : NSFont.systemFont(ofSize:size, weight: .medium)
    (s as NSString).draw(at: NSPoint(x:x,y:y), withAttributes: [.font:font,.foregroundColor:c])
}
func render(_ scene: Scene, _ index: Int, _ tick: Int) -> CGImage {
    let rep = NSBitmapImageRep(bitmapDataPlanes:nil,pixelsWide:width,pixelsHigh:height,bitsPerSample:8,samplesPerPixel:4,hasAlpha:true,isPlanar:false,colorSpaceName:.deviceRGB,bytesPerRow:0,bitsPerPixel:0)!
    NSGraphicsContext.saveGraphicsState()
    NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep:rep)
    color(0.055,0.07,0.10).setFill(); NSRect(x:0,y:0,width:width,height:height).fill()
    text("JETSON NANO  /  PYTHON 3.6",48,662,17,color(0.41,0.85,0.68))
    text(scene.title,48,594,36,.white)
    text(scene.note,48,551,21,color(0.72,0.77,0.84))
    color(0.095,0.115,0.15).setFill(); NSBezierPath(roundedRect:NSRect(x:40,y:128,width:1200,height:389),xRadius:12,yRadius:12).fill()
    text("TERMINAL  •  COMMANDS TO RUN ON YOUR NANO",64,480,15,color(0.62,0.69,0.77))
    let visible = min(scene.commands.count, 1 + tick / 7)
    for (line, command) in scene.commands.enumerated() where line < visible {
        let comment = command.hasPrefix("#")
        let prefix = comment || command.isEmpty ? "  " : "$ "
        text(prefix + command,64,424-CGFloat(line)*43,23,comment ? color(0.60,0.66,0.73) : color(0.86,0.94,0.90),mono:true)
    }
    text(scene.footer,48,83,17,color(0.74,0.79,0.85))
    text("WALKTHROUGH — NOT A RECORDING OF NANO EXECUTION",48,38,13,color(0.49,0.57,0.65))
    text("\(index+1) / \(scenes.count)",1160,38,15,color(0.49,0.57,0.65))
    NSGraphicsContext.restoreGraphicsState()
    if tick == scene.seconds*fps-1 {
        try! rep.representation(using:.png,properties:[:])!.write(to:outdir.appendingPathComponent(String(format:"scene-%02d.png",index+1)))
    }
    return rep.cgImage!
}
var frame: Int64 = 0
for (index,scene) in scenes.enumerated() {
    for tick in 0..<(scene.seconds*fps) {
        while !input.isReadyForMoreMediaData { Thread.sleep(forTimeInterval:0.005) }
        var buffer: CVPixelBuffer?
        CVPixelBufferCreate(nil,width,height,kCVPixelFormatType_32ARGB,nil,&buffer)
        let pixelBuffer=buffer!
        CVPixelBufferLockBaseAddress(pixelBuffer,[])
        let context=CGContext(data:CVPixelBufferGetBaseAddress(pixelBuffer),width:width,height:height,bitsPerComponent:8,bytesPerRow:CVPixelBufferGetBytesPerRow(pixelBuffer),space:CGColorSpaceCreateDeviceRGB(),bitmapInfo:CGImageAlphaInfo.noneSkipFirst.rawValue)!
        context.draw(render(scene,index,tick),in:CGRect(x:0,y:0,width:width,height:height))
        CVPixelBufferUnlockBaseAddress(pixelBuffer,[])
        if !adaptor.append(pixelBuffer,withPresentationTime:CMTime(value:frame,timescale:Int32(fps))) { fatalError("Append failed: \(String(describing:writer.error))") }
        frame += 1
    }
    print("Rendered scene \(index+1)/\(scenes.count)")
}
writer.endSession(atSourceTime:CMTime(value:frame,timescale:Int32(fps)))
input.markAsFinished()
let semaphore=DispatchSemaphore(value:0)
writer.finishWriting { semaphore.signal() }
semaphore.wait()
guard writer.status == .completed else { fatalError("Video failed: \(String(describing:writer.error))") }
print("Saved \(output.path), \(frame / Int64(fps)) seconds")
