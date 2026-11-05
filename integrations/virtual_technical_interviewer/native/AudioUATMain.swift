import AppKit

@main
enum TIAAudioLabMain {
    static func main() {
        if CommandLine.arguments.contains("--self-test") {
            let voice = runVoiceTests()
            let lab = runAudioLabTests()
            exit(voice == 0 && lab == 0 ? 0 : 1)
        }
        let application = NSApplication.shared
        application.setActivationPolicy(.regular)
        let delegate = TIAAudioLabApp(synthetic: CommandLine.arguments.contains("--smoke"))
        application.delegate = delegate
        withExtendedLifetime(delegate) { application.run() }
    }
}
