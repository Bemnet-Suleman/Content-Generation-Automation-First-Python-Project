#!/usr/bin/env python3

import os
import sys
import json
import logging
import subprocess
import time
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class HealthCheck:
    def __init__(self):
        self.checks = {
            'python_environment': self.check_python_environment,
            'dependencies': self.check_dependencies,
            'directories': self.check_directories,
            'disk_space': self.check_disk_space,
            'ffmpeg': self.check_ffmpeg
        }

    def check_python_environment(self) -> dict:
        """Check Python version and environment"""
        try:
            version = sys.version_info
            result = {
                'status': 'healthy',
                'version': f"{version.major}.{version.minor}.{version.micro}",
                'executable': sys.executable
            }
            
            if version.major < 3 or (version.major == 3 and version.minor < 7):
                result['status'] = 'warning'
                result['message'] = 'Python 3.7+ recommended'
            
            return result
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def check_dependencies(self) -> dict:
        """Check required Python packages"""
        required_packages = [
            'moviepy', 'pillow', 'pydub', 'requests', 
            'google-api-python-client', 'google-auth-oauthlib'
        ]
        
        missing = []
        installed = []
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                installed.append(package)
            except ImportError:
                missing.append(package)
        
        if missing:
            return {
                'status': 'error',
                'message': f'Missing packages: {", ".join(missing)}',
                'missing': missing,
                'installed': installed
            }
        else:
            return {
                'status': 'healthy',
                'message': 'All dependencies installed',
                'installed': installed
            }

    def check_directories(self) -> dict:
        """Check required directories exist"""
        required_dirs = ['downloads', 'edited', 'thumbnails', 'temp']
        status = 'healthy'
        missing = []
        existing = []
        
        for directory in required_dirs:
            if Path(directory).exists():
                existing.append(directory)
            else:
                missing.append(directory)
                try:
                    Path(directory).mkdir(exist_ok=True)
                    existing.append(directory)
                except Exception:
                    status = 'error'
        
        return {
            'status': status,
            'existing': existing,
            'missing': missing,
            'message': f'Directories checked: {len(existing)}/{len(required_dirs)}'
        }

    def check_disk_space(self) -> dict:
        """Check available disk space"""
        try:
            statvfs = os.statvfs('.')
            free_bytes = statvfs.f_frsize * statvfs.f_bavail
            total_bytes = statvfs.f_frsize * statvfs.f_blocks
            
            free_gb = free_bytes / (1024**3)
            total_gb = total_bytes / (1024**3)
            used_percent = (1 - free_bytes/total_bytes) * 100
            
            status = 'healthy'
            if free_gb < 5:
                status = 'error'
                message = 'Less than 5GB free space'
            elif free_gb < 20:
                status = 'warning'
                message = 'Less than 20GB free space'
            else:
                message = f'{free_gb:.1f}GB available'
            
            return {
                'status': status,
                'message': message,
                'free_gb': round(free_gb, 1),
                'total_gb': round(total_gb, 1),
                'used_percent': round(used_percent, 1)
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def check_ffmpeg(self) -> dict:
        """Check if FFmpeg is available"""
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                # Extract version from output
                lines = result.stdout.split('\n')
                version_line = next((line for line in lines if 'ffmpeg version' in line), '')
                version = version_line.split(' ')[2] if version_line else 'unknown'
                
                return {
                    'status': 'healthy',
                    'version': version,
                    'message': 'FFmpeg available'
                }
            else:
                return {
                    'status': 'error',
                    'message': 'FFmpeg not working properly'
                }
        except subprocess.TimeoutExpired:
            return {'status': 'error', 'message': 'FFmpeg check timed out'}
        except FileNotFoundError:
            return {
                'status': 'error',
                'message': 'FFmpeg not found in PATH'
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def run_all_checks(self) -> dict:
        """Run all health checks"""
        results = {}
        overall_status = 'healthy'
        
        for check_name, check_func in self.checks.items():
            logging.info(f"Running check: {check_name}")
            results[check_name] = check_func()
            
            # Update overall status
            if results[check_name]['status'] == 'error':
                overall_status = 'error'
            elif results[check_name]['status'] == 'warning' and overall_status != 'error':
                overall_status = 'warning'
        
        return {
            'timestamp': time.time(),
            'overall_status': overall_status,
            'checks': results
        }

def main():
    """Main health check function"""
    health_check = HealthCheck()
    
    try:
        logging.info("Starting system health check...")
        results = health_check.run_all_checks()
        
        # Print results
        print(f"\nSystem Health Check Results")
        print(f"Overall Status: {results['overall_status'].upper()}")
        print("-" * 50)
        
        for check_name, check_result in results['checks'].items():
            status_indicator = {
                'healthy': '✓',
                'warning': '⚠',
                'error': '✗'
            }.get(check_result['status'], '?')
            
            print(f"{status_indicator} {check_name}: {check_result.get('message', check_result['status'])}")
            
            # Show additional details for some checks
            if check_name == 'dependencies' and 'missing' in check_result:
                if check_result['missing']:
                    print(f"  Missing: {', '.join(check_result['missing'])}")
            
            if check_name == 'disk_space' and 'free_gb' in check_result:
                print(f"  Free space: {check_result['free_gb']}GB ({check_result['used_percent']}% used)")
        
        # Return appropriate exit code
        if results['overall_status'] == 'error':
            print("\n❌ Health check failed - system has errors")
            sys.exit(1)
        elif results['overall_status'] == 'warning':
            print("\n⚠️ Health check passed with warnings")
            sys.exit(0)
        else:
            print("\n✅ All health checks passed")
            sys.exit(0)
            
    except Exception as e:
        logging.error(f"Health check failed: {e}")
        print(f"❌ Health check failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
