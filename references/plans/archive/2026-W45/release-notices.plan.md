# Release notices: researchteam v1.0.4 and v1.1.0-rc.5 to derived repositories

Date: 2026-11-05. Operator: Jim (asked 2026-11-05: "Send the release notices").

## Goal

Tell each derived repository's session about the new signed researchteam tag on its line. The notice is
**information, not operator approval**: each repository adopts through its own session, and Jim approves and signs
there.

| Repo | Line | Move to | Extra step in that repo |
|---|---|---|---|
| baseAgent | 1.0 | `v1.0.4` | none new. Its 1.1 adoption (#283) stays held until Experiment 1 is done, and its `main` must not be pushed during the experiment. |
| Batallion | 1.0 | `v1.0.4` | none new |
| mathAgents | 1.1 | `v1.1.0-rc.5` | add `"s10_cooldown_exempt_repos": ["jlcatonjr/agentteams"]` to its brief, and Jim signs its own `s10-cooldown-exempt:jlcatonjr/agentteams` row there. mathAgents adopts through its own `refresh_agent_surfaces.sh`, and this session never touches it. |

## Facts every notice carries (all verified 2026-11-05)

- **v1.0.4:**
  - tag object 412bb8374e29ae67cb9b91d06e8adf45ceee17f0, peeled f3396f0b7eefb1149e7077ddc3abe89682f7c499;
  - pins agentteams v1.0.7 (8b934600b554d14c1bd02adebe519a4999473c13);
  - GitHub release marked Latest.
- **v1.1.0-rc.5:**
  - tag object 125b46652e79fc29ec9cdc2b4c0fd24dab0dfe00, peeled f4be2d996c3266bf26f34e9590bcd50d0b4535b8;
  - pins agentteams v1.1.0-rc.16 (a036d09f75cc9d6dc1961e1deb803a3436b22f35);
  - pre-release.
- Release key SHA256:IPdnLwlFdHNhr7QGKVWU40BOKyYzv2u8qxP/qxnzTNM. Each repository verifies the tag itself before
  pinning (`check_toolchain.py --verify-tag researchteam <tag>`). It must not rely on these hashes alone.
- **What changed:**
  - S-10 cooldown restored, with the vulnerability carve-out and the local-interdependent-repo carve-out;
  - the exemption renders on all four surfaces;
  - the bootstrap pins pip==26.2.2. This is in v1.0.4 only; on the 1.1 line it ships after rc.5.

## Delivery

No session can be identified as a repository's from `ListAgents`: names are prefixes, and there are three
baseagent-* sessions and no Batallion session. So:
1. Jim picks the recipients (AskUserQuestion).
2. I send each chosen session its notice with SendMessage. The first line says what it is and that it carries no
   approval.
3. Any repository without a picked session gets a notice file at
   `tmp/by-week/2026-W45/notices/<repo>.md` for Jim to paste when he opens that repository's session. Writing into
   another repository would be a cross-repo write (C-5), so it is not done.
4. Record each delivery (session name and msg_id, or the file path) in the steps CSV.

## Not done

No edits to baseAgent, Batallion or mathAgents. Messages request nothing that this session's permissions would
block.

## Audit revisions (@adversarial, 2026-11-05)

- **The notices request no action.** Each one says the re-pin, any brief edit and any signed row are Jim's to
  decide in that repository. The send criterion is now "requests no action at all".
- **baseAgent:** adopting means committing to its `main`, which must not move during Experiment 1. Its notice
  therefore says adoption waits until the experiment ends. Delivery defaults to file only, because a message into a
  running experiment session could contaminate it. Jim can override.
- **Facts split by tag, each checked at its own tag:**
  - v1.0.4: all four `@security` surfaces render `jlcatonjr/agentteams` (checked at the tag, 1 each).
  - rc.5: the same, and agentteams-54 independently confirmed the per-surface HALT behaviour.
- **Step 1 widened:** release-key fingerprint, Latest/pre-release flags, and the `release/1.0` and `release/1.1`
  tips (f3396f0b, f4be2d99). All checked 2026-11-05.
