#!/usr/bin/env python3

import os
import sys
import argparse
import logging
import json
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
    import numpy as np
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

class ThumbnailGenerator:
    def __init__(self, config_path: str = "config.json"):
        self.config = self.load_config(config_path)
        self.width = 1280
        self.height = 720

    def load_config(self, config_path: str) -> dict:
        """Load thumbnail configuration"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "thumbnail": {
                    "styles": {
                        "glitch": {
                            "primary_color": (0, 255, 0),  # Neon green
                            "secondary_color": (255, 0, 0),  # Red
                            "bg_color": (10, 10, 15),  # Dark blue-black
                            "text_color": (255, 255, 255)
                        },
                        "error": {
                            "primary_color": (255, 0, 0),  # Red
                            "secondary_color": (255, 255, 0),  # Yellow
                            "bg_color": (20, 0, 0),  # Dark red
                            "text_color": (255, 255, 255)
                        },
                        "matrix": {
                            "primary_color": (0, 255, 0),  # Matrix green
                            "secondary_color": (0, 180, 0),  # Darker green
                            "bg_color": (0, 0, 0),  # Black
                            "text_color": (0, 255, 0)
                        }
                    }
                }
            }

    def create_glitch_thumbnail(self, text: str, output_path: str, 
                               base_image: str = None, style: str = "glitch") -> bool:
        """Create a glitch-style thumbnail"""
        try:
            logging.info(f"Creating {style} thumbnail: {text}")
            
            # Get style configuration
            style_config = self.config["thumbnail"]["styles"].get(style, 
                self.config["thumbnail"]["styles"]["glitch"])
            
            # Create base image
            if base_image and os.path.exists(base_image):
                img = Image.open(base_image).resize((self.width, self.height))
            else:
                img = self.create_background(style_config)
            
            # Apply glitch effects
            img = self.apply_glitch_effects(img, style_config)
            
            # Add text overlay
            img = self.add_text_overlay(img, text, style_config)
            
            # Add branding
            img = self.add_branding(img, style_config)
            
            # Save thumbnail
            img.save(output_path, "JPEG", quality=95, optimize=True)
            logging.info(f"Thumbnail saved: {output_path}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to create thumbnail: {e}")
            return False

    def create_background(self, style_config: dict) -> Image.Image:
        """Create stylized background"""
        img = Image.new('RGB', (self.width, self.height), style_config["bg_color"])
        
        # Add gradient overlay
        gradient = self.create_gradient(style_config)
        img = Image.alpha_composite(img.convert('RGBA'), gradient).convert('RGB')
        
        # Add noise for texture
        noise = self.add_noise(img)
        return noise

    def create_gradient(self, style_config: dict) -> Image.Image:
        """Create gradient overlay"""
        gradient = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(gradient)
        
        primary = style_config["primary_color"] + (50,)  # Add alpha
        secondary = style_config["secondary_color"] + (30,)
        
        # Create diagonal gradient effect
        for i in range(self.height):
            alpha = int(50 * (i / self.height))
            color = tuple(int(primary[j] + (secondary[j] - primary[j]) * (i / self.height)) 
                         for j in range(3)) + (alpha,)
            draw.line([(0, i), (self.width, i)], fill=color)
        
        return gradient

    def add_noise(self, img: Image.Image) -> Image.Image:
        """Add noise texture to image"""
        try:
            # Convert to numpy for noise generation
            img_array = np.array(img)
            
            # Generate noise
            noise = np.random.randint(-20, 20, img_array.shape, dtype=np.int16)
            
            # Add noise to image
            noisy = np.clip(img_array.astype(np.int16) + noise, 0, 255).astype(np.uint8)
            
            return Image.fromarray(noisy)
        except:
            return img  # Return original if noise fails

    def apply_glitch_effects(self, img: Image.Image, style_config: dict) -> Image.Image:
        """Apply glitch visual effects"""
        try:
            # Create RGB channel shifts
            r, g, b = img.split()
            
            # Shift red channel
            r_array = np.array(r)
            r_shifted = np.roll(r_array, 5, axis=1)  # Horizontal shift
            r_shifted = Image.fromarray(r_shifted)
            
            # Shift blue channel
            b_array = np.array(b)
            b_shifted = np.roll(b_array, -3, axis=1)  # Opposite shift
            b_shifted = Image.fromarray(b_shifted)
            
            # Recombine with effects
            glitched = Image.merge('RGB', (r_shifted, g, b_shifted))
            
            # Add scan lines
            glitched = self.add_scan_lines(glitched)
            
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(glitched)
            glitched = enhancer.enhance(1.3)
            
            return glitched
            
        except Exception as e:
            logging.warning(f"Failed to apply glitch effects: {e}")
            return img

    def add_scan_lines(self, img: Image.Image) -> Image.Image:
        """Add retro CRT scan lines"""
        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Draw horizontal lines every few pixels
        for y in range(0, self.height, 4):
            draw.line([(0, y), (self.width, y)], fill=(0, 0, 0, 30))
        
        # Composite with original
        return Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')

    def add_text_overlay(self, img: Image.Image, text: str, style_config: dict) -> Image.Image:
        """Add text overlay with effects"""
        try:
            draw = ImageDraw.Draw(img)
            
            # Try to load fonts
            try:
                title_font = ImageFont.truetype("arial.ttf", 60)
                subtitle_font = ImageFont.truetype("arial.ttf", 30)
            except:
                title_font = ImageFont.load_default()
                subtitle_font = ImageFont.load_default()
            
            # Prepare text
            lines = self.wrap_text(text, 25)  # Wrap long text
            
            # Calculate positioning
            y_start = self.height - 180
            text_color = style_config["text_color"]
            
            # Add text shadow/outline
            shadow_offset = 3
            for line_num, line in enumerate(lines):
                y = y_start + (line_num * 70)
                x = 50
                
                # Draw shadow
                for dx in range(-shadow_offset, shadow_offset + 1):
                    for dy in range(-shadow_offset, shadow_offset + 1):
                        if dx != 0 or dy != 0:
                            draw.text((x + dx, y + dy), line, font=title_font, fill=(0, 0, 0))
                
                # Draw main text
                draw.text((x, y), line, font=title_font, fill=text_color)
            
            return img
            
        except Exception as e:
            logging.warning(f"Failed to add text overlay: {e}")
            return img

    def wrap_text(self, text: str, width: int) -> list:
        """Wrap text to fit in thumbnail"""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            if len(test_line) <= width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Limit to 2 lines
        return lines[:2]

    def add_branding(self, img: Image.Image, style_config: dict) -> Image.Image:
        """Add 404 Circus branding"""
        try:
            draw = ImageDraw.Draw(img)
            
            # Try to load font for branding
            try:
                brand_font = ImageFont.truetype("arial.ttf", 40)
            except:
                brand_font = ImageFont.load_default()
            
            # Brand text
            brand_text = "404 CIRCUS"
            brand_color = style_config["primary_color"]
            
            # Position in top-right
            text_bbox = draw.textbbox((0, 0), brand_text, font=brand_font)
            text_width = text_bbox[2] - text_bbox[0]
            x = self.width - text_width - 30
            y = 30
            
            # Add glow effect
            for offset in range(1, 4):
                draw.text((x - offset, y), brand_text, font=brand_font, 
                         fill=tuple(max(0, c - 50) for c in brand_color))
                draw.text((x + offset, y), brand_text, font=brand_font, 
                         fill=tuple(max(0, c - 50) for c in brand_color))
                draw.text((x, y - offset), brand_text, font=brand_font, 
                         fill=tuple(max(0, c - 50) for c in brand_color))
                draw.text((x, y + offset), brand_text, font=brand_font, 
                         fill=tuple(max(0, c - 50) for c in brand_color))
            
            # Main brand text
            draw.text((x, y), brand_text, font=brand_font, fill=brand_color)
            
            return img
            
        except Exception as e:
            logging.warning(f"Failed to add branding: {e}")
            return img

def main():
    parser = argparse.ArgumentParser(description='404 Circus Thumbnail Generator')
    parser.add_argument('--projectId', help='Project ID')
    parser.add_argument('--text', required=True, help='Thumbnail text')
    parser.add_argument('--outputPath', required=True, help='Output thumbnail path')
    parser.add_argument('--baseImage', help='Base image path (optional)')
    parser.add_argument('--style', choices=['glitch', 'error', 'matrix'], 
                       default='glitch', help='Thumbnail style')
    
    args = parser.parse_args()
    
    generator = ThumbnailGenerator()
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.outputPath), exist_ok=True)
    
    try:
        success = generator.create_glitch_thumbnail(
            text=args.text,
            output_path=args.outputPath,
            base_image=args.baseImage,
            style=args.style
        )
        
        if success:
            print(f"SUCCESS: {args.outputPath}")
            if args.projectId:
                logging.info(f"Thumbnail generated for project {args.projectId}")
        else:
            logging.error("Thumbnail generation failed")
            sys.exit(1)
            
    except Exception as e:
        logging.error(f"Thumbnail generation process failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
