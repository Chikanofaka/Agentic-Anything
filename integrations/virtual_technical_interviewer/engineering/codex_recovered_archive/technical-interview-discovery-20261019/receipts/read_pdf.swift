import Foundation
import PDFKit
import AppKit
let input = CommandLine.arguments[1]
let output = CommandLine.arguments[2]
guard let doc = PDFDocument(url: URL(fileURLWithPath: input)) else { fatalError("Cannot open PDF") }
var all = ""
print("pages=\(doc.pageCount)")
for i in 0..<doc.pageCount {
    guard let page = doc.page(at:i) else { continue }
    let text = page.string ?? ""
    all += "\n--- PAGE \(i+1) ---\n\(text)\n"
    print("page=\(i+1) characters=\(text.count)")
    let image = page.thumbnail(of: NSSize(width: 1200, height: 1700), for: .mediaBox)
    if let tiff = image.tiffRepresentation, let rep = NSBitmapImageRep(data:tiff), let png = rep.representation(using:.png,properties:[:]) {
        try png.write(to:URL(fileURLWithPath:"\(output)/review-page-\(i+1).png"))
    }
}
try all.write(toFile:"\(output)/review_pdf_text.txt",atomically:true,encoding:.utf8)
