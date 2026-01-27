# === START A NEW SESSION (creates + enters it) ===
cmd> tmux new-session -s agent-001673


# Or with a command that runs inside:
cmd>  tmux new-session -s agent-001 -d "opencode"  # -d = detached (doesn't attach)

# === LIST ALL SESSIONS ===
cmd> tmux list-sessions
cmd>  tmux ls



# === ATTACH TO EXISTING SESSION ===
cmd> tmux attach -t agent-001


# === DETACH (from inside session) ===
# Press: Ctrl+b, then d

# === SEND KEYS TO A SESSION ===
cmd> tmux send-keys -t agent-001 "echo hello" Enter


# === CAPTURE PANE CONTENTS ===
cmd> tmux capture-pane -t agent-001 -p
psmux capture-pane -t agent-001 -p
# -p = print to stdout
# Without -p, it goes to paste buffer

# === CHECK IF SESSION EXISTS ===
cmd> tmux has-session -t agent-001
psmux has-session -t agent-001
# Exit code: 0 = exists, 1 = doesn't exist

# === KILL A SESSION ===
cmd> tmux kill-session -t agent-001
psmux kill-session -t agent-001