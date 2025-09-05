#!/usr/bin/env python3

import os
import sys
import argparse
import logging
import json
from pathlib import Path
from typing import Dict, Any

try:
    import moviepy.editor as mp
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    from pydub import AudioSegment, effects
    import requests
except ImportError as e:
    print(f"Missing required dependency: {e}")
    print("Please run: pip install -r requirements.txt")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('automation.log'),
        logging.StreamHandler()
    ]
)

class VideoProcessor:
    def __init__(self, config_path: str = "config.json"):
        self.config = self.load_config(config_path)
        self.setup_directories()

    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logging.warning(f"Config file {config_path} not found, using defaults")
            return {
                "video": {
                    "max_duration": 8,
                    "output_format": "mp4",
                    "quality": "high",
                    "fps": 30
                },
                "audio": {
                    "normalize": True,
                    "fade_in": 0.5,
                    "fade_out": 0.5
                },
                "text": {
                    "font_size": 50,
                    "font_color": "white",
                    "bg_color": "black",
                    "position": "top"
                }
            }

    def setup_directories(self):
        """Create necessary directories"""
        directories = ['downloads', 'edited', 'thumbnails', 'temp']
        for directory in directories:
            Path(directory).mkdir(exist_ok=True)

    def download_video(self, url: str, output_path: str) -> bool:
        """Download video from URL"""
        try:
            logging.info(f"Downloading video from: {url}")
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logging.info(f"Successfully downloaded: {output_path}")
            return True
        except Exception as e:
            logging.error(f"Failed to download {url}: {e}")
            return False

    def process_video(self, input_path: str, output_path: str, meme_text: str = "", 
                     glitch_effect: bool = True) -> bool:
        """Process video with effects and overlays"""
        try:
            logging.info(f"Processing video: {input_path}")
            
            # Load video clip
            clip = mp.VideoFileClip(input_path)
            
            # Trim to max duration
            max_duration = self.config["video"]["max_duration"]
            if clip.duration > max_duration:
                clip = clip.subclip(0, max_duration)
            
            # Add glitch effects if requested
            if glitch_effect:
                clip = self.add_glitch_effects(clip)
            
            # Add text overlay if provided
            if meme_text:
                clip = self.add_text_overlay(clip, meme_text)
            
            # Enhance audio
            clip = self.enhance_audio(clip)
            
            # Write final video
            clip.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp/temp-audio.m4a',
                remove_temp=True,
                fps=self.config["video"]["fps"]
            )
            
            clip.close()
            logging.info(f"Successfully processed: {output_path}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to process video {input_path}: {e}")
            return False

    def add_glitch_effects(self, clip):
        """Add cyberpunk glitch effects to video"""
        try:
            # Create glitch effect by duplicating and offsetting frames
            def glitch_frame(get_frame, t):
                frame = get_frame(t)
                if int(t * 10) % 7 == 0:  # Glitch every ~0.7 seconds
                    # Add slight color channel shift
                    frame = frame.copy()
                    frame[:, :, 0] = frame[:, :, 0] * 1.2  # Boost red channel
                    frame[:, :, 2] = frame[:, :, 2] * 0.8  # Reduce blue channel
                return frame
            
            return clip.fl(glitch_frame)
        except Exception as e:
            logging.warning(f"Failed to add glitch effects: {e}")
            return clip

    def add_text_overlay(self, clip, text: str):
        """Add text overlay with 404 Circus styling"""
        try:
            # Create text clip
            txt_clip = mp.TextClip(
                text,
                fontsize=self.config["text"]["font_size"],
                color=self.config["text"]["font_color"],
                bg_color=self.config["text"]["bg_color"],
                method='caption',
                size=(clip.w * 0.9, None),
                align='center'
            )
            
            # Position text
            position = self.config["text"]["position"]
            if position == "top":
                txt_clip = txt_clip.set_position(('center', 50))
            elif position == "bottom":
                txt_clip = txt_clip.set_position(('center', clip.h - 100))
            else:
                txt_clip = txt_clip.set_position('center')
            
            # Set duration and add effects
            txt_clip = txt_clip.set_duration(clip.duration)
            
            # Composite with main clip
            return mp.CompositeVideoClip([clip, txt_clip])
            
        except Exception as e:
            logging.warning(f"Failed to add text overlay: {e}")
            return clip

    def enhance_audio(self, clip):
        """Enhance audio quality and add effects"""
        try:
            if clip.audio is None:
                return clip
            
            audio_config = self.config["audio"]
            
            if audio_config.get("normalize", False):
                # Basic audio normalization via moviepy
                clip = clip.volumex(1.2)  # Slight volume boost
            
            # Add fade effects
            fade_in = audio_config.get("fade_in", 0)
            fade_out = audio_config.get("fade_out", 0)
            
            if fade_in > 0:
                clip = clip.audio_fadein(fade_in)
            if fade_out > 0:
                clip = clip.audio_fadeout(fade_out)
            
            return clip
            
        except Exception as e:
            logging.warning(f"Failed to enhance audio: {e}")
            return clip

    def create_thumbnail(self, video_path: str, output_path: str, 
                        title: str = "", glitch_style: bool = True) -> bool:
        """Create thumbnail from video with 404 Circus branding"""
        try:
            logging.info(f"Creating thumbnail for: {video_path}")
            
            # Extract frame from middle of video
            clip = mp.VideoFileClip(video_path)
            frame = clip.get_frame(clip.duration / 2)
            clip.close()
            
            # Convert to PIL Image
            img = Image.fromarray(frame)
            img = img.resize((1280, 720), Image.Resampling.LANCZOS)
            
            if glitch_style:
                img = self.apply_glitch_thumbnail(img)
            
            # Add title text
            if title:
                img = self.add_thumbnail_text(img, title)
            
            # Save thumbnail
            img.save(output_path, "JPEG", quality=95)
            logging.info(f"Thumbnail created: {output_path}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to create thumbnail: {e}")
            return False

    def apply_glitch_thumbnail(self, img: Image.Image) -> Image.Image:
        """Apply glitch effects to thumbnail"""
        try:
            # Create color channel shifts
            r, g, b = img.split()
            
            # Shift red channel
            r_shifted = Image.new('L', img.size)
            r_shifted.paste(r, (5, 0))
            
            # Shift blue channel
            b_shifted = Image.new('L', img.size)
            b_shifted.paste(b, (-3, 2))
            
            # Recombine with effects
            glitch_img = Image.merge('RGB', (r_shifted, g, b_shifted))
            
            # Add slight blur for CRT effect
            glitch_img = glitch_img.filter(ImageFilter.GaussianBlur(radius=0.5))
            
            return glitch_img
            
        except Exception as e:
            logging.warning(f"Failed to apply glitch effect: {e}")
            return img

    def add_thumbnail_text(self, img: Image.Image, title: str) -> Image.Image:
        """Add title text to thumbnail"""
        try:
            draw = ImageDraw.Draw(img)
            
            # Try to load custom font, fall back to default
            try:
                font = ImageFont.truetype("arial.ttf", 60)
            except:
                font = ImageFont.load_default()
            
            # Add text with outline for visibility
            x, y = 50, img.height - 150
            
            # Draw outline
            for adj in range(-2, 3):
                for adj2 in range(-2, 3):
                    draw.text((x + adj, y + adj2), title, font=font, fill=(0, 0, 0))
            
            # Draw main text
            draw.text((x, y), title, font=font, fill=(0, 255, 0))  # Neon green
            
            return img
            
        except Exception as e:
            logging.warning(f"Failed to add thumbnail text: {e}")
            return img

