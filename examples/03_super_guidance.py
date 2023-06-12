import random
import re
from enum import Enum
from itertools import accumulate
from operator import itemgetter
from typing import Generator, Iterable

from guidance import Program, llms
from pydantic import BaseModel


def empty_get(d: dict, key: str) -> str:
    """
    Returns the value of a key in a dictionary, or an empty string if the key is not present.

    Args:
        d: The dictionary to get the value from.
        key: The key to get the value for.

    Returns:
        The value of the key in the dictionary, or an empty string if the key is not present.
    """
    return d.get(key, "")


def parse_int(options):
    """Parse the best integer from a list of options."""
    for option in options:
        try:
            # remove any non numeric characters
            return int(re.sub("[^0-9]", "", option))
        except ValueError:
            pass
    return 0


def jsonformer2guidance(schema, key=None, indent=0, refs=None):
    if refs is None and schema.get("definitions"):
        refs = schema["definitions"]

    out = ""
    if schema["type"] == "object":
        out += "  " * indent + "{\n"
        num_items = len(schema["properties"])
        for i, (k, v) in enumerate(schema["properties"].items()):
            if v.get("$ref"):
                v = refs[v["$ref"].split("/")[-1]]
                v["type"] = "string"
            out += (
                "  " * (indent + 1)
                + '"'
                + k
                + '"'
                + ": "
                + jsonformer2guidance(v, k, indent + 1, refs)
                + (",\n" if i < num_items - 1 else "\n")
            )
        out += "  " * indent + "}"
        return out
    elif schema["type"] == "array":
        if "max_items" in schema:
            extra_args = f" max_iterations={schema['max_items']}"
        else:
            extra_args = ""
        return (
            "[{{#geneach '"
            + key
            + "' stop=']'"
            + extra_args
            + "}}{{#unless @first}}, {{/unless}}"
            + jsonformer2guidance(schema["items"], "this", refs)
            + "{{/geneach}}]"
        )
    elif schema["type"] == "string":
        if hasattr(schema, "enum"):
            s = "{{#select '" + key + "'}}"
            for e in schema["enum"]:
                s += e + "{{or}}"
            s += "{{/select}}"
            return s
        return "\"{{gen '" + key + "' stop='\"'}}\""
    elif schema["type"] == "number":
        return "{{gen '" + key + "' max_tokens=1}}"
    elif schema["type"] == "boolean":
        return "{{#select '" + key + "'}}True{{or}}False{{/select}}"
    elif schema["type"] == "integer":
        return "{{parse_int (gen '" + key + "' max_tokens=1 n=5)}}"


class StrengthEnum(Enum):
    high = "high"
    medium = "medium"
    low = "low"


class InGameItem(BaseModel):
    name: str
    cost: int
    description: str
    enchantments: list[str]
    strength: StrengthEnum


def generate_item(general_description: str) -> InGameItem:
    """
    Generates a story for a given name.

    Args:
        name: The name of the person in the story.

    Yields:
        A stream of story content from the llm.
    """

    json_schema = InGameItem.schema()

    base_template = f"""
    # Goal
    
    You are an AI game developer. Your goal is to generate a video game item information for "{general_description}".
    
    Please generate the appropriate json for this item based on the following schema:
    
    ```jsonschema
    {json_schema}
    ```
    
    Please ensure that all the fields are not null and are of the correct type. Ensure the values are
    true to the description of the item.
    
    # Output
    
    ```json
    {jsonformer2guidance(json_schema)}
    ``` 
    """

    # define a guidance program that adapts a proverb
    program_result: Program = Program(
        base_template, llm=llms.OpenAI("text-davinci-003"), caching=False, silent=True
    )(parse_int=parse_int)

    match = re.search("```json\n(.*?)```", program_result.text, re.DOTALL)
    if not match:
        raise ValueError("Could not find json output")
    return InGameItem.parse_raw(match.group(1))


item = generate_item("Harry Potter's wand")
print(item)
