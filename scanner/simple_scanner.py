# Simplified License Scanner for Vercel
# This version works without Scancode Toolkit

import os
import re
from pathlib import Path

class SimpleLicenseScanner:
    """
    Simplified license scanner that works in Vercel's serverless environment.
    Uses pattern matching instead of Scancode Toolkit.
    """
    
    # Common license patterns
    LICENSE_PATTERNS = {
        'MIT': [
            r'MIT License',
            r'Permission is hereby granted',
            r'THE SOFTWARE IS PROVIDED "AS IS"'
        ],
        'Apache': [
            r'Apache License',
            r'Version 2\.0',
            r'Licensed under the Apache License'
        ],
        'GPL': [
            r'GNU GENERAL PUBLIC LICENSE',
            r'GPL v[23]',
            r'Free Software Foundation'
        ],
        'BSD': [
            r'BSD License',
            r'Redistribution and use',
            r'All rights reserved'
        ],
        'ISC': [
            r'ISC License',
            r'Permission to use, copy, modify'
        ]
    }
    
    def scan_file(self, file_path):
        """
        Scan a single file for license information.
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Look for license patterns
            detected_licenses = []
            confidence_scores = []
            
            for license_name, patterns in self.LICENSE_PATTERNS.items():
                matches = 0
                for pattern in patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        matches += 1
                
                if matches > 0:
                    confidence = min(matches / len(patterns), 1.0)
                    detected_licenses.append(license_name)
                    confidence_scores.append(confidence)
            
            if detected_licenses:
                # Return the license with highest confidence
                best_license = detected_licenses[confidence_scores.index(max(confidence_scores))]
                return {
                    'license': best_license,
                    'confidence': max(confidence_scores),
                    'method': 'pattern_matching'
                }
            else:
                return {
                    'license': '',
                    'confidence': 0.0,
                    'method': 'pattern_matching'
                }
                
        except Exception as e:
            return {
                'license': '',
                'confidence': 0.0,
                'method': 'pattern_matching',
                'error': str(e)
            }
    
    def scan_directory(self, directory_path):
        """
        Scan all files in a directory for license information.
        """
        results = {}
        
        try:
            for root, dirs, files in os.walk(directory_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # Skip binary files and common non-code files
                    if self._should_skip_file(file):
                        continue
                    
                    result = self.scan_file(file_path)
                    results[file_path] = result
                    
        except Exception as e:
            print(f"Error scanning directory: {e}")
        
        return results
    
    def _should_skip_file(self, filename):
        """
        Determine if a file should be skipped during scanning.
        """
        skip_extensions = {
            '.pyc', '.pyo', '.pyd', '.so', '.dll', '.exe', '.bin',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico',
            '.mp3', '.mp4', '.avi', '.mov', '.wav',
            '.zip', '.tar', '.gz', '.rar', '.7z',
            '.pdf', '.doc', '.docx', '.xls', '.xlsx'
        }
        
        file_ext = os.path.splitext(filename)[1].lower()
        return file_ext in skip_extensions
