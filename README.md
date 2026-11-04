# Video Skill Doctor

A small, local-first preflight for video-focused agent skills. Point it at a downloaded skill folder and it checks whether common tools mentioned in the skill's docs—such as FFmpeg, Python, Node, or Docker—are available on your PATH.

> **Status:** Early prototype. It is a text-based helper, not a dependency resolver, security scanner, or proof that a skill will work.

## Why this exists

Video skills often need a mix of system tools, language runtimes, and optional services. Setup instructions can be spread across a `README.md`, `SKILL.md`, and `install.md`. This tool gives you one local report before you start following those setup steps.

## Run it

Requires Python 3.9+ and uses only the Python standard library.

```sh
python3 skill_doctor.py ~/Downloads/claude-video-effects-main
```

Check several downloaded folders at once:

```sh
python3 skill_doctor.py \
  ~/Downloads/claude-video-effects-main \
  ~/Downloads/claude-remotion-skill-main
```

For scripts or other tools, use JSON output:

```sh
python3 skill_doctor.py --json ~/Downloads/video-use-main
```

It looks in `README.md`, `SKILL.md`, `install.md`, and common dependency manifests. It prints where each tool name appeared so you can check whether the skill calls it required or optional. A tool being found does not prove the installed version is suitable.

## What it checks

- `ffmpeg`, `ffprobe`, `python`, `node`, `npm`, `npx`, `uv`, `docker`, and `yt-dlp`
- Whether one of the matching executable names can be found on `PATH`
- Which recognized files mention each tool

## Limits

- A tool name in documentation may be optional or just an example; review the cited lines.
- It does not inspect every package manager, version constraint, API key, model file, GPU, or service.
- It does not verify JavaScript packages such as Playwright or browser installations.
- It does not read environment-variable values, execute scripts, install packages, or modify the skill folder.
- It is not a security audit. Read and trust a skill's source before running it.

## Contributing

Suggestions are welcome, especially new common tools and examples of confusing setup instructions. Please include the skill file that mentions the dependency and whether it is required or optional. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT. See [LICENSE](LICENSE).
