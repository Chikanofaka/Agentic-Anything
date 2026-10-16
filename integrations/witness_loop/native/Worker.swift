import Foundation

// The renderer never talks directly to this process, and this process never receives credentials.
final class CoreWorker {
    static let maximumRequestBytes = 32768
    static let maximumResponseBytes = 8 * 1024 * 1024
    private let process = Process()
    private let input = Pipe()
    private let output = Pipe()
    private let queue = DispatchQueue(label: "hal.core.stdio")
    private var buffer = Data()
    private var nextID = 0
    private var pending: (String, ([String: Any]) -> Void)?
    private var stopped = false
    var onFailure: (() -> Void)?

    init(runtime: URL, dataDirectory: URL) throws {
        process.executableURL = URL(fileURLWithPath: "/usr/bin/python3")
        process.arguments = ["-B", "-u", "-m", "hal_core.interactive", "--data-dir", dataDirectory.path]
        process.currentDirectoryURL = runtime
        process.environment = ["PATH": "/usr/bin:/bin", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1"]
        process.standardInput = input
        process.standardOutput = output
        process.standardError = FileHandle.nullDevice
        output.fileHandleForReading.readabilityHandler = { [weak self] handle in
            let data = handle.availableData
            self?.queue.async { [weak self] in self?.receive(data) }
        }
        process.terminationHandler = { [weak self] _ in self?.queue.async { [weak self] in self?.fail() } }
        try process.run()
    }

    func request(_ action: String, params: [String: Any] = [:], completion: @escaping ([String: Any]) -> Void) {
        queue.async {
            guard !self.stopped, self.pending == nil else {
                DispatchQueue.main.async { completion(["ok": false, "error": "The local Core is unavailable or busy."]) }; return
            }
            self.nextID += 1
            let id = "native-\(self.nextID)"
            guard let data = try? JSONSerialization.data(withJSONObject: ["id": id, "action": action, "params": params]), data.count <= Self.maximumRequestBytes else {
                DispatchQueue.main.async { completion(["ok": false, "error": "The local request exceeded its limit."]) }; return
            }
            self.pending = (id, completion)
            do { try self.input.fileHandleForWriting.write(contentsOf: data + Data([10])) }
            catch { self.fail(); return }
            self.queue.asyncAfter(deadline: .now() + 15) {
                if self.pending?.0 == id { self.fail() }
            }
        }
    }

    func stop() { queue.async { self.fail() } }

    private func receive(_ data: Data) {
        guard !stopped else { return }
        guard !data.isEmpty, buffer.count + data.count <= Self.maximumResponseBytes else { fail(); return }
        buffer.append(data)
        while let newline = buffer.firstIndex(of: 10) {
            let line = buffer.prefix(upTo: newline)
            buffer.removeSubrange(...newline)
            guard let object = try? JSONSerialization.jsonObject(with: line) as? [String: Any],
                  let id = object["id"] as? String, let awaiting = pending, awaiting.0 == id,
                  object["ok"] is Bool else { fail(); return }
            pending = nil
            DispatchQueue.main.async { awaiting.1(object) }
        }
    }

    private func fail() {
        guard !stopped else { return }
        stopped = true
        output.fileHandleForReading.readabilityHandler = nil
        try? input.fileHandleForWriting.close()
        if process.isRunning { process.terminate() }
        let awaiting = pending
        pending = nil
        DispatchQueue.main.async {
            awaiting?.1(["ok": false, "error": "The local Core stopped or returned an invalid response. Restart the app."])
            self.onFailure?()
        }
    }
}
