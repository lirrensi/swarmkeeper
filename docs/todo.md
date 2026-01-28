[?]
`list` command should also fetch status and log lines, so we can see easy without requesting manager

[?]
remake to allow to be installed with pipx/uv tool
update readme to have a proper cli command examples


[?]
watch <s> (default 180s)
command to continuously watch, or rather call manager command repeatedly;
stopping when anyone of them detected `stopped`, waiting for you to pay attention to terms and fix/change
we have to stop else it will continue same loop! 
Its logical anyway - one is stopped, either close it or put to work;
Anyone wants faster reaction time - 3min is enough, and will see stops right away
Anyone who wants to come every 30min or so - will see that one is stopped, loop stopped and we did not waste tokens checking up on others...

False positive? require 2 times check? need experiments on success rate...


[ ] 
notifications when a session stops working => when in watch mode;
use os native api for that preferably + maybe a sound cue
define a custom function/cli command to call - so devs can integrate with channels

[ ]
smarter snapshot - grab but split lines based on columns
cutoff useless whitespace
> take not entire window but bottom part of it, where actual state happens
but also in a way that does not cuts info if TUI is top first



---

v2 - proactive management
[ ] detect when agent failed due to internal error, not a real end turn - like malformed tool call or other
[ ] add manager sending in "continue" when it stops failing
[ ] create an interface with swarmkeeper translating your "go on" into detailed instructions 