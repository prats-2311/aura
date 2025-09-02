# AURA Command Restructure Proposal

## Making Commands Scalable and Wider Scope

### Current Limitations:

1. **Rigid Pattern Matching**: Commands must match exact regex patterns
2. **Limited Scope**: Each command type is hardcoded for specific actions
3. **Poor Extensibility**: Adding new commands requires code changes
4. **Context Insensitive**: Commands don't adapt to different applications/contexts

### Proposed Solution: Intent-Based Command Architecture

## 1. Universal Action Verbs

Replace specific patterns with universal action verbs that can apply to any context:

### Current vs Proposed:

```
CURRENT: "click on the sign in button"
PROPOSED: "activate sign in" | "select sign in" | "use sign in"

CURRENT: "type 'hello world'"
PROPOSED: "enter hello world" | "input hello world" | "provide hello world"

CURRENT: "scroll down"
PROPOSED: "navigate down" | "move down" | "go down"

CURRENT: "fill out the form"
PROPOSED: "complete this" | "populate this" | "handle this"
```

## 2. Context-Aware Command Processing

### Universal Command Structure:

```
[ACTION] + [TARGET] + [OPTIONAL_CONTEXT]

Examples:
- "activate [button/link/menu]" → Universal activation
- "navigate [direction/location]" → Universal navigation
- "provide [information/data]" → Universal input
- "analyze [element/screen/content]" → Universal analysis
- "complete [task/form/process]" → Universal completion
```

## 3. Semantic Command Categories

### Core Intent Categories:

1. **ACTIVATION**: activate, select, choose, use, trigger, execute
2. **NAVIGATION**: navigate, move, go, browse, explore, travel
3. **INPUT**: provide, enter, supply, give, input, specify
4. **ANALYSIS**: analyze, examine, describe, explain, review, inspect
5. **COMPLETION**: complete, finish, finalize, submit, process, handle
6. **MODIFICATION**: change, update, modify, edit, adjust, configure

## 4. Dynamic Target Resolution

Instead of hardcoded element types, use semantic target resolution:

### Current Approach:

```python
'click': [
    r'click\s+(?:on\s+)?(?:the\s+)?(.+)',
    r'press\s+(?:the\s+)?(.+)',
    r'tap\s+(?:on\s+)?(?:the\s+)?(.+)'
]
```

### Proposed Approach:

```python
'activation': {
    'verbs': ['activate', 'select', 'choose', 'use', 'trigger', 'execute', 'click', 'press', 'tap'],
    'targets': 'any_interactive_element',
    'contexts': ['button', 'link', 'menu', 'option', 'control', 'element']
}
```

## 5. Application-Aware Commands

Commands that adapt based on the current application context:

### Universal Commands with Context Adaptation:

```
"complete this" →
  - In web browser: Fill and submit form
  - In text editor: Finish document/save
  - In email client: Send email
  - In file manager: Complete file operation

"navigate forward" →
  - In web browser: Go to next page
  - In document: Go to next page/section
  - In media player: Skip forward
  - In file manager: Go to next folder
```

## 6. Scalable Command Patterns

### Proposed New Pattern Structure:

```python
UNIVERSAL_COMMAND_PATTERNS = {
    'activation': {
        'patterns': [
            r'(?:activate|select|choose|use|trigger|execute|click|press|tap)\s+(?:on\s+)?(?:the\s+)?(.+)',
            r'(?:open|launch|start)\s+(.+)',
            r'(?:go\s+to|navigate\s+to)\s+(.+)'
        ],
        'intent': 'interact_with_element',
        'scope': 'universal'
    },

    'navigation': {
        'patterns': [
            r'(?:navigate|move|go|browse|scroll)\s+(up|down|left|right|forward|back|to\s+.+)',
            r'(?:next|previous|back|forward)',
            r'(?:page\s+)?(up|down)'
        ],
        'intent': 'change_location_or_view',
        'scope': 'universal'
    },

    'input': {
        'patterns': [
            r'(?:provide|enter|supply|give|input|type|write)\s+(.+)',
            r'(?:set|specify|define)\s+(.+)\s+(?:to|as)\s+(.+)',
            r'(?:fill|populate)\s+(.+)\s+with\s+(.+)'
        ],
        'intent': 'provide_information',
        'scope': 'universal'
    },

    'analysis': {
        'patterns': [
            r'(?:analyze|examine|describe|explain|review|inspect)\s+(.+)',
            r'(?:what|how|where|when|why)\s+(.+)',
            r'(?:tell\s+me\s+about|show\s+me)\s+(.+)'
        ],
        'intent': 'get_information',
        'scope': 'universal'
    },

    'completion': {
        'patterns': [
            r'(?:complete|finish|finalize|submit|process|handle)\s+(.+)',
            r'(?:done|finished)\s+with\s+(.+)',
            r'(?:save|store|keep)\s+(.+)'
        ],
        'intent': 'complete_task',
        'scope': 'universal'
    }
}
```

