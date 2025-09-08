"""
PDF reader-specific tests for Content Comprehension Fast Path

This module provides comprehensive tests for PDF-specific content extraction
including Preview.app and Adobe Reader specific scenarios.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from handlers.question_answering_handler import QuestionAnsweringHandler
from modules.application_detector import ApplicationType


class TestPreviewAppFastPath:
    """Preview.app-specific fast path tests."""
    
    @pytest.fixture
    def handler(self):
        """Create handler for Preview.app testing."""
        mock_orchestrator = Mock()
        return QuestionAnsweringHandler(mock_orchestrator)
    
    @pytest.fixture
    def preview_app_info(self):
        """Create Preview.app application info."""
        app_info = Mock()
        app_info.name = "Preview"
        app_info.app_type = ApplicationType.PDF_READER
        return app_info
    
    def test_preview_research_paper_extraction(self, handler, preview_app_info):
        """Test Preview.app content extraction from research paper."""
        research_paper_content = """
        Machine Learning in Healthcare: A Comprehensive Review
        
        Abstract
        
        This systematic review examines the current state and future prospects of machine learning applications in healthcare. We analyzed 150 peer-reviewed articles published between 2020-2024 to identify key trends, challenges, and opportunities in the field.
        
        Key findings include:
        • 78% increase in ML adoption across healthcare institutions
        • Significant improvements in diagnostic accuracy (average 15% improvement)
        • Persistent challenges in data privacy and model interpretability
        • Growing focus on federated learning approaches
        
        1. Introduction
        
        Healthcare systems worldwide are experiencing a digital transformation driven by advances in artificial intelligence and machine learning. The integration of ML technologies promises to revolutionize patient care, clinical decision-making, and operational efficiency.
        
        The COVID-19 pandemic has accelerated the adoption of digital health technologies, creating unprecedented opportunities for ML applications in areas such as:
        - Predictive modeling for patient outcomes
        - Drug discovery and development
        - Medical imaging analysis
        - Electronic health record optimization
        
        2. Methodology
        
        We conducted a systematic literature review following PRISMA guidelines. Our search strategy included the following databases:
        - PubMed/MEDLINE
        - IEEE Xplore
        - ACM Digital Library
        - Google Scholar
        
        Inclusion criteria:
        - Peer-reviewed articles
        - Published 2020-2024
        - Focus on ML applications in healthcare
        - English language
        
        Page 1 of 25
        """
        
        cleaned_content = research_paper_content.strip()
        
        with patch.object(handler, '_detect_active_application', return_value=preview_app_info):
            with patch('modules.pdf_handler.PDFHandler') as mock_pdf_class:
                mock_pdf_handler = Mock()
                mock_pdf_handler.extract_text_from_open_document.return_value = research_paper_content
                mock_pdf_class.return_value = mock_pdf_handler
                
                with patch.object(handler, '_validate_and_clean_pdf_content', return_value=cleaned_content):
                    result = handler._extract_pdf_content()
        
        assert result == cleaned_content
        assert len(result) > 50  # Meets minimum content requirement
        assert "Machine Learning in Healthcare" in result
        assert "Abstract" in result
        mock_pdf_handler.extract_text_from_open_document.assert_called_once_with("Preview")
    
    def test_preview_technical_manual_extraction(self, handler, preview_app_info):
        """Test Preview.app content extraction from technical manual."""
        technical_manual_content = """
        AURA Voice Assistant
        Technical Documentation
        Version 3.2
        
        Table of Contents
        
        1. System Overview ................................. 3
        2. Architecture .................................... 5
        3. Installation Guide .............................. 8
        4. Configuration .................................. 12
        5. API Reference .................................. 18
        6. Troubleshooting ................................ 25
        7. Appendices ..................................... 30
        
        1. System Overview
        
        AURA (Autonomous Universal Reasoning Assistant) is an advanced voice-controlled AI system designed to provide natural language interaction capabilities for desktop environments. The system integrates multiple AI technologies including:
        
        • Speech Recognition: Real-time voice input processing
        • Natural Language Understanding: Intent recognition and parsing
        • Computer Vision: Screen content analysis and interpretation
        • Automation: GUI interaction and task execution
        • Text-to-Speech: Natural voice response generation
        
        1.1 Key Features
        
        - Wake word detection ("Computer")
        - Multi-modal input processing (voice, vision, text)
        - Contextual conversation handling
        - Cross-platform compatibility (macOS, Windows, Linux)
        - Extensible plugin architecture
        - Privacy-focused local processing
        
        1.2 System Requirements
        
        Minimum Requirements:
        - macOS 12.0 or later
        - 8 GB RAM
        - 2 GB available storage
        - Microphone and speakers
        - Internet connection (for initial setup)
        
        Recommended Requirements:
        - macOS 13.0 or later
        - 16 GB RAM
        - 5 GB available storage
        - High-quality USB microphone
        - Dedicated GPU (for vision processing)
        """
        
        cleaned_content = technical_manual_content.strip()
        
        with patch.object(handler, '_detect_active_application', return_value=preview_app_info):
            with patch('modules.pdf_handler.PDFHandler') as mock_pdf_class:
                mock_pdf_handler = Mock()
                mock_pdf_handler.extract_text_from_open_document.return_value = technical_manual_content
                mock_pdf_class.return_value = mock_pdf_handler
                
                with patch.object(handler, '_validate_and_clean_pdf_content', return_value=cleaned_content):
                    result = handler._extract_pdf_content()
        
        assert result == cleaned_content
        assert "AURA Voice Assistant" in result
        assert "Technical Documentation" in result
        assert "System Overview" in result
    
    def test_preview_financial_report_extraction(self, handler, preview_app_info):
        """Test Preview.app content extraction from financial report."""
        financial_report_content = """
        TechCorp Inc.
        Annual Financial Report 2024
        
        Executive Summary
        
        TechCorp Inc. delivered strong financial performance in 2024, with record revenue growth and improved operational efficiency. Key highlights include:
        
        Financial Highlights:
        • Total Revenue: $2.4 billion (+18% YoY)
        • Net Income: $485 million (+22% YoY)
        • Operating Margin: 24.3% (+1.8 percentage points)
        • Free Cash Flow: $520 million (+15% YoY)
        
        Operational Highlights:
        • Launched 3 new AI-powered products
        • Expanded to 12 new international markets
        • Achieved 99.9% system uptime across all services
        • Reduced carbon footprint by 35%
        
        Revenue by Segment (in millions):
        
        Cloud Services: $1,200 (50% of total revenue)
        - Infrastructure as a Service: $720
        - Platform as a Service: $300
        - Software as a Service: $180
        
        AI Solutions: $720 (30% of total revenue)
        - Machine Learning Platform: $432
        - Computer Vision APIs: $180
        - Natural Language Processing: $108
        
        Professional Services: $480 (20% of total revenue)
        - Consulting: $288
        - Implementation: $120
        - Training and Support: $72
        
        Geographic Revenue Distribution:
        • North America: 45%
        • Europe: 30%
        • Asia-Pacific: 20%
        • Other regions: 5%
        """
        
        cleaned_content = financial_report_content.strip()
        
        with patch.object(handler, '_detect_active_application', return_value=preview_app_info):
            with patch('modules.pdf_handler.PDFHandler') as mock_pdf_class:
                mock_pdf_handler = Mock()
                mock_pdf_handler.extract_text_from_open_document.return_value = financial_report_content
                mock_pdf_class.return_value = mock_pdf_handler
                
                with patch.object(handler, '_validate_and_clean_pdf_content', return_value=cleaned_content):
                    result = handler._extract_pdf_content()
        
        assert result == cleaned_content
        assert "TechCorp Inc." in result
        assert "Annual Financial Report" in result
        assert "Revenue" in result
    
    def test_preview_extraction_performance(self, handler, preview_app_info):
        """Test Preview.app extraction performance requirements."""
        content = "Preview PDF content with more than 50 characters for validation testing."
        cleaned_content = content.strip()
        
        start_time = time.time()
        
        with patch.object(handler, '_detect_active_application', return_value=preview_app_info):
            with patch('modules.pdf_handler.PDFHandler') as mock_pdf_class:
                mock_pdf_handler = Mock()
                mock_pdf_handler.extract_text_from_open_document.return_value = content
                mock_pdf_class.return_value = mock_pdf_handler
                
                with patch.object(handler, '_validate_and_clean_pdf_content', return_value=cleaned_content):
                    result = handler._extract_pdf_content()
        
        execution_time = time.time() - start_time
        
        assert result == cleaned_content
        assert execution_time < 2.0  # Should complete within 2 seconds
    
    def test_preview_extraction_timeout_handling(self, handler, preview_app_info):
        """Test Preview.app extraction timeout handling."""
        def slow_extraction(*args):
            time.sleep(2.5)  # Longer than 2 second timeout
            return "content"
        
        with patch.object(handler, '_detect_active_application', return_value=preview_app_info):
            with patch('modules.pdf_handler.PDFHandler') as mock_pdf_class:
                mock_pdf_handler = Mock()
                mock_pdf_handler.extract_text_from_open_document.side_effect = slow_extraction
                mock_pdf_class.return_value = mock_pdf_handler
                
                result = handler._extract_pdf_content()
        
        assert result is None
        assert handler._last_fallback_reason == "pdf_extraction_timeout"


class TestAdobeReaderFastPath:
    """Adobe Reader-specific fast path tests."""
    
    @pytest.fixture
    def handler(self):
        """Create handler for Adobe Reader testing."""
        mock_orchestrator = Mock()
        return QuestionAnsweringHandler(mock_orchestrator)
    
    @pytest.fixture
    def adobe_reader_app_info(self):
        """Create Adobe Reader application info."""
        app_info = Mock()
        app_info.name = "Adobe Acrobat Reader DC"
        app_info.app_type = ApplicationType.PDF_READER
        return app_info
    
    def test_adobe_reader_legal_document_extraction(self, handler, adobe_reader_app_info):
        """Test Adobe Reader content extraction from legal document."""
        legal_document_content = """
        SOFTWARE LICENSE AGREEMENT
        
        This Software License Agreement ("Agreement") is entered into as of the date of acceptance by the end user ("Licensee") and TechCorp Inc., a Delaware corporation ("Licensor").
        
        WHEREAS, Licensor has developed certain computer software programs and related documentation described herein; and
        
        WHEREAS, Licensee desires to obtain a license to use such software programs and documentation;
        
        NOW, THEREFORE, in consideration of the mutual covenants contained herein and for other good and valuable consideration, the receipt and sufficiency of which are hereby acknowledged, the parties agree as follows:
        
        1. GRANT OF LICENSE
        
        1.1 License Grant. Subject to the terms and conditions of this Agreement, Licensor hereby grants to Licensee a non-exclusive, non-transferable license to use the Software (as defined below) solely for Licensee's internal business purposes.
        
        1.2 Restrictions. Licensee shall not:
        (a) modify, adapt, alter, translate, or create derivative works of the Software;
        (b) reverse engineer, disassemble, decompile, or otherwise attempt to derive the source code of the Software;
        (c) distribute, sublicense, lease, rent, loan, or otherwise transfer the Software to any third party;
        (d) use the Software for any unlawful purpose or in any manner that violates applicable laws or regulations.
        
        2. INTELLECTUAL PROPERTY RIGHTS
        
        2.1 Ownership. Licensor retains all right, title, and interest in and to the Software, including all intellectual property rights therein. No title to or ownership of the Software is transferred to Licensee.
        
        2.2 Feedback. Any suggestions, enhancement requests, feedback, or other recommendations provided by Licensee relating to the Software shall be owned by Licensor.
        
        3. TERM AND TERMINATION
        
        3.1 Term. This Agreement shall commence on the date of acceptance and shall continue until terminated in accordance with this Section 3.
        
        3.2 Termination. Either party may terminate this Agreement at any time with thirty (30) days' written notice to the other party.
        """
        
        cleaned_content = legal_document_content.strip()
        
        with patch.object(handler, '_detect_active_application', return_value=adobe_reader_app_info):
            with patch('modules.pdf_handler.PDFHandler') as mock_pdf_class:
                mock_pdf_handler = Mock()
                mock_pdf_handler.extract_text_from_open_document.return_value = legal_document_content
                mock_pdf_class.return_value = mock_pdf_handler
                
                with patch.object(handler, '_validate_and_clean_pdf_content', return_value=cleaned_content):
                    result = handler._extract_pdf_content()
        
        assert result == cleaned_content
        assert "SOFTWARE LICENSE AGREEMENT" in result
        assert "TechCorp Inc." in result
        assert "GRANT OF LICENSE" in result
        mock_pdf_handler.extract_text_from_open_document.assert_called_once_with("Adobe Acrobat Reader DC")
    
    def test_adobe_reader_academic_paper_extraction(self, handler, adobe_reader_app_info):
        """Test Adobe Reader content extraction from academic paper."""
        academic_paper_content = """
        Advances in Natural Language Processing: A Survey of Transformer Architectures
        
        Authors: Dr. Sarah Johnson¹, Prof. Michael Chen², Dr. Emily Rodriguez³
        ¹Stanford University, ²MIT, ³University of Toronto
        
        Abstract
        
        Natural Language Processing (NLP) has experienced unprecedented growth following the introduction of transformer architectures. This survey provides a comprehensive overview of transformer-based models, their evolution, and applications across various NLP tasks. We analyze 200+ research papers published between 2017-2024, identifying key innovations, performance improvements, and emerging trends.
        
        Our analysis reveals three major evolutionary phases:
        1. Foundation Era (2017-2019): Introduction of attention mechanisms and basic transformer architectures
        2. Scaling Era (2019-2022): Development of large language models and parameter scaling
        3. Efficiency Era (2022-present): Focus on model compression, efficiency, and specialized architectures
        
        Keywords: Natural Language Processing, Transformers, Attention Mechanisms, Large Language Models, BERT, GPT, T5
        
        1. Introduction
        
        The field of Natural Language Processing has undergone a paradigm shift with the introduction of the Transformer architecture by Vaswani et al. (2017). This revolutionary approach, based entirely on attention mechanisms, has replaced traditional recurrent and convolutional architectures as the dominant paradigm for sequence-to-sequence tasks.
        
        The success of transformers can be attributed to several key factors:
        • Parallelizable computation enabling efficient training on large datasets
        • Effective modeling of long-range dependencies through self-attention
        • Transfer learning capabilities through pre-training and fine-tuning
        • Scalability to billions of parameters with consistent performance improvements
        
        2. Background and Related Work
        
        2.1 Pre-Transformer Era
        
        Before transformers, NLP models primarily relied on:
        - Recurrent Neural Networks (RNNs) for sequential processing
        - Convolutional Neural Networks (CNNs) for local pattern recognition
        - Attention mechanisms as supplementary components
        
        These approaches faced limitations in:
        - Sequential processing bottlenecks
        - Difficulty capturing long-range dependencies
        - Limited parallelization capabilities
        """
        
        cleaned_content = academic_paper_content.strip()
        
        with patch.object(handler, '_detect_active_application', return_value=adobe_reader_app_info):
            with patch('modules.pdf_handler.PDFHandler') as mock_pdf_class:
                mock_pdf_handler = Mock()
                mock_pdf_handler.extract_text_from_open_document.return_value = academic_paper_content
                mock_pdf_class.return_value = mock_pdf_handler
                
                with patch.object(handler, '_validate_and_clean_pdf_content', return_value=cleaned_content):
                    result = handler._extract_pdf_content()
        
        assert result == cleaned_content
        assert "Natural Language Processing" in result
        assert "Transformer Architectures" in result
        assert "Abstract" in result
    
    def test_adobe_reader_user_manual_extraction(self, handler, adobe_reader_app_info):
        """Test Adobe Reader content extraction from user manual."""
        user_manual_content = """
        SmartHome Pro System
        User Manual
        Model: SH-2024-PRO
        
        Welcome to SmartHome Pro
        
        Thank you for choosing the SmartHome Pro System, the most advanced home automation solution available. This manual will guide you through setup, configuration, and daily use of your new system.
        
        What's in the Box:
        • SmartHome Pro Hub (1x)
        • Wireless Sensors (4x)
        • Smart Switches (6x)
        • Motion Detectors (2x)
        • Door/Window Sensors (8x)
        • Power Adapters and Cables
        • Quick Start Guide
        • Warranty Information
        
        Chapter 1: Getting Started
        
        1.1 System Requirements
        
        Before installation, ensure you have:
        - Stable Wi-Fi network (2.4GHz and 5GHz)
        - Smartphone or tablet (iOS 14+ or Android 10+)
        - Available electrical outlets near installation points
        - Basic tools (screwdriver, drill for mounting)
        
        1.2 Initial Setup
        
        Step 1: Download the SmartHome Pro app from the App Store or Google Play
        Step 2: Create your account and verify your email address
        Step 3: Connect the hub to your router using the included Ethernet cable
        Step 4: Power on the hub and wait for the blue LED indicator
        Step 5: Follow the in-app setup wizard to configure your network
        
        1.3 Adding Devices
        
        The SmartHome Pro system supports over 200 different device types:
        - Lighting controls (dimmers, switches, smart bulbs)
        - Climate control (thermostats, temperature sensors)
        - Security devices (cameras, door locks, alarms)
        - Entertainment systems (speakers, TVs, streaming devices)
        - Appliances (smart plugs, outlets, garage door openers)
        
        To add a new device:
        1. Open the SmartHome Pro app
        2. Tap the "+" icon in the top right corner
        3. Select "Add Device" from the menu
        4. Choose your device type from the list
        5. Follow the specific pairing instructions for your device
        """
        
        cleaned_content = user_manual_content.strip()
        
        with patch.object(handler, '_detect_active_application', return_value=adobe_reader_app_info):
            with patch('modules.pdf_handler.PDFHandler') as mock_pdf_class:
                mock_pdf_handler = Mock()
                mock_pdf_handler.extract_text_from_open_document.return_value = user_manual_content
                mock_pdf_class.return_value = mock_pdf_handler
                
                with patch.object(handler, '_validate_and_clean_pdf_content', return_value=cleaned_content):
                    result = handler._extract_pdf_content()
        
        assert result == cleaned_content
        assert "SmartHome Pro System" in result
        assert "User Manual" in result
        assert "Getting Started" in result
    
    def test_adobe_reader_extraction_performance(self, handler, adobe_reader_app_info):
        """Test Adobe Reader extraction performance requirements."""
        content = "Adobe Reader PDF content with more than 50 characters for validation testing."
        cleaned_content = content.strip()
        
        start_time = time.time()
        
        with patch.object(handler, '_detect_active_application', return_value=adobe_reader_app_info):
            with patch('modules.pdf_handler.PDFHandler') as mock_pdf_class:
                mock_pdf_handler = Mock()
                mock_pdf_handler.extract_text_from_open_document.return_value = content
                mock_pdf_class.return_value = mock_pdf_handler
                
                with patch.object(handler, '_validate_and_clean_pdf_content', return_value=cleaned_content):
                    result = handler._extract_pdf_content()
        
        execution_time = time.time() - start_time
        
        assert result == cleaned_content
        assert execution_time < 2.0  # Should complete within 2 seconds


class TestPDFContentValidation:
    """Tests for PDF content validation and cleaning."""
    
    @pytest.fixture
    def handler(self):
        """Create handler for validation testing."""
        mock_orchestrator = Mock()
        return QuestionAnsweringHandler(mock_orchestrator)
    
    def test_pdf_content_length_validation(self, handler):
        """Test PDF content length validation requirements."""
        # Test content too short
        short_content = "Short"  # Less than 50 characters
        result = handler._validate_and_clean_pdf_content(short_content)
        assert result is None
        
        # Test content just long enough
        valid_content = "This PDF content is exactly fifty characters!!"  # 50 characters
        result = handler._validate_and_clean_pdf_content(valid_content)
        assert result == valid_content.strip()
        
        # Test content well above minimum
        long_content = "This is a much longer piece of PDF content that definitely exceeds the minimum character requirement for validation."
        result = handler._validate_and_clean_pdf_content(long_content)
        assert result == long_content.strip()
    
    def test_pdf_content_cleaning(self, handler):
        """Test PDF content cleaning functionality."""
        # Test content with extra whitespace
        messy_content = """
        
        
        PDF Document Title
        
        
        This is the main content with extra whitespace.
        
        
        More content here.
        
        
        """
        
        result = handler._validate_and_clean_pdf_content(messy_content)
        expected = "PDF Document Title\n\n\nThis is the main content with extra whitespace.\n\n\nMore content here."
        assert result == expected
    
    def test_pdf_content_with_page_numbers(self, handler):
        """Test PDF content cleaning with page numbers and headers/footers."""
        content_with_page_numbers = """
        Research Paper Title
        
        Abstract
        This is the abstract content of the research paper.
        
        1. Introduction
        This is the introduction section with detailed information.
        
        Page 1 of 25
        
        2. Methodology
        This section describes the research methodology.
        
        Footer: Copyright 2024 - All Rights Reserved
        Page 2 of 25
        """
        
        # The cleaning should preserve the content structure
        result = handler._validate_and_clean_pdf_content(content_with_page_numbers)
        assert result is not None
        assert "Research Paper Title" in result
        assert "Abstract" in result
        assert "Introduction" in result
    
    def test_pdf_content_with_special_characters(self, handler):
        """Test PDF content with special characters and formatting."""
        content_with_special_chars = """
        Technical Specification Document
        
        • Bullet point 1
        • Bullet point 2
        ◦ Sub-bullet point
        
        Mathematical formulas:
        E = mc²
        ∑(x₁ + x₂ + ... + xₙ)
        
        Currency symbols: $100, €85, ¥1000
        
        Quotation marks: "This is a quote" and 'another quote'
        
        Em dashes — and en dashes –
        
        Trademark symbols: TechCorp™, Product®
        """
        
        result = handler._validate_and_clean_pdf_content(content_with_special_chars)
        assert result is not None
        assert "Technical Specification" in result
        assert "E = mc²" in result
        assert "TechCorp™" in result
    
    def test_pdf_content_with_tables(self, handler):
        """Test PDF content with table-like structures."""
        content_with_tables = """
        Financial Report Q4 2024
        
        Revenue by Quarter:
        Q1 2024    $1.2M    +15%
        Q2 2024    $1.4M    +18%
        Q3 2024    $1.6M    +22%
        Q4 2024    $1.8M    +25%
        
        Department Breakdown:
        Sales          $800K    45%
        Marketing      $400K    22%
        Engineering    $600K    33%
        
        Total Revenue: $1.8M
        """
        
        result = handler._validate_and_clean_pdf_content(content_with_tables)
        assert result is not None
        assert "Financial Report" in result
        assert "Revenue by Quarter" in result
        assert "$1.8M" in result
    
    def test_pdf_content_empty_or_whitespace(self, handler):
        """Test PDF content validation with empty or whitespace-only content."""
        # Test empty content
        assert handler._validate_and_clean_pdf_content("") is None
        
        # Test whitespace-only content
        assert handler._validate_and_clean_pdf_content("   \n\t   ") is None
        
        # Test content with only newlines
        assert handler._validate_and_clean_pdf_content("\n\n\n\n") is None
    
    def test_pdf_content_with_code_blocks(self, handler):
        """Test PDF content with code blocks and technical content."""
        content_with_code = """
        Python Programming Guide
        
        Chapter 3: Functions and Classes
        
        Here's how to define a class in Python:
        
        class DataProcessor:
            def __init__(self, data):
                self.data = data
                self.processed = False
            
            def process(self):
                # Process the data
                result = []
                for item in self.data:
                    if item > 0:
                        result.append(item * 2)
                self.processed = True
                return result
        
        Usage example:
        processor = DataProcessor([1, 2, 3, -1, 4])
        result = processor.process()
        print(result)  # Output: [2, 4, 6, 8]
        
        This demonstrates object-oriented programming principles.
        """
        
        result = handler._validate_and_clean_pdf_content(content_with_code)
        assert result is not None
        assert "Python Programming Guide" in result
        assert "class DataProcessor:" in result
        assert "def process(self):" in result


class TestPDFErrorHandling:
    """Tests for PDF-specific error handling scenarios."""
    
    @pytest.fixture
    def handler(self):
        """Create handler for error testing."""
        mock_orchestrator = Mock()
        return QuestionAnsweringHandler(mock_orchestrator)
    
    def test_pdf_handler_initialization_failure(self, handler):
        """Test handling when PDFHandler fails to initialize."""
        app_info = Mock()
        app_info.app_type = ApplicationType.PDF_READER
        
        with patch.object(handler, '_detect_active_application', return_value=app_info):
            with patch('modules.pdf_handler.PDFHandler', side_effect=Exception("Init failed")):
                result = handler._extract_pdf_content()
        
        assert result is None
    
    def test_pdf_extraction_exception(self, handler):
        """Test handling when PDF extraction raises an exception."""
        app_info = Mock()
        app_info.name = "Preview"
        app_info.app_type = ApplicationType.PDF_READER
        
        with patch.object(handler, '_detect_active_application', return_value=app_info):
            with patch('modules.pdf_handler.PDFHandler') as mock_pdf_class:
                mock_pdf_handler = Mock()
                mock_pdf_handler.extract_text_from_open_document.side_effect = Exception("Extraction failed")
                mock_pdf_class.return_value = mock_pdf_handler
                
                result = handler._extract_pdf_content()
        
        assert result is None
    
    def test_pdf_extraction_returns_none(self, handler):
        """Test handling when PDF extraction returns None."""
        app_info = Mock()
        app_info.name = "Preview"
        app_info.app_type = ApplicationType.PDF_READER
        
        with patch.object(handler, '_detect_active_application', return_value=app_info):
            with patch('modules.pdf_handler.PDFHandler') as mock_pdf_class:
                mock_pdf_handler = Mock()
                mock_pdf_handler.extract_text_from_open_document.return_value = None
                mock_pdf_class.return_value = mock_pdf_handler
                
                result = handler._extract_pdf_content()
        
        assert result is None
    
    def test_pdf_extraction_returns_empty_string(self, handler):
        """Test handling when PDF extraction returns empty string."""
        app_info = Mock()
        app_info.name = "Preview"
        app_info.app_type = ApplicationType.PDF_READER
        
        with patch.object(handler, '_detect_active_application', return_value=app_info):
            with patch('modules.pdf_handler.PDFHandler') as mock_pdf_class:
                mock_pdf_handler = Mock()
                mock_pdf_handler.extract_text_from_open_document.return_value = ""
                mock_pdf_class.return_value = mock_pdf_handler
                
                result = handler._extract_pdf_content()
        
        assert result is None
    
    def test_pdf_content_validation_failure(self, handler):
        """Test handling when PDF content fails validation."""
        app_info = Mock()
        app_info.name = "Preview"
        app_info.app_type = ApplicationType.PDF_READER
        
        content = "Valid content that passes length requirements but fails other validation."
        
        with patch.object(handler, '_detect_active_application', return_value=app_info):
            with patch('modules.pdf_handler.PDFHandler') as mock_pdf_class:
                mock_pdf_handler = Mock()
                mock_pdf_handler.extract_text_from_open_document.return_value = content
                mock_pdf_class.return_value = mock_pdf_handler
                
                with patch.object(handler, '_validate_and_clean_pdf_content', return_value=None):
                    result = handler._extract_pdf_content()
        
        assert result is None
    
    def test_pdf_extraction_with_corrupted_file(self, handler):
        """Test handling when PDF file is corrupted or unreadable."""
        app_info = Mock()
        app_info.name = "Preview"
        app_info.app_type = ApplicationType.PDF_READER
        
        with patch.object(handler, '_detect_active_application', return_value=app_info):
            with patch('modules.pdf_handler.PDFHandler') as mock_pdf_class:
                mock_pdf_handler = Mock()
                mock_pdf_handler.extract_text_from_open_document.side_effect = Exception("Corrupted PDF file")
                mock_pdf_class.return_value = mock_pdf_handler
                
                result = handler._extract_pdf_content()
        
        assert result is None
    
    def test_pdf_extraction_with_password_protected_file(self, handler):
        """Test handling when PDF file is password protected."""
        app_info = Mock()
        app_info.name = "Adobe Acrobat Reader DC"
        app_info.app_type = ApplicationType.PDF_READER
        
        with patch.object(handler, '_detect_active_application', return_value=app_info):
            with patch('modules.pdf_handler.PDFHandler') as mock_pdf_class:
                mock_pdf_handler = Mock()
                mock_pdf_handler.extract_text_from_open_document.side_effect = Exception("Password protected PDF")
                mock_pdf_class.return_value = mock_pdf_handler
                
                result = handler._extract_pdf_content()
        
        assert result is None


class TestPDFPerformanceRequirements:
    """Performance-specific tests for PDF extraction."""
    
    @pytest.fixture
    def handler(self):
        """Create handler for performance testing."""
        mock_orchestrator = Mock()
        return QuestionAnsweringHandler(mock_orchestrator)
    
    def test_pdf_extraction_performance_under_2_seconds(self, handler):
        """Test that PDF extraction completes within 2 seconds."""
        app_info = Mock()
        app_info.name = "Preview"
        app_info.app_type = ApplicationType.PDF_READER
        
        content = "PDF content with more than 50 characters for validation testing."
        cleaned_content = content.strip()
        
        start_time = time.time()
        
        with patch.object(handler, '_detect_active_application', return_value=app_info):
            with patch('modules.pdf_handler.PDFHandler') as mock_pdf_class:
                mock_pdf_handler = Mock()
                mock_pdf_handler.extract_text_from_open_document.return_value = content
                mock_pdf_class.return_value = mock_pdf_handler
                
                with patch.object(handler, '_validate_and_clean_pdf_content', return_value=cleaned_content):
                    result = handler._extract_pdf_content()
        
        execution_time = time.time() - start_time
        
        assert result == cleaned_content
        assert execution_time < 2.0  # Must complete within 2 seconds
    
    def test_pdf_extraction_timeout_handling(self, handler):
        """Test PDF extraction timeout after 2 seconds."""
        app_info = Mock()
        app_info.name = "Preview"
        app_info.app_type = ApplicationType.PDF_READER
        
        def slow_extraction(*args):
            time.sleep(2.5)  # Longer than 2 second timeout
            return "content"
        
        start_time = time.time()
        
        with patch.object(handler, '_detect_active_application', return_value=app_info):
            with patch('modules.pdf_handler.PDFHandler') as mock_pdf_class:
                mock_pdf_handler = Mock()
                mock_pdf_handler.extract_text_from_open_document.side_effect = slow_extraction
                mock_pdf_class.return_value = mock_pdf_handler
                
                result = handler._extract_pdf_content()
        
        execution_time = time.time() - start_time
        
        assert result is None
        assert execution_time < 3.0  # Should timeout before 3 seconds
        assert handler._last_fallback_reason == "pdf_extraction_timeout"
    
    def test_large_pdf_handling(self, handler):
        """Test handling of large PDF documents."""
        app_info = Mock()
        app_info.name = "Preview"
        app_info.app_type = ApplicationType.PDF_READER
        
        # Simulate large PDF content (50KB limit mentioned in requirements)
        large_content = "This is a large PDF document with lots of content. " * 1000  # ~50KB
        cleaned_content = large_content.strip()
        
        with patch.object(handler, '_detect_active_application', return_value=app_info):
            with patch('modules.pdf_handler.PDFHandler') as mock_pdf_class:
                mock_pdf_handler = Mock()
                mock_pdf_handler.extract_text_from_open_document.return_value = large_content
                mock_pdf_class.return_value = mock_pdf_handler
                
                with patch.object(handler, '_validate_and_clean_pdf_content', return_value=cleaned_content):
                    result = handler._extract_pdf_content()
        
        assert result == cleaned_content
        assert len(result) > 50  # Meets minimum requirement
        # Should handle large content without issues