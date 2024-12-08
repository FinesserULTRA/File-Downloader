import { Button } from "@/components/ui/button"
import { RefreshCw } from 'lucide-react'

interface FileInfo {
    name: string;
    size: number;
}

interface FileListProps {
    files: FileInfo[]
    onSelectFile: (file: FileInfo) => void
    onRefresh: () => void
}

function formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

export function FileList({ files, onSelectFile, onRefresh }: FileListProps) {
    return (
        <div className="bg-white p-4 rounded-lg shadow">
            <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-semibold">Available Files</h2>
                <Button onClick={onRefresh} variant="outline" size="icon">
                    <RefreshCw className="h-4 w-4" />
                </Button>
            </div>
            <ul className="space-y-2">
                {files.map((file) => (
                    <li key={file.name} className="flex items-center justify-between">
                        <div>
                            <span className="font-medium">{file.name}</span>
                            <span className="text-sm text-gray-500 ml-2">({formatFileSize(file.size)})</span>
                        </div>
                        <Button onClick={() => onSelectFile(file)} variant="outline" size="sm">
                            Download
                        </Button>
                    </li>
                ))}
            </ul>
        </div>
    )
}

