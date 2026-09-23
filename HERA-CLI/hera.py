import argparse
import os
import runpy
import sys

STEPS = [
    "workspace",
    "capturing",
    "flow",
    "dataset",
    "labelling",
]


def run_step(step_name: str, shared_globals: dict) -> None:
    script_path = f"{step_name}.py"

    if not os.path.exists(script_path):
        print(f"[Error] File not found: {script_path}")
        sys.exit(1)

    print(f"\n{'='*50}")
    print(f" Executing step: {step_name.upper()} ({script_path})")
    print(f"{'='*50}")

    result_ns = runpy.run_path(
        script_path, init_globals=shared_globals, run_name="__main__"
    )

    shared_globals.update(result_ns)


def main():
    parser = argparse.ArgumentParser(
        description="CLI Pipeline runner replacing notebook execution."
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--step",
        choices=STEPS,
        help="Run a single specific step from the pipeline.",
    )
    group.add_argument(
        "--from-step",
        choices=STEPS,
        dest="from_step",
        help="Start execution from this step through the end.",
    )

    parser.add_argument(
        "--pause-after-workspace",
        action="store_true",
        help="Prompt and wait after workspace.py so you can fill out a newly generated config file.",
    )

    args = parser.parse_args()

    if args.step:
        steps_to_run = [args.step]
    elif args.from_step:
        start_idx = STEPS.index(args.from_step)
        steps_to_run = STEPS[start_idx:]
    else:
        steps_to_run = STEPS

    shared_globals = {}

    for step in steps_to_run:
        run_step(step, shared_globals)

        if step == "workspace" and args.pause_after_workspace:
            input(
                "\n[Pause] Check/edit your configuration file, then press Enter to continue..."
            )

    print(f"\n{'='*50}")
    print("Done!")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()