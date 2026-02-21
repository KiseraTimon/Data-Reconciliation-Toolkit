from modules import Scanner, Scrapper, Validator

from utils import errhandler

from secret import credentials

USER = credentials()

def pipeline():
    print("\n###\nWelcome to our Data Reconciliation Pipeline\n")

    # Input
    file_path = input("Enter the file path to reconcile: ").strip()

    # Removing quotes if user copied path as "C:\Path"
    if file_path.startswith('"') and file_path.endswith('"'):
        file_path = file_path[1:-1]

    case_num_col = input("Enter Case Number column name: ").strip()
    citation_col = input("Enter Citation column name: ").strip()

    print("\n-----------------\n")

    # --- Validation Phase ---
    validate = Validator(
        file_path=file_path,
        case_num_column=case_num_col,
        citation_column=citation_col
    )

    if not validate.file_exists():
        return

    sheet = validate.create_sheet()
    if sheet is None:
        return

    # NOTE: check_annotations updates validate.case_num_column if it auto-detects a different name
    if not validate.check_annotations(sheet=sheet):
        print("❌ Column validation failed.")
        return

    print("\n-----------------\n")

    # --- Processing Phase ---
    scanner = Scanner(
        case_num_column=validate.case_num_column,
        citation_column=validate.citation_column
    )

    count = scanner.count_records(sheet=sheet)
    print(f"✅ Found {count} records.")

    file_data = scanner.file_extractor(sheet=sheet)

    if file_data:
        print(f"✅ Successfully extracted {len(file_data)} items.\nHighlights\n")
        for item in file_data[:1]:
            print("✨ Row:", item)

    else:
        print("❌ No data extracted.")

    print("\n-----------------\n")

    # --- Scraping Phase ---
    scrapper = Scrapper(
        username=USER['username'],
        password=USER['password'],
        data=file_data
    )

    if not scrapper.authenticator():
        return

    extracted = scrapper.extractor()

    if not extracted:
        print("❌ No data scrapped from the system.")

        return

    print(f"✅ Successfully scrapped {len(extracted)} items from the system.\nHighlights:\n")
    for item in extracted[:1]:
        print("✨ Row:", item, "\n")

    print("\n-----------------\n")

    # --- Reconciliation Phase ---

    reconciled_data = scrapper.comparator(extracted_data=extracted)

    if not reconciled_data:
        print("❌ No data reconciliation achieved")

        return

    print("Highlights:\n")
    for item in reconciled_data[:3]:
        print("✨ Row:", item, "\n")

    print("\n-----------------\n")

    # --- Reporting ---

    if not scrapper.report(
        data=reconciled_data,
        file_path=file_path
    ):
        print("❌ A reconciliation report could not be drafted for your review")

        return

if __name__ == "__main__":
    pipeline()