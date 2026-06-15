"""CSRNet model definition and singleton model manager for serving.

This module defines the CSRNet (Congested Scene Recognition Network) architecture
and provides a thread-safe singleton ModelManager for loading and serving the
pretrained model. No training code is included — this is inference-only.

Architecture reference: https://arxiv.org/abs/1802.10062
"""

import collections
import logging
import threading
from typing import Optional

import torch
import torch.nn as nn
from torchvision import models

logger = logging.getLogger(__name__)


def make_layers(
    cfg: list,
    in_channels: int = 3,
    batch_norm: bool = False,
    dilation: bool = False,
) -> nn.Sequential:
    """Build sequential convolutional layers from a configuration list.

    Args:
        cfg: Layer configuration. Integers specify output channels for Conv2d
            layers; the string ``'M'`` inserts a 2×2 max-pooling layer.
        in_channels: Number of input channels for the first convolution.
        batch_norm: If ``True``, append BatchNorm2d + ReLU after each Conv2d;
            otherwise append only ReLU.
        dilation: If ``True``, use dilation rate 2 for all Conv2d layers
            (used in the CSRNet backend to enlarge the receptive field).

    Returns:
        An ``nn.Sequential`` container with the constructed layers.
    """
    d_rate: int = 2 if dilation else 1
    layers: list[nn.Module] = []

    for v in cfg:
        if v == "M":
            layers.append(nn.MaxPool2d(kernel_size=2, stride=2))
        else:
            conv2d = nn.Conv2d(
                in_channels, v, kernel_size=3, padding=d_rate, dilation=d_rate
            )
            if batch_norm:
                layers += [conv2d, nn.BatchNorm2d(v), nn.ReLU(inplace=True)]
            else:
                layers += [conv2d, nn.ReLU(inplace=True)]
            in_channels = v

    return nn.Sequential(*layers)


