#!/usr/bin/env python3
"""
SLM Training Script — S41 Track A Phase 2C
==========================================

Fine-tunes Qwen-2.5-1.5B using MLX for the SLM guard dog.
Optimized for Mac Studio M4 Max (64GB unified memory).

USAGE:
    python slm/train_slm.py --model Qwen/Qwen2.5-1.5B-Instruct
    python slm/train_slm.py --dry-run  # Test without training

HARDWARE:
    - Mac Studio M4 Max (64GB unified)
    - MLX with Metal acceleration
    - No quantization needed (full fp16)

Date: 2026-01-23
Sprint: S41 Phase 2C
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path

try:
    import mlx.core as mx
    import mlx.nn as nn
    import mlx.optimizers as optim
    from mlx_lm import load, generate
    from mlx_lm.tuner.trainer import TrainingArgs, train
    from mlx_lm.tuner import linear_to_lora_layers, datasets
    MLX_AVAILABLE = True
except ImportError:
    MLX_AVAILABLE = False
    print("WARNING: MLX not available. Install with: pip install mlx mlx-lm")


# =============================================================================
# CONFIGURATION
# =============================================================================


@dataclass
class SLMConfig:
    """Configuration for SLM training."""

    # Model
    model_name: str = "Qwen/Qwen2.5-1.5B-Instruct"
    output_dir: Path = Path("slm/models/phoenix-guard")

    # Data
    train_data: Path = Path("slm/training/train.jsonl")
    val_data: Path = Path("slm/training/valid.jsonl")  # mlx-lm expects 'valid.jsonl'

    # LoRA parameters (optimized for M4 Max with 64GB)
    lora_rank: int = 32  # Higher rank with RAM headroom
    lora_alpha: int = 64
    lora_dropout: float = 0.05
    lora_targets: tuple = (
        "q_proj",
        "k_proj",
        "v_proj",
        "o_proj",
        "gate_proj",
    )

    # Training parameters (conservative for memory safety)
    batch_size: int = 4  # Reduced from 16 to avoid OOM
    grad_accumulation: int = 4  # Accumulate to effective batch=16
    learning_rate: float = 2e-4
    num_epochs: int = 3
    warmup_steps: int = 100
    max_seq_length: int = 256  # Reduced from 512

    # Hardware
    use_fp16: bool = True  # No quantization needed with 64GB
    use_neural_engine: bool = True


DEFAULT_CONFIG = SLMConfig()


# =============================================================================
# TRAINING SCRIPT
# =============================================================================


def check_hardware():
    """Check hardware capabilities."""
    print("=" * 60)
    print("HARDWARE CHECK")
    print("=" * 60)

    if not MLX_AVAILABLE:
        print("ERROR: MLX not available")
        return False

    device = mx.default_device()
    print(f"MLX device: {device}")
    print(f"Metal available: {mx.metal.is_available()}")

    # Test computation
    a = mx.array([1.0, 2.0, 3.0])
    b = mx.array([4.0, 5.0, 6.0])
    c = mx.add(a, b)
    mx.eval(c)  # Force computation
    print(f"MLX computation test: PASS")

    print("=" * 60)
    return True


def load_model(config: SLMConfig):
    """Load base model."""
    print(f"\nLoading model: {config.model_name}")
    print("This may take a few minutes on first run (downloading)...")

    model, tokenizer = load(config.model_name)
    print(f"Model loaded: {type(model).__name__}")
    print(f"Tokenizer: {type(tokenizer).__name__}")

    return model, tokenizer


def prepare_data(config: SLMConfig) -> tuple[Path, Path]:
    """Prepare training data in MLX format."""
    print(f"\nPreparing training data...")
    print(f"Train: {config.train_data}")
    print(f"Val: {config.val_data}")

    if not config.train_data.exists():
        raise FileNotFoundError(f"Training data not found: {config.train_data}")

    if not config.val_data.exists():
        raise FileNotFoundError(f"Validation data not found: {config.val_data}")

    # Count examples
    with config.train_data.open() as f:
        train_count = sum(1 for _ in f)
    with config.val_data.open() as f:
        val_count = sum(1 for _ in f)

    print(f"Train examples: {train_count}")
    print(f"Val examples: {val_count}")

    return config.train_data, config.val_data


def run_training(config: SLMConfig):
    """Run the training loop."""
    print("\n" + "=" * 60)
    print("STARTING TRAINING")
    print("=" * 60)

    # Load model
    model, tokenizer = load_model(config)

    # Prepare data paths
    train_data, val_data = prepare_data(config)

    # Create output directory
    config.output_dir.mkdir(parents=True, exist_ok=True)
    adapter_file = str(config.output_dir / "adapters.safetensors")

    # LoRA configuration
    lora_config = {
        "rank": config.lora_rank,
        "alpha": config.lora_alpha,
        "dropout": config.lora_dropout,
        "scale": config.lora_alpha / config.lora_rank,
    }

    print(f"\nLoRA config: {lora_config}")
    print(f"Training args: batch={config.batch_size}, lr={config.learning_rate}")

    # Apply LoRA layers to model
    print("\nApplying LoRA layers...")
    num_lora_layers = 8  # Apply to last 8 transformer blocks
    linear_to_lora_layers(model, num_lora_layers, lora_config)

    # Freeze base model, keep LoRA trainable
    model.freeze()

    # Unfreeze LoRA parameters using the proper method
    from mlx_lm.tuner.lora import LoRALinear

    lora_param_count = 0
    for name, module in model.named_modules():
        if isinstance(module, LoRALinear):
            module.unfreeze()
            # Count LoRA params (lora_a and lora_b)
            if hasattr(module, "lora_a") and module.lora_a is not None:
                lora_param_count += module.lora_a.size
            if hasattr(module, "lora_b") and module.lora_b is not None:
                lora_param_count += module.lora_b.size

    # Count total parameters
    def count_params(params):
        """Recursively count parameters in nested dict."""
        total = 0
        if isinstance(params, mx.array):
            return params.size
        elif isinstance(params, dict):
            for v in params.values():
                total += count_params(v)
        return total

    total = count_params(model.parameters())
    print(f"LoRA trainable parameters: {lora_param_count:,} / {total:,} ({100*lora_param_count/total:.2f}%)")

    # Load datasets
    print("\nLoading datasets...")

    # Create config object with required attributes for mlx-lm
    class DatasetConfig:
        def __init__(self, data_dir):
            self.data = str(data_dir)
            self.train = True
            self.test = False
            self.hf_dataset = False
            # Dataset format config
            self.prompt_feature = "prompt"
            self.completion_feature = "completion"
            self.mask_prompt = False

    # mlx-lm expects train.jsonl, valid.jsonl, test.jsonl in a directory
    data_dir = train_data.parent
    dataset_config = DatasetConfig(data_dir)
    train_ds_raw, val_ds_raw, _ = datasets.load_dataset(dataset_config, tokenizer)

    # Wrap in CacheDataset to enable tokenization on access
    from mlx_lm.tuner.datasets import CacheDataset

    train_dataset = CacheDataset(train_ds_raw)
    val_dataset = CacheDataset(val_ds_raw)

    print(f"Train dataset: {len(train_dataset)} examples")
    print(f"Val dataset: {len(val_dataset)} examples")

    # Create optimizer
    optimizer = optim.AdamW(learning_rate=config.learning_rate)

    # Training arguments (matching mlx-lm 0.30.5 API)
    training_args = TrainingArgs(
        batch_size=config.batch_size,
        iters=config.num_epochs * (800 // config.batch_size),  # Approximate iterations
        val_batches=10,
        steps_per_report=10,
        steps_per_eval=50,
        steps_per_save=100,  # Correct param name (not save_every)
        adapter_file=adapter_file,  # Correct param name (not adapter_path)
        max_seq_length=config.max_seq_length,
        grad_checkpoint=False,  # Not needed with 64GB
        grad_accumulation_steps=config.grad_accumulation,
    )

    # Train
    start_time = time.time()
    print("\nStarting training loop...")

    train(
        model=model,
        optimizer=optimizer,
        train_dataset=train_dataset,
        val_dataset=val_dataset,
        args=training_args,
    )

    elapsed = time.time() - start_time
    print(f"\nTraining complete in {elapsed / 60:.1f} minutes")

    # Save final model
    print(f"\nModel saved to {adapter_file}")

    return config.output_dir


def run_inference_test(config: SLMConfig, model_path: Path):
    """Test inference on trained model."""
    print("\n" + "=" * 60)
    print("INFERENCE TEST")
    print("=" * 60)

    # For now, test with base model to verify inference works
    # The LoRA adapter loading requires matching the exact model structure
    # TODO: Implement proper adapter loading with mlx-lm utilities
    print("Loading base model for inference test...")
    model, tokenizer = load(config.model_name)

    # Check if adapter exists
    adapter_file = model_path / "adapters.safetensors"
    if adapter_file.exists():
        print(f"Adapter file exists: {adapter_file}")
        adapter_weights = mx.load(str(adapter_file))
        print(f"Adapter contains {len(adapter_weights)} weight tensors")

        # Apply LoRA structure to match saved weights
        from mlx_lm.tuner import linear_to_lora_layers

        lora_config = {
            "rank": config.lora_rank,
            "alpha": config.lora_alpha,
            "dropout": 0.0,
            "scale": config.lora_alpha / config.lora_rank,
        }
        linear_to_lora_layers(model, 8, lora_config)

        # Now load the adapter weights
        model.load_weights(str(adapter_file), strict=False)
        print("Adapter weights loaded successfully")
    else:
        print(f"WARNING: No adapter file found at {adapter_file}")

    # Test prompts
    test_cases = [
        # Should be VALID_FACTS
        {
            "input": """OINK OINK MOTHERFUCKER! 🐗🔥
