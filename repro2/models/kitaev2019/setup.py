import argparse

from overrides import overrides

from repro2 import MODELS_ROOT
from repro2.commands.subcommand import SetupSubcommand
from repro2.common.docker import BuildDockerImageSubcommand, build_image
from repro2.models.kitaev2019 import DEFAULT_IMAGE, MODEL_NAME


@SetupSubcommand.register(MODEL_NAME)
class Kitaev2019SetupSubcommand(BuildDockerImageSubcommand):
    def __init__(self) -> None:
        super().__init__(f"{MODELS_ROOT}/{MODEL_NAME}", DEFAULT_IMAGE)

    @overrides
    def add_subparser(self, model: str, parser: argparse._SubParsersAction):
        description = f'Build a Docker image for model "{model}"'
        self.parser = parser.add_parser(
            model, description=description, help=description
        )
        self.parser.add_argument(
            "--image-name",
            default=DEFAULT_IMAGE,
            help="The name of the image to build",
        )
        self.parser.add_argument(
            "--models",
            nargs="+",
            default=["benepar_en3"],
            help="Indicates which Benepar models should be downloaded",
        )
        self.parser.add_argument(
            "--silent",
            action="store_true",
            help="Silences the output from the build command",
        )
        self.parser.set_defaults(subfunc=self.run)

    @overrides
    def run(self, args):
        build_args = {"MODELS": ",".join(args.models)}
        build_image(
            self.root, args.image_name, build_args=build_args, silent=args.silent
        )
