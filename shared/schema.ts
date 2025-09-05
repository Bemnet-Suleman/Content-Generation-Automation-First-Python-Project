import { sql, relations } from "drizzle-orm";
import { pgTable, text, varchar, integer, timestamp, boolean, json, decimal } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

export const users = pgTable("users", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  username: text("username").notNull().unique(),
  password: text("password").notNull(),
});

export const projects = pgTable("projects", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  title: text("title").notNull(),
  description: text("description"),
  status: text("status").notNull().default("draft"), // draft, processing, ready, uploaded, error
  progress: integer("progress").notNull().default(0),
  sourceUrl: text("source_url"),
  sourceText: text("source_text"),
  outputPath: text("output_path"),
  thumbnailPath: text("thumbnail_path"),
  youtubeVideoId: text("youtube_video_id"),
  scheduledUploadTime: timestamp("scheduled_upload_time"),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").defaultNow().notNull(),
  userId: varchar("user_id").references(() => users.id),
  metadata: json("metadata").$type<{
    tags?: string[];
    category?: string;
    duration?: number;
    fileSize?: number;
    error?: string;
  }>(),
});

export const contentSources = pgTable("content_sources", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  url: text("url").notNull(),
  title: text("title").notNull(),
  description: text("description"),
  source: text("source").notNull(), // reddit, tiktok, twitter, etc.
  upvotes: integer("upvotes").default(0),
  views: integer("views").default(0),
  likes: integer("likes").default(0),
  trendingScore: integer("trending_score").default(0),
  tags: json("tags").$type<string[]>().default([]),
  thumbnailUrl: text("thumbnail_url"),
  isProcessed: boolean("is_processed").default(false),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

export const analytics = pgTable("analytics", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  projectId: varchar("project_id").references(() => projects.id),
  views: integer("views").default(0),
  likes: integer("likes").default(0),
  dislikes: integer("dislikes").default(0),
  comments: integer("comments").default(0),
  shares: integer("shares").default(0),
  revenue: decimal("revenue", { precision: 10, scale: 2 }).default("0.00"),
  watchTime: integer("watch_time").default(0), // in seconds
  impressions: integer("impressions").default(0),
  clickThroughRate: decimal("click_through_rate", { precision: 5, scale: 2 }).default("0.00"),
  date: timestamp("date").defaultNow().notNull(),
});

export const uploadQueue = pgTable("upload_queue", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  projectId: varchar("project_id").references(() => projects.id).notNull(),
  scheduledTime: timestamp("scheduled_time").notNull(),
  status: text("status").notNull().default("pending"), // pending, uploading, completed, failed
  retryCount: integer("retry_count").default(0),
  error: text("error"),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

export const systemStatus = pgTable("system_status", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  service: text("service").notNull().unique(), // content_scraper, video_processor, upload_manager, analytics_engine
  status: text("status").notNull(), // online, offline, processing, error
  lastUpdate: timestamp("last_update").defaultNow().notNull(),
  metadata: json("metadata").$type<{
    queueSize?: number;
    lastScan?: string;
    error?: string;
  }>(),
});

// Relations
export const projectsRelations = relations(projects, ({ one, many }) => ({
  user: one(users, { fields: [projects.userId], references: [users.id] }),
  analytics: many(analytics),
  uploadQueue: one(uploadQueue),
}));

export const analyticsRelations = relations(analytics, ({ one }) => ({
  project: one(projects, { fields: [analytics.projectId], references: [projects.id] }),
}));

export const uploadQueueRelations = relations(uploadQueue, ({ one }) => ({
  project: one(projects, { fields: [uploadQueue.projectId], references: [projects.id] }),
}));

// Insert schemas
export const insertProjectSchema = createInsertSchema(projects).omit({
  id: true,
  createdAt: true,
  updatedAt: true,
});

export const insertContentSourceSchema = createInsertSchema(contentSources).omit({
  id: true,
  createdAt: true,
});

export const insertAnalyticsSchema = createInsertSchema(analytics).omit({
  id: true,
  date: true,
});

export const insertUploadQueueSchema = createInsertSchema(uploadQueue).omit({
  id: true,
  createdAt: true,
});

export const insertSystemStatusSchema = createInsertSchema(systemStatus).omit({
  id: true,
  lastUpdate: true,
});

// Types
export type InsertProject = z.infer<typeof insertProjectSchema>;
export type Project = typeof projects.$inferSelect;
export type InsertContentSource = z.infer<typeof insertContentSourceSchema>;
export type ContentSource = typeof contentSources.$inferSelect;
export type InsertAnalytics = z.infer<typeof insertAnalyticsSchema>;
export type Analytics = typeof analytics.$inferSelect;
export type InsertUploadQueue = z.infer<typeof insertUploadQueueSchema>;
export type UploadQueue = typeof uploadQueue.$inferSelect;
export type InsertSystemStatus = z.infer<typeof insertSystemStatusSchema>;
export type SystemStatus = typeof systemStatus.$inferSelect;

export type InsertUser = z.infer<typeof insertUserSchema>;
export type User = typeof users.$inferSelect;

export const insertUserSchema = createInsertSchema(users).pick({
  username: true,
  password: true,
});
