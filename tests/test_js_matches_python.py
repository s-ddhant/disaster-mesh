"""The phone (JavaScript) and the gateway (Python) must produce identical bytes.

Runs phone/frame.js under Node.js; skipped if Node is not installed.
"""

import json
import random
import shutil
import subprocess
from pathlib import Path

import pytest

from protocol.frame import encode
from tests.test_frame import random_message

NODE = shutil.which("node")
FRAME_JS = Path(__file__).resolve().parent.parent / "phone" / "frame.js"


@pytest.mark.skipif(NODE is None, reason="Node.js not installed")
def test_js_encoder_matches_python_on_500_messages():
    rng = random.Random(11)
    messages = [random_message(rng) for _ in range(500)]
    script = (
        f"const {{ encodeFrame }} = require({json.dumps(str(FRAME_JS))});"
        "const msgs = JSON.parse(require('fs').readFileSync(0, 'utf8'));"
        "console.log(JSON.stringify(msgs.map(m => Buffer.from(encodeFrame(m)).toString('hex'))));"
    )
    out = subprocess.run([NODE, "-e", script], input=json.dumps(messages),
                         capture_output=True, text=True, check=True)
    js_frames = json.loads(out.stdout)
    for msg, js_hex in zip(messages, js_frames):
        assert js_hex == encode(msg).hex(), msg
