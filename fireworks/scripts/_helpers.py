import os
from argparse import Namespace
from typing import Sequence, Tuple, Union

cfg_file_vldtor = Tuple[str, str, bool, Union[str, None]]


def _validate_config_file_paths(args: Namespace, cfg_files_to_validate: Sequence[cfg_file_vldtor]) -> None:
    """Validate the CLI config files.

    Args:
        args (argparse.Namespace): The parsed arguments from the CLI.
        cfg_files_to_validate (list[tuple[str, str, bool, str | None]]): config files to validate.

    Raises:
        ValueError: If a path to a required config file is not provided.
        FileNotFoundError: If a config file is provided but does not exist.
    """
    for config_file, cli_flag, required, default_loc in cfg_files_to_validate:

        file_name = f"{config_file}_file"
        file_path = getattr(args, file_name)

        # args.config_dir defaults to '.' if not specified
        if file_path is None and os.path.exists(os.path.join(args.config_dir, f"my_{file_name}.yaml")):
            setattr(args, file_name, os.path.join(args.config_dir, f"my_{file_name}.yaml"))
        elif file_path is None:
            setattr(args, file_name, default_loc)

        file_path = getattr(args, file_name, None)

        # throw on missing config files
        if file_path is None and required:
            raise ValueError(
                f"No path specified for {file_name}. Use the {cli_flag} flag to specify or check the value "
                f"of CONFIG_FILE_DIR and make sure it points at where all your config files are."
            )
        if file_path is not None and not os.path.exists(file_path):
            raise FileNotFoundError(f"{file_name} '{file_path}' does not exist!")