## 7. Implementation Strategy

### Phase 1: Extend Current System

Add universal patterns alongside existing ones:

```python
def classify_command_intent(self, command: str) -> Dict[str, Any]:
    """Classify command using both legacy patterns and new universal patterns"""

    # Try universal patterns first
    for intent_category, config in UNIVERSAL_COMMAND_PATTERNS.items():
        for pattern in config['patterns']:
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                return {
                    'intent': config['intent'],
                    'category': intent_category,
                    'scope': config['scope'],
                    'target': match.groups(),
                    'confidence': 0.9
                }

    # Fallback to legacy patterns
    return self.legacy_pattern_matching(command)
```

### Phase 2: Context-Aware Processing

```python
def process_universal_command(self, intent_data: Dict, screen_context: Dict) -> Dict:
    """Process command based on intent and current context"""

    intent = intent_data['intent']
    category = intent_data['category']
    target = intent_data['target']

    # Determine application context
    app_context = self.detect_application_context(screen_context)

    # Generate context-aware action plan
    if intent == 'interact_with_element':
        return self.generate_activation_plan(target, app_context, screen_context)
    elif intent == 'change_location_or_view':
        return self.generate_navigation_plan(target, app_context, screen_context)
    # ... etc
```

### Phase 3: Machine Learning Enhancement

```python
def enhance_with_ml(self, command: str, context: Dict) -> Dict:
    """Use ML to improve command understanding over time"""

    # Use embeddings for semantic similarity
    command_embedding = self.get_command_embedding(command)

    # Find similar successful commands
    similar_commands = self.find_similar_commands(command_embedding)

    # Adapt based on user patterns
    user_patterns = self.get_user_command_patterns()

    return self.generate_enhanced_action_plan(command, context, similar_commands, user_patterns)
```

## 8. Benefits of This Approach

### Scalability:

- **Easy Extension**: Add new verbs to existing categories
- **Context Adaptation**: Same command works in different applications
- **User Learning**: System learns user preferences over time

### Wider Scope:

- **Universal Actions**: Commands work across all applications
- **Semantic Understanding**: Focus on intent rather than exact wording
- **Natural Language**: More flexible command phrasing

### Minimal Changes Required:

- **Backward Compatibility**: Keep existing patterns as fallback
- **Gradual Migration**: Implement universal patterns alongside current ones
- **Configuration-Based**: Most changes are in configuration, not core logic

## 9. Example Transformations

### Current Limited Scope:

```
"click on the sign in button" → Only works for buttons labeled "sign in"
"type 'password123'" → Only works for exact text input
"scroll down" → Only works for basic scrolling
```

### New Universal Scope:

```
"activate authentication" → Works for any login method (button, link, form, etc.)
"provide credentials" → Intelligently fills username/password fields
"navigate deeper" → Context-aware navigation (scroll, next page, drill down, etc.)
```

## 10. Implementation Priority

1. **High Priority**: Implement universal activation patterns (covers 80% of use cases)
2. **Medium Priority**: Add context-aware navigation and input patterns
3. **Low Priority**: Implement ML enhancement and user learning

This approach transforms AURA from a pattern-matching system to an intent-understanding system, dramatically increasing its scope and scalability while requiring minimal changes to the core architecture.
