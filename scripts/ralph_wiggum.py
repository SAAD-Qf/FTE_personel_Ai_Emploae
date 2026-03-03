"""
Ralph Wiggum Loop Plugin

Implements the "Ralph Wiggum" pattern for autonomous task completion.
This Stop hook intercepts Claude's exit and feeds the prompt back until
the task is complete.

Architecture:
1. Orchestrator creates state file with prompt
2. Claude works on task
3. Claude tries to exit
4. Stop hook checks: Is task file in /Done?
5. YES → Allow exit (complete)
6. NO → Block exit, re-inject prompt (loop continues)

Reference: https://github.com/anthropics/claude-code/tree/main/.claude/plugins/ralph-wiggum

Usage:
    python ralph_wiggum.py --vault-path ./AI_Employee_Vault start "Process all pending items"
    python ralph_wiggum.py --vault-path ./AI_Employee_Vault status
    python ralph_wiggum.py --vault-path ./AI_Employee_Vault stop
"""

import argparse
import json
import subprocess
import sys
import time
import signal
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class LoopStatus(Enum):
    RUNNING = 'running'
    COMPLETED = 'completed'
    STOPPED = 'stopped'
    ERROR = 'error'
    MAX_ITERATIONS = 'max_iterations'


@dataclass
class LoopState:
    """Represents the state of a Ralph Wiggum loop."""
    id: str
    prompt: str
    status: LoopStatus
    created: datetime
    last_iteration: datetime
    iteration_count: int
    max_iterations: int
    completion_promise: Optional[str] = None
    completion_file: Optional[str] = None
    error_message: Optional[str] = None


