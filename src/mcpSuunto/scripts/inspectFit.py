from pathlib import Path
import fitdecode


FILENAME = "2026-10-03_08.26.37-trail_running.fit"

FIT_FILE = Path("data/inbox") / FILENAME
OUTPUT_DIR = Path("data/inspection")
OUTPUT_FILE = OUTPUT_DIR / f"{Path(FILENAME).stem}.txt"


def inspect_fit(fit_file: Path, output_file: Path) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with fitdecode.FitReader(fit_file) as fit:
        with output_file.open("w", encoding="utf-8") as output:

            for frame in fit:
                if isinstance(frame, fitdecode.FitDataMessage):

                    output.write(f"\n[{frame.name}]\n")

                    for field in frame.fields:
                        output.write(
                            f"  {field.name}: "
                            f"{field.value} "
                            f"({field.units})\n"
                        )


def main():
    inspect_fit(FIT_FILE, OUTPUT_FILE)
    print(f"Inspection enregistrée dans : {OUTPUT_FILE}")


if __name__ == "__main__":
    main()