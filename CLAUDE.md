# CLAUDE.md

## Project Context

IMPORTANT
ALWAYS READ THE FOLLOWING FILES FOR PROJECT CONTEXT:
@project-context/ARCHITECTURE.md
@project-context/SERVICES.md
@project-context/KNOWLEDGE.md
@project-context/SESSION-STATE.md 

## Rules
- Always use Tailscale IPs for inter-node communication
- When running commands in the compute node, verify where you are, most likely you are already there.
- For any kubectl command you need to run, there is no need to ssh.
- After working on any of the apps (dashboard, family assistant or any other) remember to commit and push.

