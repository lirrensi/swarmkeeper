[ ]
`list` command should also fetch status and log lines, so we can see easy without requesting manager



[ ] 
watch <s> (default 180s)
command to continuously watch, or rather call manager command repeatedly;
stopping when anyone of them detected `stopped`

[ ] 
notifications when a session stops working
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