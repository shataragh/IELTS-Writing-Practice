import customtkinter as ctk
from customtkinter import CTkTextbox, CTkButton, CTkLabel, CTkFrame, CTkEntry, CTkRadioButton
from CTkMessagebox import CTkMessagebox
import threading
import time
import random
import requests
from bs4 import BeautifulSoup
import os
from transformers import pipeline
import torch
import io
from PIL import Image
from tkinter import filedialog, Menu

ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")

class IELTSWritingApp:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("IELTS / TOEFL / Tolimo Writing Practice")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)

        self.timer_running = False
        self.remaining_seconds = 0
        self.used_topics_file = "used_topics.txt"
        self.used_topics = self.load_used_topics()
        self.last_content = ""
        self.off_topic_alerted = False
        self.warning_5min_shown = False
        self.warning_3min_shown = False
        self.first_task1_selection = True
        self.original_pil_image = None
        self.is_zoomed = False
        self.is_frozen = False

        print("Loading AI model... (first run may take 20-60 seconds)")
        device = 0 if torch.cuda.is_available() else -1
        self.classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli", device=device)

        self.setup_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def load_used_topics(self):
        if os.path.exists(self.used_topics_file):
            with open(self.used_topics_file, "r", encoding="utf-8") as f:
                return set(line.strip() for line in f if line.strip())
        return set()

    def save_used_topic(self, topic):
        if topic not in self.used_topics:
            with open(self.used_topics_file, "a", encoding="utf-8") as f:
                f.write(topic + "\n")
            self.used_topics.add(topic)

    def show_help(self):
        help_text = """
IELTS / TOEFL / Tolimo Writing Practice Tool - User Guide

1. Select Exam & Time
   - 20 minutes – IELTS Academic Task 1: Describe charts, graphs, processes, maps.
   - 40 minutes – IELTS Task 2: Opinion / discussion essays.
   - 30 minutes – Tolimo Writing: Tolimo-style tasks.

   Timer starts when you click "Start Timer". Warnings appear at 5 and 3 minutes (for 30/40 min tasks).

2. Topic / Question
   - Type or paste the full question.
   - For Task 2: "Fetch Random Topic" provides a new unused IELTS Task 2 question.
   - Click "Apply Topic" to insert it into the writing area.

3. Diagram / Chart for Task 1
   - Appears only in 20-minute mode with side-by-side layout.
   - Load image via URL or local file.
   - "Magnify Image" zooms in for detail viewing.
   - "Reset Size" returns to standard size.

4. Write Your Response
   - Full-width in Task 2/Tolimo, right panel in Task 1.
   - Scrollable vertically if text is long.
   - Right-click context menu: Copy / Paste / Select All (disabled when time is up and box is frozen).

5. Real-time Feedback
   - Word Count: Counts only your response. Turns green when target reached (150 for Task 1, 250 for others).
   - Paragraph Quality: Colored squares for each paragraph (excellent → strong green, weak → red).

6. Controls
   - Copy Response: Copies topic + your writing.
   - Clear Response: Clears only your writing (keeps topic).
   - Help: This guide.

When time expires, the writing box freezes (read-only). You can still copy text.

For questions or feedback, contact the developer:
https://www.linkedin.com/in/sir1/

Good luck with your practice!
        """

        CTkMessagebox(
            title="Help & User Guide",
            message=help_text,
            icon="info",
            width=800,
            height=600
        )

    def setup_ui(self):
        # Top bar with Help button
        top_bar = ctk.CTkFrame(self.root, height=50, corner_radius=0)
        top_bar.pack(fill="x", side="top")
        top_bar.pack_propagate(False)

        ctk.CTkLabel(top_bar, text="Writing Practice Tool", font=ctk.CTkFont(size=24, weight="bold")).pack(side="left", padx=20, pady=10)

        ctk.CTkButton(top_bar, text="Help", width=120, fg_color="#2196F3", command=self.show_help).pack(side="right", padx=20, pady=10)

        main_container = ctk.CTkFrame(self.root, corner_radius=0, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)

        # Mode & Timer
        mode_card = ctk.CTkFrame(main_container, corner_radius=15)
        mode_card.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(mode_card, text="Select Exam & Time", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=(12, 8))

        self.mode_var = ctk.StringVar(value="40")

        radio_frame = ctk.CTkFrame(mode_card, fg_color="transparent")
        radio_frame.pack(pady=8, padx=20, anchor="w")

        ctk.CTkRadioButton(radio_frame, text="20 minutes – IELTS Academic Task 1", variable=self.mode_var, value="20").pack(side="left", padx=25)
        ctk.CTkRadioButton(radio_frame, text="40 minutes – IELTS Task 2", variable=self.mode_var, value="40").pack(side="left", padx=25)
        ctk.CTkRadioButton(radio_frame, text="30 minutes – Tolimo Writing", variable=self.mode_var, value="30").pack(side="left", padx=25)

        self.timer_label = ctk.CTkLabel(mode_card, text="Timer: --:--", font=ctk.CTkFont(size=28, weight="bold"))
        self.timer_label.pack(pady=12)

        timer_controls = ctk.CTkFrame(mode_card, fg_color="transparent")
        timer_controls.pack(pady=(0, 12))
        ctk.CTkButton(timer_controls, text="Start Timer", width=120, fg_color="#4CAF50", command=self.start_timer).pack(side="left", padx=10)
        ctk.CTkButton(timer_controls, text="Stop Timer", width=120, fg_color="#f44336", command=self.stop_timer).pack(side="left", padx=10)

        # Topic Section
        topic_card = ctk.CTkFrame(main_container, corner_radius=15)
        topic_card.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(topic_card, text="Topic / Question", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=(12, 8))

        self.topic_entry = ctk.CTkEntry(topic_card, height=40, font=ctk.CTkFont(size=14), placeholder_text="Enter your topic/question here...")
        self.topic_entry.pack(fill="x", padx=20, pady=(0, 10))

        topic_btn_frame = ctk.CTkFrame(topic_card, fg_color="transparent")
        topic_btn_frame.pack(pady=(0, 12), padx=20)

        ctk.CTkButton(topic_btn_frame, text="Fetch Random Topic (Task 2 only)", width=220, command=self.fetch_random_topic_threaded).pack(side="left", padx=5)
        ctk.CTkButton(topic_btn_frame, text="Apply Topic", width=140, fg_color="#2196F3", command=self.apply_topic).pack(side="left", padx=5)

        # Main Content
        self.content_frame = ctk.CTkFrame(main_container)
        self.content_frame.pack(fill="both", expand=True, pady=(0, 20))

        # Full-width layout
        self.full_writing_card = ctk.CTkFrame(self.content_frame, corner_radius=15)

        ctk.CTkLabel(self.full_writing_card, text="Write Your Response", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=(12, 8))

        full_scroll_frame = ctk.CTkFrame(self.full_writing_card)
        full_scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.full_text_box = ctk.CTkTextbox(full_scroll_frame, font=ctk.CTkFont(size=14), wrap="word")
        self.full_text_box.pack(side="left", fill="both", expand=True)

        full_scrollbar = ctk.CTkScrollbar(full_scroll_frame, command=self.full_text_box.yview)
        full_scrollbar.pack(side="right", fill="y")
        self.full_text_box.configure(yscrollcommand=full_scrollbar.set)

        self.full_status = ctk.CTkFrame(self.full_writing_card, fg_color="transparent")
        self.full_status.pack(fill="x", padx=20, pady=(0, 15))

        self.full_word_label = ctk.CTkLabel(self.full_status, text="Word Count: 0", font=ctk.CTkFont(size=14, weight="bold"), text_color="gray")
        self.full_word_label.pack(side="left")

        ctk.CTkLabel(self.full_status, text="Paragraph Quality:", font=ctk.CTkFont(size=12)).pack(side="left", padx=(40, 5))

        self.full_paragraph_indicators_frame = ctk.CTkFrame(self.full_status, fg_color="transparent")
        self.full_paragraph_indicators_frame.pack(side="left")
        self.full_paragraph_indicators = []

        # Side-by-side layout
        self.side_frame = ctk.CTkFrame(self.content_frame)

        self.figure_card = ctk.CTkFrame(self.side_frame, corner_radius=15)
        self.figure_card.pack(side="left", fill="both", expand=True, padx=(0, 10))

        ctk.CTkLabel(self.figure_card, text="Diagram / Chart for Task 1", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=(12, 8))

        figure_input = ctk.CTkFrame(self.figure_card, fg_color="transparent")
        figure_input.pack(fill="x", padx=20, pady=(0, 10))

        self.figure_entry = ctk.CTkEntry(figure_input, height=40, placeholder_text="Paste image URL or browse local file")
        self.figure_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkButton(figure_input, text="Load from URL", width=150, command=self.load_figure_from_url).pack(side="left", padx=5)
        ctk.CTkButton(figure_input, text="Browse Local File", width=180, command=self.browse_and_load_image).pack(side="left", padx=5)

        zoom_frame = ctk.CTkFrame(self.figure_card, fg_color="transparent")
        zoom_frame.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkButton(zoom_frame, text="Magnify Image", width=140, command=self.zoom_image).pack(side="left", padx=5)
        ctk.CTkButton(zoom_frame, text="Reset Size", width=140, command=self.reset_image_size).pack(side="left", padx=5)

        self.figure_label = ctk.CTkLabel(self.figure_card, text="No diagram loaded", image=None)
        self.figure_label.pack(fill="both", expand=True, padx=20, pady=10)

        self.side_writing_card = ctk.CTkFrame(self.side_frame, corner_radius=15)
        self.side_writing_card.pack(side="right", fill="both", expand=True)

        ctk.CTkLabel(self.side_writing_card, text="Write Your Response", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=(12, 8))

        side_scroll_frame = ctk.CTkFrame(self.side_writing_card)
        side_scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.side_text_box = ctk.CTkTextbox(side_scroll_frame, font=ctk.CTkFont(size=14), wrap="word")
        self.side_text_box.pack(side="left", fill="both", expand=True)

        side_scrollbar = ctk.CTkScrollbar(side_scroll_frame, command=self.side_text_box.yview)
        side_scrollbar.pack(side="right", fill="y")
        self.side_text_box.configure(yscrollcommand=side_scrollbar.set)

        self.side_status = ctk.CTkFrame(self.side_writing_card, fg_color="transparent")
        self.side_status.pack(fill="x", padx=20, pady=(0, 15))

        self.side_word_label = ctk.CTkLabel(self.side_status, text="Word Count: 0", font=ctk.CTkFont(size=14, weight="bold"), text_color="gray")
        self.side_word_label.pack(side="left")

        ctk.CTkLabel(self.side_status, text="Paragraph Quality:", font=ctk.CTkFont(size=12)).pack(side="left", padx=(40, 5))

        self.side_paragraph_indicators_frame = ctk.CTkFrame(self.side_status, fg_color="transparent")
        self.side_paragraph_indicators_frame.pack(side="left")
        self.side_paragraph_indicators = []

        # Bottom buttons
        bottom = ctk.CTkFrame(main_container, fg_color="transparent")
        bottom.pack(fill="x")
        ctk.CTkButton(bottom, text="Copy Response", width=160, fg_color="#4CAF50", command=self.copy_response).pack(side="left", padx=10, pady=10)
        ctk.CTkButton(bottom, text="Clear Response", width=160, fg_color="#f44336", command=self.clear_response).pack(side="left", padx=10, pady=10)

        # Initial layout
        self.full_writing_card.pack(fill="both", expand=True)
        self.side_frame.pack_forget()

        self.active_text_box = self.full_text_box
        self.active_word_label = self.full_word_label
        self.active_paragraph_indicators_frame = self.full_paragraph_indicators_frame
        self.active_paragraph_indicators = self.full_paragraph_indicators

        self.mode_var.trace("w", self.on_mode_change)
        self.on_mode_change()

        self.full_text_box.bind("<KeyRelease>", lambda e: self.root.after(1000, self.schedule_analysis))
        self.side_text_box.bind("<KeyRelease>", lambda e: self.root.after(1000, self.schedule_analysis))

        self.setup_context_menu()

    def setup_context_menu(self):
        self.context_menu = Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Copy", command=self.context_copy)
        self.context_menu.add_command(label="Paste", command=lambda: self.context_paste() if not self.is_frozen else None)
        self.context_menu.add_command(label="Select All", command=self.context_select_all)

        def show_context_menu(event):
            if not self.is_frozen:
                self.context_menu.tk_popup(event.x_root, event.y_root)

        self.full_text_box.bind("<Button-3>", show_context_menu)
        self.side_text_box.bind("<Button-3>", show_context_menu)
        self.topic_entry.bind("<Button-3>", show_context_menu)

    def context_copy(self):
        try:
            self.active_text_box.event_generate("<<Copy>>")
        except:
            pass

    def context_paste(self):
        if not self.is_frozen:
            try:
                self.active_text_box.event_generate("<<Paste>>")
            except:
                pass

    def context_select_all(self):
        self.active_text_box.tag_add("sel", "1.0", "end")

    def on_mode_change(self, *args):
        mode = self.mode_var.get()
        if mode == "20":
            self.full_writing_card.pack_forget()
            self.side_frame.pack(fill="both", expand=True)

            content = self.full_text_box.get("1.0", "end")
            self.side_text_box.delete("1.0", "end")
            self.side_text_box.insert("1.0", content)

            self.active_text_box = self.side_text_box
            self.active_word_label = self.side_word_label
            self.active_paragraph_indicators_frame = self.side_paragraph_indicators_frame
            self.active_paragraph_indicators = self.side_paragraph_indicators

            if self.first_task1_selection:
                guidance = (
                    "You are now in IELTS Academic Task 1 mode (20 minutes).\n\n"
                    "Instructions:\n"
                    "1. Enter the full Task 1 question above.\n"
                    "2. Click 'Apply Topic'.\n"
                    "3. Load the diagram using URL or local file.\n\n"
                    "The image appears on the left, writing area on the right — both visible simultaneously.\n\n"
                    "Use 'Magnify Image' to zoom in for details, and 'Reset Size' to return to normal.\n\n"
                    "Press 'Start Timer' when ready."
                )
                CTkMessagebox(title="IELTS Task 1 Mode", message=guidance, icon="info", option_1="Understood")
                self.first_task1_selection = False
        else:
            self.side_frame.pack_forget()
            self.full_writing_card.pack(fill="both", expand=True)

            content = self.side_text_box.get("1.0", "end")
            self.full_text_box.delete("1.0", "end")
            self.full_text_box.insert("1.0", content)

            self.active_text_box = self.full_text_box
            self.active_word_label = self.full_word_label
            self.active_paragraph_indicators_frame = self.full_paragraph_indicators_frame
            self.active_paragraph_indicators = self.full_paragraph_indicators

            self.figure_label.configure(image=None, text="No diagram loaded")
            self.original_pil_image = None
            self.is_zoomed = False

    def browse_and_load_image(self):
        file_path = filedialog.askopenfilename(
            title="Select Task 1 Diagram / Chart",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.gif *.bmp *.webp *.tiff")]
        )
        if not file_path:
            return
        try:
            img = Image.open(file_path)
            self.load_image(img)
            CTkMessagebox(title="Success", message="Diagram loaded successfully.", icon="check")
        except Exception as e:
            CTkMessagebox(title="Error", message=f"Failed to load image:\n{str(e)}", icon="cancel")

    def load_figure_from_url(self):
        url = self.figure_entry.get().strip()
        if not url:
            CTkMessagebox(title="Error", message="Please enter an image URL.", icon="cancel")
            return
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            img = Image.open(io.BytesIO(resp.content))
            self.load_image(img)
            CTkMessagebox(title="Success", message="Diagram loaded successfully.", icon="check")
        except Exception as e:
            CTkMessagebox(title="Error", message=f"Failed to load image:\n{str(e)}", icon="cancel")

    def load_image(self, pil_img):
        self.original_pil_image = pil_img.copy()
        self.display_image(pil_img)
        self.is_zoomed = False

    def display_image(self, pil_img):
        max_width = 650
        max_height = 700
        display_img = pil_img.copy()
        if display_img.width > max_width or display_img.height > max_height:
            display_img.thumbnail((max_width, max_height), Image.LANCZOS)

        self.current_image = ctk.CTkImage(light_image=display_img, dark_image=display_img, size=display_img.size)
        self.figure_label.configure(image=self.current_image, text="")
        self.figure_label.image = self.current_image

    def zoom_image(self):
        if not self.original_pil_image or self.is_zoomed:
            return
        zoomed = self.original_pil_image.copy()
        new_width = int(zoomed.width * 1.8)
        new_height = int(zoomed.height * 1.8)
        zoomed = zoomed.resize((new_width, new_height), Image.LANCZOS)

        self.current_image = ctk.CTkImage(light_image=zoomed, dark_image=zoomed, size=(new_width, new_height))
        self.figure_label.configure(image=self.current_image, text="")
        self.figure_label.image = self.current_image
        self.is_zoomed = True

    def reset_image_size(self):
        if not self.original_pil_image or not self.is_zoomed:
            return
        self.display_image(self.original_pil_image)
        self.is_zoomed = False

    def update_word_count_and_paragraph_quality(self):
        content = self.active_text_box.get("1.0", "end").strip()
        if content == self.last_content:
            return
        self.last_content = content

        parts = content.split('='*70, 1)
        user_text = parts[1].strip() if len(parts) > 1 else content

        words = len(user_text.split())
        mins = int(self.mode_var.get())
        target = 150 if mins == 20 else 250
        if words >= target:
            self.active_word_label.configure(text=f"Word Count: {words} (target reached)", text_color="#4CAF50")
        else:
            self.active_word_label.configure(text=f"Word Count: {words}", text_color="gray")

        paragraphs = [p.strip() for p in user_text.split('\n\n') if p.strip()]

        for widget in self.active_paragraph_indicators_frame.winfo_children():
            widget.destroy()
        self.active_paragraph_indicators.clear()

        for para in paragraphs:
            para_words = len(para.split())
            if para_words < 30:
                color = "#f44336"
            elif para_words > 120:
                color = "#FF5722"
            else:
                try:
                    result = self.classifier(
                        para,
                        candidate_labels=["excellent writing", "good writing", "average writing", "weak writing"],
                        hypothesis_template="This paragraph shows {}."
                    )
                    top = result['labels'][0]
                    color = "#4CAF50" if top == "excellent writing" else "#8BC34A" if top == "good writing" else "#FFC107" if top == "average writing" else "#f44336"
                except:
                    color = "#9E9E9E"

            indicator = ctk.CTkFrame(self.active_paragraph_indicators_frame, width=24, height=24, corner_radius=6, fg_color=color)
            indicator.pack(side="left", padx=4)
            self.active_paragraph_indicators.append(indicator)

    def schedule_analysis(self):
        self.root.after(1000, self.update_word_count_and_paragraph_quality)

    def fetch_random_topic_threaded(self):
        threading.Thread(target=self.fetch_random_topic, daemon=True).start()

    def fetch_random_topic(self):
        if self.mode_var.get() != "40":
            CTkMessagebox(title="Information", message="Random topic fetching is available only for IELTS Task 2 (40 minutes).", icon="info")
            return

        attempts = 0
        while attempts < 15:
            page = random.randint(1, 2050)
            url = "https://engnovate.com/ugc-ielts-writing-task-2-topics/" if page == 1 else f"https://engnovate.com/ugc-ielts-writing-task-2-topics/page/{page}/"
            try:
                headers = {"User-Agent": "Mozilla/5.0"}
                r = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(r.content, 'html.parser')
                main = soup.find('div', class_='site-content') or soup.body  # ← Fixed line
                candidates = [t.strip() for t in main.get_text(separator='\n').split('\n') if t.strip().endswith('?') and 40 < len(t.strip()) < 300]
                new = [t for t in candidates if t not in self.used_topics]
                if new:
                    topic = random.choice(new)
                    self.root.after(0, lambda t=topic: (self.topic_entry.delete(0, "end"), self.topic_entry.insert(0, t)))
                    self.root.after(0, lambda: CTkMessagebox(title="Success", message=f"New topic loaded:\n\n{topic}", icon="check"))
                    return
            except:
                pass
            attempts += 1
        self.root.after(0, lambda: CTkMessagebox(title="Not Found", message="No new topics found. Please try again later.", icon="warning"))

    def apply_topic(self):
        topic = self.topic_entry.get().strip()
        if not topic:
            CTkMessagebox(title="Error", message="Please enter a topic first.", icon="cancel")
            return
        self.active_text_box.delete("1.0", "end")
        self.active_text_box.insert("1.0", f"{topic}\n\n{'='*70}\n\n")
        self.save_used_topic(topic)
        CTkMessagebox(title="Applied", message="Topic applied successfully. You may now begin writing.", icon="check")

    def start_timer(self):
        if self.timer_running:
            return
        mins = int(self.mode_var.get())
        self.remaining_seconds = mins * 60
        self.timer_running = True
        self.warning_5min_shown = False
        self.warning_3min_shown = False

        def countdown():
            while self.remaining_seconds > 0 and self.timer_running:
                m, s = divmod(self.remaining_seconds, 60)
                self.root.after(0, lambda t=f"Timer: {m:02d}:{s:02d}": self.timer_label.configure(text=t))

                if mins in (30, 40) and self.remaining_seconds == 300 and not self.warning_5min_shown:
                    self.root.after(0, lambda: self.timer_label.configure(fg_color="#FF9800", text_color="white"))
                    self.root.after(0, lambda: CTkMessagebox(title="Proofreading Time", message="Last 5 minutes remaining.\nIt is recommended to begin proofreading.", icon="info"))
                    self.warning_5min_shown = True

                if self.remaining_seconds == 180 and not self.warning_3min_shown:
                    self.root.after(0, lambda: self.timer_label.configure(fg_color="#f44336", text_color="white"))
                    self.root.after(0, lambda: CTkMessagebox(title="Final Check", message="Last 3 minutes remaining.\nTime for a final review.", icon="warning"))
                    self.warning_3min_shown = True

                time.sleep(1)
                self.remaining_seconds -= 1

            if self.timer_running:
                self.root.after(0, lambda: self.timer_label.configure(text="TIME'S UP!", fg_color="#212121", text_color="white"))
                self.root.after(0, lambda: self.active_text_box.configure(state="disabled"))
                self.root.after(0, lambda: CTkMessagebox(title="Time Expired", message="Time has finished. Your response is now frozen.", icon="check"))
                self.is_frozen = True

            self.timer_running = False

        threading.Thread(target=countdown, daemon=True).start()

    def stop_timer(self):
        self.timer_running = False
        self.timer_label.configure(text="Timer: --:--", fg_color="transparent", text_color="gray")
        self.active_text_box.configure(state="normal")
        self.is_frozen = False

    def copy_response(self):
        content = self.active_text_box.get("1.0", "end").strip()
        parts = content.split('='*70, 1)
        user_text = parts[1].strip() if len(parts) > 1 else content
        topic = parts[0].strip().split('\n')[0] if len(parts) > 1 else "No topic"
        full = f"Topic: {topic}\n\nResponse:\n{user_text}"
        self.root.clipboard_clear()
        self.root.clipboard_append(full)
        CTkMessagebox(title="Copied", message="Topic and response copied to clipboard.", icon="check")

    def clear_response(self):
        content = self.active_text_box.get("1.0", "end")
        parts = content.split('='*70, 1)
        if len(parts) > 1:
            self.active_text_box.delete("1.0", "end")
            self.active_text_box.insert("1.0", parts[0] + "\n\n" + "="*70 + "\n\n")
        else:
            self.active_text_box.delete("1.0", "end")

    def on_closing(self):
        self.timer_running = False
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = IELTSWritingApp()
    app.run()
