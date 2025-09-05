import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { insertProjectSchema, insertContentSourceSchema, insertUploadQueueSchema } from "@shared/schema";
import { spawn } from "child_process";
import path from "path";
import multer from "multer";
import { processPythonScript } from "./python-integration";

const upload = multer({ dest: 'uploads/' });

export async function registerRoutes(app: Express): Promise<Server> {
  // Projects endpoints
  app.get("/api/projects", async (req, res) => {
    try {
      const projects = await storage.getProjects();
      res.json(projects);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch projects" });
    }
  });

  app.get("/api/projects/:id", async (req, res) => {
    try {
      const project = await storage.getProject(req.params.id);
      if (!project) {
        return res.status(404).json({ error: "Project not found" });
      }
      res.json(project);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch project" });
    }
  });

  app.post("/api/projects", async (req, res) => {
    try {
      const validatedData = insertProjectSchema.parse(req.body);
      const project = await storage.createProject(validatedData);
      
      // Trigger video processing if source is provided
      if (project.sourceUrl) {
        processPythonScript('process_video', {
          projectId: project.id,
          sourceUrl: project.sourceUrl,
          memeText: project.sourceText || project.title
        });
      }
      
      res.status(201).json(project);
    } catch (error) {
      res.status(400).json({ error: "Invalid project data" });
    }
  });

  app.patch("/api/projects/:id", async (req, res) => {
    try {
      const updates = req.body;
      const project = await storage.updateProject(req.params.id, updates);
      if (!project) {
        return res.status(404).json({ error: "Project not found" });
      }
      res.json(project);
    } catch (error) {
      res.status(500).json({ error: "Failed to update project" });
    }
  });

  app.delete("/api/projects/:id", async (req, res) => {
    try {
      const success = await storage.deleteProject(req.params.id);
      if (!success) {
        return res.status(404).json({ error: "Project not found" });
      }
      res.json({ message: "Project deleted successfully" });
    } catch (error) {
      res.status(500).json({ error: "Failed to delete project" });
    }
  });

  // Content research endpoints
  app.get("/api/content-sources", async (req, res) => {
    try {
      const limit = req.query.limit ? parseInt(req.query.limit as string) : 50;
      const sources = await storage.getContentSources(limit);
      res.json(sources);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch content sources" });
    }
  });

  app.get("/api/content-sources/trending", async (req, res) => {
    try {
      const limit = req.query.limit ? parseInt(req.query.limit as string) : 10;
      const trending = await storage.getTrendingContent(limit);
      res.json(trending);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch trending content" });
    }
  });

  app.post("/api/content-sources", async (req, res) => {
    try {
      const validatedData = insertContentSourceSchema.parse(req.body);
      const source = await storage.createContentSource(validatedData);
      res.status(201).json(source);
    } catch (error) {
      res.status(400).json({ error: "Invalid content source data" });
    }
  });

  app.post("/api/content-sources/scrape", async (req, res) => {
    try {
      // Trigger content scraping
      processPythonScript('scrape_content', {});
      res.json({ message: "Content scraping started" });
    } catch (error) {
      res.status(500).json({ error: "Failed to start content scraping" });
    }
  });

  // Analytics endpoints
  app.get("/api/analytics/channel", async (req, res) => {
    try {
      const startDate = req.query.startDate ? new Date(req.query.startDate as string) : undefined;
      const endDate = req.query.endDate ? new Date(req.query.endDate as string) : undefined;
      const analytics = await storage.getChannelAnalytics(startDate, endDate);
      res.json(analytics);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch channel analytics" });
    }
  });

  app.get("/api/analytics/projects/:id", async (req, res) => {
    try {
      const analytics = await storage.getProjectAnalytics(req.params.id);
      res.json(analytics);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch project analytics" });
    }
  });

  // Upload queue endpoints
  app.get("/api/upload-queue", async (req, res) => {
    try {
      const queue = await storage.getUploadQueue();
      res.json(queue);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch upload queue" });
    }
  });

  app.post("/api/upload-queue", async (req, res) => {
    try {
      const validatedData = insertUploadQueueSchema.parse(req.body);
      const queueItem = await storage.addToUploadQueue(validatedData);
      res.status(201).json(queueItem);
    } catch (error) {
      res.status(400).json({ error: "Invalid upload queue data" });
    }
  });

  app.patch("/api/upload-queue/:id", async (req, res) => {
    try {
      const updates = req.body;
      const queueItem = await storage.updateUploadQueueItem(req.params.id, updates);
      if (!queueItem) {
        return res.status(404).json({ error: "Queue item not found" });
      }
      res.json(queueItem);
    } catch (error) {
      res.status(500).json({ error: "Failed to update queue item" });
    }
  });

  app.delete("/api/upload-queue/:id", async (req, res) => {
    try {
      const success = await storage.removeFromUploadQueue(req.params.id);
      if (!success) {
        return res.status(404).json({ error: "Queue item not found" });
      }
      res.json({ message: "Queue item removed successfully" });
    } catch (error) {
      res.status(500).json({ error: "Failed to remove queue item" });
    }
  });

  // Upload operations
  app.post("/api/upload/:projectId", async (req, res) => {
    try {
      const project = await storage.getProject(req.params.projectId);
      if (!project) {
        return res.status(404).json({ error: "Project not found" });
      }

      // Trigger YouTube upload
      processPythonScript('upload_video', {
        projectId: project.id,
        videoPath: project.outputPath,
        title: project.title,
        description: project.description,
        thumbnailPath: project.thumbnailPath
      });

      await storage.updateProject(project.id, { status: 'uploading' });
      res.json({ message: "Upload started" });
    } catch (error) {
      res.status(500).json({ error: "Failed to start upload" });
    }
  });

  // System status endpoints
  app.get("/api/system-status", async (req, res) => {
    try {
      const status = await storage.getSystemStatus();
      res.json(status);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch system status" });
    }
  });

  // Thumbnail generation
  app.post("/api/thumbnails/generate", async (req, res) => {
    try {
      const { text, projectId } = req.body;
      
      processPythonScript('generate_thumbnail', {
        projectId,
        text,
        outputPath: `thumbnails/thumb_${projectId}.jpg`
      });

      res.json({ message: "Thumbnail generation started" });
    } catch (error) {
      res.status(500).json({ error: "Failed to generate thumbnail" });
    }
  });

  // File upload endpoint
  app.post("/api/upload-file", upload.single('video'), async (req, res) => {
    try {
      if (!req.file) {
        return res.status(400).json({ error: "No file uploaded" });
      }

      // Process uploaded file
      const project = await storage.createProject({
        title: req.body.title || "Untitled Project",
        description: req.body.description || "",
        status: "processing",
        sourceUrl: req.file.path,
        sourceText: req.body.text || ""
      });

      processPythonScript('process_uploaded_video', {
        projectId: project.id,
        inputPath: req.file.path,
        memeText: req.body.text || project.title
      });

      res.status(201).json(project);
    } catch (error) {
      res.status(500).json({ error: "Failed to process uploaded file" });
    }
  });

  const httpServer = createServer(app);
  return httpServer;
}
