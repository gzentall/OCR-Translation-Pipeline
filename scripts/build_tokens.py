#!/usr/bin/env python3
"""
Simple design token builder for Flask app.
Converts tokens.json to CSS variables.
"""

import json
import os
from pathlib import Path

def resolve_references(tokens, path=""):
    """Resolve token references like {color.primary.40}"""
    if isinstance(tokens, dict):
        return {k: resolve_references(v, f"{path}.{k}" if path else k) for k, v in tokens.items()}
    elif isinstance(tokens, str) and tokens.startswith("{") and tokens.endswith("}"):
        # Extract reference path
        ref_path = tokens[1:-1]  # Remove { and }
        parts = ref_path.split(".")
        
        # Navigate to the referenced value
        current = tokens_data
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                # If we can't resolve, return the original string
                return tokens
        
        return current
    else:
        return tokens

def generate_css_variables(tokens, prefix="--md-sys"):
    """Generate CSS variables from tokens"""
    css_lines = []
    
    def process_dict(data, current_path=""):
        for key, value in data.items():
            if isinstance(value, dict):
                process_dict(value, f"{current_path}-{key}" if current_path else key)
            else:
                var_name = f"{prefix}-{current_path}-{key}" if current_path else f"{prefix}-{key}"
                css_lines.append(f"  {var_name}: {value};")
    
    process_dict(tokens)
    return "\n".join(css_lines)

def main():
    global tokens_data
    
    # Load tokens
    tokens_file = Path(__file__).parent.parent / "design" / "tokens.json"
    with open(tokens_file, 'r') as f:
        tokens_data = json.load(f)
    
    # Resolve references
    resolved_tokens = resolve_references(tokens_data)
    
    # Generate CSS
    css_content = f""":root {{
{generate_css_variables(resolved_tokens)}
}}

/* Dark mode overrides */
[data-theme="dark"] {{
{generate_css_variables(resolved_tokens.get('modes', {}).get('dark', {}), '--md-sys')}
}}
"""
    
    # Write CSS file
    output_file = Path(__file__).parent.parent / "static" / "css" / "tokens.css"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        f.write(css_content)
    
    print(f"✅ Generated design tokens CSS: {output_file}")
    print(f"📊 Generated {len(css_content.split(';'))} CSS variables")

if __name__ == "__main__":
    main()
