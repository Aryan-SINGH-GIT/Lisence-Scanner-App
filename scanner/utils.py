import os
import re
import json
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import requests


class LicenseScanner:
    """
    Main class for scanning files and detecting licenses using AboutCode's ScanCode toolkit.
    Uses ScanCode for comprehensive license detection.
    """
    
    def __init__(self):
        """
        Initialize the license scanner with configuration.
        """
        # Common license file names
        self.license_files = [
            'LICENSE', 'LICENSE.txt', 'LICENSE.md', 'LICENSE.rst',
            'LICENCE', 'LICENCE.txt', 'LICENCE.md', 'LICENCE.rst',
            'COPYING', 'COPYING.txt', 'COPYING.md',
            'UNLICENSE', 'UNLICENSE.txt',
            'README', 'README.txt', 'README.md', 'README.rst',
        ]
        
        # File extensions to scan
        self.scannable_extensions = {
            '.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.hpp',
            '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt',
            '.scala', '.clj', '.hs', '.ml', '.fs', '.vb', '.m',
            '.mm', '.pl', '.pm', '.sh', '.bash', '.zsh', '.fish',
            '.r', '.R', '.jl', '.dart', '.lua', '.vim', '.el',
            '.tex', '.md', '.rst', '.txt', '.json', '.yaml', '.yml',
            '.xml', '.html', '.css', '.scss', '.sass', '.less',
        }
    
    def scan_directory(self, directory_path: str) -> Dict[str, Dict]:
        """
        Scan a directory for license information using ScanCode toolkit.
        
        Args:
            directory_path: Path to the directory to scan
            
        Returns:
            Dictionary mapping file paths to license detection results
        """
        results = {}
        
        try:
            # Use ScanCode toolkit for comprehensive scanning
            scancode_results = self._run_scancode(directory_path)
            results.update(scancode_results)
            
            # Also perform manual license file detection as backup
            manual_results = self._scan_license_files_manual(directory_path)
            results.update(manual_results)
            
        except Exception as e:
            print(f"Error scanning directory {directory_path}: {e}")
            # Fallback to manual scanning
            results = self._scan_license_files_manual(directory_path)
        
        return results
    
    def _run_scancode(self, directory_path: str) -> Dict[str, Dict]:
        """
        Run ScanCode toolkit on the directory.
        
        Args:
            directory_path: Path to the directory to scan
            
        Returns:
            Dictionary of scan results
        """
        results = {}
        
        try:
            # Get ScanCode binary path from Django settings
            from django.conf import settings
            scancode_bin = getattr(settings, 'SCANCODE_BIN', 'scancode')
            
            # Create temporary file for ScanCode output
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                temp_output = temp_file.name
            
            # Run ScanCode command
            cmd = [
                scancode_bin,
                '--license',
                '--copyright',
                '--info',
                '--json', temp_output,
                '--strip-root',
                directory_path
            ]
            
            # Execute ScanCode
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if process.returncode == 0:
                # Parse ScanCode results
                with open(temp_output, 'r', encoding='utf-8') as f:
                    scancode_data = json.load(f)
                
                # Process ScanCode results
                results = self._process_scancode_results(scancode_data, directory_path)
            
            else:
                print(f"ScanCode failed with return code {process.returncode}")
                print(f"Error: {process.stderr}")
            
            # Clean up temporary file
            os.unlink(temp_output)
            
        except subprocess.TimeoutExpired:
            print("ScanCode timed out")
        except FileNotFoundError:
            print("ScanCode not found. Please install scancode-toolkit")
        except Exception as e:
            print(f"Error running ScanCode: {e}")
        
        return results
    
    def _process_scancode_results(self, scancode_data: dict, base_path: str) -> Dict[str, Dict]:
        """
        Process ScanCode JSON results into our format.
        
        Args:
            scancode_data: Raw ScanCode JSON output
            base_path: Base path of the scanned directory
            
        Returns:
            Dictionary of processed results
        """
        results = {}
        
        try:
            files = scancode_data.get('files', [])
            
            for file_info in files:
                file_path = file_info.get('path', '')
                
                # Skip directories
                if file_info.get('type') == 'directory':
                    continue
                
                # Get license information
                licenses = file_info.get('licenses', [])
                copyrights = file_info.get('copyrights', [])
                
                if licenses or copyrights:
                    # Find the best license match
                    best_license = self._find_best_license_match(licenses)
                    
                    if best_license:
                        results[file_path] = {
                            'license': best_license.get('key', ''),
                            'confidence': best_license.get('score', 0.0) / 100.0,  # Convert to 0-1 scale
                            'method': 'scancode',
                            'license_text': best_license.get('matched_text', ''),
                            'notes': f"Detected by ScanCode with {best_license.get('score', 0)}% confidence"
                        }
                        
                        # Add copyright information if available
                        if copyrights:
                            copyright_text = '; '.join([c.get('copyright', '') for c in copyrights])
                            results[file_path]['notes'] += f" | Copyrights: {copyright_text}"
        
        except Exception as e:
            print(f"Error processing ScanCode results: {e}")
        
        return results
    
    def _find_best_license_match(self, licenses: List[dict]) -> Optional[dict]:
        """
        Find the best license match from ScanCode results.
        
        Args:
            licenses: List of license matches from ScanCode
            
        Returns:
            Best license match or None
        """
        if not licenses:
            return None
        
        # Sort by score (confidence) and return the highest
        sorted_licenses = sorted(licenses, key=lambda x: x.get('score', 0), reverse=True)
        return sorted_licenses[0]
    
    def _scan_license_files_manual(self, directory_path: str) -> Dict[str, Dict]:
        """
        Manual scan for dedicated license files as backup method.
        
        Args:
            directory_path: Path to the directory to scan
            
        Returns:
            Dictionary of license file results
        """
        results = {}
        
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                if file.upper() in [f.upper() for f in self.license_files]:
                    file_path = os.path.join(root, file)
                    try:
                        license_info = self._detect_license_in_file_manual(file_path)
                        if license_info:
                            results[file_path] = license_info
                    except Exception as e:
                        print(f"Error scanning license file {file_path}: {e}")
        
        return results
    
    def _detect_license_in_file_manual(self, file_path: str) -> Optional[Dict]:
        """
        Manual license detection in a file using pattern matching.
        
        Args:
            file_path: Path to the file to scan
            
        Returns:
            License information dictionary or None
        """
        try:
            # Read file content
            content = self._read_file_content(file_path)
            if not content:
                return None
            
            # Use pattern matching for license detection
            pattern_result = self._detect_with_patterns(content)
            if pattern_result:
                return pattern_result
            
        except Exception as e:
            print(f"Error in manual license detection for {file_path}: {e}")
        
        return None
    
    def _detect_with_patterns(self, content: str) -> Optional[Dict]:
        """
        Detect licenses using pattern matching as fallback.
        
        Args:
            content: File content to analyze
            
        Returns:
            License information dictionary or None
        """
        content_upper = content.upper()
        
        # Common license patterns
        license_patterns = {
            'MIT': [
                r'MIT\s+License',
                r'Permission\s+is\s+hereby\s+granted',
                r'THE\s+SOFTWARE\s+IS\s+PROVIDED\s+"AS\s+IS"',
            ],
            'Apache-2.0': [
                r'Apache\s+License\s+Version\s+2\.0',
                r'Licensed\s+under\s+the\s+Apache\s+License',
                r'http://www\.apache\.org/licenses/LICENSE-2\.0',
            ],
            'GPL-3.0': [
                r'GNU\s+General\s+Public\s+License\s+Version\s+3',
                r'GPL\s+version\s+3',
                r'Free\s+Software\s+Foundation',
            ],
            'GPL-2.0': [
                r'GNU\s+General\s+Public\s+License\s+Version\s+2',
                r'GPL\s+version\s+2',
            ],
            'BSD-3-Clause': [
                r'Redistribution\s+and\s+use\s+in\s+source\s+and\s+binary\s+forms',
                r'BSD\s+3-Clause\s+License',
            ],
            'BSD-2-Clause': [
                r'Redistribution\s+and\s+use\s+in\s+source\s+and\s+binary\s+forms',
                r'BSD\s+2-Clause\s+License',
            ],
            'ISC': [
                r'ISC\s+License',
                r'Permission\s+to\s+use,\s+copy,\s+modify',
            ],
            'Unlicense': [
                r'This\s+is\s+free\s+and\s+unencumbered\s+software',
                r'UNLICENSE',
            ],
        }
        
        for license_name, patterns in license_patterns.items():
            matches = 0
            total_patterns = len(patterns)
            
            for pattern in patterns:
                if re.search(pattern, content_upper, re.IGNORECASE | re.MULTILINE):
                    matches += 1
            
            # Calculate confidence based on pattern matches
            if matches > 0:
                confidence = min(0.9, 0.5 + (matches / total_patterns) * 0.4)
                
                return {
                    'license': license_name,
                    'confidence': confidence,
                    'method': 'pattern_matching',
                    'license_text': self._extract_license_text(content, license_name),
                    'notes': f"Detected using pattern matching ({matches}/{total_patterns} patterns matched)"
                }
        
        return None
    
    def _read_file_content(self, file_path: str) -> Optional[str]:
        """
        Read file content with proper encoding detection.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File content as string or None
        """
        try:
            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    return content
                except UnicodeDecodeError:
                    continue
            
            # If all encodings fail, read as binary and decode with errors='ignore'
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                content = raw_data.decode('utf-8', errors='ignore')
                return content
                
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return None
    
    def _extract_license_text(self, content: str, license_name: str) -> str:
        """
        Extract license text from file content.
        
        Args:
            content: File content
            license_name: Detected license name
            
        Returns:
            Extracted license text
        """
        # Try to find license section
        patterns = [
            r'(?i)license[:\s]*\n(.*?)(?=\n\n|\n[A-Z]|\Z)',
            r'(?i)copyright[:\s]*\n(.*?)(?=\n\n|\n[A-Z]|\Z)',
            r'(?i)permission[:\s]*\n(.*?)(?=\n\n|\n[A-Z]|\Z)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # If no specific section found, return first few lines
        lines = content.split('\n')
        return '\n'.join(lines[:20])
    
    def get_license_info(self, license_key: str) -> Optional[dict]:
        """
        Get detailed information about a license from AboutCode LicenseDB.
        
        Args:
            license_key: License key to look up
            
        Returns:
            License information or None
        """
        try:
            url = f"https://scancode-licensedb.aboutcode.org/{license_key}.json"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching license info for {license_key}: {e}")
            return None
