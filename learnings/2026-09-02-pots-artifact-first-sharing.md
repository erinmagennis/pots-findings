# Choose the product's shareable object before building sharing infrastructure

**Date:** 2026-09-02  **Context:** Open POTS sharing and BYOK chat

## The approach that worked

- Started from the reported provider error and mapped the maintenance needed for a reliable BYOK chat.
- Followed the proposed conversation-sharing flow until accounts, email ownership, privacy, and revision history appeared.
- Erin identified that the flow was overcomplicated and clarified that artifacts, graphs, and data are what she wants people to share.
- Reframed chat as an optional experiment and made static, versioned artifact sharing the core direction.

## Judgment calls

- Keep only the small compatibility repair for the existing chat instead of expanding providers and infrastructure.
- Prefer shareable URLs and exports because they fit the static site and do not require keys, accounts, or conversation storage.
- Wait for observed chat usage before adding provider monitoring or a publication backend.

## Reusable rule

Name the primary shareable object before designing accounts, storage, email, or version history around it.
