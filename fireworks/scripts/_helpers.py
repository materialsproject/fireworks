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

        fname = f"{config_file}_file"
        file_path = getattr(args, fname)

        if file_path is None and os.path.exists(os.path.join(args.config_dir, f"my_{fname}.yaml")):
            setattr(args, fname, os.path.join(args.config_dir, f"my_{fname}.yaml"))
        elif file_path is None:
            setattr(args, fname, default_loc)

        file_path = getattr(args, fname, None)

        # throw on missing config files
        if file_path is None and required:
            raise ValueError(
                f"no path specified for {fname}. Check the value of CONFIG_FILE_DIR and make sure it points "
                f"at where your config files are or use the {cli_flag} flag to specify the path."
            )
        if file_path is not None and not os.path.exists(file_path):
            raise FileNotFoundError(f"{fname} '{file_path}' does not exist!")
