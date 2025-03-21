import json
import logging
import os
from typing import Dict, List, Union

from overrides import overrides

from repro2.common import TemporaryDirectory
from repro2.common.docker import make_volume_map, run_command
from repro2.common.io import write_to_text_file
from repro2.models import Model, SingleDocumentSummarizationModel
from repro2.models.model import DocumentType, SummaryType
from repro2.models.lewis2020 import DEFAULT_IMAGE, MODEL_NAME

logger = logging.getLogger(__name__)


@Model.register(f"{MODEL_NAME}-bart")
class BART(SingleDocumentSummarizationModel):
    """
    A wrapper around the BART model from `Lewis et al. (2020) <https://arxiv.org/abs/1910.13461>`.
    Currently, only the models trained on the CNN/DailyMail and XSum datasets are supported.
    """

    def __init__(
        self,
        model: str = "bart.large.cnn",
        batch_size: int = None,
        image: str = DEFAULT_IMAGE,
        nbest: int = 1,
        beam_size: int = None,
        device: int = 0,
    ) -> None:
        """
        Parameters
        ----------
        model : str, default="bart.large.cnn"
            The name of the pretrained model, either "bart.large.cnn" or "bart.large.xsum"
        batch_size : int, default=None
            The batch size for prediction. If `None`, defaults to the BART code's default.
        image : str, default="lewis2020"
            The name of the Docker image to run prediction in
        nbest : int, default=1
            The number of outputs to return
        beam_size : int, default=None
            The inference beam size, defaults to the BART code's default.
        device : int, default=0
            The ID of the GPU to use, -1 if CPU
        """
        if model not in ["bart.large.cnn", "bart.large.xsum"]:
            raise Exception(f"Unknown pretrained model: {model}")
        self.model = model
        self.batch_size = batch_size
        self.image = image
        self.nbest = nbest
        self.beam_size = beam_size
        self.device = device

    @overrides
    def predict_batch(
        self, inputs: list[Dict[str, DocumentType]], *args, **kwargs
    ) -> list[SummaryType] | list[list[SummaryType]]:
        documents = [inp["document"] for inp in inputs]
        logger.info(f"Predicting summaries for {len(documents)} documents with Docker image {self.image}")

        with TemporaryDirectory() as temp:
            input_dir = f"{temp}/input"
            output_dir = f"{temp}/output"
            volume_map = make_volume_map(input_dir, output_dir)

            host_input_file = f"{input_dir}/documents.txt"
            container_input_file = f"{volume_map[input_dir]}/documents.txt"
            write_to_text_file(documents, host_input_file)

            # Run inference. The output_dir must exist before running
            # the docker command
            os.makedirs(output_dir)
            host_output_file = f"{output_dir}/summaries.txt"
            container_output_file = f"{volume_map[output_dir]}/summaries.txt"
            command = (
                f"cd fairseq && "
                f"CUDA_VISIBLE_DEVICES={self.device} "
                f"python examples/bart/summarize.py"
                f"  --model-dir ../{self.model}"
                f"  --model-file model.pt"
                f"  --src {container_input_file}"
                f"  --out {container_output_file}"
                f"  --nbest {self.nbest}"
            )

            if self.batch_size is not None:
                command += f" --bsz {self.batch_size}"

            if self.model == "bart.large.xsum":
                command += " --xsum-kwargs"

            if self.beam_size is not None:
                command += f" --beam-size {self.beam_size}"

            cuda = self.device != -1
            run_command(self.image, command, volume_map=volume_map, cuda=cuda)

            # Load the output summaries
            summaries = []
            with open(host_output_file, "r") as f:
                for line in f:
                    data = json.loads(line)
                    if len(data) == 1:
                        summaries.append(data[0])
                    else:
                        summaries.append(data)
            return summaries
