import Foundation
import Darwin

// One-shot local PostgreSQL work never blocks the 15-second controller Worker.
// Native owns process lifetime; input/output are bounded and no executable path
// or credential is accepted from WebKit. Cancellation ignores late process output.
final class TIAPostInterviewSQLRunner {
    private var process: Process?
    private var generation = UUID()
    func run(_ packet: [String: Any], runtime: URL, completion: @escaping ([String: Any]?) -> Void) -> Bool {
        guard process == nil, let data = try? JSONSerialization.data(withJSONObject: packet),
              data.count <= 131072 else { return false }
        let task = Process(), input = Pipe(), output = Pipe()
        task.executableURL = URL(fileURLWithPath: "/usr/bin/python3")
        task.arguments = ["-B", "-u", "-m", "tia_runtime.post_interview_sql_worker"]
        task.currentDirectoryURL = runtime
        task.environment = ["PATH": "/usr/bin:/bin", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1"]
        task.standardInput = input; task.standardOutput = output; task.standardError = FileHandle.nullDevice
        do { try task.run() } catch { return false }
        let token = UUID(); generation = token; process = task
        DispatchQueue.global(qos: .userInitiated).async { [weak self] in
            var bytes = Data()
            do {
                try input.fileHandleForWriting.write(contentsOf: data)
                try input.fileHandleForWriting.close()
                while bytes.count <= 16384 {
                    let next = try output.fileHandleForReading.read(upToCount: 16385 - bytes.count) ?? Data()
                    if next.isEmpty { break }; bytes.append(next)
                }
                if bytes.count > 16384 { Self.stop(task) }
            } catch { Self.stop(task) }
            task.waitUntilExit()
            DispatchQueue.main.async { [weak self] in
                guard let self = self, self.generation == token else { return }
                self.process = nil
                let result = (task.terminationStatus == 0 && bytes.count <= 16384)
                    ? (try? StrictJSON.object(bytes) as? [String: Any]) : nil
                completion(result)
            }
        }
        DispatchQueue.main.asyncAfter(deadline: .now() + 360) { [weak self] in
            guard let self = self, self.generation == token, let running = self.process else { return }
            Self.stop(running)
        }
        return true
    }
    func cancel() {
        generation = UUID()
        if let task = process { Self.stop(task) }
        process = nil
    }
    // SIGTERM lets the worker unwind PostgreSQL cleanup. A private process
    // group bounds the worker and child commands still in that group.
    // PostgreSQL may daemonize; its normal shutdown is the worker finally cleanup.
    private static func stop(_ task: Process) {
        guard task.isRunning else { return }
        task.terminate()
        DispatchQueue.global().asyncAfter(deadline: .now() + 20) {
            guard task.isRunning else { return }
            kill(-task.processIdentifier, SIGKILL)
            kill(task.processIdentifier, SIGKILL)
        }
    }
    deinit { if let task = process { Self.stop(task) } }
}
