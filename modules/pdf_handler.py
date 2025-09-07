"""
PDF Content Extraction Module for AURA

This module provides PDF text extraction capabilities using command-line tools
like pdftotext for efficient content extraction from PDF documents.
"""

import logging
import subprocess
import tempfile
import os
import shutil
from typing import Optional, Dict, Any, List
from pathlib import Path
import re

class PDFHandler:
    """
    Handles PDF content extraction for fast path content summarization.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the PDF handler.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Check for required tools
        self.pdftotext_available = self._check_pdftotext_availability()
        
        self.logger.info(f"PDFHandler initialized (pdftotext available: {self.pdftotext_available})")
    
    def _check_pdftotext_availability(self) -> bool:
        """
        Check if pdftotext command-line tool is available.
        
        Returns:
            True if pdftotext is available, False otherwise
        """
        try:
            result = subprocess.run(
                ['pdftotext', '-v'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0 or result.returncode == 99  # pdftotext returns 99 for version
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            return False
    
    def extract_text_from_file(self, file_path: str) -> Optional[str]:
        """
        Extract text content from a PDF file.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Extracted text content or None if extraction fails
        """
        if not self.pdftotext_available:
            self.logger.error("pdftotext tool not available for PDF extraction")
            return None
        
        if not os.path.exists(file_path):
            self.logger.error(f"PDF file not found: {file_path}")
            return None
        
        try:
            self.logger.debug(f"Extracting text from PDF: {file_path}")
            
            # Use pdftotext to extract text
            result = subprocess.run(
                ['pdftotext', '-layout', file_path, '-'],
                capture_output=True,
                text=True,
                timeout=30  # 30 second timeout for large PDFs
            )
            
            if result.returncode == 0:
                text_content = result.stdout
                cleaned_content = self._clean_extracted_text(text_content)
                
                self.logger.info(f"Successfully extracted {len(cleaned_content)} characters from PDF")
                return cleaned_content
            else:
                self.logger.error(f"pdftotext failed with return code {result.returncode}: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"PDF text extraction timed out for file: {file_path}")
            return None
        except Exception as e:
            self.logger.error(f"Error extracting text from PDF {file_path}: {e}")
            return None
    
    def _clean_extracted_text(self, text: str) -> str:
        """
        Clean and format extracted PDF text.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned and formatted text
        """
        if not text:
            return ""
        
        # Remove excessive whitespace while preserving structure
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Strip trailing whitespace but preserve leading whitespace for structure
            cleaned_line = line.rstrip()
            
            # Skip completely empty lines but preserve single spaces for paragraph breaks
            if cleaned_line or (len(cleaned_lines) > 0 and cleaned_lines[-1].strip()):
                cleaned_lines.append(cleaned_line)
        
        # Join lines and normalize excessive line breaks
        cleaned_text = '\n'.join(cleaned_lines)
        
        # Remove excessive consecutive line breaks (more than 2)
        cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
        
        # Remove form feed characters and other control characters
        cleaned_text = re.sub(r'[\f\r\v]', '', cleaned_text)
        
        return cleaned_text.strip()
    
    def get_pdf_file_path_from_application(self, app_name: str) -> Optional[str]:
        """
        Attempt to get the file path of the currently open PDF document.
        
        Args:
            app_name: Name of the PDF reader application
            
        Returns:
            File path of the open PDF document or None if not found
        """
        try:
            self.logger.debug(f"Attempting to get PDF file path from {app_name}")
            
            # Try different methods based on the application
            if app_name.lower() in ['preview', 'preview.app']:
                return self._get_preview_file_path()
            elif 'adobe' in app_name.lower() or 'acrobat' in app_name.lower():
                return self._get_adobe_file_path()
            else:
                # Generic approach using AppleScript
                return self._get_generic_pdf_file_path(app_name)
                
        except Exception as e:
            self.logger.error(f"Error getting PDF file path from {app_name}: {e}")
            return None
    
    def _get_preview_file_path(self) -> Optional[str]:
        """
        Get file path from macOS Preview application.
        
        Returns:
            File path or None if not found
        """
        try:
            script = '''
            tell application "Preview"
                if (count of windows) > 0 then
                    set frontWindow to window 1
                    set docPath to path of document of frontWindow
                    return docPath
                end if
            end tell
            '''
            
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout.strip():
                file_path = result.stdout.strip()
                # Convert POSIX path if needed
                if file_path.startswith('/'):
                    return file_path
                else:
                    # Convert from HFS path to POSIX path
                    posix_script = f'tell application "System Events" to return POSIX path of "{file_path}"'
                    posix_result = subprocess.run(
                        ['osascript', '-e', posix_script],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if posix_result.returncode == 0:
                        return posix_result.stdout.strip()
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting Preview file path: {e}")
            return None
    
    def _get_adobe_file_path(self) -> Optional[str]:
        """
        Get file path from Adobe Acrobat/Reader.
        
        Returns:
            File path or None if not found
        """
        try:
            self.logger.debug("Attempting to get Adobe PDF file path")
            
            # Method 1: Try to get document path directly from Adobe Acrobat
            acrobat_script = '''
            try
                tell application "Adobe Acrobat Pro"
                    if (count of documents) > 0 then
                        set activeDoc to document 1
                        set docPath to file path of activeDoc
                        return docPath
                    end if
                end tell
            on error
                try
                    tell application "Adobe Acrobat Reader"
                        if (count of documents) > 0 then
                            set activeDoc to document 1
                            set docPath to file path of activeDoc
                            return docPath
                        end if
                    end tell
                on error
                    return ""
                end try
            end try
            '''
            
            result = subprocess.run(
                ['osascript', '-e', acrobat_script],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout.strip():
                file_path = result.stdout.strip()
                if file_path and file_path != "":
                    self.logger.debug(f"Got Adobe document path: {file_path}")
                    return file_path
            
            # Method 2: Try to get window title and parse it
            window_script = '''
            tell application "System Events"
                set frontApp to name of first process whose frontmost is true
                if frontApp contains "Adobe" or frontApp contains "Acrobat" then
                    tell process frontApp
                        if (count of windows) > 0 then
                            set frontWindow to window 1
                            set windowTitle to title of frontWindow
                            return windowTitle
                        end if
                    end tell
                end if
            end tell
            '''
            
            result = subprocess.run(
                ['osascript', '-e', window_script],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout.strip():
                window_title = result.stdout.strip()
                self.logger.debug(f"Got Adobe window title: {window_title}")
                
                # Parse window title to extract filename/path
                if '.pdf' in window_title.lower():
                    # Adobe often shows "filename.pdf - Adobe Acrobat Reader" or similar
                    # Try to extract just the filename part
                    if ' - ' in window_title:
                        filename = window_title.split(' - ')[0].strip()
                        if filename.lower().endswith('.pdf'):
                            # Try to find this file in common locations
                            return self._find_pdf_file_by_name(filename)
                    else:
                        # Window title might be just the filename
                        if window_title.lower().endswith('.pdf'):
                            return self._find_pdf_file_by_name(window_title)
            
            # Method 3: Try to get the most recently accessed PDF file
            return self._get_recent_pdf_file()
            
        except Exception as e:
            self.logger.error(f"Error getting Adobe file path: {e}")
            return None
    
    def _get_generic_pdf_file_path(self, app_name: str) -> Optional[str]:
        """
        Generic method to get PDF file path using AppleScript.
        
        Args:
            app_name: Name of the application
            
        Returns:
            File path or None if not found
        """
        try:
            # Try to get window title which often contains filename
            script = f'''
            tell application "System Events"
                tell process "{app_name}"
                    if (count of windows) > 0 then
                        set frontWindow to window 1
                        set windowTitle to title of frontWindow
                        return windowTitle
                    end if
                end tell
            end tell
            '''
            
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout.strip():
                window_title = result.stdout.strip()
                # If window title contains .pdf, it might be a filename
                if '.pdf' in window_title.lower():
                    return window_title
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting generic PDF file path from {app_name}: {e}")
            return None
    
    def extract_text_from_open_document(self, app_name: str) -> Optional[str]:
        """
        Extract text from currently open PDF document in the specified application.
        
        Args:
            app_name: Name of the PDF reader application
            
        Returns:
            Extracted text content or None if extraction fails
        """
        try:
            self.logger.info(f"Attempting to extract text from PDF in {app_name}")
            
            # Method 1: Try to get the exact file path and extract from file
            file_path = self.get_pdf_file_path_from_application(app_name)
            
            if file_path and os.path.exists(file_path):
                self.logger.info(f"Found PDF file path: {file_path}")
                content = self.extract_text_from_file(file_path)
                if content and len(content.strip()) > 50:  # Ensure we got substantial content
                    return content
                else:
                    self.logger.warning("File extraction returned insufficient content, trying AppleScript")
            else:
                self.logger.warning(f"Could not determine exact PDF file path from {app_name}")
            
            # Method 2: Fallback to AppleScript accessibility extraction
            self.logger.info("Attempting AppleScript extraction as fallback")
            applescript_content = self._extract_text_via_applescript(app_name)
            if applescript_content and len(applescript_content.strip()) > 50:
                return applescript_content
            
            # Method 3: Try enhanced AppleScript methods for Adobe specifically
            if 'adobe' in app_name.lower() or 'acrobat' in app_name.lower():
                self.logger.info("Trying Adobe-specific extraction methods")
                adobe_content = self._extract_text_from_adobe_direct(app_name)
                if adobe_content and len(adobe_content.strip()) > 50:
                    return adobe_content
            
            self.logger.error(f"All extraction methods failed for {app_name}")
            return None
                
        except Exception as e:
            self.logger.error(f"Error extracting text from open PDF in {app_name}: {e}")
            return None
    
    def _extract_text_via_applescript(self, app_name: str) -> Optional[str]:
        """
        Fallback method to extract text using AppleScript accessibility.
        
        Args:
            app_name: Name of the application
            
        Returns:
            Extracted text or None if extraction fails
        """
        try:
            self.logger.debug(f"Attempting AppleScript text extraction from {app_name}")
            
            # Enhanced script that tries multiple approaches
            script = f'''
            tell application "System Events"
                tell process "{app_name}"
                    if (count of windows) > 0 then
                        set frontWindow to window 1
                        
                        -- Try to get all text content from various UI elements
                        set allText to {{}}
                        
                        -- Get static text elements
                        try
                            set staticTexts to value of every static text of frontWindow
                            set allText to allText & staticTexts
                        end try
                        
                        -- Get text from text areas and text fields
                        try
                            set textAreas to value of every text area of frontWindow
                            set allText to allText & textAreas
                        end try
                        
                        try
                            set textFields to value of every text field of frontWindow
                            set allText to allText & textFields
                        end try
                        
                        -- Get text from scroll areas (common in PDF viewers)
                        try
                            set scrollAreas to every scroll area of frontWindow
                            repeat with scrollArea in scrollAreas
                                try
                                    set scrollTexts to value of every static text of scrollArea
                                    set allText to allText & scrollTexts
                                end try
                            end repeat
                        end try
                        
                        -- Combine all text
                        set AppleScript's text item delimiters to " "
                        set combinedText to allText as string
                        set AppleScript's text item delimiters to ""
                        return combinedText
                    end if
                end tell
            end tell
            '''
            
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout.strip():
                text_content = result.stdout.strip()
                cleaned_content = self._clean_extracted_text(text_content)
                
                if len(cleaned_content) > 50:  # Only return if we got substantial content
                    self.logger.info(f"AppleScript extraction successful: {len(cleaned_content)} characters")
                    return cleaned_content
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error in AppleScript text extraction: {e}")
            return None
    
    def _extract_text_from_adobe_direct(self, app_name: str) -> Optional[str]:
        """
        Adobe-specific text extraction using direct AppleScript commands.
        
        Args:
            app_name: Name of the Adobe application
            
        Returns:
            Extracted text or None if extraction fails
        """
        try:
            self.logger.debug(f"Attempting Adobe-specific text extraction from {app_name}")
            
            # Try Adobe-specific AppleScript commands
            adobe_script = '''
            try
                tell application "Adobe Acrobat Pro"
                    if (count of documents) > 0 then
                        set activeDoc to document 1
                        set docText to text of activeDoc
                        return docText
                    end if
                end tell
            on error
                try
                    tell application "Adobe Acrobat Reader"
                        if (count of documents) > 0 then
                            set activeDoc to document 1
                            set docText to text of activeDoc
                            return docText
                        end if
                    end tell
                on error
                    -- Fallback to accessibility approach for Adobe
                    tell application "System Events"
                        set adobeProcess to first process whose name contains "Adobe" or name contains "Acrobat"
                        tell adobeProcess
                            if (count of windows) > 0 then
                                set frontWindow to window 1
                                
                                -- Try to find the main content area
                                set allText to {}
                                
                                -- Look for groups that might contain PDF content
                                try
                                    set contentGroups to every group of frontWindow
                                    repeat with contentGroup in contentGroups
                                        try
                                            set groupTexts to value of every static text of contentGroup
                                            set allText to allText & groupTexts
                                        end try
                                    end repeat
                                end try
                                
                                -- Also try scroll areas which often contain PDF content
                                try
                                    set scrollAreas to every scroll area of frontWindow
                                    repeat with scrollArea in scrollAreas
                                        try
                                            set scrollTexts to value of every static text of scrollArea
                                            set allText to allText & scrollTexts
                                        end try
                                    end repeat
                                end try
                                
                                set AppleScript's text item delimiters to " "
                                set combinedText to allText as string
                                set AppleScript's text item delimiters to ""
                                return combinedText
                            end if
                        end tell
                    end tell
                end try
            end try
            '''
            
            result = subprocess.run(
                ['osascript', '-e', adobe_script],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout.strip():
                text_content = result.stdout.strip()
                cleaned_content = self._clean_extracted_text(text_content)
                
                if len(cleaned_content) > 50:  # Only return if we got substantial content
                    self.logger.info(f"Adobe-specific extraction successful: {len(cleaned_content)} characters")
                    return cleaned_content
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error in Adobe-specific text extraction: {e}")
            return None
    
    def is_pdf_application(self, app_name: str, bundle_id: str = None) -> bool:
        """
        Check if the given application is a PDF reader.
        
        Args:
            app_name: Name of the application
            bundle_id: Bundle identifier of the application (optional)
            
        Returns:
            True if the application is likely a PDF reader
        """
        app_name_lower = app_name.lower()
        
        # Common PDF reader applications
        pdf_apps = [
            'preview',
            'adobe acrobat',
            'adobe reader',
            'acrobat reader',
            'pdf expert',
            'skim',
            'pdfpen',
            'goodreader',
            'pdf viewer'
        ]
        
        # Check by name
        for pdf_app in pdf_apps:
            if pdf_app in app_name_lower:
                return True
        
        # Check by bundle ID if provided
        if bundle_id:
            bundle_id_lower = bundle_id.lower()
            pdf_bundle_patterns = [
                'com.apple.preview',
                'com.adobe.acrobat',
                'com.adobe.reader',
                'com.readdle.pdfexpert',
                'net.sourceforge.skim-app.skim',
                'com.smileonmymac.pdfpen',
                'com.goodreader'
            ]
            
            for pattern in pdf_bundle_patterns:
                if pattern in bundle_id_lower:
                    return True
        
        return False
    
    def _find_pdf_file_by_name(self, filename: str) -> Optional[str]:
        """
        Find a PDF file by name in common locations.
        
        Args:
            filename: Name of the PDF file to find
            
        Returns:
            Full path to the file if found, None otherwise
        """
        try:
            self.logger.debug(f"Searching for PDF file: {filename}")
            
            # Common locations where PDFs might be found
            search_paths = [
                os.path.expanduser("~/Downloads"),
                os.path.expanduser("~/Documents"),
                os.path.expanduser("~/Desktop"),
                "/tmp",
                "/var/tmp"
            ]
            
            for search_path in search_paths:
                if os.path.exists(search_path):
                    potential_path = os.path.join(search_path, filename)
                    if os.path.exists(potential_path):
                        self.logger.debug(f"Found PDF file at: {potential_path}")
                        return potential_path
                    
                    # Also search subdirectories (one level deep)
                    try:
                        for item in os.listdir(search_path):
                            item_path = os.path.join(search_path, item)
                            if os.path.isdir(item_path):
                                potential_path = os.path.join(item_path, filename)
                                if os.path.exists(potential_path):
                                    self.logger.debug(f"Found PDF file at: {potential_path}")
                                    return potential_path
                    except (PermissionError, OSError):
                        continue
            
            self.logger.warning(f"Could not find PDF file: {filename}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error searching for PDF file {filename}: {e}")
            return None
    
    def _get_recent_pdf_file(self) -> Optional[str]:
        """
        Get the most recently accessed PDF file as a fallback.
        
        Returns:
            Path to the most recent PDF file, or None if not found
        """
        try:
            self.logger.debug("Looking for recently accessed PDF files")
            
            # Search common locations for recently modified PDF files
            search_paths = [
                os.path.expanduser("~/Downloads"),
                os.path.expanduser("~/Documents"),
                os.path.expanduser("~/Desktop")
            ]
            
            recent_pdfs = []
            
            for search_path in search_paths:
                if os.path.exists(search_path):
                    try:
                        for root, dirs, files in os.walk(search_path):
                            # Limit depth to avoid deep searches
                            if root.count(os.sep) - search_path.count(os.sep) > 2:
                                continue
                                
                            for file in files:
                                if file.lower().endswith('.pdf'):
                                    file_path = os.path.join(root, file)
                                    try:
                                        mtime = os.path.getmtime(file_path)
                                        recent_pdfs.append((file_path, mtime))
                                    except OSError:
                                        continue
                    except (PermissionError, OSError):
                        continue
            
            if recent_pdfs:
                # Sort by modification time (most recent first)
                recent_pdfs.sort(key=lambda x: x[1], reverse=True)
                most_recent = recent_pdfs[0][0]
                self.logger.debug(f"Found most recent PDF: {most_recent}")
                return most_recent
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding recent PDF files: {e}")
            return None
    
    def get_installation_instructions(self) -> str:
        """
        Get instructions for installing required tools.
        
        Returns:
            Installation instructions string
        """
        if self.pdftotext_available:
            return "PDF text extraction tools are already installed and available."
        
        return """
PDF text extraction requires the 'pdftotext' tool from poppler-utils.

To install on macOS:
1. Using Homebrew: brew install poppler
2. Using MacPorts: sudo port install poppler

After installation, restart AURA to enable PDF text extraction.
        """.strip()