from pathlib import Path


def load_prompt(name:str):
    prompt_file=Path(__file__).parents[2] / "prompts"/f"{name}.prompt"

    return prompt_file.read_text(encoding="utf-8")

