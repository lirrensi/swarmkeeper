create a project mvp

initial draft at design.md

how it works:
python main.py start => opens tmux session right here
wrapper just creates own session index
capture command if present, else empty
1. generates name in patern {agent-XX-{suffux}}

ANIMALS = [
    "bee", "ant", "wasp", "beetle", "moth", "cricket",
    "spider", "ladybug", "firefly", "dragonfly", "mantis",
    "caterpillar", "butterfly", "hornet", "termite", "locust",
    "cicada", "aphid", "roach", "flea", "gnat", "mite"
]

2. saves in ~/swarmkeeper/sessions.json

{
  "agent-01-spider": {
    "created": "2026-01-27T14:30:00",
    "command": "opencode",
    "checks": []
  }
}


btw it creates ~/swarmkeeper/config.json
apiBase:str
model: str
apiKey: str
params: {
    temperature: 0.2
    ...
}

3. add basic 
4. now it can see on demand whats happening inside
`swarmkeeper list`
=> collects active sessions (not killed, but detached will work here)
`swarmkeeper dump`
=> sends all sessions rendered state right in stdout:


5. add `swarmkeeper manager`

1. checks that session not dead, if dead => removes from the list + notifies print
2. gets each session output
3. calls api (openai compatible with settings in configs)
4. system (from swarmkeeper_check.md prompt) + user (tui rendered dump)
5. returns to user with a print report what each is doing

6. appends checks[]
{"time": "14:35:00", "status": "working", "log": "Analyzing src/auth.py..."},
