from repro2 import MODELS_ROOT
from repro2.commands.subcommand import SetupSubcommand
from repro2.common.docker import BuildDockerImageSubcommand
from repro2.models.denkowski2014 import DEFAULT_IMAGE, MODEL_NAME


@SetupSubcommand.register(MODEL_NAME)
class Denkowski2014SetupSubcommand(BuildDockerImageSubcommand):
    def __init__(self) -> None:
        super().__init__(f"{MODELS_ROOT}/{MODEL_NAME}", DEFAULT_IMAGE)
