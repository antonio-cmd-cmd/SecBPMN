"""
BPMN Soundness Verification Script

This script reads all BPMN files from a specified folder and verifies their soundness
by interacting with the backend API validation endpoint.
"""

import os
import requests
from pathlib import Path
import json
from datetime import datetime
from typing import List, Dict
import csv


# ===== CONFIGURATION =====
# Path to the folder containing BPMN files to verify
BPMN_FOLDER_PATH = "/mnt/c/Users/ianna/OneDrive - Uniparthenope/Uniparthenope1/Dottorato/Periodo estero/studio/Masterproject-Sourcecode/Masterproject-Sourcecode/Masterproject-Backend"
# Backend API endpoint URL
BACKEND_URL = "http://localhost:8000/validate-bpmn/"

# Folder where results will be saved
RESULTS_FOLDER = "soundness_results"


def get_bpmn_files(folder_path: str) -> List[Path]:
    """
    Get all BPMN files from the specified folder.
    
    Args:
        folder_path: Path to folder containing BPMN files
        
    Returns:
        List of Path objects for BPMN files
    """
    folder = Path(folder_path)
    
    if not folder.exists():
        raise FileNotFoundError(f"Folder not found: {folder_path}")
    
    if not folder.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {folder_path}")
    
    # Get all .bpmn files
    bpmn_files = list(folder.glob("*.bpmn"))
    
    return bpmn_files


def validate_bpmn_file(file_path: Path, backend_url: str) -> Dict:
    """
    Validate a single BPMN file by sending it to the backend API.
    
    Args:
        file_path: Path to BPMN file
        backend_url: URL of the backend validation endpoint
        
    Returns:
        Dictionary with validation results
    """
    try:
        # Read the BPMN file
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f, 'application/xml')}
            
            # Send POST request to backend
            response = requests.post(backend_url, files=files, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'file': file_path.name,
                    'status': 'success',
                    'valid': result.get('valid', False),
                    'sound': result.get('sound', False),
                    'message': result.get('message', ''),
                    'details': result
                }
            else:
                return {
                    'file': file_path.name,
                    'status': 'error',
                    'valid': False,
                    'sound': False,
                    'message': f'HTTP Error {response.status_code}: {response.text}',
                    'details': {}
                }
                
    except requests.exceptions.RequestException as e:
        return {
            'file': file_path.name,
            'status': 'error',
            'valid': False,
            'sound': False,
            'message': f'Request error: {str(e)}',
            'details': {}
        }
    except Exception as e:
        return {
            'file': file_path.name,
            'status': 'error',
            'valid': False,
            'sound': False,
            'message': f'Unexpected error: {str(e)}',
            'details': {}
        }


def save_results(results: List[Dict], output_folder: str):
    """
    Save validation results to JSON and CSV files.
    
    Args:
        results: List of validation results
        output_folder: Folder where to save results
    """
    # Create output folder if it doesn't exist
    output_path = Path(output_folder)
    output_path.mkdir(exist_ok=True)
    
    # Generate timestamp for filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save detailed JSON results
    json_file = output_path / f"validation_results_{timestamp}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Save summary CSV
    csv_file = output_path / f"validation_summary_{timestamp}.csv"
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['file', 'status', 'valid', 'sound', 'message']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        writer.writeheader()
        for result in results:
            writer.writerow({
                'file': result['file'],
                'status': result['status'],
                'valid': result['valid'],
                'sound': result['sound'],
                'message': result['message']
            })
    
    print(f"\nResults saved to:")
    print(f"  - JSON: {json_file}")
    print(f"  - CSV:  {csv_file}")


def print_summary(results: List[Dict]):
    """
    Print a summary of validation results.
    
    Args:
        results: List of validation results
    """
    total = len(results)
    valid_count = sum(1 for r in results if r['valid'])
    sound_count = sum(1 for r in results if r['sound'])
    error_count = sum(1 for r in results if r['status'] == 'error')
    
    print("\n" + "="*80)
    print("SOUNDNESS VERIFICATION SUMMARY")
    print("="*80)
    print(f"Total files processed:     {total}")
    print(f"Valid BPMN files:          {valid_count} ({valid_count/total*100:.1f}%)")
    print(f"Sound BPMN files:          {sound_count} ({sound_count/total*100:.1f}%)")
    print(f"Errors during processing:  {error_count} ({error_count/total*100:.1f}%)")
    print("="*80)
    
    # Print details for each file
    print("\nDETAILED RESULTS:")
    print("-"*80)
    for result in results:
        status_icon = "✓" if result['sound'] else "✗"
        print(f"{status_icon} {result['file']}")
        print(f"   Valid: {result['valid']}, Sound: {result['sound']}")
        if result['message']:
            print(f"   Message: {result['message']}")
        print()


def main():
    """
    Main function to process all BPMN files in the folder.
    """
    print("="*80)
    print("BPMN SOUNDNESS VERIFICATION SCRIPT")
    print("="*80)
    print(f"BPMN Folder: {BPMN_FOLDER_PATH}")
    print(f"Backend URL: {BACKEND_URL}")
    print("="*80)
    
    try:
        # Get all BPMN files
        print("\nSearching for BPMN files...")
        bpmn_files = get_bpmn_files(BPMN_FOLDER_PATH)
        
        if not bpmn_files:
            print(f"No BPMN files found in {BPMN_FOLDER_PATH}")
            return
        
        print(f"Found {len(bpmn_files)} BPMN file(s)")
        
        # Validate each file
        results = []
        for i, bpmn_file in enumerate(bpmn_files, 1):
            print(f"\n[{i}/{len(bpmn_files)}] Validating: {bpmn_file.name}")
            result = validate_bpmn_file(bpmn_file, BACKEND_URL)
            results.append(result)
            
            # Print immediate result
            if result['status'] == 'success':
                status = "SOUND" if result['sound'] else "NOT SOUND"
                print(f"  → Result: {status}")
            else:
                print(f"  → Error: {result['message']}")
        
        # Print summary
        print_summary(results)
        
        # Save results
        save_results(results, RESULTS_FOLDER)
        
    except FileNotFoundError as e:
        print(f"\nError: {e}")
        print("Please update the BPMN_FOLDER_PATH variable in the script.")
    except NotADirectoryError as e:
        print(f"\nError: {e}")
        print("Please ensure BPMN_FOLDER_PATH points to a directory.")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
