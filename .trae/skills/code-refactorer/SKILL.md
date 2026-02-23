---
name: "code-refactorer"
description: "Refactors code for better structure, readability, and performance. Invoke when code needs optimization or restructuring."
---

# Code Refactorer

This skill analyzes code and suggests or implements refactoring improvements to enhance code quality, maintainability, and performance.

## When to Use

Invoke this skill when:
- Code has become difficult to maintain or understand
- Performance optimization is needed
- Code structure needs improvement
- Duplicated code patterns are detected
- User explicitly asks for refactoring

## Refactoring Principles

### 1. Code Organization
- Group related functions together
- Separate concerns into different modules
- Use meaningful names for functions and variables
- Keep functions focused on a single responsibility

### 2. Readability Improvements
- Add clear comments where necessary
- Use descriptive variable names
- Break complex logic into smaller functions
- Remove dead code

### 3. Performance Considerations
- Identify and eliminate redundant operations
- Optimize loops and data structures
- Consider caching strategies
- Review algorithm complexity

### 4. Best Practices
- Follow language-specific conventions
- Apply design patterns where appropriate
- Ensure proper error handling
- Maintain consistent code style

## Refactoring Process

1. **Analysis Phase**
   - Identify code smells
   - Map dependencies
   - Understand current behavior

2. **Planning Phase**
   - Define refactoring goals
   - Plan incremental changes
   - Ensure test coverage

3. **Implementation Phase**
   - Make small, focused changes
   - Run tests after each change
   - Document modifications

4. **Validation Phase**
   - Verify functionality preserved
   - Check performance improvements
   - Review code quality metrics

## Output Format

When refactoring, provide:
- Clear explanation of changes
- Before/after comparisons
- Rationale for each modification
- Any risks or considerations

## Example Refactorings

### Extract Function
```python
# Before
def process_data(data):
    # ... 50 lines of mixed logic ...

# After
def process_data(data):
    validated = validate_input(data)
    transformed = transform_data(validated)
    return format_output(transformed)

def validate_input(data):
    # ... focused validation logic ...

def transform_data(data):
    # ... focused transformation logic ...

def format_output(data):
    # ... focused formatting logic ...
```

### Remove Duplication
```python
# Before
def handle_user(user):
    # validate
    if not user.name:
        raise ValueError("Name required")
    if not user.email:
        raise ValueError("Email required")
    # process...

def handle_product(product):
    # validate
    if not product.name:
        raise ValueError("Name required")
    if not product.price:
        raise ValueError("Price required")
    # process...

# After
def validate_required(value, field_name):
    if not value:
        raise ValueError(f"{field_name} required")

def handle_user(user):
    validate_required(user.name, "Name")
    validate_required(user.email, "Email")
    # process...

def handle_product(product):
    validate_required(product.name, "Name")
    validate_required(product.price, "Price")
    # process...
```
