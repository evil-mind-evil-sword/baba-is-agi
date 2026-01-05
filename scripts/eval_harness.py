#!/usr/bin/env python3
"""
Agent-agnostic JSON evaluation harness for Baba Is You.

This script provides a stdin/stdout JSON protocol that allows any external
agent (regardless of language/framework) to interact with Baba Is You
environments for evaluation.

Protocol:
    Send JSON commands to stdin (one per line), receive JSON responses on stdout.

Commands:
    {"cmd": "list_envs"}
        -> {"status": "ok", "envs": ["simple", "wall_maze", ...]}

    {"cmd": "reset", "env": "simple"}
        -> {"status": "ok", "observation": {...}}

    {"cmd": "step", "action": "up"|"down"|"left"|"right"|"wait"}
        -> {"status": "ok", "observation": {...}, "reward": 0.0, "done": false, "info": {...}}

    {"cmd": "info"}
        -> {"status": "ok", "env": "simple", "observation": {...}}

    {"cmd": "quit"}
        -> {"status": "ok", "message": "goodbye"}

Observation format (see Grid.to_dict()):
    {
        "dimensions": {"width": 10, "height": 10},
        "objects": [{"name": "baba", "type_id": 1, "x": 2, "y": 5, "is_text": false}, ...],
        "rules": ["BABA IS YOU", "FLAG IS WIN"],
        "properties": {"BABA": ["YOU"], "FLAG": ["WIN"]},
        "transformations": {},
        "state": {"won": false, "lost": false, "steps": 0}
    }

Example usage:
    # Start the harness
    python scripts/eval_harness.py

    # Send commands (from another process or manually)
    {"cmd": "reset", "env": "simple"}
    {"cmd": "step", "action": "right"}
    {"cmd": "step", "action": "right"}
    ...
"""

import json
import sys

from baba.envs import ENVIRONMENTS, create_environment


class EvalHarness:
    """JSON-based evaluation harness for Baba Is You."""

    def __init__(self):
        self.env = None
        self.env_name = None

    def handle_command(self, cmd_data: dict) -> dict:
        """Handle a single command and return response."""
        cmd = cmd_data.get("cmd", "")

        if cmd == "list_envs":
            # Include difficulty ratings for each environment
            envs_with_difficulty = {}
            for name, env_class in ENVIRONMENTS.items():
                envs_with_difficulty[name] = {
                    "difficulty": getattr(env_class, "difficulty", 1),
                }
            return {
                "status": "ok",
                "envs": envs_with_difficulty,
            }

        elif cmd == "reset":
            env_name = cmd_data.get("env", "simple")
            if env_name not in ENVIRONMENTS:
                return {
                    "status": "error",
                    "message": f"Unknown environment: {env_name}. Use 'list_envs' to see available environments.",
                }
            self.env = create_environment(env_name)
            self.env_name = env_name
            self.env.reset()
            return {
                "status": "ok",
                "env": env_name,
                "observation": self.env.to_dict(),
            }

        elif cmd == "step":
            if self.env is None:
                return {
                    "status": "error",
                    "message": "No environment loaded. Use 'reset' first.",
                }
            action = cmd_data.get("action", "wait")
            valid_actions = ["up", "down", "left", "right", "wait"]
            if action not in valid_actions:
                return {
                    "status": "error",
                    "message": f"Invalid action: {action}. Valid actions: {valid_actions}",
                }
            obs, reward, done, info = self.env.step(action)
            return {
                "status": "ok",
                "observation": self.env.to_dict(),
                "reward": reward,
                "done": done,
                "info": info,
            }

        elif cmd == "info":
            if self.env is None:
                return {
                    "status": "error",
                    "message": "No environment loaded. Use 'reset' first.",
                }
            return {
                "status": "ok",
                "env": self.env_name,
                "observation": self.env.to_dict(),
            }

        elif cmd == "quit":
            return {"status": "ok", "message": "goodbye"}

        else:
            return {
                "status": "error",
                "message": f"Unknown command: {cmd}. Valid commands: list_envs, reset, step, info, quit",
            }

    def run(self):
        """Main loop: read JSON from stdin, write JSON to stdout."""
        # Ensure stdout is line-buffered for real-time communication
        sys.stdout.reconfigure(line_buffering=True)

        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue

            try:
                cmd_data = json.loads(line)
            except json.JSONDecodeError as e:
                response = {"status": "error", "message": f"Invalid JSON: {e}"}
                print(json.dumps(response), flush=True)
                continue

            response = self.handle_command(cmd_data)
            print(json.dumps(response), flush=True)

            # Exit on quit command
            if cmd_data.get("cmd") == "quit":
                break


def main():
    """Entry point."""
    harness = EvalHarness()
    harness.run()


if __name__ == "__main__":
    main()
