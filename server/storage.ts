import { 
  projects, 
  contentSources, 
  analytics, 
  uploadQueue, 
  systemStatus,
  users,
  type User, 
  type InsertUser,
  type Project,
  type InsertProject,
  type ContentSource,
  type InsertContentSource,
  type Analytics,
  type InsertAnalytics,
  type UploadQueue,
  type InsertUploadQueue,
  type SystemStatus,
  type InsertSystemStatus
} from "@shared/schema";
import { db } from "./db";
import { eq, desc, asc, and, gte, lte } from "drizzle-orm";

export interface IStorage {
  // Users
  getUser(id: string): Promise<User | undefined>;
  getUserByUsername(username: string): Promise<User | undefined>;
  createUser(user: InsertUser): Promise<User>;

  // Projects
  getProjects(userId?: string): Promise<Project[]>;
  getProject(id: string): Promise<Project | undefined>;
  createProject(project: InsertProject): Promise<Project>;
  updateProject(id: string, project: Partial<InsertProject>): Promise<Project | undefined>;
  deleteProject(id: string): Promise<boolean>;

  // Content Sources
  getContentSources(limit?: number): Promise<ContentSource[]>;
  createContentSource(source: InsertContentSource): Promise<ContentSource>;
  updateContentSource(id: string, source: Partial<InsertContentSource>): Promise<ContentSource | undefined>;
  getTrendingContent(limit?: number): Promise<ContentSource[]>;

  // Analytics
  getProjectAnalytics(projectId: string): Promise<Analytics[]>;
  createAnalytics(analytics: InsertAnalytics): Promise<Analytics>;
  getChannelAnalytics(startDate?: Date, endDate?: Date): Promise<Analytics[]>;

  // Upload Queue
  getUploadQueue(): Promise<UploadQueue[]>;
  addToUploadQueue(item: InsertUploadQueue): Promise<UploadQueue>;
  updateUploadQueueItem(id: string, item: Partial<InsertUploadQueue>): Promise<UploadQueue | undefined>;
  removeFromUploadQueue(id: string): Promise<boolean>;

  // System Status
  getSystemStatus(): Promise<SystemStatus[]>;
  updateSystemStatus(service: string, status: InsertSystemStatus): Promise<SystemStatus>;
}

export class DatabaseStorage implements IStorage {
  // Users
  async getUser(id: string): Promise<User | undefined> {
    const [user] = await db.select().from(users).where(eq(users.id, id));
    return user || undefined;
  }

  async getUserByUsername(username: string): Promise<User | undefined> {
    const [user] = await db.select().from(users).where(eq(users.username, username));
    return user || undefined;
  }

  async createUser(insertUser: InsertUser): Promise<User> {
    const [user] = await db
      .insert(users)
      .values(insertUser)
      .returning();
    return user;
  }

  // Projects
  async getProjects(userId?: string): Promise<Project[]> {
    if (userId) {
      return await db.select().from(projects)
        .where(eq(projects.userId, userId))
        .orderBy(desc(projects.createdAt));
    }
    return await db.select().from(projects)
      .orderBy(desc(projects.createdAt));
  }

  async getProject(id: string): Promise<Project | undefined> {
    const [project] = await db.select().from(projects).where(eq(projects.id, id));
    return project || undefined;
  }

  async createProject(project: InsertProject): Promise<Project> {
    const [newProject] = await db
      .insert(projects)
      .values([project])
      .returning();
    return newProject;
  }

  async updateProject(id: string, project: Partial<InsertProject>): Promise<Project | undefined> {
    const updateData: any = { ...project, updatedAt: new Date() };
    const [updatedProject] = await db
      .update(projects)
      .set(updateData)
      .where(eq(projects.id, id))
      .returning();
    return updatedProject || undefined;
  }

  async deleteProject(id: string): Promise<boolean> {
    const result = await db.delete(projects).where(eq(projects.id, id));
    return (result.rowCount ?? 0) > 0;
  }

  // Content Sources
  async getContentSources(limit = 50): Promise<ContentSource[]> {
    return await db
      .select()
      .from(contentSources)
      .orderBy(desc(contentSources.createdAt))
      .limit(limit);
  }

  async createContentSource(source: InsertContentSource): Promise<ContentSource> {
    const [newSource] = await db
      .insert(contentSources)
      .values([source])
      .returning();
    return newSource;
  }

  async updateContentSource(id: string, source: Partial<InsertContentSource>): Promise<ContentSource | undefined> {
    const updateData: any = source;
    const [updatedSource] = await db
      .update(contentSources)
      .set(updateData)
      .where(eq(contentSources.id, id))
      .returning();
    return updatedSource || undefined;
  }

  async getTrendingContent(limit = 10): Promise<ContentSource[]> {
    return await db
      .select()
      .from(contentSources)
      .where(eq(contentSources.isProcessed, false))
      .orderBy(desc(contentSources.trendingScore))
      .limit(limit);
  }

  // Analytics
  async getProjectAnalytics(projectId: string): Promise<Analytics[]> {
    return await db
      .select()
      .from(analytics)
      .where(eq(analytics.projectId, projectId))
      .orderBy(desc(analytics.date));
  }

  async createAnalytics(analyticsData: InsertAnalytics): Promise<Analytics> {
    const [newAnalytics] = await db
      .insert(analytics)
      .values(analyticsData)
      .returning();
    return newAnalytics;
  }

  async getChannelAnalytics(startDate?: Date, endDate?: Date): Promise<Analytics[]> {
    if (startDate && endDate) {
      return await db.select().from(analytics)
        .where(and(
          gte(analytics.date, startDate),
          lte(analytics.date, endDate)
        ))
        .orderBy(desc(analytics.date));
    }
    
    return await db.select().from(analytics)
      .orderBy(desc(analytics.date));
  }

  // Upload Queue
  async getUploadQueue(): Promise<UploadQueue[]> {
    return await db
      .select()
      .from(uploadQueue)
      .orderBy(asc(uploadQueue.scheduledTime));
  }

  async addToUploadQueue(item: InsertUploadQueue): Promise<UploadQueue> {
    const [newItem] = await db
      .insert(uploadQueue)
      .values(item)
      .returning();
    return newItem;
  }

  async updateUploadQueueItem(id: string, item: Partial<InsertUploadQueue>): Promise<UploadQueue | undefined> {
    const [updatedItem] = await db
      .update(uploadQueue)
      .set(item)
      .where(eq(uploadQueue.id, id))
      .returning();
    return updatedItem || undefined;
  }

  async removeFromUploadQueue(id: string): Promise<boolean> {
    const result = await db.delete(uploadQueue).where(eq(uploadQueue.id, id));
    return (result.rowCount ?? 0) > 0;
  }

  // System Status
  async getSystemStatus(): Promise<SystemStatus[]> {
    return await db.select().from(systemStatus);
  }

  async updateSystemStatus(service: string, statusData: InsertSystemStatus): Promise<SystemStatus> {
    const insertData: any = { ...statusData, service };
    const updateData: any = { ...statusData, lastUpdate: new Date() };
    const [updatedStatus] = await db
      .insert(systemStatus)
      .values([insertData])
      .onConflictDoUpdate({
        target: systemStatus.service,
        set: updateData
      })
      .returning();
    return updatedStatus;
  }
}

export const storage = new DatabaseStorage();
