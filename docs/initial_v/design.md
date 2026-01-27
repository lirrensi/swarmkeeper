# swarmkeeper - stop being a nanny to your agents!
(actual name change, its too common! gh found 70 repos)

How it works:
- tmux or win analog required
- works with cli/TUI based coding agents

1. open any terminal in any folder or existing
2. swarmkeeper start "cli command here"
like: `swarmkeeper start opencode`

3. it saves a global handle to the terminal session of tmux:

`tmux new-session -s agent-001` + opencode
reopens right here as if nothing happened! you use it same way!

4. now it can see on demand whats happening inside
`swarmkeeper list`
=> collects active sessions (not killed, but detached will work here)
`swarmkeeper dump`
=> sends all sessions rendered state right in stdout:

=== agent-01 ===
<TUI here>

...

5. you, and anyone can send text in anytime:
`swarmkeeper send agent-001 "pls continue"`

which is simple tmux send keys

---


# Now, the whole purpose of it!
So you dont nannysitting them!

`swarmkeeper manager`
=> iterates over each, calls output to llm to determine if agent stopped prematurely, stuck, errored, or slacking
=> chooses action:
    - skip - seems to be working ok
    - nudge - sends text to continue
    - escalate - requires your attention, end turn but for you!
=> returns to you with report of state of each agent and asks interactively:

- I will write to each => loop to ask for instructions for each one in natural language "just tell it to continue!"
=> converts to nicer instructions and sends out

- I will send general instructs => asks you single text
Where you can: "tell all to continue! but agent02 can stop now, do nothing"
=> converts to same instructs per term and sends out

`swarmkeeper manager-loop <seconds=60>`
=> same but runs infinite, reports to you when someone needs attention, non blocking;

Or, use any coding agent:
`claude -p swarmkeeper_prompt.md`

- instructs how to get dump - running subagents to get big blob and only report findings
- asks to sleep between runs
- to send its workers commands

But that suffers from same issue that we have only single end turn... but you have to watch one terminal instead of many, but easier so not require to setup another api...


---

manager should also keep track of what each was doing

MVP1
- just manager
- that watches on demand and gives you and overlook of what each is doing!