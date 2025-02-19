import zipfile
import os
import asyncio
from pathlib import Path

from app.utils.misc import modify_zip


async def test_modify_zip():
    temp_dir = Path("./tests/demo")
    input_zip = temp_dir / "input.zip"
    output_zip = temp_dir / "output.zip"

    await modify_zip(input_zip, output_zip)

asyncio.run(test_modify_zip())