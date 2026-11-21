# Human steps

Only Shreyas can do these. Do them in order.

Release commit: 099a0d95e80506354afcd232f0e1808f73837fb7 on branch `claude/project-thread-kd42dy`.

1. Open a pull request from `claude/project-thread-kd42dy` into `main` on GitHub (the session page has a button for it). Read the diff. Merge with a merge commit, so the release commit stays in the history of `main`. The project coordinator may already have done this.
2. Create the tag on the release commit. Either run `git fetch origin`, then `git tag -a v0.1.0-rc1 099a0d95e80506354afcd232f0e1808f73837fb7 -m "Release candidate 1"`, then `git push origin v0.1.0-rc1`, or create a pre-release with that tag on the GitHub releases page.
3. Run the secret scan once more: `gitleaks git -v .` in a fresh clone.
4. Check that the CI run on the merge commit is green on the Actions page.
5. Make the repo public when you are ready. All history becomes public at that moment.
6. Pages: not needed. The results page `docs/index.html` opens from disk. Turn on Pages from `/docs` only if you want it online.
7. Upload `docs/social-preview.png` in Settings, General, Social preview. Fill in the About box from [GITHUB_ABOUT.md](GITHUB_ABOUT.md) and the topics from [topics.txt](topics.txt) if the coordinator did not.
8. Pin the repo or list it in your profile README.
9. Publish to PyPI with trusted publishing, if you want the package public. The name `handoffpact` was free on 2026-11-21.
10. Stretch: add a free provider key (for example `GROQ_API_KEY`) or a network secret, then run a record mode run of about 30 tickets with a free model and count natural contract violations by type. This run could not reach the provider hosts. Free router repos such as OmniRoute and litellm also need a key.
11. Decide whether `docs/build/BUILD_PROMPT.md` stays public.
12. Do the human checks listed in the README: read the contracts, rerun the benchmark, review the leak phrases and patterns.
