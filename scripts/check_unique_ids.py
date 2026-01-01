#!/usr/bin/env python3
"""
Script to check for duplicate IDs in metacrafter-registry records.
Analyzes both datatypes and tools to ensure all IDs are unique.
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

def load_jsonl(filepath):
    """Load all records from a JSONL file."""
    records = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                records.append((record, line_num))
            except json.JSONDecodeError as e:
                print(f"ERROR: Failed to parse line {line_num} in {filepath}: {e}", file=sys.stderr)
    return records

def analyze_ids(datatypes_file, tools_file):
    """Analyze IDs for duplicates."""
    print("Loading datatypes...")
    datatype_records = load_jsonl(datatypes_file)
    print(f"Loaded {len(datatype_records)} datatype records")
    
    print("\nLoading tools...")
    tool_records = load_jsonl(tools_file)
    print(f"Loaded {len(tool_records)} tool records")
    
    # Track IDs and their occurrences
    datatype_ids = defaultdict(list)
    tool_ids = defaultdict(list)
    
    # Collect datatype IDs
    for record, line_num in datatype_records:
        record_id = record.get('id')
        if not record_id:
            print(f"WARNING: Datatype record at line {line_num} has no 'id' field")
            continue
        datatype_ids[record_id].append({
            'line': line_num,
            'name': record.get('name', 'N/A'),
            'type': record.get('type', 'unknown')
        })
    
    # Collect tool IDs
    for record, line_num in tool_records:
        record_id = record.get('id')
        if not record_id:
            print(f"WARNING: Tool record at line {line_num} has no 'id' field")
            continue
        tool_ids[record_id].append({
            'line': line_num,
            'name': record.get('name', 'N/A'),
            'category': record.get('category', 'unknown')
        })
    
    # Check for duplicates within datatypes
    print("\n" + "="*80)
    print("CHECKING DATATYPE IDS FOR DUPLICATES")
    print("="*80)
    duplicate_datatypes = {id: occurrences for id, occurrences in datatype_ids.items() if len(occurrences) > 1}
    
    if duplicate_datatypes:
        print(f"\n❌ FOUND {len(duplicate_datatypes)} DUPLICATE DATATYPE IDS:\n")
        for dup_id, occurrences in sorted(duplicate_datatypes.items()):
            print(f"  ID: '{dup_id}' appears {len(occurrences)} times:")
            for occ in occurrences:
                print(f"    - Line {occ['line']}: {occ['name']} (type: {occ['type']})")
            print()
    else:
        print("\n✅ All datatype IDs are unique!")
    
    # Check for duplicates within tools
    print("\n" + "="*80)
    print("CHECKING TOOL IDS FOR DUPLICATES")
    print("="*80)
    duplicate_tools = {id: occurrences for id, occurrences in tool_ids.items() if len(occurrences) > 1}
    
    if duplicate_tools:
        print(f"\n❌ FOUND {len(duplicate_tools)} DUPLICATE TOOL IDS:\n")
        for dup_id, occurrences in sorted(duplicate_tools.items()):
            print(f"  ID: '{dup_id}' appears {len(occurrences)} times:")
            for occ in occurrences:
                print(f"    - Line {occ['line']}: {occ['name']} (category: {occ['category']})")
            print()
    else:
        print("\n✅ All tool IDs are unique!")
    
    # Check for conflicts between datatypes and tools
    print("\n" + "="*80)
    print("CHECKING FOR ID CONFLICTS BETWEEN DATATYPES AND TOOLS")
    print("="*80)
    conflicts = set(datatype_ids.keys()) & set(tool_ids.keys())
    
    if conflicts:
        print(f"\n⚠️  FOUND {len(conflicts)} ID CONFLICTS (same ID used in both datatypes and tools):\n")
        for conflict_id in sorted(conflicts):
            print(f"  ID: '{conflict_id}'")
            print(f"    Used as datatype:")
            for occ in datatype_ids[conflict_id]:
                print(f"      - Line {occ['line']}: {occ['name']} (type: {occ['type']})")
            print(f"    Used as tool:")
            for occ in tool_ids[conflict_id]:
                print(f"      - Line {occ['line']}: {occ['name']} (category: {occ['category']})")
            print()
    else:
        print("\n✅ No conflicts between datatype and tool IDs!")
    
    # Summary statistics
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total unique datatype IDs: {len(datatype_ids)}")
    print(f"Total unique tool IDs: {len(tool_ids)}")
    print(f"Total unique IDs (datatypes + tools): {len(set(datatype_ids.keys()) | set(tool_ids.keys()))}")
    print(f"Duplicate datatype IDs: {len(duplicate_datatypes)}")
    print(f"Duplicate tool IDs: {len(duplicate_tools)}")
    print(f"ID conflicts (datatypes vs tools): {len(conflicts)}")
    
    # Return exit code
    if duplicate_datatypes or duplicate_tools or conflicts:
        print("\n❌ VALIDATION FAILED: Found duplicates or conflicts!")
        return 1
    else:
        print("\n✅ VALIDATION PASSED: All IDs are unique!")
        return 0

def main():
    """Main entry point."""
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    data_dir = repo_root / 'data'
    
    datatypes_file = data_dir / 'datatypes_latest.jsonl'
    tools_file = data_dir / 'tools_latest.jsonl'
    
    if not datatypes_file.exists():
        print(f"ERROR: Datatypes file not found: {datatypes_file}", file=sys.stderr)
        return 1
    
    if not tools_file.exists():
        print(f"ERROR: Tools file not found: {tools_file}", file=sys.stderr)
        return 1
    
    return analyze_ids(datatypes_file, tools_file)

if __name__ == '__main__':
    sys.exit(main())

