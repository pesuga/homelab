/**
 * Server-side proxy for Phase 2 core prompts endpoint
 * Handles GET (retrieve) and PUT (update) for specific core prompts
 */

import { NextResponse } from 'next/server';

const FAMILY_API_URL = process.env.FAMILY_API_URL || 'http://family-assistant-backend.homelab.svc:8001';

export async function GET(
  request: Request,
  { params }: { params: Promise<{ name: string }> }
) {
  try {
    const { name } = await params;

    // First try the backend API
    try {
      const response = await fetch(`${FAMILY_API_URL}/api/phase2/prompts/core/${name}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        return NextResponse.json(data);
      }
    } catch (backendError) {
      console.log('Backend not available, trying local file system');
    }

    // Fallback: Read from public directory (embedded at build time)
    const fs = await import('fs/promises');
    const path = await import('path');

    // Read from public/prompts/core directory
    const corePromptsPath = path.join(process.cwd(), 'public', 'prompts', 'core', `${name}.md`);

    try {
      const content = await fs.readFile(corePromptsPath, 'utf8');
      const stats = await fs.stat(corePromptsPath);

      // Create the expected response format
      const data = {
        metadata: {
          name: name,
          display_name: name.replace(/_/g, ' '),
          description: `Core prompt: ${name}`,
          file_path: `/prompts/core/${name}.md`,
          version_count: 0,
          last_modified: stats.mtime.toISOString(),
          size_bytes: stats.size,
          token_estimate: Math.ceil(stats.size / 4), // Rough estimate: 1 token ≈ 4 characters
        },
        content: content,
        versions: [], // No version tracking yet
      };

      return NextResponse.json(data);
    } catch (fileError) {
      return NextResponse.json(
        { error: 'File not found', details: `Could not find ${name}.md in core prompts` },
        { status: 404 }
      );
    }
  } catch (error) {
    console.error('Error getting core prompt detail:', error);
    return NextResponse.json(
      { error: 'Failed to load prompt', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}

export async function PUT(
  request: Request,
  { params }: { params: Promise<{ name: string }> }
) {
  try {
    const { name } = await params;
    const body = await request.json();

    // First try the backend API
    try {
      const response = await fetch(`${FAMILY_API_URL}/api/phase2/prompts/core/${name}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      });

      if (response.ok) {
        const data = await response.json();
        return NextResponse.json(data);
      }
    } catch (backendError) {
      console.log('Backend not available, trying local file system');
    }

    // Fallback: Write to local filesystem (embedded at build time)
    const fs = await import('fs/promises');
    const path = await import('path');

    // Write to public/prompts/core directory
    const corePromptsPath = path.join(process.cwd(), 'public', 'prompts', 'core', `${name}.md`);

    try {
      // Create backup before saving
      const backupPath = path.join(process.cwd(), 'public', 'prompts', 'core', `${name}.md.backup.${Date.now()}`);
      try {
        await fs.copyFile(corePromptsPath, backupPath);
        console.log(`Created backup: ${backupPath}`);
      } catch (backupError) {
        console.log('Could not create backup (file might not exist yet)');
      }

      // Write new content
      await fs.writeFile(corePromptsPath, body.content, 'utf8');

      const stats = await fs.stat(corePromptsPath);

      // Return success response
      return NextResponse.json({
        success: true,
        message: 'Prompt updated successfully',
        version: '1', // Simple version tracking
        timestamp: new Date().toISOString(),
        size_bytes: stats.size,
        token_estimate: Math.ceil(stats.size / 4),
      });
    } catch (fileError) {
      return NextResponse.json(
        { error: 'Failed to save file', details: fileError instanceof Error ? fileError.message : 'Unknown error' },
        { status: 500 }
      );
    }
  } catch (error) {
    console.error('Error updating core prompt:', error);
    return NextResponse.json(
      { error: 'Failed to update prompt', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
