# IELTS / TOEFL / Tolimo Writing Practice Tool

<div align="center">

[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)  
[![Python ≥3.9](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)  
[![Offline AI](https://img.shields.io/badge/ai-local%20%26%20offline-success)](#features)

![Task 1 Interface](https://i.imgur.com/3qxaWYF.png)  
*IELTS Academic Task 1: Side-by-side diagram and writing pane*

![Task 2 Interface](https://i.imgur.com/2clIYGH.png)  
*Task 2 & Tolimo: Full-response writing with real-time AI feedback*

</div>

> A privacy-focused, **offline-first desktop application** for practicing **IELTS Academic Writing (Task 1 & Task 2)**, **TOEFL**, and **Tolimo** essays — featuring **local AI-powered paragraph analysis**, exam-accurate timing, and intelligent topic management. Designed for self-directed learners targeting **Band 7+**.

---

## ✨ Key Features

- **Context-Aware Layouts**  
  - **Task 1 (20 min)**: Dual-pane UI with diagram viewer (left) and writing area (right).  
  - **Task 2 / Tolimo (30–40 min)**: Full-width writing canvas with distraction-free focus.

- **Diagram Handling**  
  - Load charts/graphs via **URL** or **local file** (PNG, JPG, WebP, etc.).  
  - **Zoom (1.8×)** and **reset** controls for detailed visual analysis.

- **On-Device AI Evaluation**  
  Uses Hugging Face’s `facebook/bart-large-mnli` zero-shot classifier **locally** (no cloud):  
  - Each paragraph scored in real time as:  
    - ✅ **Excellent** → `#4CAF50`  
    - 👍 **Good** → `#8BC34A`  
    - ⚠️ **Average** → `#FFC107`  
    - ❌ **Weak** → `#F44336`  
  - Runs on **CPU or GPU** (CUDA auto-detected).

- **Precision Word Counting**  
  Counts only the user’s response (excludes the prompt). Visual target indicators:  
  - **150 words** for Task 1  
  - **250 words** for Task 2 & Tolimo

- **Authentic Exam Timer**  
  - Modes: **20 min** (Task 1), **40 min** (Task 2), **30 min** (Tolimo).  
  - Automatic alerts:  
    - ⏱️ **5-minute warning** (proofreading phase)  
    - ⏳ **3-minute warning** (final review)  
  - **Freezes input** on expiry while allowing copy/export.

- **Smart Topic Management**  
  - **Random IELTS Task 2 prompts** fetched from [Engnovate](https://engnovate.com/ugc-ielts-writing-task-2-topics/).  
  - Tracks used topics (`used_topics.txt`) to **avoid repetition**.

- **Enhanced Usability**  
  - Right-click context menu (Copy / Paste / Select All) — **disabled when frozen**.  
  - **Scrollable text area** for long responses.  
  - **Built-in help guide** with mode-specific instructions.

- **100% Offline After Initialization**  
  AI model (~500 MB) downloads **once on first launch**. No internet required thereafter.

---

## 🚀 Installation & Setup

### Prerequisites
- Python **3.9 or higher**
- Internet connection (for **first-time model download only**)

### Steps

```bash
git clone https://github.com/shataragh/IELTS-Writing-Practice.git
cd IELTS-Writing-Practice
pip install -r requirements.txt
python main.py
