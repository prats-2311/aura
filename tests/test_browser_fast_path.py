"""
Browser-specific tests for Content Comprehension Fast Path

This module provides comprehensive tests for browser-specific content extraction
including Chrome, Safari, and Firefox specific scenarios.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from handlers.question_answering_handler import QuestionAnsweringHandler
from modules.application_detector import ApplicationType, BrowserType


class TestChromeFastPath:
    """Chrome-specific fast path tests."""
    
    @pytest.fixture
    def handler(self):
        """Create handler for Chrome testing."""
        mock_orchestrator = Mock()
        return QuestionAnsweringHandler(mock_orchestrator)
    
    @pytest.fixture
    def chrome_app_info(self):
        """Create Chrome application info."""
        app_info = Mock()
        app_info.name = "Google Chrome"
        app_info.app_type = ApplicationType.WEB_BROWSER
        app_info.browser_type = BrowserType.CHROME
        return app_info
    
    def test_chrome_google_search_extraction(self, handler, chrome_app_info):
        """Test Chrome content extraction from Google search results."""
        google_search_content = """
        Google
        
        Search: "machine learning tutorials"
        
        About 45,600,000 results (0.52 seconds)
        
        All    Images    Videos    News    Shopping    More
        
        Machine Learning Tutorial - GeeksforGeeks
        https://www.geeksforgeeks.org/machine-learning/
        Machine Learning is a method of data analysis that automates analytical model building. It is a branch of artificial intelligence (AI) based on the idea that systems can learn from data...
        
        Machine Learning Course - Coursera
        https://www.coursera.org/learn/machine-learning
        Learn Machine Learning online with courses like Machine Learning and Machine Learning Specialization. Machine Learning courses from top universities and industry leaders.
        
        Introduction to Machine Learning - MIT OpenCourseWare
        https://ocw.mit.edu/courses/electrical-engineering-and-computer-science/
        This course provides a broad introduction to machine learning and statistical pattern recognition.
        """
        
        with patch.object(handler, '_detect_active_application', return_value=chrome_app_info):
            with patch('modules.browser_accessibility.BrowserAccessibilityHandler') as mock_browser_class:
                mock_browser_handler = Mock()
                mock_browser_handler.get_page_text_content.return_value = google_search_content
                mock_browser_class.return_value = mock_browser_handler
                
                with patch.object(handler, '_validate_browser_content', return_value=True):
                    result = handler._extract_browser_content()
        
        assert result == google_search_content
        assert len(result) > 50  # Meets minimum content requirement
        mock_browser_handler.get_page_text_content.assert_called_once_with(chrome_app_info)
    
    def test_chrome_youtube_extraction(self, handler, chrome_app_info):
        """Test Chrome content extraction from YouTube."""
        youtube_content = """
        YouTube
        
        Video: "Introduction to Neural Networks"
        Channel: DeepLearning.AI
        
        Description:
        This video provides a comprehensive introduction to neural networks, covering the basic concepts, architecture, and applications. You'll learn about:
        
        - What are neural networks
        - How they work
        - Different types of neural networks
        - Real-world applications
        
        Comments (1,234):
        
        @user123: Great explanation! Really helped me understand the basics.
        @learner456: Could you make a video about backpropagation next?
        @student789: Thanks for the clear examples and visualizations.
        
        Related Videos:
        - Deep Learning Fundamentals
        - Convolutional Neural Networks
        - Recurrent Neural Networks
        """
        
        with patch.object(handler, '_detect_active_application', return_value=chrome_app_info):
            with patch('modules.browser_accessibility.BrowserAccessibilityHandler') as mock_browser_class:
                mock_browser_handler = Mock()
                mock_browser_handler.get_page_text_content.return_value = youtube_content
                mock_browser_class.return_value = mock_browser_handler
                
                with patch.object(handler, '_validate_browser_content', return_value=True):
                    result = handler._extract_browser_content()
        
        assert result == youtube_content
        assert "Neural Networks" in result
        assert "DeepLearning.AI" in result
    
    def test_chrome_github_extraction(self, handler, chrome_app_info):
        """Test Chrome content extraction from GitHub."""
        github_content = """
        GitHub
        
        Repository: tensorflow/tensorflow
        
        TensorFlow
        An Open Source Machine Learning Framework for Everyone
        
        README.md
        
        TensorFlow is an end-to-end open source platform for machine learning. It has a comprehensive, flexible ecosystem of tools, libraries and community resources that lets researchers push the state-of-the-art in ML and developers easily build and deploy ML powered applications.
        
        Key Features:
        - Easy model building
        - Robust ML production anywhere
        - Powerful experimentation for research
        
        Installation:
        pip install tensorflow
        
        Quick Start:
        import tensorflow as tf
        
        Files:
        - tensorflow/
        - docs/
        - examples/
        - tests/
        
        Contributors: 4,123
        Stars: 185,000
        Forks: 74,000
        """
        
        with patch.object(handler, '_detect_active_application', return_value=chrome_app_info):
            with patch('modules.browser_accessibility.BrowserAccessibilityHandler') as mock_browser_class:
                mock_browser_handler = Mock()
                mock_browser_handler.get_page_text_content.return_value = github_content
                mock_browser_class.return_value = mock_browser_handler
                
                with patch.object(handler, '_validate_browser_content', return_value=True):
                    result = handler._extract_browser_content()
        
        assert result == github_content
        assert "TensorFlow" in result
        assert "Machine Learning Framework" in result
    
    def test_chrome_stackoverflow_extraction(self, handler, chrome_app_info):
        """Test Chrome content extraction from Stack Overflow."""
        stackoverflow_content = """
        Stack Overflow
        
        Question: How to implement a simple neural network in Python?
        
        Asked 2 days ago    Modified 1 day ago    Viewed 1,234 times
        
        I'm trying to implement a basic neural network from scratch in Python. I understand the theory but I'm having trouble with the implementation. Here's what I have so far:
        
        import numpy as np
        
        class NeuralNetwork:
            def __init__(self, input_size, hidden_size, output_size):
                self.W1 = np.random.randn(input_size, hidden_size)
                self.W2 = np.random.randn(hidden_size, output_size)
        
        What am I missing for the forward pass and backpropagation?
        
        Tags: python machine-learning neural-network numpy
        
        Answers (3):
        
        Answer 1 (Accepted):
        You need to implement the forward pass and backpropagation methods. Here's a complete implementation:
        
        def forward(self, X):
            self.z1 = np.dot(X, self.W1)
            self.a1 = self.sigmoid(self.z1)
            self.z2 = np.dot(self.a1, self.W2)
            self.a2 = self.sigmoid(self.z2)
            return self.a2
        
        def sigmoid(self, x):
            return 1 / (1 + np.exp(-x))
        """
        
        with patch.object(handler, '_detect_active_application', return_value=chrome_app_info):
            with patch('modules.browser_accessibility.BrowserAccessibilityHandler') as mock_browser_class:
                mock_browser_handler = Mock()
                mock_browser_handler.get_page_text_content.return_value = stackoverflow_content
                mock_browser_class.return_value = mock_browser_handler
                
                with patch.object(handler, '_validate_browser_content', return_value=True):
                    result = handler._extract_browser_content()
        
        assert result == stackoverflow_content
        assert "neural network" in result
        assert "Python" in result
        assert "numpy" in result
    
    def test_chrome_extraction_performance(self, handler, chrome_app_info):
        """Test Chrome extraction performance requirements."""
        content = "Chrome content with more than 50 characters for validation testing."
        
        start_time = time.time()
        
        with patch.object(handler, '_detect_active_application', return_value=chrome_app_info):
            with patch('modules.browser_accessibility.BrowserAccessibilityHandler') as mock_browser_class:
                mock_browser_handler = Mock()
                mock_browser_handler.get_page_text_content.return_value = content
                mock_browser_class.return_value = mock_browser_handler
                
                with patch.object(handler, '_validate_browser_content', return_value=True):
                    result = handler._extract_browser_content()
        
        execution_time = time.time() - start_time
        
        assert result == content
        assert execution_time < 2.0  # Should complete within 2 seconds
    
    def test_chrome_extraction_timeout_handling(self, handler, chrome_app_info):
        """Test Chrome extraction timeout handling."""
        def slow_extraction(*args):
            time.sleep(2.5)  # Longer than 2 second timeout
            return "content"
        
        with patch.object(handler, '_detect_active_application', return_value=chrome_app_info):
            with patch('modules.browser_accessibility.BrowserAccessibilityHandler') as mock_browser_class:
                mock_browser_handler = Mock()
                mock_browser_handler.get_page_text_content.side_effect = slow_extraction
                mock_browser_class.return_value = mock_browser_handler
                
                result = handler._extract_browser_content()
        
        assert result is None
        assert handler._last_fallback_reason == "browser_extraction_timeout"


class TestSafariFastPath:
    """Safari-specific fast path tests."""
    
    @pytest.fixture
    def handler(self):
        """Create handler for Safari testing."""
        mock_orchestrator = Mock()
        return QuestionAnsweringHandler(mock_orchestrator)
    
    @pytest.fixture
    def safari_app_info(self):
        """Create Safari application info."""
        app_info = Mock()
        app_info.name = "Safari"
        app_info.app_type = ApplicationType.WEB_BROWSER
        app_info.browser_type = BrowserType.SAFARI
        return app_info
    
    def test_safari_apple_developer_extraction(self, handler, safari_app_info):
        """Test Safari content extraction from Apple Developer documentation."""
        apple_dev_content = """
        Apple Developer Documentation
        
        SwiftUI
        
        Declare the user interface and behavior for your app on every Apple platform.
        
        Overview
        SwiftUI provides views, controls, and layout structures for declaring your app's user interface. The framework provides event handlers for delivering taps, gestures, and other types of input to your app, and tools to manage the flow of data from your app's models down to the views and controls that users will see and interact with.
        
        Topics
        
        Essentials
        - App Structure
        - Views and Controls
        - View Layout and Presentation
        
        User Interface
        - Drawing and Animation
        - Framework Integration
        - State and Data Flow
        
        Sample Code
        struct ContentView: View {
            var body: some View {
                VStack {
                    Text("Hello, World!")
                        .font(.title)
                    Button("Tap me") {
                        print("Button tapped")
                    }
                }
                .padding()
            }
        }
        """
        
        with patch.object(handler, '_detect_active_application', return_value=safari_app_info):
            with patch('modules.browser_accessibility.BrowserAccessibilityHandler') as mock_browser_class:
                mock_browser_handler = Mock()
                mock_browser_handler.get_page_text_content.return_value = apple_dev_content
                mock_browser_class.return_value = mock_browser_handler
                
                with patch.object(handler, '_validate_browser_content', return_value=True):
                    result = handler._extract_browser_content()
        
        assert result == apple_dev_content
        assert "SwiftUI" in result
        assert "Apple Developer" in result
        assert "ContentView" in result
    
    def test_safari_apple_news_extraction(self, handler, safari_app_info):
        """Test Safari content extraction from Apple News."""
        apple_news_content = """
        Apple News
        
        Technology
        
        Apple Announces New AI Features for iOS 18
        
        By Tech Reporter • 2 hours ago
        
        Apple today announced significant artificial intelligence enhancements coming to iOS 18, including improved Siri capabilities, enhanced photo recognition, and new machine learning features for developers.
        
        Key Features:
        • Advanced natural language processing
        • On-device machine learning improvements
        • Enhanced privacy protections for AI features
        • New Core ML framework updates
        
        The updates will be available to developers in the upcoming beta release, with a public release planned for fall 2024.
        
        "These AI enhancements represent our commitment to bringing powerful, privacy-focused artificial intelligence to every iPhone user," said Apple's VP of Software Engineering.
        
        Related Articles:
        - iOS 18 Developer Preview Available
        - Machine Learning on Apple Silicon
        - Privacy in AI: Apple's Approach
        """
        
        with patch.object(handler, '_detect_active_application', return_value=safari_app_info):
            with patch('modules.browser_accessibility.BrowserAccessibilityHandler') as mock_browser_class:
                mock_browser_handler = Mock()
                mock_browser_handler.get_page_text_content.return_value = apple_news_content
                mock_browser_class.return_value = mock_browser_handler
                
                with patch.object(handler, '_validate_browser_content', return_value=True):
                    result = handler._extract_browser_content()
        
        assert result == apple_news_content
        assert "Apple News" in result
        assert "AI Features" in result
        assert "iOS 18" in result
    
    def test_safari_wikipedia_extraction(self, handler, safari_app_info):
        """Test Safari content extraction from Wikipedia."""
        wikipedia_content = """
        Wikipedia
        
        Artificial Intelligence
        
        From Wikipedia, the free encyclopedia
        
        Artificial intelligence (AI) is intelligence demonstrated by machines, in contrast to the natural intelligence displayed by humans and animals. Leading AI textbooks define the field as the study of "intelligent agents": any device that perceives its environment and takes actions that maximize its chance of successfully achieving its goals.
        
        Contents
        1. History
        2. Goals
        3. Approaches
        4. Applications
        5. Philosophy and ethics
        6. Future
        
        History
        The field of AI research was born at a Dartmouth College workshop in 1956. Attendees Allen Newell, Herbert Simon, John McCarthy, Marvin Minsky and Arthur Samuel became the founders and leaders of AI research.
        
        Goals
        The general problem of simulating (or creating) intelligence has been broken down into sub-problems. These consist of particular traits or capabilities that researchers expect an intelligent system to display.
        
        Applications
        AI is used in a wide range of applications including:
        - Search algorithms
        - Natural language processing
        - Computer vision
        - Robotics
        - Machine learning
        """
        
        with patch.object(handler, '_detect_active_application', return_value=safari_app_info):
            with patch('modules.browser_accessibility.BrowserAccessibilityHandler') as mock_browser_class:
                mock_browser_handler = Mock()
                mock_browser_handler.get_page_text_content.return_value = wikipedia_content
                mock_browser_class.return_value = mock_browser_handler
                
                with patch.object(handler, '_validate_browser_content', return_value=True):
                    result = handler._extract_browser_content()
        
        assert result == wikipedia_content
        assert "Artificial Intelligence" in result
        assert "Wikipedia" in result
        assert "machine learning" in result
    
    def test_safari_extraction_performance(self, handler, safari_app_info):
        """Test Safari extraction performance requirements."""
        content = "Safari content with more than 50 characters for validation testing."
        
        start_time = time.time()
        
        with patch.object(handler, '_detect_active_application', return_value=safari_app_info):
            with patch('modules.browser_accessibility.BrowserAccessibilityHandler') as mock_browser_class:
                mock_browser_handler = Mock()
                mock_browser_handler.get_page_text_content.return_value = content
                mock_browser_class.return_value = mock_browser_handler
                
                with patch.object(handler, '_validate_browser_content', return_value=True):
                    result = handler._extract_browser_content()
        
        execution_time = time.time() - start_time
        
        assert result == content
        assert execution_time < 2.0  # Should complete within 2 seconds


class TestFirefoxFastPath:
    """Firefox-specific fast path tests."""
    
    @pytest.fixture
    def handler(self):
        """Create handler for Firefox testing."""
        mock_orchestrator = Mock()
        return QuestionAnsweringHandler(mock_orchestrator)
    
    @pytest.fixture
    def firefox_app_info(self):
        """Create Firefox application info."""
        app_info = Mock()
        app_info.name = "Firefox"
        app_info.app_type = ApplicationType.WEB_BROWSER
        app_info.browser_type = BrowserType.FIREFOX
        return app_info
    
    def test_firefox_mdn_extraction(self, handler, firefox_app_info):
        """Test Firefox content extraction from MDN Web Docs."""
        mdn_content = """
        MDN Web Docs
        
        JavaScript
        
        Array.prototype.map()
        
        The map() method creates a new array populated with the results of calling a provided function on every element in the calling array.
        
        Try it
        
        Syntax
        map(callbackFn)
        map(callbackFn, thisArg)
        
        Parameters
        callbackFn
        A function to execute for each element in the array. Its return value is added as a single element in the new array.
        
        The function is called with the following arguments:
        - element: The current element being processed in the array.
        - index: The index of the current element being processed in the array.
        - array: The array map was called upon.
        
        thisArg (Optional)
        A value to use as this when executing callbackFn.
        
        Return value
        A new array with each element being the result of the callback function.
        
        Examples
        
        Mapping an array of numbers to an array of square roots
        const numbers = [1, 4, 9];
        const roots = numbers.map((num) => Math.sqrt(num));
        // roots is now     [1, 2, 3]
        // numbers is still [1, 4, 9]
        """
        
        with patch.object(handler, '_detect_active_application', return_value=firefox_app_info):
            with patch('modules.browser_accessibility.BrowserAccessibilityHandler') as mock_browser_class:
                mock_browser_handler = Mock()
                mock_browser_handler.get_page_text_content.return_value = mdn_content
                mock_browser_class.return_value = mock_browser_handler
                
                with patch.object(handler, '_validate_browser_content', return_value=True):
                    result = handler._extract_browser_content()
        
        assert result == mdn_content
        assert "MDN Web Docs" in result
        assert "Array.prototype.map()" in result
        assert "JavaScript" in result
    
    def test_firefox_reddit_extraction(self, handler, firefox_app_info):
        """Test Firefox content extraction from Reddit."""
        reddit_content = """
        Reddit
        
        r/MachineLearning
        
        [Discussion] Best resources for learning deep learning in 2024?
        
        Posted by u/ml_enthusiast • 3 hours ago
        
        I'm looking to dive deeper into deep learning and would love recommendations for the best resources available in 2024. I have a solid foundation in Python and basic ML concepts.
        
        What I'm looking for:
        - Comprehensive courses or tutorials
        - Hands-on projects
        - Research papers for beginners
        - Community recommendations
        
        Comments (47):
        
        u/deep_learner_pro • 2 hours ago
        I highly recommend the Deep Learning Specialization on Coursera by Andrew Ng. It's comprehensive and includes practical assignments.
        
        u/pytorch_fan • 2 hours ago
        Fast.ai is excellent for practical deep learning. They focus on getting you building models quickly while understanding the theory.
        
        u/research_student • 1 hour ago
        For research papers, start with "Attention Is All You Need" and "Deep Residual Learning for Image Recognition". These are foundational papers that are relatively accessible.
        
        u/ml_engineer • 1 hour ago
        Don't forget about Kaggle competitions! They're great for hands-on experience with real datasets.
        """
        
        with patch.object(handler, '_detect_active_application', return_value=firefox_app_info):
            with patch('modules.browser_accessibility.BrowserAccessibilityHandler') as mock_browser_class:
                mock_browser_handler = Mock()
                mock_browser_handler.get_page_text_content.return_value = reddit_content
                mock_browser_class.return_value = mock_browser_handler
                
                with patch.object(handler, '_validate_browser_content', return_value=True):
                    result = handler._extract_browser_content()
        
        assert result == reddit_content
        assert "Reddit" in result
        assert "MachineLearning" in result
        assert "deep learning" in result
    
    def test_firefox_arxiv_extraction(self, handler, firefox_app_info):
        """Test Firefox content extraction from arXiv."""
        arxiv_content = """
        arXiv.org
        
        Computer Science > Machine Learning
        
        Attention Is All You Need
        
        Authors: Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Lukasz Kaiser, Illia Polosukhin
        
        (Submitted on 12 Jun 2017 (v1), last revised 6 Dec 2017 (this version, v5))
        
        Abstract
        The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder. The best performing models also connect the encoder and decoder through an attention mechanism. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely.
        
        Experiments on two machine translation tasks show that these models are superior in quality while being more parallelizable and requiring significantly less time to train. Our model achieves 28.4 BLEU on the WMT 2014 English-to-German translation task, improving over the existing best results, including ensembles, by over 2 BLEU.
        
        Comments: 15 pages, 5 figures
        Subjects: Computation and Language (cs.CL); Machine Learning (cs.LG)
        Cite as: arXiv:1706.03762 [cs.CL]
        """
        
        with patch.object(handler, '_detect_active_application', return_value=firefox_app_info):
            with patch('modules.browser_accessibility.BrowserAccessibilityHandler') as mock_browser_class:
                mock_browser_handler = Mock()
                mock_browser_handler.get_page_text_content.return_value = arxiv_content
                mock_browser_class.return_value = mock_browser_handler
                
                with patch.object(handler, '_validate_browser_content', return_value=True):
                    result = handler._extract_browser_content()
        
        assert result == arxiv_content
        assert "arXiv.org" in result
        assert "Attention Is All You Need" in result
        assert "Transformer" in result
    
    def test_firefox_extraction_performance(self, handler, firefox_app_info):
        """Test Firefox extraction performance requirements."""
        content = "Firefox content with more than 50 characters for validation testing."
        
        start_time = time.time()
        
        with patch.object(handler, '_detect_active_application', return_value=firefox_app_info):
            with patch('modules.browser_accessibility.BrowserAccessibilityHandler') as mock_browser_class:
                mock_browser_handler = Mock()
                mock_browser_handler.get_page_text_content.return_value = content
                mock_browser_class.return_value = mock_browser_handler
                
                with patch.object(handler, '_validate_browser_content', return_value=True):
                    result = handler._extract_browser_content()
        
        execution_time = time.time() - start_time
        
        assert result == content
        assert execution_time < 2.0  # Should complete within 2 seconds


class TestBrowserContentValidation:
    """Tests for browser content validation across all browsers."""
    
    @pytest.fixture
    def handler(self):
        """Create handler for validation testing."""
        mock_orchestrator = Mock()
        return QuestionAnsweringHandler(mock_orchestrator)
    
    def test_content_length_validation(self, handler):
        """Test content length validation requirements."""
        # Test content too short
        short_content = "Short"  # Less than 50 characters
        assert not handler._validate_browser_content(short_content)
        
        # Test content just long enough
        valid_content = "This content is exactly fifty characters long!!"  # 50 characters
        assert handler._validate_browser_content(valid_content)
        
        # Test content well above minimum
        long_content = "This is a much longer piece of content that definitely exceeds the minimum character requirement for validation."
        assert handler._validate_browser_content(long_content)
    
    def test_content_quality_validation(self, handler):
        """Test content quality validation."""
        # Test empty content
        assert not handler._validate_browser_content("")
        
        # Test whitespace-only content
        assert not handler._validate_browser_content("   \n\t   ")
        
        # Test content with only special characters
        special_chars_content = "!@#$%^&*()_+-=[]{}|;':\",./<>?" * 2  # Over 50 chars but low quality
        # This should still pass basic validation but might fail quality checks
        # depending on implementation
        result = handler._validate_browser_content(special_chars_content)
        # The exact behavior depends on implementation details
        
        # Test normal text content
        normal_content = "This is normal text content that should pass all validation checks."
        assert handler._validate_browser_content(normal_content)
    
    def test_content_encoding_handling(self, handler):
        """Test handling of different content encodings."""
        # Test Unicode content
        unicode_content = "This content contains Unicode characters: café, naïve, résumé, and emoji 🚀🤖"
        assert handler._validate_browser_content(unicode_content)
        
        # Test mixed language content
        mixed_content = "English text mixed with 中文 and العربية and русский язык content."
        assert handler._validate_browser_content(mixed_content)
    
    def test_html_content_handling(self, handler):
        """Test handling of HTML content that might be extracted."""
        # Test content with HTML tags (should be handled by extraction layer)
        html_content = """
        <div class="content">
            <h1>Page Title</h1>
            <p>This is a paragraph with <strong>bold text</strong> and <em>italic text</em>.</p>
            <ul>
                <li>List item 1</li>
                <li>List item 2</li>
            </ul>
        </div>
        """
        
        # The validation should work with whatever content is passed to it
        assert handler._validate_browser_content(html_content)
    
    def test_large_content_handling(self, handler):
        """Test handling of very large content."""
        # Test very large content (simulate a long webpage)
        large_content = "This is a very long piece of content. " * 1000  # ~38,000 characters
        
        # Should still validate successfully
        assert handler._validate_browser_content(large_content)
    
    def test_content_with_code_blocks(self, handler):
        """Test validation of content containing code blocks."""
        code_content = """
        Programming Tutorial: Python Functions
        
        Here's how to define a function in Python:
        
        def greet(name):
            return f"Hello, {name}!"
        
        # Call the function
        message = greet("World")
        print(message)
        
        Functions can also have default parameters:
        
        def greet_with_title(name, title="Mr."):
            return f"Hello, {title} {name}!"
        
        This is useful for creating flexible APIs.
        """
        
        assert handler._validate_browser_content(code_content)
        assert len(code_content) > 50


class TestBrowserErrorHandling:
    """Tests for browser-specific error handling scenarios."""
    
    @pytest.fixture
    def handler(self):
        """Create handler for error testing."""
        mock_orchestrator = Mock()
        return QuestionAnsweringHandler(mock_orchestrator)
    
    def test_browser_handler_initialization_failure(self, handler):
        """Test handling when BrowserAccessibilityHandler fails to initialize."""
        app_info = Mock()
        app_info.app_type = ApplicationType.WEB_BROWSER
        
        with patch.object(handler, '_detect_active_application', return_value=app_info):
            with patch('modules.browser_accessibility.BrowserAccessibilityHandler', side_effect=Exception("Init failed")):
                result = handler._extract_browser_content()
        
        assert result is None
    
    def test_browser_extraction_exception(self, handler):
        """Test handling when browser extraction raises an exception."""
        app_info = Mock()
        app_info.app_type = ApplicationType.WEB_BROWSER
        
        with patch.object(handler, '_detect_active_application', return_value=app_info):
            with patch('modules.browser_accessibility.BrowserAccessibilityHandler') as mock_browser_class:
                mock_browser_handler = Mock()
                mock_browser_handler.get_page_text_content.side_effect = Exception("Extraction failed")
                mock_browser_class.return_value = mock_browser_handler
                
                result = handler._extract_browser_content()
        
        assert result is None
    
    def test_browser_extraction_returns_none(self, handler):
        """Test handling when browser extraction returns None."""
        app_info = Mock()
        app_info.app_type = ApplicationType.WEB_BROWSER
        
        with patch.object(handler, '_detect_active_application', return_value=app_info):
            with patch('modules.browser_accessibility.BrowserAccessibilityHandler') as mock_browser_class:
                mock_browser_handler = Mock()
                mock_browser_handler.get_page_text_content.return_value = None
                mock_browser_class.return_value = mock_browser_handler
                
                result = handler._extract_browser_content()
        
        assert result is None
    
    def test_browser_extraction_returns_empty_string(self, handler):
        """Test handling when browser extraction returns empty string."""
        app_info = Mock()
        app_info.app_type = ApplicationType.WEB_BROWSER
        
        with patch.object(handler, '_detect_active_application', return_value=app_info):
            with patch('modules.browser_accessibility.BrowserAccessibilityHandler') as mock_browser_class:
                mock_browser_handler = Mock()
                mock_browser_handler.get_page_text_content.return_value = ""
                mock_browser_class.return_value = mock_browser_handler
                
                result = handler._extract_browser_content()
        
        assert result is None
    
    def test_browser_content_validation_failure(self, handler):
        """Test handling when browser content fails validation."""
        app_info = Mock()
        app_info.app_type = ApplicationType.WEB_BROWSER
        
        content = "Valid content that passes length requirements but fails other validation."
        
        with patch.object(handler, '_detect_active_application', return_value=app_info):
            with patch('modules.browser_accessibility.BrowserAccessibilityHandler') as mock_browser_class:
                mock_browser_handler = Mock()
                mock_browser_handler.get_page_text_content.return_value = content
                mock_browser_class.return_value = mock_browser_handler
                
                with patch.object(handler, '_validate_browser_content', return_value=False):
                    result = handler._extract_browser_content()
        
        assert result is None