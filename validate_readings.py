#!/usr/bin/env python3
"""
Validation script to check liturgy_fetcher.py readings database
"""
import ast
import sys

def extract_readings_database():
    """Extract the readings_database dictionary from liturgy_fetcher.py"""
    with open('liturgy_fetcher.py', 'r') as f:
        content = f.read()
    
    tree = ast.parse(content)
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == '_get_date_specific_readings':
            for stmt in node.body:
                if isinstance(stmt, ast.Assign):
                    for target in stmt.targets:
                        if isinstance(target, ast.Name) and target.id == 'readings_database':
                            return ast.literal_eval(stmt.value)
    return None

def validate_readings():
    """Validate all readings have required components"""
    readings_db = extract_readings_database()
    
    if not readings_db:
        print("ERROR: Could not extract readings_database")
        return False
    
    required_keys = ['first_reading', 'psalm', 'second_reading', 'gospel', 'collect']
    
    print(f"Found {len(readings_db)} date entries")
    print("\nValidating each entry...\n")
    
    all_valid = True
    for date, readings in sorted(readings_db.items()):
        missing_keys = [key for key in required_keys if key not in readings]
        
        if missing_keys:
            print(f"❌ {date}: MISSING {missing_keys}")
            all_valid = False
        else:
            print(f"✓ {date}: Complete (all 5 components)")
    
    if all_valid:
        print("\n✅ All entries are complete!")
    else:
        print("\n❌ Some entries are incomplete")
    
    return all_valid

if __name__ == '__main__':
    valid = validate_readings()
    sys.exit(0 if valid else 1)
