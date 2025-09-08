#!/usr/bin/env python3
"""
Test to verify prompt length calculation.
"""

def test_prompt_length():
    # Simulate the prompt template
    command = "what's on my screen"
    content = "X" * 1200  # 1200 characters of content
    
    prompt = f"""Please provide a concise summary of the following content. The user asked: "{command}"

Focus on the key information that would be most relevant to answering their question. Keep the summary clear, informative, and conversational.

Content to summarize:
{content}

Please provide a summary that I can speak to the user as a direct response to their question."""
    
    print(f"Command length: {len(command)}")
    print(f"Content length: {len(content)}")
    print(f"Total prompt length: {len(prompt)}")
    print(f"Within 2000 char limit: {len(prompt) <= 2000}")
    
    return len(prompt) <= 2000

if __name__ == "__main__":
    success = test_prompt_length()
    print(f"Test {'PASSED' if success else 'FAILED'}")