class RalphWiggumLoop:
    """
    Ralph Wiggum Loop implementation for autonomous task completion.

    This pattern keeps Claude Code working until a task is complete by
    intercepting the exit signal and re-injecting the prompt.
    """

    def __init__(
        self,
        vault_path: str,
        max_iterations: int = 10,
        completion_promise: Optional[str] = None,
        completion_file: Optional[str] = None
    ):
        """
        Initialize Ralph Wiggum loop.

        Args:
            vault_path: Path to the Obsidian vault directory
            max_iterations: Maximum loop iterations before stopping
            completion_promise: Promise string to look for in output
            completion_file: File path that indicates completion when moved to Done
        """
        self.vault_path = Path(vault_path)
        self.max_iterations = max_iterations
        self.completion_promise = completion_promise
        self.completion_file = completion_file

        # State folder
        self.state_folder = self.vault_path / '.ralph_state'
        self.state_folder.mkdir(parents=True, exist_ok=True)

        # State file
        self.state_file = self.state_folder / 'current_loop.json'

        # Current state
        self.current_state: Optional[LoopState] = None

        # Load existing state if present
        self._load_state()

    def _load_state(self):
        """Load existing loop state."""
        if self.state_file.exists():
            try:
                data = json.loads(self.state_file.read_text(encoding='utf-8'))
                self.current_state = LoopState(
                    id=data['id'],
                    prompt=data['prompt'],
                    status=LoopStatus(data['status']),
                    created=datetime.fromisoformat(data['created']),
                    last_iteration=datetime.fromisoformat(data['last_iteration']),
                    iteration_count=data['iteration_count'],
                    max_iterations=data['max_iterations'],
                    completion_promise=data.get('completion_promise'),
                    completion_file=data.get('completion_file'),
                    error_message=data.get('error_message')
                )
            except Exception as e:
                print(f"Warning: Could not load state file: {e}")

    def _save_state(self):
        """Save current loop state."""
        if self.current_state:
            data = {
                'id': self.current_state.id,
                'prompt': self.current_state.prompt,
                'status': self.current_state.status.value,
                'created': self.current_state.created.isoformat(),
                'last_iteration': self.current_state.last_iteration.isoformat(),
                'iteration_count': self.current_state.iteration_count,
                'max_iterations': self.current_state.max_iterations,
                'completion_promise': self.current_state.completion_promise,
                'completion_file': self.current_state.completion_file,
                'error_message': self.current_state.error_message
            }
            self.state_file.write_text(json.dumps(data, indent=2), encoding='utf-8')

    def start(self, prompt: str) -> LoopState:
        """
        Start a new Ralph Wiggum loop.

        Args:
            prompt: The task prompt for Claude

        Returns:
            Initial loop state
        """
        # Check if already running
        if self.current_state and self.current_state.status == LoopStatus.RUNNING:
            print(f"Warning: Loop already running (ID: {self.current_state.id})")
            return self.current_state

        # Create new state
        self.current_state = LoopState(
            id=datetime.now().strftime('%Y%m%d_%H%M%S'),
            prompt=prompt,
            status=LoopStatus.RUNNING,
            created=datetime.now(),
            last_iteration=datetime.now(),
            iteration_count=0,
            max_iterations=self.max_iterations,
            completion_promise=self.completion_promise,
            completion_file=self.completion_file
        )

        self._save_state()
        print(f"Ralph Wiggum loop started (ID: {self.current_state.id})")
        print(f"Task: {prompt}")
        print(f"Max iterations: {self.max_iterations}")

        if self.completion_promise:
            print(f"Completion promise: {self.completion_promise}")
        if self.completion_file:
            print(f"Completion file: {self.completion_file}")

        return self.current_state

    def check_completion(self, claude_output: str) -> bool:
        """
        Check if the task is complete.

        Args:
            claude_output: Output from Claude Code

        Returns:
            True if task is complete
        """
        if not self.current_state:
            return False

        # Check for completion promise in output
        if self.completion_promise and self.completion_promise in claude_output:
            print(f"Completion promise found: {self.completion_promise}")
            return True

        # Check for completion file movement
        if self.completion_file:
            done_file = self.vault_path / 'Done' / Path(self.completion_file).name
            needs_action_file = self.vault_path / 'Needs_Action' / Path(self.completion_file).name
            in_progress_file = self.vault_path / 'In_Progress' / Path(self.completion_file).name

            # Check if file moved to Done
            if done_file.exists():
                print(f"Completion file moved to Done: {self.completion_file}")
                return True

            # Check if file no longer exists (processed)
            if not needs_action_file.exists() and not in_progress_file.exists():
                print(f"Completion file processed: {self.completion_file}")
                return True

        # Check if all files in Needs_Action have been processed
        needs_action = self.vault_path / 'Needs_Action'
        if needs_action.exists():
            pending_files = list(needs_action.glob('*.md'))
            if not pending_files:
                print("All pending items processed")
                return True

        return False

    def should_continue(self) -> bool:
        """
        Check if the loop should continue.

        Returns:
            True if loop should continue
        """
        if not self.current_state:
            return False

        # Check status
        if self.current_state.status != LoopStatus.RUNNING:
            return False

        # Check max iterations
        if self.current_state.iteration_count >= self.current_state.max_iterations:
            self.current_state.status = LoopStatus.MAX_ITERATIONS
            self._save_state()
            print(f"Max iterations reached: {self.max_iterations}")
            return False

        return True

    def record_iteration(self, claude_output: str):
        """
        Record an iteration.

        Args:
            claude_output: Output from Claude Code
        """
        if not self.current_state:
            return

        self.current_state.iteration_count += 1
        self.current_state.last_iteration = datetime.now()

        # Check for completion
        if self.check_completion(claude_output):
            self.current_state.status = LoopStatus.COMPLETED
            print(f"Task completed in {self.current_state.iteration_count} iteration(s)")

        self._save_state()

    def stop(self):
        """Stop the loop."""
        if self.current_state:
            self.current_state.status = LoopStatus.STOPPED
            self._save_state()
            print(f"Ralph Wiggum loop stopped (ID: {self.current_state.id})")

    def get_status(self) -> Optional[Dict]:
        """
        Get current loop status.

        Returns:
            Status dictionary or None
        """
        if not self.current_state:
            return None

        return {
            'id': self.current_state.id,
            'prompt': self.current_state.prompt,
            'status': self.current_state.status.value,
            'iteration_count': self.current_state.iteration_count,
            'max_iterations': self.current_state.max_iterations,
            'created': self.current_state.created.isoformat(),
            'last_iteration': self.current_state.last_iteration.isoformat(),
            'completion_promise': self.current_state.completion_promise,
            'completion_file': self.current_state.completion_file
        }

    def run_claude_iteration(self, working_directory: str = None) -> str:
        """
        Run a single Claude Code iteration.

        Args:
            working_directory: Working directory for Claude

        Returns:
            Claude's output
        """
        if not self.current_state:
            return ""

        # Build Claude command
        cmd = [
            'claude',
            '--prompt', self.current_state.prompt,
            '--verbose'
        ]

        # Add working directory
        cwd = working_directory or str(self.vault_path)

        try:
            print(f"\n--- Iteration {self.current_state.iteration_count + 1} ---")
            print(f"Running: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout per iteration
                cwd=cwd
            )

            output = result.stdout + result.stderr

            # Record iteration
            self.record_iteration(output)

            return output

        except subprocess.TimeoutExpired:
            error_msg = "Claude iteration timed out (5 minutes)"
            print(error_msg)
            self.record_iteration(error_msg)
            return error_msg
        except FileNotFoundError:
            error_msg = "Claude Code not found in PATH"
            print(error_msg)
            self.current_state.status = LoopStatus.ERROR
            self.current_state.error_message = error_msg
            self._save_state()
            return error_msg
        except Exception as e:
            error_msg = f"Error running Claude: {e}"
            print(error_msg)
            self.current_state.status = LoopStatus.ERROR
            self.current_state.error_message = error_msg
            self._save_state()
            return error_msg


