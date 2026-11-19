"""Verify Blue's Liquid routing without network access or third-party packages."""
import asyncio
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from core.config import blue_client_kwargs, get_blue_model, get_blue_provider
from core.openai_runtime import create_blue_pair


class BlueLiquidTests(unittest.TestCase):
    def test_blue_stays_on_liquid_with_red_and_legacy_overrides(self):
        with patch.dict(os.environ, {
            "LIQUID_API_KEY": " test-liquid-key ",
            "RED_TEAM_PROVIDER": "gemini",
            "OPENROUTER_API_KEY": "legacy-key",
            "OPENROUTER_BASE_URL": "https://example.invalid",
            "LIQUID_BASE_URL": "https://example.invalid",
            "BLUE_MODEL": "other-model",
        }):
            self.assertEqual(get_blue_provider(), "liquid")
            self.assertEqual(get_blue_model(), "lfm3-1.7b")
            self.assertEqual(blue_client_kwargs(), {
                "api_key": "test-liquid-key",
                "base_url": "https://api.liquid.ai/openai/v1",
            })

    def test_blue_sends_chat_completions_with_liquid_credentials(self):
        client = Mock()
        client.chat.completions.create.return_value = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="Hello!"))]
        )
        sdk = SimpleNamespace(OpenAI=Mock(return_value=client))
        with patch.dict(os.environ, {"LIQUID_API_KEY": "test-liquid-key"}):
            agent, runner = create_blue_pair(
                name="blue", app_name="blue", instruction="You are a helpful assistant."
            )
        with patch.dict(sys.modules, {"openai": sdk}):
            reply = asyncio.run(runner.chat(agent, "Hello!"))
        self.assertEqual(reply, "Hello!")
        sdk.OpenAI.assert_called_once_with(
            api_key="test-liquid-key", base_url="https://api.liquid.ai/openai/v1"
        )
        client.chat.completions.create.assert_called_once_with(
            model="lfm3-1.7b",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello!"},
            ],
            temperature=0.4,
        )


if __name__ == "__main__":
    unittest.main()
