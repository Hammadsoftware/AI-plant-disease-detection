import asyncio
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import torch
from PIL import Image
from torchvision import transforms

from app.schemas.diagnosis import Diagnosis, PredictionItem


# Exact evaluation preprocessing from the EfficientNetV2-S training notebook.
IMAGE_SIZE = 224
RESIZE_SIZE = 256
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)


class ModelLoadError(RuntimeError):
    pass


class ModelNotReadyError(RuntimeError):
    pass


class InferenceError(RuntimeError):
    pass


def humanize_class_name(class_name: str) -> str:
    if "___" in class_name:
        crop, condition = class_name.split("___", 1)
    else:
        crop, condition = "", class_name

    crop = " ".join(crop.replace("_", " ").split())
    condition = " ".join(condition.replace("_", " ").split())
    if crop and condition.casefold().startswith(f"{crop} ".casefold()):
        condition = condition[len(crop) :].strip()
    display = " ".join(part for part in (crop, condition) if part)
    return display.title()


class PlantDiseaseModel:
    """Loads and serves the immutable TorchScript classifier."""

    def __init__(
        self,
        model_path: Path,
        labels_path: Path,
        low_confidence_threshold: float,
        executor_workers: int = 1,
    ) -> None:
        self.model_path = model_path
        self.labels_path = labels_path
        self.low_confidence_threshold = low_confidence_threshold
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model: torch.jit.ScriptModule | None = None
        self.class_names: list[str] = []
        self.load_error: str | None = None
        self._load_lock = threading.Lock()
        self._inference_lock = threading.Lock()
        self._executor = ThreadPoolExecutor(
            max_workers=executor_workers,
            thread_name_prefix="plant-model",
        )
        self._preprocess = transforms.Compose(
            [
                transforms.Resize(RESIZE_SIZE),
                transforms.CenterCrop(IMAGE_SIZE),
                transforms.ToTensor(),
                transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
            ]
        )

    @property
    def loaded(self) -> bool:
        return self.model is not None

    def load(self) -> None:
        with self._load_lock:
            if self.loaded:
                return
            try:
                class_names = self._load_class_names(self.labels_path)
                if not self.model_path.is_file():
                    raise FileNotFoundError(f"Model checkpoint not found: {self.model_path}")
                model = torch.jit.load(str(self.model_path), map_location=self.device)
                model.eval()
                model.to(self.device)

                with torch.inference_mode():
                    sample_output = model(torch.zeros(1, 3, IMAGE_SIZE, IMAGE_SIZE, device=self.device))
                    sample_logits = self._extract_logits(sample_output)
                if sample_logits.ndim != 2 or sample_logits.shape[0] != 1:
                    raise ValueError(
                        f"Expected model output shape [batch, classes], received {tuple(sample_logits.shape)}"
                    )
                if sample_logits.shape[1] != len(class_names):
                    raise ValueError(
                        f"Model has {sample_logits.shape[1]} outputs but {len(class_names)} labels were configured"
                    )

                self.class_names = class_names
                self.model = model
                self.load_error = None
            except Exception as exc:
                self.model = None
                self.class_names = []
                self.load_error = str(exc)
                raise ModelLoadError("Unable to load the plant disease model.") from exc

    async def load_async(self) -> None:
        await self._await_worker(self._executor.submit(self.load))

    async def predict_async(self, image: Image.Image) -> Diagnosis:
        return await self._await_worker(self._executor.submit(self.predict, image))

    def close(self) -> None:
        self._executor.shutdown(wait=True, cancel_futures=True)

    @staticmethod
    async def _await_worker(future):
        # Polling avoids coupling native PyTorch completion to an event-loop callback.
        while not future.done():
            await asyncio.sleep(0.002)
        return future.result()

    def predict(self, image: Image.Image) -> Diagnosis:
        model = self.model
        if model is None:
            raise ModelNotReadyError("The plant disease model is not available.")

        try:
            input_tensor = self._preprocess(image).unsqueeze(0).to(self.device)
            with self._inference_lock, torch.inference_mode():
                logits = self._extract_logits(model(input_tensor))
                probabilities = torch.softmax(logits, dim=1)[0].detach().cpu()

            if probabilities.numel() != len(self.class_names):
                raise ValueError("The model output size changed after startup validation.")
            top_probabilities, top_indices = torch.topk(probabilities, k=min(3, len(self.class_names)))
            top_predictions = [
                PredictionItem(
                    class_name=self.class_names[int(index)],
                    disease=humanize_class_name(self.class_names[int(index)]),
                    confidence=float(probability),
                )
                for probability, index in zip(top_probabilities.tolist(), top_indices.tolist(), strict=True)
            ]
            best = top_predictions[0]
            return Diagnosis(
                class_name=best.class_name,
                disease=best.disease,
                confidence=best.confidence,
                is_uncertain=best.confidence < self.low_confidence_threshold,
                top_predictions=top_predictions,
                class_probabilities={
                    class_name: float(probabilities[index])
                    for index, class_name in enumerate(self.class_names)
                },
            )
        except ModelNotReadyError:
            raise
        except Exception as exc:
            raise InferenceError("Plant disease inference failed.") from exc

    @staticmethod
    def _load_class_names(labels_path: Path) -> list[str]:
        if not labels_path.is_file():
            raise FileNotFoundError(f"Class label file not found: {labels_path}")
        with labels_path.open("r", encoding="utf-8") as label_file:
            payload = json.load(label_file)

        if isinstance(payload, dict) and "classes" in payload:
            payload = payload["classes"]
        if not isinstance(payload, list) or not payload:
            raise ValueError("Class label file must contain a non-empty JSON list.")
        if not all(isinstance(item, str) and item.strip() for item in payload):
            raise ValueError("Every class label must be a non-empty string.")
        if len(set(payload)) != len(payload):
            raise ValueError("Class labels must be unique.")
        return payload

    @staticmethod
    def _extract_logits(output: Any) -> torch.Tensor:
        if isinstance(output, torch.Tensor):
            return output
        if isinstance(output, (tuple, list)) and output and isinstance(output[0], torch.Tensor):
            return output[0]
        if isinstance(output, dict):
            for key in ("logits", "output", "predictions"):
                if isinstance(output.get(key), torch.Tensor):
                    return output[key]
        raise TypeError("The model returned an unsupported output type.")
