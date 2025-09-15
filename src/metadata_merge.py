import json
import os
import sys
from typing import List, Dict, Any


def merge_two_json(json1, json2):
    if json1 == {}:
        return json2
    if json2 == {}:
        return json1
    json1_root = json1["tools"][0]
    json2_root = json2["tools"][0]
    # We append info from json2 to json1 from here on out
    json1_root["result_source_files"].update(json2_root["result_source_files"])
    json1_root["skipped"] = json1_root["skipped"] + json2_root["skipped"]
    # Merge time
    json1_root["timestamps"]["begin"] = min(
        float(json1_root["timestamps"]["begin"]),
        float(json2_root["timestamps"]["begin"]),
    )
    json1_root["timestamps"]["end"] = max(
        float(json1_root["timestamps"]["end"]),
        float(json2_root["timestamps"]["end"]),
    )
    # Merge analyzers
    for key, value in json2_root["analyzers"].items():
        json1_stat = json1_root["analyzers"][key]["analyzer_statistics"]
        json2_stat = json2_root["analyzers"][key]["analyzer_statistics"]
        json1_stat["failed"] = json1_stat["failed"] + json2_stat["failed"]
        json1_stat["failed_sources"].extend(json2_stat["failed_sources"])
        json1_stat["successful"] = (
            json1_stat["successful"] + json2_stat["successful"]
        )
        json1_stat["successful_sources"].extend(
            json2_stat["successful_sources"]
        )
    return json1


def merge_json_files(file_paths: List[str]) -> Dict[str, Any]:
    merged_data = {}
    for file_path in file_paths:
        if not os.path.exists(file_path):
            print(
                f"Error: File not found at '{file_path}'. Skipping.",
                file=sys.stderr,
            )
            continue

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                merged_data = merge_two_json(merged_data, data)
        except json.JSONDecodeError:
            print(
                f"Error: Could not decode JSON from '{file_path}'. Skipping.",
                file=sys.stderr,
            )
        except Exception as e:
            print(
                f"An unexpected error occurred while processing '{file_path}': {e}",
                file=sys.stderr,
            )

    return merged_data


def save_json_file(data: Dict[str, Any], output_path: str) -> None:
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        print(f"\nSuccessfully saved merged data to '{output_path}'")
    except Exception as e:
        print(f"An error occurred while saving the file: {e}", file=sys.stderr)


if __name__ == "__main__":
    output_file = sys.argv[1]
    input_files = sys.argv[2:]

    merged_data = merge_json_files(input_files)
    if merged_data:
        save_json_file(merged_data, output_file)
    else:
        print("\nNo data was merged. Output file will not be created.")
