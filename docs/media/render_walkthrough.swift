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
    Scene(title: "Jetson Nano / Chairman demo menu", note: "Run on the original Nano 4GB with JetPack 4 and Ubuntu 18.04.", commands: ["# System Python 3.6; no pip needed for the core menu", "# Stable power, cooling and free disk space are required", "# Prepare and rehearse BEFORE the presentation"], footer: "Command walkthrough only. No Nano execution or desktop capture is shown.", seconds: 9),
    Scene(title: "1 / Download the repository", note: "Open a terminal on your Jetson Nano.", commands: ["git clone https://github.com/nileshsarkar-ai/JetsonNano-Demo.git", "cd JetsonNano-Demo", "", "# Already cloned? Enter that folder and run:", "git pull --ff-only"], footer: "Choose a fresh clone OR update the existing clone.", seconds: 12),
    Scene(title: "2 / Open the menu", note: "One Bash command is the entry point for all supported demos.", commands: ["bash scripts/run_demo.sh", "", "# The board is checked first. Then the menu opens.", "# No demo starts automatically."], footer: "Same command on every visit. Do not bypass the board check on a Mac or Orin.", seconds: 10),
    Scene(title: "3 / Prepare before the event", note: "In the menu, enter 1 and press Enter.", commands: ["# 1 = Prepare / repair core setup", "# Installs packages (sudo may request your password)", "# Builds CPU runtimes with one build job", "# Downloads and verifies the starter models", "", "# Wait for preparation to finish."], footer: "Needs Internet, time and at least 6 GiB free disk. Do not do first-time setup live.", seconds: 12),
    Scene(title: "4 / Check readiness", note: "Back in the menu, enter 2 and press Enter.", commands: ["# 2 = Board / dependency / resource report", "# Check memory, temperature, disk and missing tools", "# Optional camera and PyTorch need separate preparation", "# Rehearse each planned demo on the actual board"], footer: "Software checks cannot guarantee power, peripherals, model quality or peak memory.", seconds: 10),
    Scene(title: "5 / Choose a language demo", note: "Type the menu number and press Enter.", commands: ["# 3 = Interactive chat; /quit returns to the menu", "# 4 = Ask one question", "# 5 = Inspect tokens", "# 6 = Extract grounded JSON", "# 7 = Calculator (try: Multiply 12 by 7.)"], footer: "The menu starts the LLM server only when needed and stops it after the selection.", seconds: 12),
    Scene(title: "6 / More demos, one at a time", note: "The same menu also offers these choices.", commands: ["# 8  = RAG: index your notes, retrieve, or ask", "# 9  = Speech: say, transcribe, or voice assistant", "# 10 = TinyStories", "# 11 = CPU benchmark", "# 12 = Evaluate your JSONL prompts"], footer: "Use your own small prepared inputs. Check actual results before the presentation.", seconds: 12),
    Scene(title: "7 / Camera and optional training", note: "Prepare these separately before using them in the live sequence.", commands: ["# 13 = Vision: install, detect, classify, pose, segment", "# Connect and rehearse the actual camera or video", "# 14 = Tiny CPU LoRA: base, adapt, generate", "# Requires a compatible legacy PyTorch installation", "# External GPU QLoRA cannot run on this Nano"], footer: "First vision use may download models and compile TensorRT engines.", seconds: 12),
    Scene(title: "8 / Cancel or recover", note: "A failed selection reports its error and returns to the menu.", commands: ["# Ctrl+C = cancel the current demo", "# Logs and unique outputs are under runs/demo-*", "# Low memory or high temperature stops monitored demos", "# Close other programs or cool the board before retrying", "# Package installers are not resource-killed mid-install"], footer: "No silent fallback or fake success. Resolve a failed rehearsal before presenting it.", seconds: 12),
    Scene(title: "9 / Exit and restart", note: "Choose 0 to exit the menu.", commands: ["# 0 = Exit; stops the model server owned by this menu", "", "# Next time, from the repository folder:", "bash scripts/run_demo.sh"], footer: "Suggested rehearsal: 2 -> 3 -> 7 -> 10 -> 0. Add other demos after testing them.", seconds: 10),
]
let outdir = URL(fileURLWithPath: CommandLine.arguments[1], isDirectory: true)
let output = outdir.appendingPathComponent("jetson-nano-menu.mp4")
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
