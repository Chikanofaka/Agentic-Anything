import Foundation

// Adapted from Witness Loop native/StrictJSON.swift; no domain behavior.
// Foundation's object decoder accepts duplicate keys. Reject ambiguity before decoding
// both the provider envelope and its structured text, with a bounded nesting depth.
struct StrictJSON {
    private var bytes: [UInt8]
    private var offset = 0
    private init(_ data: Data) { bytes = Array(data) }
    static func object(_ data: Data) throws -> Any {
        var scanner = StrictJSON(data)
        try scanner.value(depth: 0)
        scanner.space()
        guard scanner.offset == scanner.bytes.count else { throw TIAProviderFailure.invalidResponse }
        return try JSONSerialization.jsonObject(with: data)
    }
    private mutating func space() { while offset < bytes.count && [9, 10, 13, 32].contains(bytes[offset]) { offset += 1 } }
    private mutating func take(_ byte: UInt8) throws {
        space()
        guard offset < bytes.count && bytes[offset] == byte else { throw TIAProviderFailure.invalidResponse }
        offset += 1
    }
    private mutating func string() throws -> String {
        space()
        let start = offset
        try take(34)
        while offset < bytes.count {
            let byte = bytes[offset]
            offset += 1
            if byte == 34 {
                guard let result = try JSONSerialization.jsonObject(with: Data(bytes[start..<offset]), options: [.fragmentsAllowed]) as? String else { throw TIAProviderFailure.invalidResponse }
                return result
            }
            if byte == 92 { guard offset < bytes.count else { throw TIAProviderFailure.invalidResponse }; offset += 1 }
        }
        throw TIAProviderFailure.invalidResponse
    }
    private mutating func value(depth: Int) throws {
        space()
        guard depth <= 32 && offset < bytes.count else { throw TIAProviderFailure.invalidResponse }
        if bytes[offset] == 123 {
            offset += 1; space()
            if offset < bytes.count && bytes[offset] == 125 { offset += 1; return }
            var keys = Set<String>()
            while true {
                let key = try string()
                guard keys.insert(key).inserted else { throw TIAProviderFailure.invalidResponse }
                try take(58)
                try value(depth: depth + 1)
                space()
                guard offset < bytes.count else { throw TIAProviderFailure.invalidResponse }
                if bytes[offset] == 125 { offset += 1; return }
                try take(44)
            }
        }
        if bytes[offset] == 91 {
            offset += 1; space()
            if offset < bytes.count && bytes[offset] == 93 { offset += 1; return }
            while true {
                try value(depth: depth + 1)
                space()
                guard offset < bytes.count else { throw TIAProviderFailure.invalidResponse }
                if bytes[offset] == 93 { offset += 1; return }
                try take(44)
            }
        }
        if bytes[offset] == 34 { _ = try string(); return }
        let start = offset
        while offset < bytes.count && ![9, 10, 13, 32, 44, 93, 125].contains(bytes[offset]) { offset += 1 }
        guard start != offset else { throw TIAProviderFailure.invalidResponse }
        // Foundation subsequently checks number and literal syntax.
    }
}
