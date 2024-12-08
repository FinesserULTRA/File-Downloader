import { useState, useEffect } from 'react'
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Play, Pause, RotateCcw, XCircle } from 'lucide-react'
import { useToast } from "@/components/ui/use-toast"

interface DownloadManagerProps {
    filename: string
    onComplete: () => void
}

export function DownloadManager({ filename, onComplete }: DownloadManagerProps) {
    const [progress, setProgress] = useState(0)
    const [status, setStatus] = useState<'idle' | 'downloading' | 'paused' | 'completed' | 'failed'>('idle')
    const [error, setError] = useState<string | null>(null)
    const { toast } = useToast()

    useEffect(() => {
        let eventSource: EventSource | null = null;

        const startDownload = async () => {
            try {
                const response = await fetch('/api/download', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ filename, action: 'start' }),
                });

                if (!response.ok) {
                    throw new Error('Failed to start download');
                }

                setStatus('downloading');
                eventSource = new EventSource(`/api/download?filename=${encodeURIComponent(filename)}`);

                eventSource.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    if (data.progress) {
                        setProgress(parseFloat(data.progress));
                    } else if (data.error) {
                        setError(data.error);
                        setStatus('failed');
                        toast({
                            title: "Error",
                            description: data.error,
                            variant: "destructive",
                        })
                    } else if (data.complete) {
                        setStatus('completed');
                        onComplete();
                        toast({
                            title: "Download Complete",
                            description: `${filename} has been downloaded successfully.`,
                        })
                    }
                };

                eventSource.onerror = () => {
                    setError('Connection to server lost');
                    setStatus('failed');
                    toast({
                        title: "Error",
                        description: "Connection to server lost. Please try again.",
                        variant: "destructive",
                    })
                };
            } catch (error) {
                setError(error instanceof Error ? error.message : 'An error occurred');
                setStatus('failed');
                toast({
                    title: "Error",
                    description: error instanceof Error ? error.message : 'An error occurred',
                    variant: "destructive",
                })
            }
        };

        if (status === 'idle') {
            startDownload();
        }

        return () => {
            if (eventSource) {
                eventSource.close();
            }
        };
    }, [filename, status, onComplete, toast]);

    const handlePause = async () => {
        try {
            const response = await fetch('/api/download', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filename, action: 'pause' }),
            });

            if (!response.ok) {
                throw new Error('Failed to pause download');
            }

            setStatus('paused');
            toast({
                title: "Download Paused",
                description: `${filename} has been paused.`,
            })
        } catch (error) {
            setError(error instanceof Error ? error.message : 'An error occurred');
            toast({
                title: "Error",
                description: "Failed to pause download. Please try again.",
                variant: "destructive",
            })
        }
    };

    const handleResume = async () => {
        try {
            const response = await fetch('/api/download', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filename, action: 'resume' }),
            });

            if (!response.ok) {
                throw new Error('Failed to resume download');
            }

            setStatus('downloading');
            toast({
                title: "Download Resumed",
                description: `${filename} has been resumed.`,
            })
        } catch (error) {
            setError(error instanceof Error ? error.message : 'An error occurred');
            toast({
                title: "Error",
                description: "Failed to resume download. Please try again.",
                variant: "destructive",
            })
        }
    };

    const handleCancel = async () => {
        try {
            const response = await fetch('/api/download', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filename, action: 'cancel' }),
            });

            if (!response.ok) {
                throw new Error('Failed to cancel download');
            }

            setStatus('idle');
            setProgress(0);
            onComplete();
            toast({
                title: "Download Cancelled",
                description: `${filename} has been cancelled.`,
            })
        } catch (error) {
            setError(error instanceof Error ? error.message : 'An error occurred');
            toast({
                title: "Error",
                description: "Failed to cancel download. Please try again.",
                variant: "destructive",
            })
        }
    };

    return (
        <div className="bg-card text-card-foreground p-4 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">Downloading: {filename}</h2>
            <Progress value={progress} className="mb-4" />
            <div className="flex justify-between items-center">
                <span>{status === 'completed' ? 'Download complete' : `${progress.toFixed(2)}%`}</span>
                <div className="space-x-2">
                    {status === 'downloading' && (
                        <Button onClick={handlePause}>
                            <Pause className="mr-2 h-4 w-4" /> Pause
                        </Button>
                    )}
                    {status === 'paused' && (
                        <Button onClick={handleResume}>
                            <Play className="mr-2 h-4 w-4" /> Resume
                        </Button>
                    )}
                    {(status === 'failed' || status === 'completed') && (
                        <Button onClick={() => {
                            setStatus('idle');
                            setProgress(0);
                            setError(null);
                        }}>
                            <RotateCcw className="mr-2 h-4 w-4" /> Retry
                        </Button>
                    )}
                    {status !== 'idle' && (
                        <Button onClick={handleCancel} variant="destructive">
                            <XCircle className="mr-2 h-4 w-4" /> Cancel
                        </Button>
                    )}
                </div>
            </div>
            {error && (
                <div className="mt-4 p-2 bg-red-100 text-red-700 rounded">
                    Error: {error}
                </div>
            )}
        </div>
    )
}

