import { exec } from 'child_process'
import { NextResponse } from 'next/server'

export async function GET() {
    return new Promise((resolve) => {
        exec('python client.py --list', (error, stdout, stderr) => {
            if (error) {
                console.error(`Error: ${error.message}`)
                return resolve(NextResponse.json({ error: 'Failed to fetch files' }, { status: 500 }))
            }
            if (stderr) {
                console.error(`stderr: ${stderr}`)
                return resolve(NextResponse.json({ error: 'Failed to fetch files' }, { status: 500 }))
            }

            const files = stdout.split('\n')
                .filter(line => line.startsWith('- '))
                .map(line => line.substring(2).trim())

            resolve(NextResponse.json({ files }))
        })
    })
}

