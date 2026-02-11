# SwarmKeeper

Like to open a trillion ClaudeCodes in parallel but tired of watching them?
We got some ease for your ADHD!
A CLI tool to manage and observe coding agent sessions using tmux and LLM analysis.

## Overview

SwarmKeeper creates named tmux sessions, monitors their output, and uses OpenAICompatible api to determine if agents are working or stopped. 
It maintains a registry of current sessions and their health history.

Compared to other methods like ACP (AgentClientProtocol) this allows agents to work in their native interface.
Overseer is just a small layer to get current state and monitor.

## How it works:

1. Open a terminal and run `swarmkeeper start` => opens tmux => you enter your coding agent
2. (in separate pane) Run `swarmkeeper list` to see tracked sessions, `swarmkeeper manager` to analyze them.

## Why this exists when...

Why you solve a simple task with llm, just use some hooks!

- Not all coding agents have turn end, and you have to fork and stay behind to add this.
- Not all of them support ACP, and even if it was the case - it may be inconvenient to your workflow. We want to work everywhere at once and support whatever.
- Just looking is not all of it, greater goal - to intelligently monitor and autorespond.


### Key Features

- **Session Management**: Automatic animal-based naming (agent-01-spider, agent-02-bear, etc.)
- **LLM Analysis**: Automatically detects if agents are working or stopped
- **Session Registry**: Tracks all sessions and their health history
- **Custom Naming**: Use `--name` flag for custom session names
- **Auto-configuration**: Creates config files automatically on first use
- **Dead Session Cleanup**: Automatically removes stopped sessions from registry

### Use Cases

- Run multiple agent sessions in parallel
- Monitor agent progress without manual checking
- Keep history of agent activity
- Debug stopped or stuck sessions

---

## Prerequisites

### Windows Users

SwarmKeeper uses tmux, which needs a Windows-compatible implementation:

**psmux** (recommended for basic usage)
   - GitHub: https://github.com/marlocarlo/psmux
   - Install: `choco install psmux` or download from GitHub (better - its more fresh rn)


### Unix/Linux Users

tmux is typically pre-installed. If not:
- Ubuntu/Debian: `sudo apt-get install tmux`
- macOS: `brew install tmux`

---

## Installation

### Using pipx (Recommended for CLI tools)

```bash
pipx install .
# or from GitHub
pipx install git+https://github.com/lirrensi/swarmkeeper.git
```

### Using uv

```bash
uv tool install .
# or from GitHub
uv tool install git+https://github.com/lirrensi/swarmkeeper.git
```

### Manual Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd SwarmKeeper
   ```

2. Install Python dependencies:
   ```bash
   uv sync
   ```

---

## Configuration

Create a config file at `~/swarmkeeper/config.json`:
(it auto created at first call anyway)

```json
{
  "apiBase": "http://localhost:8080/v1",
  "model": "llamacpp",
  "apiKey": "your-api-key-here",
  "params": {
    "temperature": 0.2
    ...any other llm params
  }
}
```

### Configuration Options

- `apiBase`: Base URL for the LLM API (default: OpenAI's API)
- `model`: Model identifier (default: "gpt-4o-mini")
- `apiKey`: Your API key for the LLM service
- `params`: Additional model parameters (e.g., temperature)

The config file will be automatically created on first use if it doesn't exist.

---

## Usage

### Basic Commands

```bash
# Start a new session
swarmkeeper start "echo hello"

# Start with custom name
swarmkeeper start --name "my-agent" "echo hello"

# List all sessions
swarmkeeper list

# Dump session output to file
swarmkeeper dump