def main():
    parser = argparse.ArgumentParser(description='404 Circus Video Processor')
    parser.add_argument('--projectId', required=True, help='Project ID')
    parser.add_argument('--sourceUrl', help='Source video URL')
    parser.add_argument('--inputPath', help='Input video path')
    parser.add_argument('--memeText', help='Text overlay for video')
    parser.add_argument('--outputPath', help='Output video path')
    parser.add_argument('--thumbnailPath', help='Output thumbnail path')
    parser.add_argument('--title', help='Video title for thumbnail')
    
    args = parser.parse_args()
    
    processor = VideoProcessor()
    
    try:
        project_id = args.projectId
        base_name = f"video_{project_id}"
        
        # Determine input and output paths
        if args.sourceUrl:
            input_path = f"downloads/{base_name}.mp4"
            if not processor.download_video(args.sourceUrl, input_path):
                sys.exit(1)
        elif args.inputPath:
            input_path = args.inputPath
        else:
            logging.error("Either --sourceUrl or --inputPath must be provided")
            sys.exit(1)
        
        output_path = args.outputPath or f"edited/{base_name}_edited.mp4"
        
        # Process video
        success = processor.process_video(
            input_path, 
            output_path, 
            args.memeText or "",
            glitch_effect=True
        )
        
        if not success:
            logging.error("Video processing failed")
            sys.exit(1)
        
        # Create thumbnail if requested
        if args.thumbnailPath:
            thumbnail_path = args.thumbnailPath
        else:
            thumbnail_path = f"thumbnails/{base_name}_thumb.jpg"
            
        processor.create_thumbnail(
            output_path,
            thumbnail_path,
            args.title or args.memeText or "404 Circus",
            glitch_style=True
        )
        
        logging.info(f"Processing completed successfully for project {project_id}")
        print(f"SUCCESS: {output_path}")
        
    except Exception as e:
        logging.error(f"Processing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
