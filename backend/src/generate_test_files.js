const fs = require('fs');
const path = require('path');

function generateRandomContent(size) {
    return Buffer.from(Array(size).fill().map(() => Math.floor(Math.random() * 256)));
}

function generateTextContent(size) {
    return Buffer.from(Array(size).fill().map(() => Math.floor(Math.random() * 26) + 65).map(c => String.fromCharCode(c)).join(''));
}

function generateXMLContent(size) {
    const header = '<?xml version="1.0" encoding="UTF-8"?>\n<root>\n';
    const footer = '</root>';
    const contentSize = size - header.length - footer.length;
    const content = Array(Math.floor(contentSize / 20)).fill().map((_, i) => `  <item${i}>${Math.random().toString(36).substring(2, 15)}</item${i}>`).join('\n');
    return Buffer.from(header + content + footer);
}

function generateFile(filename, size, type) {
    let content;
    switch (type) {
        case 'bin':
            content = generateRandomContent(size);
            break;
        case 'txt':
            content = generateTextContent(size);
            break;
        case 'xml':
            content = generateXMLContent(size);
            break;
        default:
            throw new Error(`Unsupported file type: ${type}`);
    }

    fs.writeFileSync(filename, content);
    console.log(`Generated ${filename} (${size} bytes)`);
}

const testFiles = [
    // { name: 'small_file.bin', size: 1024 * 1024, type: 'bin' },
    // { name: 'medium_file.txt', size: 10 * 1024 * 1024, type: 'txt' },
    { name: 'xml_large.xml', size: 100 * 1024 * 1024, type: 'xml' }
];

const testDir = 'test_files';
if (!fs.existsSync(testDir)) {
    fs.mkdirSync(testDir);
}

testFiles.forEach(file => {
    generateFile(path.join(testDir, file.name), file.size, file.type);
});

console.log('Test files generated successfully.');