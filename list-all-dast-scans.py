import argparse
import csv
from veracode_api_py import Analyses, BusinessUnits, Occurrences
from veracode_api_py.apihelper import APIHelper

def get_actual_start_date(occurrence):
    return occurrence["actual_start_date"] if "actual_start_date" in occurrence else "NONE"

def get_scheduled_start_date(occurrence):
    return occurrence["start_date"] if "start_date" in occurrence else "NONE"

def get_create_date(base_analysis):
    return base_analysis["created_on"] if "created_on" in base_analysis else "NONE"

def get_actual_end_date(occurrence):
    return occurrence["actual_end_date"] if "actual_end_date" in occurrence else "NONE"

def get_scheduled_end_date(occurrence):
    return occurrence["end_date"] if "end_date" in occurrence else "NONE"

def get_status(occurrence):
    if "status" in occurrence and "status_type" in occurrence["status"]:
        return occurrence["status"]["status_type"]
    return 'No status found'

def main():
    parser = argparse.ArgumentParser(
        description="Lists all DAST scans available to the current user."
    )

    parser.add_argument(
        "-o",
        "--output_file",
        help="Name of the CSV file to save (default: 'All_DAST_Scans.csv').",
        required=False
    )

    parser.add_argument(
        "-s",
        "--start_date",
        help="Minimum scheduled start date (YYYY-MM-DDTHH:mm:ssZ).",
        required=False
    )

    parser.add_argument(
        "-e",
        "--end_date",
        help="Maximum scheduled start date (YYYY-MM-DDTHH:mm:ssZ).",
        required=False
    )

    args =  parser.parse_args()
    output_file = args.output_file

    if not output_file:
        output_file = "All_DAST_Scans.csv"

    print("Fetching list of DAST scans")
    all_dast_scans = []
    if args.start_date or args.end_date:
        scan_filters = {}
        if args.start_date:
            scan_filters["start_date_after"] = args.start_date
        if args.end_date:
            scan_filters["start_date_before"] = args.end_date
        all_occurrences = APIHelper()._rest_paged_request('was/configservice/v1/analysis_occurrences','GET','analysis_occurrences', scan_filters)
    else:
        all_occurrences = Occurrences().get_all()

    business_unit_map = dict()
    for bu in BusinessUnits().get_all():
        business_unit_map.update({str(bu["bu_legacy_id"]): bu["bu_name"]})

    for occurrence in all_occurrences:
        base_analysis = Analyses().get(occurrence["analysis_id"])
        bu_id = base_analysis["org_info"]["business_unit_id"] if ("org_info" in base_analysis and "business_unit_id" in base_analysis["org_info"]) else None
        business_unit = business_unit_map[bu_id] if str(bu_id) in business_unit_map else "No Business Unit"
        all_dast_scans.append({ "name": base_analysis["name"], "business_unit": business_unit, "create_date": get_create_date(base_analysis), "scheduled_start_date": get_scheduled_start_date(occurrence), "actual_start_date": get_actual_start_date(occurrence), "scheduled_end_date": get_scheduled_end_date(occurrence), "actual_end_date": get_actual_end_date(occurrence), "status": get_status(occurrence)})         

    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["Name", "Business Unit", "Create Date", "Start Date (scheduled)", "Start Date (actual)", "End Date (scheduled)", "End Date (actual)", "Status"])
        for entry in all_dast_scans:
            csv_writer.writerow([entry["name"], entry["business_unit"], entry["create_date"], entry["scheduled_start_date"], entry["actual_start_date"], entry["scheduled_end_date"], entry["actual_end_date"], entry["status"]])

if __name__ == '__main__':
    main()