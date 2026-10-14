# P1 ↔ P2 Claude comms protocol

This branch (`comms`) is a message bus between Person 1's and Person 2's Claude Code sessions, replacing
copy-paste through the humans. It holds only messages, never code.

## Files
- `p1-to-p2/NNNN-short-title.md`: written by Person 1's Claude, read by Person 2's.
- `p2-to-p1/NNNN-short-title.md`: written by Person 2's Claude, read by Person 1's.
- `NNNN` is a 4-digit number, increasing per direction (`0001`, `0002`, …). One message per file, never edited
  after pushing. To correct something, send a new message. One file per message means there are no merge conflicts.
- `STATUS.md`: optional. Each side may rewrite only its own section with a one-screen status.

## Message format
```markdown
# P1→P2 #0003 (re P2→P1 #0002)
Prefix: CONTRACT | PUSHED | BLOCKED | SYNC READY | MERGED | CUT | REQUEST | ANSWER | FYI
Needs reply: yes|no

1. Point one (concrete: branch + SHA, exact field names, file paths, signatures)
2. ...
```

## Loop each Claude runs
```bash
# from the main checkout, without touching code branches
git fetch -q origin comms
git log --oneline HEAD..origin/comms -- p2-to-p1/   # (Person 1's side; P2 reads p1-to-p2/)
git show origin/comms:p2-to-p1/0001-hello.md
```
To send, keep a worktree of this branch (`git worktree add ../sevaicheck-comms comms`), then
`git pull --rebase -q && git add <file> && git commit -m "comms: P1→P2 #NNNN <title>" && git push`.

Poll every ~5 minutes while working (e.g. `/loop 5m check the comms branch for new messages and act on them`).

## Rules
1. **Ownership still applies** (CLAUDE.md §1). A message is a request, never permission to edit the other side's
   paths. Only Person 1 edits `contract/`.
2. **Humans decide.** Anything that changes scope, cuts a feature or changes the contract is confirmed by the
   human on the receiving side before acting. Routine answers and FYIs need no confirmation.
3. **Be concrete:** branch + SHA for pushes, version + exact fields for contract changes.
4. **No secrets** in messages (they are in git history forever). Secrets go human to human by DM.
5. Keep messages short. Link to files on `main` instead of pasting code.
