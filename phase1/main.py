from simulation.runner import run_from_config
from analysis.summarize_runs import summarize_run_directory
from simulation.utils import load_yaml


def main() -> None:
    config_path = "config/baseline.yaml"
    config = load_yaml(config_path)

    run_from_config(config_path)

    summarize_run_directory(
        run_dir=config["logging"]["output_dir"],
        output_path=f"{config['analysis']['output_dir']}/summary.json",
    )


if __name__ == "__main__":
    main()