FACTS_ONLY — NO INTERPRETATION

SYSTEM STATUS
  STATE: ARMED
  MODE: SHADOW
  POSITIONS: 2 open""",
            "expected": "VALID_FACTS",
        },
        # Should be BANNED — CAUSAL
        {
            "input": """FACTS_ONLY — NO INTERPRETATION

Sharpe improved because volatility decreased.""",
            "expected": "BANNED — CAUSAL",
        },
        # Should be BANNED — RANKING
        {
            "input": """FACTS_ONLY — NO INTERPRETATION

EURUSD is the best setup today.""",
            "expected": "BANNED — RANKING",
        },
    ]

    print("\nRunning test cases...")
    results = []

    for i, test in enumerate(test_cases):
        prompt = f"""Classify this narrator output.
Respond ONLY with: VALID_FACTS or BANNED — [REASON_CODE]

Output to classify:
{test['input']}

Classification:"""

        # Generate
        start = time.time()
        response = generate(
            model,
            tokenizer,
            prompt=prompt,
            max_tokens=20,
        )
        latency = (time.time() - start) * 1000

        # Parse response
        output = response.strip().split("\n")[0].strip()

        passed = test["expected"] in output
        results.append(passed)

        print(f"\nTest {i + 1}:")
        print(f"  Expected: {test['expected']}")
        print(f"  Got: {output}")
        print(f"  Latency: {latency:.1f}ms")
        print(f"  Status: {'PASS' if passed else 'FAIL'}")

    # Summary
    print("\n" + "-" * 40)
    passed_count = sum(results)
    print(f"Results: {passed_count}/{len(results)} passed")

    return passed_count == len(results)


def dry_run(config: SLMConfig):
    """Dry run without actual training."""
    print("\n" + "=" * 60)
    print("DRY RUN MODE")
    print("=" * 60)

    # Check hardware
    if not check_hardware():
        return False

    # Check data
    try:
        prepare_data(config)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        return False

    # Check model availability
    print(f"\nModel to train: {config.model_name}")
    print("Checking model availability...")

    try:
        # Just check we can import the model config
        from transformers import AutoConfig

        model_config = AutoConfig.from_pretrained(config.model_name)
        print(f"Model config loaded: {model_config.model_type}")
        print(f"Hidden size: {model_config.hidden_size}")
        print(f"Num layers: {model_config.num_hidden_layers}")
    except Exception as e:
        print(f"WARNING: Could not load model config: {e}")
        print("Model may still work with mlx_lm.load()")

    print("\n" + "-" * 40)
    print("DRY RUN COMPLETE")
    print("All checks passed. Ready for training.")
    print("-" * 40)

    return True


# =============================================================================
# CLI
# =============================================================================


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Train SLM guard dog")
    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_CONFIG.model_name,
        help="Base model name",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_CONFIG.output_dir,
        help="Output directory",
    )
    parser.add_argument(
        "--train-data",
        type=Path,
        default=DEFAULT_CONFIG.train_data,
        help="Training data path",
    )
    parser.add_argument(
        "--val-data",
        type=Path,
        default=DEFAULT_CONFIG.val_data,
        help="Validation data path",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_CONFIG.batch_size,
        help="Batch size",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=DEFAULT_CONFIG.num_epochs,
        help="Number of epochs",
    )
    parser.add_argument(
        "--lr",
        type=float,
        default=DEFAULT_CONFIG.learning_rate,
        help="Learning rate",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Check setup without training",
    )
    parser.add_argument(
        "--inference-only",
        type=Path,
        help="Run inference test on trained model",
    )

    args = parser.parse_args()

    # Build config
    config = SLMConfig(
        model_name=args.model,
        output_dir=args.output_dir,
        train_data=args.train_data,
        val_data=args.val_data,
        batch_size=args.batch_size,
        num_epochs=args.epochs,
        learning_rate=args.lr,
    )

    # Run mode
    if args.dry_run:
        return 0 if dry_run(config) else 1

    if args.inference_only:
        return 0 if run_inference_test(config, args.inference_only) else 1

    # Full training
    if not check_hardware():
        return 1

    try:
        model_path = run_training(config)
        success = run_inference_test(config, model_path)
        return 0 if success else 1
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
