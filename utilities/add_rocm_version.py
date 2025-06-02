#!/usr/bin/env python3

import argparse
import os
import re
import sys
from pathlib import Path

def find_yaml_files(directory):
    """Find all packages.yaml files in the directory tree."""
    yaml_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file == "packages.yaml":
                yaml_files.append(os.path.join(root, file))
    return yaml_files

def get_rocm_packages():
    """Return list of ROCm-related packages that need updating."""
    return [
        "hip",
        "hipsparse", 
        "hipblas",
        "hipblas-common",
        "hipsolver",
        "llvm-amdgpu",
        "hsa-rocr-dev",
        "rocminfo",
        "rocm-device-libs",
        "rocprim",
        "rocthrust",
        "rocsparse",
        "rocrand",
        "rocblas",
        "rocsolver",
        "rocm-core",
        "cray-mpich"  # Has ROCm compiler variants
    ]

def parse_existing_versions(content, package_name):
    """Parse existing ROCm versions for a package."""
    versions = set()
    
    # Look for version lines like: version: [5.7.1, 6.1.2, 6.2.4, 6.3.1]
    version_pattern = rf"{package_name}:\s*\n\s*version:\s*\[(.*?)\]"
    match = re.search(version_pattern, content, re.MULTILINE)
    if match:
        version_str = match.group(1)
        # Extract versions
        for v in re.findall(r'(\d+\.\d+\.\d+)', version_str):
            versions.add(v)
    
    # Also look for spec lines to find versions
    spec_pattern = rf"- spec: {package_name}@(\d+\.\d+\.\d+)"
    for match in re.finditer(spec_pattern, content):
        versions.add(match.group(1))
    
    return sorted(versions, key=lambda x: [int(i) for i in x.split('.')])

def get_prefix_pattern(package_name, version):
    """Generate the expected prefix path for a package and version."""
    if package_name == "hip":
        if version in ["5.7.1"]:
            return f"/opt/rocm-{version}/hip"
        else:
            return f"/opt/rocm-{version}"
    elif package_name == "llvm-amdgpu":
        return f"/opt/rocm-{version}/llvm"
    elif package_name == "cray-mpich":
        return f"/usr/tce/packages/cray-mpich/cray-mpich-8.1.31-rocmcc-{version}-magic"
    else:
        return f"/opt/rocm-{version}"

def parse_externals_entries(externals_content, package_name):
    """Parse existing externals entries and return them as structured data."""
    entries = []
    
    # Split into individual entries (each starting with "- spec:")
    entry_pattern = r'(\s*- spec: ' + package_name + r'@(\d+\.\d+\.\d+).*?\n\s*prefix: .*?)(?=\n\s*- spec:|\n\s*\w+:|\Z)'
    
    for match in re.finditer(entry_pattern, externals_content, re.DOTALL):
        entry_text = match.group(1)
        version = match.group(2)
        entries.append((version, entry_text))
    
    return entries

def add_rocm_version_to_package(content, package_name, new_version):
    """Add a new ROCm version to a specific package in the YAML content."""
    
    # Skip if package not found
    if f"{package_name}:" not in content:
        return content
    
    # Get existing versions
    existing_versions = parse_existing_versions(content, package_name)
    
    # Skip if version already exists
    if new_version in existing_versions:
        print(f"  Version {new_version} already exists for {package_name}")
        return content
    
    # Add new version to the list
    updated_versions = existing_versions + [new_version]
    updated_versions.sort(key=lambda x: [int(i) for i in x.split('.')])
    
    # Update version list
    version_pattern = rf"({package_name}:\s*\n\s*version:\s*\[)(.*?)(\])"
    version_list = ", ".join(updated_versions)
    
    def replace_version_list(match):
        return f"{match.group(1)}{version_list}{match.group(3)}"
    
    content = re.sub(version_pattern, replace_version_list, content, flags=re.MULTILINE)
    
    # Generate new spec entry
    prefix = get_prefix_pattern(package_name, new_version)
    
    # Special handling for cray-mpich (has compiler variant)
    if package_name == "cray-mpich":
        new_entry = f"    - spec: cray-mpich@8.1.31%rocmcc@{new_version}\n      prefix: {prefix}"
    else:
        new_entry = f"    - spec: {package_name}@{new_version}%rocmcc@{new_version}\n      prefix: {prefix}"
    
    # Find the externals section and rebuild it with proper ordering
    externals_pattern = rf"({package_name}:.*?externals:\s*\n)(.*?)(\n\s*\w+:|\Z)"
    
    def rebuild_externals(match):
        externals_header = match.group(1)
        externals_content = match.group(2)
        rest = match.group(3) if match.group(3) else ""
        
        # Parse existing entries
        existing_entries = parse_externals_entries(externals_content, package_name)
        
        # Add new entry to the list
        existing_entries.append((new_version, new_entry))
        
        # Sort by version
        existing_entries.sort(key=lambda x: [int(i) for i in x[0].split('.')])
        
        # Rebuild externals section
        rebuilt_externals = ""
        for version, entry_text in existing_entries:
            # Clean up the entry text and ensure proper formatting
            clean_entry = entry_text.strip()
            if not clean_entry.startswith("    "):
                # Add proper indentation if missing
                clean_entry = "    " + clean_entry.lstrip()
            rebuilt_externals += clean_entry + "\n"
        
        return f"{externals_header}{rebuilt_externals}{rest}"
    
    content = re.sub(externals_pattern, rebuild_externals, content, flags=re.MULTILINE | re.DOTALL)
    
    print(f"  Added version {new_version} to {package_name}")
    return content

def update_yaml_file(file_path, new_version):
    """Update a single YAML file with the new ROCm version."""
    print(f"Updating {file_path}")
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        original_content = content
        rocm_packages = get_rocm_packages()
        
        for package in rocm_packages:
            content = add_rocm_version_to_package(content, package, new_version)
        
        # Only write if content changed
        if content != original_content:
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"  Updated {file_path}")
        else:
            print(f"  No changes needed for {file_path}")
            
    except Exception as e:
        print(f"Error updating {file_path}: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Add a new ROCm version to all relevant packages in packages.yaml files"
    )
    parser.add_argument("rocm_version", help="ROCm version to add (e.g., 6.4.0)")
    parser.add_argument(
        "--directory", 
        default=".", 
        help="Directory to search for packages.yaml files (default: current directory)"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true", 
        help="Show what would be changed without making changes"
    )
    
    args = parser.parse_args()
    
    # Validate version format
    if not re.match(r'^\d+\.\d+\.\d+$', args.rocm_version):
        print(f"Error: Invalid version format '{args.rocm_version}'. Expected format: X.Y.Z")
        sys.exit(1)
    
    # Find all packages.yaml files
    yaml_files = find_yaml_files(args.directory)
    
    if not yaml_files:
        print("No packages.yaml files found")
        sys.exit(1)
    
    print(f"Found {len(yaml_files)} packages.yaml files")
    print(f"Adding ROCm version {args.rocm_version}")
    
    if args.dry_run:
        print("DRY RUN - No files will be modified")
    
    for yaml_file in yaml_files:
        if not args.dry_run:
            update_yaml_file(yaml_file, args.rocm_version)
        else:
            print(f"Would update: {yaml_file}")

if __name__ == "__main__":
    main()