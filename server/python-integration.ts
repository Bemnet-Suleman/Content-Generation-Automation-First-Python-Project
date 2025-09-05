import { spawn } from 'child_process';
import path from 'path';
import { storage } from './storage';

export interface PythonScriptParams {
  [key: string]: any;
}

export function processPythonScript(scriptName: string, params: PythonScriptParams): Promise<string> {
  return new Promise((resolve, reject) => {
    const pythonPath = process.env.PYTHON_PATH || 'python3';
    const scriptPath = path.join(process.cwd(), 'automation', `${scriptName}.py`);
    
    const args = [scriptPath];
    
    // Add parameters as command line arguments
    Object.entries(params).forEach(([key, value]) => {
      args.push(`--${key}`, String(value));
    });

    const pythonProcess = spawn(pythonPath, args);
    
    let stdout = '';
    let stderr = '';

    pythonProcess.stdout.on('data', (data) => {
      stdout += data.toString();
      console.log(`Python stdout: ${data}`);
    });

    pythonProcess.stderr.on('data', (data) => {
      stderr += data.toString();
      console.error(`Python stderr: ${data}`);
    });

    pythonProcess.on('close', async (code) => {
      if (code === 0) {
        console.log(`Python script ${scriptName} completed successfully`);
        
        // Update system status
        try {
          await storage.updateSystemStatus('video_processor', {
            service: 'video_processor',
            status: 'online',
            metadata: { lastProcess: new Date().toISOString() }
          });
        } catch (error) {
          console.error('Failed to update system status:', error);
        }
        
        resolve(stdout);
      } else {
        console.error(`Python script ${scriptName} failed with code ${code}`);
        
        // Update project status if projectId is provided
        if (params.projectId) {
          try {
            await storage.updateProject(params.projectId, {
              status: 'error',
              metadata: { error: stderr || `Process failed with code ${code}` }
            });
          } catch (error) {
            console.error('Failed to update project status:', error);
          }
        }
        
        reject(new Error(`Script failed: ${String(stderr)}`));
      }
    });

    pythonProcess.on('error', (error) => {
      console.error(`Failed to start Python script: ${error}`);
      reject(error);
    });
  });
}

// Initialize system status on startup
export async function initializeSystemStatus() {
  const services = ['content_scraper', 'video_processor', 'upload_manager', 'analytics_engine'];
  
  for (const service of services) {
    try {
      await storage.updateSystemStatus(service, {
        service,
        status: 'online',
        metadata: { initialized: new Date().toISOString() }
      });
    } catch (error) {
      console.error(`Failed to initialize ${service} status:`, error);
    }
  }
}

// Background task to check system health
setInterval(async () => {
  try {
    // Check if Python scripts are responsive
    const healthCheck = await processPythonScript('health_check', {});
    console.log('System health check passed');
  } catch (error) {
    console.error('System health check failed:', error);
    
    // Update system status to reflect issues
    try {
      await storage.updateSystemStatus('video_processor', {
        service: 'video_processor',
        status: 'error',
        metadata: { error: error.message }
      });
    } catch (statusError) {
      console.error('Failed to update system status:', statusError);
    }
  }
}, 5 * 60 * 1000); // Check every 5 minutes
