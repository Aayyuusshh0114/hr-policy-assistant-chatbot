import json
import sys

from sentence_transformers import SentenceTransformer


def main() -> None:
    request = json.loads(sys.stdin.read())
    model = SentenceTransformer(
        request["model_name"],
        local_files_only=request["local_files_only"],
        device=request["device"],
    )
    vectors = model.encode(
        request["texts"],
        batch_size=request["batch_size"],
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    json.dump(vectors.tolist(), sys.stdout)


if __name__ == "__main__":
    main()
