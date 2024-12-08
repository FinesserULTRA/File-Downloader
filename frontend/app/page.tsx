'use client'

import { useState, useEffect } from 'react'
import { FileList } from '../components/FileList'
import { DownloadManager } from '../components/DownloadManager'
import { ThemeToggle } from '../components/theme-toggle'
import { useToast } from "@/components/ui/use-toast"

interface FileInfo {
    name: string;
    size: number;
}

export default function Home() {
    const [availableFiles, setAvailableFiles] = useState<FileInfo[]>([])
    const [selectedFile, setSelectedFile] = useState<string | null>(null)
    const { toast } = useToast()

    useEffect(() => {
        fetchAvailableFiles()
    }, [])

    const fetchAvailableFiles = async () => {
        try {
            const response = await fetch('/api/files')
            const data = await response.json()
            setAvailableFiles(data.files)
        } catch (error) {
            console.error('Error fetching available files:', error)
            toast({
                title: "Error",
                description: "Failed to fetch available files. Please try again.",
                variant: "destructive",
            })
        }
    }

    return (
        <div className="container mx-auto p-4">
            <div className="flex justify-between items-center mb-8">
                <h1 className="text-3xl font-bold">Distributed File Downloader</h1>
                <ThemeToggle />
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <FileList
                    files={availableFiles}
                    onSelectFile={(file) => setSelectedFile(file.name)}
                    onRefresh={fetchAvailableFiles}
                />
                {selectedFile ? (
                    <DownloadManager
                        filename={selectedFile}
                        onComplete={() => setSelectedFile(null)}
                    />
                ) : (
                    <div className="bg-card text-card-foreground p-4 rounded-lg shadow flex items-center justify-center">
                        <p className="text-lg text-center">Select a file to start downloading</p>
                    </div>
                )}
            </div>
        </div>
    )
}

