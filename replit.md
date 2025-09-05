# Replit Configuration

## Overview

The 404 Circus project is a YouTube automation platform designed to create viral tech fail compilation videos. The system automates content discovery, video processing, thumbnail generation, and YouTube uploads through a full-stack web application with Python automation scripts.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: React with TypeScript using Vite as the build tool
- **UI System**: Shadcn/ui components with Radix UI primitives for consistent design
- **Styling**: Tailwind CSS with custom CSS variables for dark theme
- **State Management**: TanStack Query for server state management
- **Routing**: Wouter for lightweight client-side routing
- **Design Theme**: Cyberpunk/hacker aesthetic with neon green accents and dark backgrounds

### Backend Architecture
- **Runtime**: Node.js with Express.js framework
- **Language**: TypeScript with ES modules
- **Database ORM**: Drizzle ORM for type-safe database operations
- **API Design**: RESTful endpoints following conventional patterns
- **File Processing**: Integration with Python scripts for video/image processing
- **Session Management**: Express sessions with PostgreSQL storage

### Database Schema
- **Users**: Basic user authentication and management
- **Projects**: Video project lifecycle tracking (draft, processing, ready, uploaded, error)
- **Content Sources**: Scraped content from Reddit, TikTok, Twitter with trending scores
- **Analytics**: YouTube metrics tracking (views, likes, comments, revenue, watch time)
- **Upload Queue**: Scheduled upload management with retry logic
- **System Status**: Service health monitoring for automation components

### Python Automation Layer
- **Content Scraping**: Automated discovery from social media platforms
- **Video Processing**: MoviePy for video editing, effects, and compilation
- **Thumbnail Generation**: PIL/Pillow for custom thumbnail creation with glitch effects
- **YouTube Integration**: Google API client for automated uploads with metadata
- **Health Monitoring**: System status checks and dependency validation

### Development Workflow
- **Monorepo Structure**: Shared TypeScript types between client/server
- **Hot Reloading**: Vite development server with backend proxy
- **Type Safety**: Strict TypeScript configuration across all layers
- **Path Aliases**: Organized imports with `@/` for client and `@shared/` for common code

## External Dependencies

### Database
- **Neon PostgreSQL**: Serverless PostgreSQL database with connection pooling
- **Drizzle Kit**: Database migrations and schema management

### YouTube Platform
- **Google APIs**: YouTube Data API v3 for video uploads and metadata management
- **OAuth 2.0**: Google authentication for YouTube channel access

### Content Sources
- **Reddit API**: PRAW (Python Reddit API Wrapper) for content discovery
- **Social Media APIs**: BeautifulSoup for web scraping when APIs are unavailable

### Media Processing
- **FFmpeg**: Required system dependency for video processing
- **MoviePy**: Python video editing library built on FFmpeg
- **Pillow**: Python image processing for thumbnail generation
- **Pydub**: Audio processing and manipulation

### Development Tools
- **Replit Environment**: Cloud development with specific Replit integrations
- **Vite Plugins**: Runtime error overlay and development enhancements

### Third-Party Services
- **File Storage**: Local file system for video/image assets with upload directory
- **Session Store**: PostgreSQL-backed session storage using connect-pg-simple
- **Health Monitoring**: Custom health check system for Python automation services