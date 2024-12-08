import { exec } from 'child_process';
import { NextRequest, NextResponse } from 'next/server';
import { EventEmitter } from 'events';
import { Readable } from 'stream';

const downloadEmitter = new EventEmitter();

export async function POST(req: NextRequest) {
    const { filename, action } = await req.json();

    if (!filename) {
        return NextResponse.json({ error: 'Filename is required' }, { status: 400 });
    }

    if (action === 'start') {
        const outputFile = `downloads/${filename}`;
        const command = `python client.py "${filename}" "${outputFile}"`;

        const child = exec(command);

        child.stdout?.on('data', (data) => {
            downloadEmitter.emit('progress', { filename, data: data.toString() });
        });

        child.stderr?.on('data', (data) => {
            downloadEmitter.emit('error', { filename, error: data.toString() });
        });

        child.on('close', (code) => {
            downloadEmitter.emit('complete', { filename, code });
        });

        return NextResponse.json({ message: 'Download started' });
    } else if (action === 'pause' || action === 'resume' || action === 'cancel') {
        // These actions would require modifications to the Python client
        // For now, we'll just return a message
        return NextResponse.json({ message: `${action} action received for ${filename}` });
    } else {
        return NextResponse.json({ error: 'Invalid action' }, { status: 400 });
    }
}

export async function GET(req: NextRequest) {
    const searchParams = req.nextUrl.searchParams;
    const filename = searchParams.get('filename');

    if (!filename) {
        return NextResponse.json({ error: 'Filename is required' }, { status: 400 });
    }

    const stream = new ReadableStream({
        start(controller) {
            const listener = ({ data }: { data: string }) => {
                controller.enqueue(`data: ${JSON.stringify({ filename, progress: data })}\n\n`);
            };

            downloadEmitter.on('progress', listener);

            const errorListener = ({ error }: { error: string }) => {
                controller.enqueue(`data: ${JSON.stringify({ filename, error })}\n\n`);
            };

            downloadEmitter.on('error', errorListener);

            const completeListener = ({ code }: { code: number }) => {
                controller.enqueue(`data: ${JSON.stringify({ filename, complete: true, code })}\n\n`);
                controller.close();
            };

            downloadEmitter.on('complete', completeListener);

            return () => {
                downloadEmitter.off('progress', listener);
                downloadEmitter.off('error', errorListener);
                downloadEmitter.off('complete', completeListener);
            };
        },
    });

    return new NextResponse(stream, {
        headers: {
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
        },
    });
}