class CSRNet(nn.Module):
    """CSRNet — Congested Scene Recognition Network.

    Uses a VGG-16 front-end (first 10 conv layers up to pool3) combined with
    a dilated-convolution back-end to produce a density map whose integral
    approximates the crowd count.

    Args:
        load_weights: If ``True``, skip VGG-16 weight initialisation (used when
            loading a fully pretrained checkpoint). If ``False`` (default), copy
            VGG-16 ImageNet weights into the front-end and randomly initialise
            the back-end.
    """

    def __init__(self, load_weights: bool = False) -> None:
        super().__init__()

        self.seen: int = 0
        self.frontend_feat: list = [64, 64, "M", 128, 128, "M", 256, 256, 256, "M", 512, 512, 512]
        self.backend_feat: list = [512, 512, 512, 256, 128, 64]

        self.frontend: nn.Sequential = make_layers(self.frontend_feat)
        self.backend: nn.Sequential = make_layers(
            self.backend_feat, in_channels=512, dilation=True
        )
        self.output_layer: nn.Conv2d = nn.Conv2d(64, 1, kernel_size=1)

        if not load_weights:
            # Initialise back-end weights randomly …
            self._initialize_weights()
            # … then copy VGG-16 ImageNet weights into the front-end.
            mod = models.vgg16(weights=models.VGG16_Weights.DEFAULT)
            fsd: collections.OrderedDict = collections.OrderedDict()
            frontend_items = list(self.frontend.state_dict().items())
            vgg_items = list(mod.state_dict().items())
            for i in range(len(frontend_items)):
                temp_key = frontend_items[i][0]
                fsd[temp_key] = vgg_items[i][1]
            self.frontend.load_state_dict(fsd)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Run a forward pass through the network.

        Args:
            x: Input image tensor of shape ``(B, 3, H, W)``.

        Returns:
            Predicted density map of shape ``(B, 1, H', W')``.
        """
        x = self.frontend(x)
        x = self.backend(x)
        x = self.output_layer(x)
        return x

    def _initialize_weights(self) -> None:
        """Initialise Conv2d and BatchNorm2d weights with sensible defaults."""
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.normal_(m.weight, std=0.01)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)


class ModelManager:
    """Thread-safe singleton that manages the lifecycle of a CSRNet model.

    Usage::

        manager = ModelManager()
        manager.load_model("path/to/csrnet_final.pth")
        manager.warmup()
        model = manager.get_model()

    The singleton pattern ensures exactly one model instance is held in memory
    across all Flask request threads / workers.
    """

    _instance: Optional["ModelManager"] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> "ModelManager":
        """Return the single ``ModelManager`` instance (create on first call)."""
        if cls._instance is None:
            with cls._lock:
                # Double-checked locking
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance.model: Optional[CSRNet] = None  # type: ignore[annotation-unchecked]
                    instance.device: Optional[torch.device] = None  # type: ignore[annotation-unchecked]
                    instance.is_loaded: bool = False  # type: ignore[annotation-unchecked]
                    cls._instance = instance
        return cls._instance

    def load_model(self, model_path: str) -> None:
        """Load a pretrained CSRNet checkpoint from *model_path*.

        The method auto-detects whether a CUDA GPU is available and places the
        model on the appropriate device.  The model is set to ``eval()`` mode
        immediately — no training should ever happen through this manager.

        Args:
            model_path: Filesystem path to a ``.pth`` checkpoint file.

        Raises:
            FileNotFoundError: If *model_path* does not exist.
            RuntimeError: If the checkpoint cannot be loaded (corrupt file, etc.).
        """
        import os

        if not os.path.isfile(model_path):
            raise FileNotFoundError(
                f"Model checkpoint not found at: {model_path}"
            )

        # Determine the best available device.
        if torch.cuda.is_available():
            self.device = torch.device("cuda")
            logger.info("CUDA GPU detected — using GPU for inference.")
        else:
            self.device = torch.device("cpu")
            logger.info("No CUDA GPU detected — using CPU for inference.")

        try:
            # load_weights=True skips VGG-16 ImageNet init because we are
            # loading a fully-trained checkpoint.
            self.model = CSRNet(load_weights=True)

            checkpoint = torch.load(
                model_path,
                map_location=self.device,
                weights_only=False,
            )

            # Handle both raw state_dict and wrapped checkpoint formats.
            if isinstance(checkpoint, dict) and "state_dict" in checkpoint:
                state_dict = checkpoint["state_dict"]
            else:
                state_dict = checkpoint

            self.model.load_state_dict(state_dict)
            self.model.to(self.device)
            self.model.eval()
            self.is_loaded = True

            param_count = sum(p.numel() for p in self.model.parameters())
            logger.info(
                "Model loaded successfully from '%s' on %s "
                "(%s parameters).",
                model_path,
                self.device,
                f"{param_count:,}",
            )

        except Exception as exc:
            self.model = None
            self.is_loaded = False
            logger.exception("Failed to load model from '%s'.", model_path)
            raise RuntimeError(
                f"Failed to load model from '{model_path}': {exc}"
            ) from exc

    def get_model(self) -> CSRNet:
        """Return the loaded CSRNet model.

        Returns:
            The ``CSRNet`` model instance in eval mode.

        Raises:
            RuntimeError: If no model has been loaded yet.
        """
        if not self.is_loaded or self.model is None:
            raise RuntimeError(
                "Model has not been loaded. Call load_model() first."
            )
        return self.model

    def get_device(self) -> torch.device:
        """Return the ``torch.device`` the model resides on.

        Returns:
            ``torch.device('cuda')`` or ``torch.device('cpu')``.

        Raises:
            RuntimeError: If no model has been loaded yet.
        """
        if self.device is None:
            raise RuntimeError(
                "Device not set. Call load_model() first."
            )
        return self.device

    def warmup(self) -> None:
        """Run a single dummy inference to warm up CUDA/CPU caches.

        This avoids a latency spike on the first real request.  The method is
        a no-op if the model is not loaded.
        """
        if not self.is_loaded or self.model is None:
            logger.warning("warmup() called but no model is loaded — skipping.")
            return

        try:
            dummy_input = torch.randn(1, 3, 224, 224, device=self.device)
            with torch.no_grad():
                _ = self.model(dummy_input)
            logger.info("Model warmup complete on %s.", self.device)
        except Exception:
            logger.exception("Warmup inference failed — model may still work.")

    def unload_model(self) -> None:
        """Unload the model and free associated memory.

        After calling this method, ``get_model()`` will raise until
        ``load_model()`` is called again.
        """
        if self.model is not None:
            del self.model
            self.model = None

        self.is_loaded = False
        self.device = None

        # Attempt to reclaim GPU memory if CUDA was in use.
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        logger.info("Model unloaded and memory released.")