# Run manager to check all sessions
swarmkeeper manager
```

### Workflow

1. **Start sessions**:
   ```bash
   # Agent 1: Running a task
   swarmkeeper start "python task.py"

   # Agent 2: Monitoring logs
   swarmkeeper start "tail -f /var/log/app.log"
   ```

2. **Monitor sessions**:
   ```bash
   # Check health of all sessions
   swarmkeeper manager
   ```

3. **View output**:
   ```bash
   # Dump output to file
   swarmkeeper dump > session-output.txt
   ```

4. **Clean up**:
   ```bash
   # Kill a specific session
   swarmkeeper stop agent-01-spider

   # Kill all sessions
   swarmkeeper stop all
   ```

---

## CLI Commands

### `start`

Start a new tmux session with the given command.

**Usage:**
```bash
swarmkeeper start [--name NAME] <command>
```

**Options:**
- `--name NAME`: Custom session name (optional, uses auto-generated name if omitted)
- `<command>`: The command to run in the session

**Examples:**
```bash
swarmkeeper start "echo hello"
swarmkeeper start --name "my-custom-agent" "python script.py"
```

### `list`

List all tracked sessions.

**Usage:**
```bash
swarmkeeper list
```

**Output:**
```
agent-01-spider    working    analyzing code
agent-02-bear      stopped    Session no longer exists
```

### `dump`

Dump the output of all sessions.

**Usage:**
```bash
swarmkeeper dump
```

**Options:**
- `output_file`: Output filename (default: `~/swarmkeeper/session-output.txt`)

**Examples:**
```bash
python main.py dump
python main.py dump > my-session.txt
```

### `manager`

Run the LLM manager to check all sessions and update their health status.

**Usage:**
```bash
swarmkeeper manager
```

**Behavior:**
- Analyzes all tracked sessions using LLM
- Updates session registry with health checks
- Automatically removes dead sessions from registry
- Prints status for each session

**Output:**
```
Session agent-01-spider: working - analyzing code
Session agent-02-bear: dead - removing from registry
```

### `manager-loop`

Run continuous monitoring loop that repeatedly checks all sessions and stops when any session becomes stopped.

**Usage:**
```bash
swarmkeeper manager-loop [options]
```

**Options:**
- `--interval SECONDS`: Check interval in seconds (default: 180)
- `--confirm`: Require 2 consecutive checks before stopping

**Behavior:**
- Repeatedly calls manager to check all sessions
- Stops when ANY session is stopped (alive=False)
- Non-blocking - runs in foreground
- Saves registry after each check
- User can interrupt with Ctrl+C
- Configurable timing for speed vs efficiency
- False positive prevention via confirmation mode

**Fast Mode (default):**
```bash
swarmkeeper manager-loop
```
Stops immediately on first stopped session detection.

**Conservative Mode:**
```bash
swarmkeeper manager-loop --confirm
```
Requires 2 consecutive stopped checks per session before stopping (reduces false positives).

**Custom Interval:**
```bash
swarmkeeper manager-loop --interval 60
```
Checks every 60 seconds instead of default 180 seconds.

**Example Workflow:**
```bash
# Start a few agent sessions
swarmkeeper start "python backend.py"
swarmkeeper start "python frontend.py"

# Run loop with fast mode (default)
swarmkeeper manager-loop

# Or run with conservative mode if false positives are an issue
swarmkeeper manager-loop --confirm
```

**Exit Behavior:**
```
Running manager loop
  Interval: 180 seconds
  Confirmation mode: disabled
  Sessions to monitor: 2

Press Ctrl+C to stop

