from overrides import overrides
from typing import List

from repro2.common.io import read_jsonl_file
from repro2.data.dataset_readers import DatasetReader
from repro2.data.types import InstanceDict
from repro2.models.chen2020 import MODEL_NAME


@DatasetReader.register(f"{MODEL_NAME}-eval")
class Chen2020EvaluationDatasetReader(DatasetReader):
    @overrides
    def _read(self, *input_files: str) -> List[InstanceDict]:
        instances = []
        for input_file in input_files:
            predictions = read_jsonl_file(input_file)
            for prediction in predictions:
                instances.append(
                    {
                        "dataset": prediction["input"]["constituent_dataset"],
                        "source": prediction["input"]["metadata"]["source"],
                        "score": prediction["input"]["score"],
                        "prediction": prediction["prediction"],
                    }
                )
        return instances