class RalphWiggumOrchestrator:
    """
    Orchestrator for Ralph Wiggum loops.

    Manages the continuous execution of Claude Code with the Ralph Wiggum pattern.
    """

    def __init__(self, vault_path: str):
        """
        Initialize orchestrator.

        Args:
            vault_path: Path to the Obsidian vault directory
        """
        self.vault_path = Path(vault_path)
        self.current_loop: Optional[RalphWiggumLoop] = None

    def start_loop(
        self,
        prompt: str,
        max_iterations: int = 10,
        completion_promise: Optional[str] = None,
        completion_file: Optional[str] = None
    ) -> RalphWiggumLoop:
        """
        Start a new Ralph Wiggum loop.

        Args:
            prompt: Task prompt for Claude
            max_iterations: Maximum iterations
            completion_promise: Promise string to look for
            completion_file: File that indicates completion

        Returns:
            Loop instance
        """
        self.current_loop = RalphWiggumLoop(
            vault_path=str(self.vault_path),
            max_iterations=max_iterations,
            completion_promise=completion_promise,
            completion_file=completion_file
        )

        self.current_loop.start(prompt)
        return self.current_loop

    def run_autonomous(
        self,
        prompt: str,
        max_iterations: int = 10,
        completion_promise: Optional[str] = "TASK_COMPLETE"
    ):
        """
        Run autonomous loop until completion.

        Args:
            prompt: Task prompt
            max_iterations: Maximum iterations
            completion_promise: Promise string to look for
        """
        loop = self.start_loop(
            prompt=prompt,
            max_iterations=max_iterations,
            completion_promise=completion_promise
        )

        print("\n" + "=" * 60)
        print("RALPH WIGGUM AUTONOMOUS LOOP")
        print("=" * 60)
        print(f"Task: {prompt}")
        print(f"Max iterations: {max_iterations}")
        print(f"Completion promise: {completion_promise}")
        print("=" * 60 + "\n")

        # Run iterations
        while loop.should_continue():
            output = loop.run_claude_iteration()

            if loop.current_state.status == LoopStatus.COMPLETED:
                print("\n✅ Task completed successfully!")
                break

            if loop.current_state.status == LoopStatus.MAX_ITERATIONS:
                print(f"\n⚠️ Stopped: Max iterations ({max_iterations}) reached")
                break

            if loop.current_state.status == LoopStatus.ERROR:
                print(f"\n❌ Error: {loop.current_state.error_message}")
                break

            # Small delay between iterations
            time.sleep(1)

        # Final status
        status = loop.get_status()
        print("\n" + "=" * 60)
        print("FINAL STATUS")
        print("=" * 60)
        print(f"Status: {status['status']}")
        print(f"Iterations: {status['iteration_count']}")
        print("=" * 60)

        return status


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Ralph Wiggum Loop Plugin'
    )
    parser.add_argument(
        '--vault-path',
        type=str,
        required=True,
        help='Path to the Obsidian vault directory'
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Start command
    start_parser = subparsers.add_parser('start', help='Start a new loop')
    start_parser.add_argument('prompt', type=str, help='Task prompt for Claude')
    start_parser.add_argument('--max-iterations', type=int, default=10, help='Maximum iterations')
    start_parser.add_argument('--completion-promise', type=str, default='TASK_COMPLETE', help='Completion promise string')
    start_parser.add_argument('--completion-file', type=str, help='File that indicates completion')
    start_parser.add_argument('--auto', action='store_true', help='Run autonomously')

    # Status command
    subparsers.add_parser('status', help='Get current loop status')

    # Stop command
    subparsers.add_parser('stop', help='Stop the current loop')

    # Run command (single iteration)
    run_parser = subparsers.add_parser('run', help='Run a single iteration')
    run_parser.add_argument('prompt', type=str, help='Task prompt')

    args = parser.parse_args()

    orchestrator = RalphWiggumOrchestrator(vault_path=args.vault_path)

    if args.command == 'start':
        if args.auto:
            # Run autonomously
            status = orchestrator.run_autonomous(
                prompt=args.prompt,
                max_iterations=args.max_iterations,
                completion_promise=args.completion_promise
            )
            print(f"\nFinal status: {status['status']}")
        else:
            # Just start the loop
            loop = orchestrator.start_loop(
                prompt=args.prompt,
                max_iterations=args.max_iterations,
                completion_promise=args.completion_promise,
                completion_file=args.completion_file
            )
            print(f"\nLoop started. Run 'ralph_wiggum.py run' to execute iterations.")

    elif args.command == 'status':
        loop = RalphWiggumLoop(vault_path=args.vault_path)
        status = loop.get_status()
        if status:
            print("Current Loop Status:")
            print(f"  ID: {status['id']}")
            print(f"  Status: {status['status']}")
            print(f"  Prompt: {status['prompt'][:100]}...")
            print(f"  Iterations: {status['iteration_count']}/{status['max_iterations']}")
            print(f"  Created: {status['created']}")
            print(f"  Last Iteration: {status['last_iteration']}")
        else:
            print("No active loop")

    elif args.command == 'stop':
        loop = RalphWiggumLoop(vault_path=args.vault_path)
        loop.stop()
        print("Loop stopped")

    elif args.command == 'run':
        loop = RalphWiggumLoop(vault_path=args.vault_path)
        if loop.current_state:
            output = loop.run_claude_iteration()
            print("\n--- Claude Output ---")
            print(output)
        else:
            print("No active loop. Start one with 'ralph_wiggum.py start'")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