[Loop check #1] Checking sessions...
All sessions are active. Continuing check...

[Loop check #2] Checking sessions...
Detected stopped session(s): agent-01-spider
  agent-01-spider: stopped - stopped working

Stopping loop (fast mode).

Registry saved. 1 sessions tracked.
```

### `stop`

Stop a specific session or all sessions.

**Usage:**
```bash
swarmkeeper stop <session_name> | all
```

**Options:**
- `<session_name>`: Name of the session to stop (e.g., `agent-01-spider`)
- `all`: Stop all tracked sessions

**Examples:**
```bash
swarmkeeper stop agent-01-spider
swarmkeeper stop all
```

---

## Architecture

### Components

1. **Configuration Module** (`swarmkeeper/config/`)
   - Manages config and sessions registry files
   - Auto-creates files on first use

2. **Session Management Module** (`swarmkeeper/session/`)
   - Generates animal-based session names
   - Tracks session health history
   - Manages session registry

3. **Tmux Integration Module** (`swarmkeeper/tmux/`)
   - Windows-compatible tmux wrapper
   - Captures pane output
   - Manages tmux sessions

4. **Manager/Observer Module** (`swarmkeeper/manager/`)
    - LLM-based session analysis
    - Generates health reports
    - Updates session status

5. **Loop Control Module** (`swarmkeeper/manager/loop.py`)
    - Continuous monitoring loop
    - Configurable timing and exit conditions
    - False positive prevention

6. **CLI Interface** (`main.py`)
    - User command-line interface
    - Handles all user interactions

### Session Naming Convention

Sessions are automatically named with the pattern: `agent-XX-{animal}`
- `XX`: Sequential number (01, 02, 03, ...)
- `{animal}`: Random animal from a predefined list

This makes it easy to identify and manage multiple sessions.

### Health Detection

The manager uses LLM analysis to determine session health:
- **working**: Session is actively processing work
- **stopped**: Session has stopped (no longer exists or idle)
- **error**: Session encountered an error

---

## Advanced Usage

### Custom Session Names

Use the `--name` flag for custom naming:

```bash
swarmkeeper start --name "database-migration" "python migrate.py"
swarmkeeper start --name "frontend-dev" "npm run dev"
```

### Running Multiple Agents

Start multiple sessions and monitor them together:

```bash
# Terminal 1
swarmkeeper start "python backend.py"

# Terminal 2
swarmkeeper start "python frontend.py"

# Terminal 3 (monitor all with loop)
swarmkeeper manager-loop
```

### Continuous Monitoring Loop

For unattended monitoring, use the manager-loop command:

```bash
# Fast mode - stops immediately when any session stops
swarmkeeper manager-loop

# Conservative mode - requires 2 checks before stopping
swarmkeeper manager-loop --confirm

# Custom interval (every 30 minutes)
swarmkeeper manager-loop --interval 1800

# Combine options
swarmkeeper manager-loop --interval 60 --confirm
```

**When to use fast mode:**
- You want immediate attention to stopped sessions
- Sessions rarely have false positives
- You're actively watching and want to react quickly

**When to use confirmation mode:**
- Sessions sometimes appear stopped briefly (network issues, loading, etc.)
- You want to reduce false alarms
- You can tolerate slightly longer reaction time

**Tips:**
- Use shorter intervals for faster detection (e.g., 60s)
- Use confirmation mode for conservative monitoring
- Interrupt loop with Ctrl+C at any time
- Loop saves registry after each check

### Viewing Session History

The session registry (`~/swarmkeeper/sessions.json`) contains the full history:

```json
{
  "agent-01-spider": {
    "created": "2026-01-28T00:57:56",
    "command": "echo hello",
    "checks": [
      {"time": "2026-01-28T01:00:00", "status": "working", "log": "analyzing code"},
      {"time": "2026-01-28T01:01:00", "status": "stopped", "log": "Session no longer exists"}
    ]
  }
}
```


---

## Troubleshooting

### Session not found
- Check session name with `swarmkeeper list`
- Verify session exists with `tmux ls`

### LLM API errors
- Check `~/swarmkeeper/config.json` for correct API key
- Verify `apiBase` points to valid LLM server
- Test API connection: `curl <apiBase>/models`

### Windows tmux issues
- Ensure psmux is installed and in PATH
- Check tmux version: `tmux -V`
- Try restarting tmux server: `tmux kill-server`

---

## Roadmap

### v1 - monitoring first

Goal: one interface to rule them all

[x] basic checking the current state on demand
[ ] watch sessions and analyze when they stop/wait for you to check/errored
[ ] notifications when a session stops working

??? your idea? web gui?

### v2 - proactive management

Goal: reduce your time babysitting them 5x

[ ] detect when agent failed due to internal error, not a real end turn - like malformed tool call or other
[ ] add manager sending in "continue" when it stops failing
[ ] create an interface with swarmkeeper translating your "go on" into detailed instructions 


## You may also like:

**silc**:
- For advanced usage requiring full shell control, it allows you to coexist with your agent in same shell same way as tmux does
- GitHub: https://github.com/lirrensi/silc
- Use when you need features like shared shells, multiple panes, etc.

## License

MIT License