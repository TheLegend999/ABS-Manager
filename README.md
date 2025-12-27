Markdown

# Audiobookshelf Metadata Manager

> **⚠️ DISCLAIMER: I AM NOT A CODER.**
> I do not code as a job or a hobby. I built this tool using AI (Gemini) solely because I was annoyed that my audiobooks weren't grouping correctly in Audiobookshelf.
>
> **Use this tool with caution. Always backup your library before running mass updates.**

## Project Overview

A Python GUI tool to manage, audit, and fix metadata for `.m4b` audiobook libraries.

I created this because **my entire library is in `.m4b` format, but none of the files had the correct internal tags.** Audiobookshelf wasn't grouping them properly because the files themselves were empty or wrong. This tool fixes that by writing the correct data directly into the files.

## Features

* **Visual Audit:** Scans your folder and displays a tree of `Author > Series > Book`.
* **Smart Parsing:** Reads data from `metadata.json` (ABS export) or filename regex to figure out what the tags *should* be.
* **Tag Syncing:** Writes the correct tags into the `.m4b` files so they stick permanently.
    * Sets `©grp` to `Series Name #Index`.
    * Sets `disk` number to the Series Index.
    * Syncs `©ART` (Author) and `©nam` (Title).
* **Safety:** It edits metadata in place but **does not** rename or move your files.

## Setup

**Environment:**

* Arch Linux / Fish Shell
* Python 3.13

**Dependencies:**

```bash
pip install PyQt6 mutagen

Usage

Activate Environment:
Bash

source ~/audiobook-env/bin/activate.fish

Run the Tool:

python main.py
