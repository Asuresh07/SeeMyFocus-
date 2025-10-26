import cv2
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import time
import json
import os
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib
matplotlib.use('TkAgg')

try:
    import pyttsx3
    TTS_AVAILABLE = True
except:
    TTS_AVAILABLE = False

class SeeMyFocusApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SeeMyFocus - AI Focus Coach")
        self.root.geometry("1400x800")
        
        # Dark mode setup
        self.dark_mode = tk.BooleanVar(value=False)
        self.dark_mode.trace_add('write', lambda *args: self.on_dark_mode_change())
        self.setup_theme()
        
        self.current_screen = "home"
        self.cap = None
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        
        # Enhanced eye tracking - focused on eye gaze, not head movement
        self.eye_history = []
        self.eye_history_length = 15  # Longer history for smoother tracking
        self.gaze_deviation_threshold = 25  # LOWERED - more strict, catches side-eyeing
        self.looking_away_frames = 0
        self.looking_away_threshold = 8  # More frames needed to register looking away
        
        # Session variables
        self.session_active = False
        self.session_start_time = None
        self.session_id = None
        self.session_task = ""
        self.session_mood = ""
        self.ai_coaching_plan = ""
        
        # Pomodoro-style session management
        self.focus_cycle_duration = 20 * 60  # 20 minutes in seconds
        self.break_cycle_duration = 5 * 60   # 5 minutes in seconds
        self.current_cycle_type = "focus"  # "focus" or "break"
        self.cycle_start_time = None
        self.cycles_completed = 0
        
        # NEW: Off-screen / Paper Mode
        self.offscreen_mode = tk.BooleanVar(value=False)
        
        # NEW: Persistent streak counter
        self.persistent_streak_count = 0  # Total streak across sessions
        self.session_cycles = 0  # Cycles in current session only
        
        self.coaching_style = tk.StringVar(value="Gentle")
        self.privacy_shield = tk.BooleanVar(value=True)
        self.audio_cues = tk.BooleanVar(value=True)
        self.ai_sponsor = "Claude"
        
        self.tts_engine = None
        if TTS_AVAILABLE:
            try:
                self.tts_engine = pyttsx3.init()
                self.tts_engine.setProperty('rate', 150)
                self.tts_engine.setProperty('volume', 0.7)
            except:
                self.tts_engine = None
        
        # Focus tracking with buffer
        self.current_state = "Away"
        self.streak_time_sec = 0
        self.streak_count = 0
        self.longest_streak = 0
        self.wellness_points = 0
        self.focus_score = 0
        self.focused_frames = 0
        self.total_frames = 0
        self.deep_work_meter = 0
        self.last_audio_cue = 0
        
        # Gamification with XP rewards
        self.level = 1
        self.xp = 0
        self.xp_to_next_level = 100
        self.total_sessions = 0
        self.lifetime_wellness = 0
        self.health_streak = 0
        
        # XP rewards system
        self.xp_rewards = {
            "complete_cycle": 50,
            "maintain_focus_10min": 25,
            "take_break": 20,
            "complete_session": 100,
            "perfect_focus": 150
        }
        
        # NEW: Achievement system
        self.achievements = {
            "first_session": {"unlocked": False, "title": "First Steps", "description": "Complete your first session"},
            "focus_master": {"unlocked": False, "title": "Focus Master", "description": "Reach 10 cycle streak"},
            "wellness_warrior": {"unlocked": False, "title": "Wellness Warrior", "description": "Earn 500 wellness points"},
            "level_5": {"unlocked": False, "title": "Rising Star", "description": "Reach level 5"},
            "perfect_day": {"unlocked": False, "title": "Perfect Day", "description": "Complete 5 cycles in one session"},
            "streak_legend": {"unlocked": False, "title": "Streak Legend", "description": "Maintain 20 cycle streak"}
        }
        
        self.break_start_time = None
        self.total_break_time = 0
        self.eligible_for_break_reward = False
        self.break_rewarded = False
        
        self.eyes_detected_count = 0
        self.no_eyes_count = 0
        self.eye_detection_threshold = 3
        
        # Enhanced buffer system - more forgiving (INCREASED FROM 3 to 5 seconds)
        self.away_buffer_start = None
        self.return_buffer_start = None
        self.last_state = "Away"
        self.streak_start_time = None
        self.distraction_buffer = 5.0  # 5 second buffer before breaking streak
        self.distraction_start_time = None
        
        self.focus_timeline = []
        self.timeline_interval = 5
        self.last_timeline_update = None
        
        # Unfocus reminder system
        self.last_reminder_time = None
        self.reminder_cooldown = 30  # Remind every 30 seconds when unfocused
        self.reminder_count = 0
        
        self.FOCUS_TIME_REQUIRED = 60
        self.BREAK_TIME_REQUIRED = 15
        self.AWAY_BUFFER = 2.0  # Increased buffer time
        self.RETURN_BUFFER = 1.0
        self.TOO_CLOSE_THRESHOLD = 0.35
        self.AUDIO_CUE_INTERVAL = 1200
        
        self.session_data = {}
        self.history_file = "seemyfocus_history.json"
        self.session_history = []
        
        self.load_user_progress()
        self.load_session_history()
        self.setup_home_screen()
        
    def setup_theme(self):
        """Setup color theme based on dark mode"""
        if self.dark_mode.get():
            self.bg_color = '#1a1a1a'
            self.fg_color = '#ffffff'
            self.card_bg = '#2d2d2d'
            self.accent_color = '#3b82f6'
            self.text_secondary = '#a0a0a0'
        else:
            self.bg_color = '#f5f7fa'
            self.fg_color = '#111827'
            self.card_bg = '#ffffff'
            self.accent_color = '#3b82f6'
            self.text_secondary = '#6b7280'
        
        self.root.configure(bg=self.bg_color)
    
    def on_dark_mode_change(self):
        """Handle dark mode change via trace"""
        self.setup_theme()
        
        # Refresh current screen
        if self.current_screen == "home":
            self.setup_home_screen()
        elif self.current_screen == "main":
            self.setup_main_screen()
        elif self.current_screen == "history":
            self.setup_history_screen()
        elif self.current_screen == "settings":
            self.setup_settings_screen()
        elif self.current_screen == "achievements":
            self.setup_achievements_screen()
        
        self.save_user_progress()
    
    def load_user_progress(self):
        if os.path.exists("seemyfocus_progress.json"):
            try:
                with open("seemyfocus_progress.json", "r") as f:
                    data = json.load(f)
                    self.level = data.get("level", 1)
                    self.xp = data.get("xp", 0)
                    self.xp_to_next_level = data.get("xp_to_next_level", 100)
                    self.total_sessions = data.get("total_sessions", 0)
                    self.lifetime_wellness = data.get("lifetime_wellness", 0)
                    self.coaching_style.set(data.get("coaching_style", "Gentle"))
                    self.privacy_shield.set(data.get("privacy_shield", True))
                    self.audio_cues.set(data.get("audio_cues", True))
                    self.health_streak = data.get("health_streak", 0)
                    self.dark_mode.set(data.get("dark_mode", False))
                    self.persistent_streak_count = data.get("persistent_streak_count", 0)
                    self.achievements = data.get("achievements", self.achievements)
            except:
                pass
    
    def save_user_progress(self):
        data = {
            "level": self.level,
            "xp": self.xp,
            "xp_to_next_level": self.xp_to_next_level,
            "total_sessions": self.total_sessions,
            "lifetime_wellness": self.lifetime_wellness,
            "coaching_style": self.coaching_style.get(),
            "privacy_shield": self.privacy_shield.get(),
            "audio_cues": self.audio_cues.get(),
            "health_streak": self.health_streak,
            "dark_mode": self.dark_mode.get(),
            "persistent_streak_count": self.persistent_streak_count,
            "achievements": self.achievements
        }
        with open("seemyfocus_progress.json", "w") as f:
            json.dump(data, f, indent=2)
    
    def load_session_history(self):
        """Load session history from file"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r") as f:
                    self.session_history = json.load(f)
            except:
                self.session_history = []
    
    def save_session_history(self):
        """Save session history to file"""
        with open(self.history_file, "w") as f:
            json.dump(self.session_history, f, indent=2)
    
    def add_xp(self, amount, reason=""):
        """Add XP with level up system"""
        self.xp += amount
        
        # Check for level up
        while self.xp >= self.xp_to_next_level:
            self.xp -= self.xp_to_next_level
            self.level += 1
            self.xp_to_next_level = int(self.xp_to_next_level * 1.5)
            self.show_level_up_notification()
            self.check_achievements()  # Check for level achievements
        
        self.save_user_progress()
    
    def show_level_up_notification(self):
        """Show level up notification"""
        if hasattr(self, 'motivation_label'):
            self.update_motivation(f"🎉 LEVEL UP! You're now Level {self.level}!")
    
    def get_xp_rewards_info(self):
        """Return info about XP rewards - UPDATED"""
        return """
XP REWARDS:
• Complete 20min Focus Cycle: +50 XP
• Maintain Focus for 10min: +25 XP
• Take 5min Break: +20 XP
• Complete Full Session: +100 XP
• Perfect Focus Score: +150 XP

STREAK SYSTEM:
• 1 Cycle = 1 Focus Period + 1 Break Period
• Streaks persist across sessions
• Only broken by distraction during focus time
• 5-second buffer before streak breaks

WELLNESS POINTS:
• Earned for taking healthy breaks
• Shows balance between focus and rest
• Contributes to overall wellness tracking

PAPER MODE:
• For off-screen work (handwritten, reading papers)
• Tracks presence, not direct eye gaze
• Won't break streak for looking away from screen

Level up to unlock achievements and track your progress!
        """
    
    def generate_ai_coaching_plan(self, task, mood):
        """Generate AI coaching plan based on task and mood"""
        plans = {
            "focused": {
                "homework": "Great! You're feeling focused. Let's use the Pomodoro technique: Focus for 20 minutes on your homework, then take a 5-minute break. I'll track your progress and keep you accountable!",
                "work": "Perfect mindset for productivity! Work for 20 focused minutes, break for 5. I'll help you maintain this momentum.",
                "reading": "Excellent! Deep work mode activated. Read for 20 minutes with full attention, rest your eyes for 5.",
                "coding": "Let's code! 20 minutes of focused coding, 5 minute break to prevent burnout. I've got your back.",
                "studying": "Ready to learn! Study intensely for 20 minutes, brain break for 5. Repeat the cycle for best retention."
            },
            "distracted": {
                "homework": "I see you're feeling distracted. No worries! Let's start with shorter 15-minute focus blocks. I'll gently remind you if you drift off. We'll build your focus muscle together!",
                "work": "Distractions happen! Let's use the 2-Minute Rule: Start with just 2 minutes of work. Often, starting is the hardest part. I'll support you through this!",
                "reading": "Feeling scattered? Try the 'One Page at a Time' method. Focus on just one page. I'll help you stay present.",
                "coding": "Let's break it down. Focus on one small function at a time. 15-minute sprints with gentle reminders when needed.",
                "studying": "Distracted mind? Let's try active recall. Study for 10 minutes, quiz yourself for 5. I'll keep you engaged!"
            },
            "tired": {
                "homework": "Feeling tired? Let's work with your energy. 15 minutes of work, 10 minute break. Prioritize the hardest tasks first while you have energy.",
                "work": "Low energy detected. Let's do 15-minute work blocks with longer 10-minute breaks. Stay hydrated!",
                "reading": "Tired eyes? Use the 15/10 method. Read for 15, rest for 10. Consider standing or walking while reading.",
                "coding": "Fatigue impacts code quality. Let's do 15-minute focused coding with 10-minute breaks. Perfect time for debugging, not new features.",
                "studying": "Energy is low. Study the most important topics first. 15 on, 10 off. Take breaks seriously!"
            },
            "motivated": {
                "homework": "Amazing energy! Let's channel it! 25-minute deep work sessions with 5-minute breaks. You're going to crush this homework!",
                "work": "That motivation is gold! 25-minute sprints, 5-minute recovery. Let's maximize this productive state!",
                "reading": "Motivated to learn! 25 minutes of reading, 5 to reflect. I'll track your amazing progress!",
                "coding": "Let's code! With this energy, try 25-minute deep coding sessions. You'll be amazed at what you accomplish!",
                "studying": "Perfect! 25-minute study sprints with 5-minute active breaks. Your brain is ready to absorb information!"
            }
        }
        
        mood_key = mood.lower()
        task_key = task.lower()
        
        # Find matching plan
        for mood_pattern in plans:
            if mood_pattern in mood_key:
                for task_pattern in plans[mood_pattern]:
                    if task_pattern in task_key:
                        return plans[mood_pattern][task_pattern]
        
        # Default plan
        return f"Let's focus on {task}! I'll guide you through 20-minute focus blocks with 5-minute breaks. I'm here to keep you on track!"
    
    def show_ai_coach_popup(self):
        """Show AI coach popup with session plan - IMPROVED"""
        popup = tk.Toplevel(self.root)
        popup.title("🤖 AI Coach - Your Session Plan")
        popup.geometry("650x450")
        popup.configure(bg=self.card_bg)
        
        # Make popup modal
        popup.transient(self.root)
        popup.grab_set()
        
        # Header
        header = tk.Label(popup, text="🎯 Your Personalized Focus Plan",
                         font=("Helvetica", 18, "bold"),
                         bg=self.card_bg, fg=self.fg_color)
        header.pack(pady=20)
        
        # Task and mood info
        info_frame = tk.Frame(popup, bg=self.card_bg)
        info_frame.pack(pady=10)
        
        tk.Label(info_frame, text=f"📝 Task: {self.session_task}",
                font=("Helvetica", 12),
                bg=self.card_bg, fg=self.fg_color).pack()
        
        tk.Label(info_frame, text=f"😊 Mood: {self.session_mood}",
                font=("Helvetica", 12),
                bg=self.card_bg, fg=self.fg_color).pack()
        
        # AI Coaching plan
        plan_frame = tk.Frame(popup, bg=self.bg_color, relief=tk.SOLID, borderwidth=1)
        plan_frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)
        
        plan_text = tk.Text(plan_frame, wrap=tk.WORD, font=("Helvetica", 11),
                           bg=self.bg_color, fg=self.fg_color,
                           padx=15, pady=15, height=8)
        plan_text.pack(fill=tk.BOTH, expand=True)
        plan_text.insert(1.0, self.ai_coaching_plan)
        plan_text.config(state=tk.DISABLED)
        
        # IMPROVED Start button - larger, more prominent
        start_btn = tk.Button(popup, text="🚀 START SESSION NOW",
                             command=popup.destroy,
                             font=("Helvetica", 16, "bold"),
                             bg="#22c55e", fg="white",
                             padx=40, pady=15, relief=tk.FLAT,
                             cursor="hand2",
                             activebackground="#16a34a")
        start_btn.pack(pady=25)
    
    def show_unfocus_reminder(self):
        """Show reminder popup when user is unfocused"""
        current_time = time.time()
        
        # Check cooldown
        if self.last_reminder_time and (current_time - self.last_reminder_time) < self.reminder_cooldown:
            return
        
        self.last_reminder_time = current_time
        self.reminder_count += 1
        
        # Create non-intrusive reminder
        reminder = tk.Toplevel(self.root)
        reminder.title("Focus Reminder")
        reminder.geometry("400x200")
        reminder.configure(bg="#fef3c7")
        
        # Position in top right
        screen_width = self.root.winfo_screenwidth()
        reminder.geometry(f"+{screen_width-420}+20")
        
        messages = [
            "👀 Hey! Your focus drifted. Let's get back on track!",
            "⚡ Quick reminder: Your task awaits!",
            "🎯 Refocus! You've got this!",
            "💪 Your streak is waiting! Come back!",
            "🌟 Stay strong! You're doing great!"
        ]
        
        message = messages[self.reminder_count % len(messages)]
        
        tk.Label(reminder, text="🔔 Focus Coach",
                font=("Helvetica", 14, "bold"),
                bg="#fef3c7", fg="#92400e").pack(pady=15)
        
        tk.Label(reminder, text=message,
                font=("Helvetica", 12),
                bg="#fef3c7", fg="#92400e",
                wraplength=350).pack(pady=10)
        
        # XP penalty info
        xp_lost = 5
        self.xp = max(0, self.xp - xp_lost)
        
        tk.Label(reminder, text=f"⚠️ -{xp_lost} XP",
                font=("Helvetica", 10),
                bg="#fef3c7", fg="#dc2626").pack()
        
        # Auto close after 3 seconds
        reminder.after(3000, reminder.destroy)
    
    def setup_home_screen(self):
        """Enhanced home screen with professional credentials - SCROLLABLE"""
        self.clear_screen()
        self.current_screen = "home"
        
        # Create main container with canvas for scrolling
        container = tk.Frame(self.root, bg=self.bg_color)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Create canvas
        canvas = tk.Canvas(container, bg=self.bg_color, highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        
        # Create scrollable frame
        main_frame = tk.Frame(canvas, bg=self.bg_color)
        
        # Configure canvas
        main_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=main_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add mousewheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Add padding frame
        content_frame = tk.Frame(main_frame, bg=self.bg_color)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=30)
        
        # Header with dark mode toggle
        header_frame = tk.Frame(content_frame, bg=self.bg_color)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(header_frame, text="SeeMyFocus 🎯",
                font=("Helvetica", 32, "bold"),
                bg=self.bg_color, fg=self.fg_color).pack(side=tk.LEFT)
        
        # Dark mode toggle - FIXED
        toggle_frame = tk.Frame(header_frame, bg=self.bg_color)
        toggle_frame.pack(side=tk.RIGHT)
        
        tk.Label(toggle_frame, text="🌙" if not self.dark_mode.get() else "☀️",
                font=("Helvetica", 16),
                bg=self.bg_color, fg=self.fg_color).pack(side=tk.LEFT, padx=5)
        
        dark_mode_btn = tk.Checkbutton(toggle_frame, text="Dark Mode",
                                       variable=self.dark_mode,
                                       font=("Helvetica", 12),
                                       bg=self.bg_color, fg=self.fg_color,
                                       selectcolor=self.card_bg,
                                       activebackground=self.bg_color,
                                       activeforeground=self.fg_color)
        dark_mode_btn.pack(side=tk.LEFT)
        
        tk.Label(content_frame, text="AI-Powered Focus Coach & Wellness Tracker",
                font=("Helvetica", 16),
                bg=self.bg_color, fg=self.text_secondary).pack()
        
        # NEW: Professional Credentials Card
        cred_frame = tk.Frame(content_frame, bg=self.card_bg, relief=tk.RAISED, borderwidth=1)
        cred_frame.pack(pady=15, fill=tk.X)
        
        tk.Label(cred_frame, text="🔒 Privacy & Security",
                font=("Helvetica", 12, "bold"),
                bg=self.card_bg, fg=self.fg_color).pack(pady=(10, 5))
        
        privacy_info = [
            "✓ 100% Local Processing - No cloud, no servers",
            "✓ Zero Data Collection - Your data stays on your device",
            "✓ Open Source Ready - Transparent and trustworthy",
        ]
        
        for info in privacy_info:
            tk.Label(cred_frame, text=info, font=("Helvetica", 10),
                    bg=self.card_bg, fg=self.text_secondary).pack(pady=2)
        
        tk.Label(cred_frame, text="Built with Claude AI | Hackathon 2025",
                font=("Helvetica", 9, "italic"),
                bg=self.card_bg, fg=self.text_secondary).pack(pady=(5, 10))
        
        # Stats card - UPDATED with persistent streak
        stats_card = tk.Frame(content_frame, bg=self.card_bg, relief=tk.RAISED, borderwidth=1)
        stats_card.pack(pady=20, fill=tk.X)
        
        stats_grid = tk.Frame(stats_card, bg=self.card_bg)
        stats_grid.pack(padx=30, pady=20)
        
        stats = [
            ("Level", f"⭐ {self.level}", f"XP: {self.xp}/{self.xp_to_next_level}"),
            ("Sessions", f"📊 {self.total_sessions}", "Total completed"),
            ("Wellness", f"💚 {self.lifetime_wellness}", "Points earned"),
            ("Streak", f"🔥 {self.persistent_streak_count}", "Cycles")
        ]
        
        for i, (label, value, subtitle) in enumerate(stats):
            frame = tk.Frame(stats_grid, bg=self.card_bg)
            frame.grid(row=0, column=i, padx=20)
            
            tk.Label(frame, text=label, font=("Helvetica", 11),
                    bg=self.card_bg, fg=self.text_secondary).pack()
            tk.Label(frame, text=value, font=("Helvetica", 20, "bold"),
                    bg=self.card_bg, fg=self.accent_color).pack()
            tk.Label(frame, text=subtitle, font=("Helvetica", 9),
                    bg=self.card_bg, fg=self.text_secondary).pack()
        
        # Task input with Enter key support
        input_frame = tk.Frame(content_frame, bg=self.bg_color)
        input_frame.pack(pady=20, fill=tk.X)
        
        tk.Label(input_frame, text="What are you working on?",
                font=("Helvetica", 14, "bold"),
                bg=self.bg_color, fg=self.fg_color).pack(anchor=tk.W)
        
        self.task_entry = tk.Entry(input_frame, font=("Helvetica", 12),
                                   bg=self.card_bg, fg=self.fg_color,
                                   relief=tk.SOLID, borderwidth=1,
                                   insertbackground=self.fg_color)
        self.task_entry.pack(fill=tk.X, pady=5, ipady=8)
        self.task_entry.insert(0, "e.g., Homework, Coding, Reading...")
        
        # Bind Enter key
        self.task_entry.bind('<Return>', lambda e: self.on_task_entered())
        self.task_entry.bind('<FocusIn>', lambda e: self.on_task_focus_in())
        
        tk.Label(input_frame, text="💡 Press Enter to get AI coaching suggestions",
                font=("Helvetica", 9, "italic"),
                bg=self.bg_color, fg=self.text_secondary).pack(anchor=tk.W)
        
        # Mood selection
        mood_frame = tk.Frame(content_frame, bg=self.bg_color)
        mood_frame.pack(pady=20, fill=tk.X)
        
        tk.Label(mood_frame, text="How are you feeling right now?",
                font=("Helvetica", 14, "bold"),
                bg=self.bg_color, fg=self.fg_color).pack(anchor=tk.W, pady=(0, 10))
        
        moods = ["😊 Focused", "😵 Distracted", "😴 Tired", "🔥 Motivated"]
        
        mood_buttons_frame = tk.Frame(mood_frame, bg=self.bg_color)
        mood_buttons_frame.pack()
        
        self.selected_mood = tk.StringVar(value="")
        
        for mood in moods:
            btn = tk.Radiobutton(mood_buttons_frame, text=mood,
                                variable=self.selected_mood, value=mood,
                                font=("Helvetica", 12),
                                bg=self.card_bg, fg=self.fg_color,
                                selectcolor=self.accent_color,
                                indicatoron=0, width=12, pady=10,
                                activebackground=self.accent_color,
                                activeforeground="white")
            btn.pack(side=tk.LEFT, padx=5)
        
        # Buttons
        button_frame = tk.Frame(content_frame, bg=self.bg_color)
        button_frame.pack(pady=30)
        
        start_btn = tk.Button(button_frame, text="🚀 Start Focus Session",
                             command=self.start_session_from_home,
                             font=("Helvetica", 16, "bold"),
                             bg=self.accent_color, fg="white",
                             padx=40, pady=15, relief=tk.FLAT,
                             cursor="hand2",
                             activebackground="#2563eb")
        start_btn.pack(side=tk.LEFT, padx=10)
        
        history_btn = tk.Button(button_frame, text="📊 View History",
                               command=self.setup_history_screen,
                               font=("Helvetica", 14),
                               bg=self.card_bg, fg=self.fg_color,
                               padx=30, pady=12, relief=tk.SOLID,
                               borderwidth=1, cursor="hand2")
        history_btn.pack(side=tk.LEFT, padx=10)
        
        # NEW: Additional buttons
        nav_frame = tk.Frame(content_frame, bg=self.bg_color)
        nav_frame.pack(pady=10)
        
        achievements_btn = tk.Button(nav_frame, text="🏆 Achievements",
                                     command=self.setup_achievements_screen,
                                     font=("Helvetica", 12),
                                     bg=self.card_bg, fg=self.fg_color,
                                     padx=20, pady=8, relief=tk.SOLID,
                                     borderwidth=1, cursor="hand2")
        achievements_btn.pack(side=tk.LEFT, padx=5)
        
        settings_btn = tk.Button(nav_frame, text="⚙️ Settings",
                                command=self.setup_settings_screen,
                                font=("Helvetica", 12),
                                bg=self.card_bg, fg=self.fg_color,
                                padx=20, pady=8, relief=tk.SOLID,
                                borderwidth=1, cursor="hand2")
        settings_btn.pack(side=tk.LEFT, padx=5)
        
        # XP rewards info - UPDATED
        xp_info_btn = tk.Button(content_frame, text="ℹ️ How It Works (XP, Streaks, Wellness)",
                               command=self.show_xp_info,
                               font=("Helvetica", 10),
                               bg=self.bg_color, fg=self.text_secondary,
                               relief=tk.FLAT, cursor="hand2")
        xp_info_btn.pack(pady=10)
    
    def on_task_focus_in(self):
        """Clear placeholder text on focus"""
        if self.task_entry.get() == "e.g., Homework, Coding, Reading...":
            self.task_entry.delete(0, tk.END)
    
    def on_task_entered(self):
        """Handle Enter key press on task input"""
        task = self.task_entry.get().strip()
        mood = self.selected_mood.get()
        
        if not task or task == "e.g., Homework, Coding, Reading...":
            messagebox.showwarning("Missing Info", "Please enter what you're working on!")
            return
        
        if not mood:
            messagebox.showwarning("Missing Info", "Please select how you're feeling!")
            return
        
        # Generate AI coaching plan
        self.session_task = task
        self.session_mood = mood
        self.ai_coaching_plan = self.generate_ai_coaching_plan(task, mood)
        
        # Show AI suggestions
        self.show_ai_coach_popup()
    
    def show_xp_info(self):
        """Show XP rewards information - UPDATED"""
        messagebox.showinfo("How SeeMyFocus Works", self.get_xp_rewards_info())
    
    def start_session_from_home(self):
        """Start session with validation"""
        task = self.task_entry.get().strip()
        mood = self.selected_mood.get()
        
        if not task or task == "e.g., Homework, Coding, Reading...":
            messagebox.showwarning("Missing Info", "Please enter what you're working on!")
            return
        
        if not mood:
            messagebox.showwarning("Missing Info", "Please select how you're feeling!")
            return
        
        self.session_task = task
        self.session_mood = mood
        self.ai_coaching_plan = self.generate_ai_coaching_plan(task, mood)
        
        # Show AI coach plan before starting
        self.show_ai_coach_popup()
        
        # Start session
        self.setup_main_screen()
        self.start_session()
    
    def setup_main_screen(self):
        """Enhanced main screen with paper mode and streak counter"""
        self.clear_screen()
        self.current_screen = "main"
        
        main_container = tk.Frame(self.root, bg=self.bg_color)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Video and controls
        left_panel = tk.Frame(main_container, bg=self.bg_color)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header with end session button
        header_frame = tk.Frame(left_panel, bg=self.bg_color)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(header_frame, text="Focus Session",
                font=("Helvetica", 20, "bold"),
                bg=self.bg_color, fg=self.fg_color).pack(side=tk.LEFT)
        
        # IMPROVED End Session Button - better colors
        end_btn = tk.Button(header_frame, text="⏹ End Session",
                           command=self.end_session,
                           font=("Helvetica", 13, "bold"),
                           bg="#ef4444", fg="white",
                           padx=25, pady=10, relief=tk.FLAT,
                           cursor="hand2",
                           activebackground="#dc2626")
        end_btn.pack(side=tk.RIGHT)
        
        # Task and mood display
        info_frame = tk.Frame(left_panel, bg=self.card_bg, relief=tk.RAISED, borderwidth=1)
        info_frame.pack(fill=tk.X, pady=10)
        
        info_content = tk.Frame(info_frame, bg=self.card_bg)
        info_content.pack(padx=15, pady=10)
        
        tk.Label(info_content, text=f"📝 Task: {self.session_task}",
                font=("Helvetica", 11),
                bg=self.card_bg, fg=self.fg_color).pack(anchor=tk.W)
        
        tk.Label(info_content, text=f"😊 Mood: {self.session_mood}",
                font=("Helvetica", 11),
                bg=self.card_bg, fg=self.fg_color).pack(anchor=tk.W)
        
        # NEW: Paper Mode / Off-Screen Mode toggle
        paper_mode_frame = tk.Frame(left_panel, bg=self.card_bg, relief=tk.RAISED, borderwidth=1)
        paper_mode_frame.pack(fill=tk.X, pady=10)
        
        tk.Checkbutton(paper_mode_frame,
                      text="✍️ Paper Mode (Working off-screen)",
                      variable=self.offscreen_mode,
                      command=self.toggle_offscreen_mode,
                      font=("Helvetica", 11, "bold"),
                      bg=self.card_bg, fg=self.fg_color,
                      selectcolor=self.card_bg,
                      activebackground=self.card_bg,
                      padx=10, pady=10).pack()
        
        tk.Label(paper_mode_frame,
                text="Enable for handwritten work or reading papers",
                font=("Helvetica", 9, "italic"),
                bg=self.card_bg, fg=self.text_secondary).pack(pady=(0, 10))
        
        # Video feed
        video_frame = tk.Frame(left_panel, bg=self.card_bg, relief=tk.RAISED, borderwidth=2)
        video_frame.pack(pady=10)
        
        self.video_canvas = tk.Label(video_frame, bg="black")
        self.video_canvas.pack(padx=5, pady=5)
        
        # Status indicator - IMPROVED CLARITY
        status_frame = tk.Frame(left_panel, bg=self.card_bg, relief=tk.RAISED, borderwidth=1)
        status_frame.pack(fill=tk.X, pady=10)
        
        self.status_label = tk.Label(status_frame, text="Ready",
                                     font=("Helvetica", 18, "bold"),
                                     bg=self.card_bg, fg=self.fg_color,
                                     pady=15)
        self.status_label.pack()
        
        # Right panel - Stats and coaching
        right_panel = tk.Frame(main_container, bg=self.bg_color, width=400)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=20, pady=20)
        right_panel.pack_propagate(False)
        
        # XP and Level
        xp_card = tk.Frame(right_panel, bg=self.card_bg, relief=tk.RAISED, borderwidth=1)
        xp_card.pack(fill=tk.X, pady=10)
        
        xp_content = tk.Frame(xp_card, bg=self.card_bg)
        xp_content.pack(padx=20, pady=15)
        
        tk.Label(xp_content, text=f"⭐ Level {self.level}",
                font=("Helvetica", 16, "bold"),
                bg=self.card_bg, fg=self.accent_color).pack()
        
        self.xp_label = tk.Label(xp_content, text=f"XP: {self.xp}/{self.xp_to_next_level}",
                                font=("Helvetica", 12),
                                bg=self.card_bg, fg=self.fg_color)
        self.xp_label.pack(pady=5)
        
        self.xp_progress = ttk.Progressbar(xp_content, length=300, mode='determinate')
        self.xp_progress.pack(pady=5)
        self.xp_progress['value'] = (self.xp / self.xp_to_next_level) * 100
        
        # NEW: Cycle Timer
        timer_card = tk.Frame(right_panel, bg=self.card_bg, relief=tk.RAISED, borderwidth=1)
        timer_card.pack(fill=tk.X, pady=10)
        
        timer_content = tk.Frame(timer_card, bg=self.card_bg)
        timer_content.pack(padx=20, pady=15)
        
        tk.Label(timer_content, text="⏱️ Cycle Timer",
                font=("Helvetica", 14, "bold"),
                bg=self.card_bg, fg=self.fg_color).pack()
        
        self.cycle_timer_label = tk.Label(timer_content, text="00:00",
                                          font=("Helvetica", 28, "bold"),
                                          bg=self.card_bg, fg=self.accent_color)
        self.cycle_timer_label.pack(pady=5)
        
        self.cycle_type_label = tk.Label(timer_content, text="Ready to start",
                                         font=("Helvetica", 11),
                                         bg=self.card_bg, fg=self.text_secondary)
        self.cycle_type_label.pack()
        
        # NEW: Streak Counter Display
        streak_card = tk.Frame(right_panel, bg=self.card_bg, relief=tk.RAISED, borderwidth=1)
        streak_card.pack(fill=tk.X, pady=10)
        
        streak_content = tk.Frame(streak_card, bg=self.card_bg)
        streak_content.pack(padx=20, pady=15)
        
        tk.Label(streak_content, text="🔥 Cycle Streak",
                font=("Helvetica", 14, "bold"),
                bg=self.card_bg, fg=self.fg_color).pack()
        
        self.streak_counter_label = tk.Label(streak_content, 
                                             text=str(self.persistent_streak_count),
                                             font=("Helvetica", 32, "bold"),
                                             bg=self.card_bg, fg="#f59e0b")
        self.streak_counter_label.pack(pady=5)
        
        self.session_cycles_label = tk.Label(streak_content, 
                                             text="This session: 0 cycles",
                                             font=("Helvetica", 10),
                                             bg=self.card_bg, fg=self.text_secondary)
        self.session_cycles_label.pack()
        
        # Stats card - IMPROVED CLARITY
        stats_card = tk.Frame(right_panel, bg=self.card_bg, relief=tk.RAISED, borderwidth=1)
        stats_card.pack(fill=tk.X, pady=10)
        
        stats_content = tk.Frame(stats_card, bg=self.card_bg)
        stats_content.pack(padx=20, pady=15)
        
        tk.Label(stats_content, text="📊 Session Stats",
                font=("Helvetica", 12, "bold"),
                bg=self.card_bg, fg=self.fg_color).pack(pady=(0, 10))
        
        # Stats grid
        stats_grid = tk.Frame(stats_content, bg=self.card_bg)
        stats_grid.pack(fill=tk.X)
        
        # Streak Time
        tk.Label(stats_grid, text="Streak Time:",
                font=("Helvetica", 11, "bold"),
                bg=self.card_bg, fg=self.fg_color).grid(row=0, column=0, sticky=tk.W, pady=3)
        self.streak_time_label = tk.Label(stats_grid, text="0s",
                                          font=("Helvetica", 11),
                                          bg=self.card_bg, fg=self.accent_color)
        self.streak_time_label.grid(row=0, column=1, sticky=tk.E, pady=3)
        
        # Wellness Points
        tk.Label(stats_grid, text="Wellness Points:",
                font=("Helvetica", 11, "bold"),
                bg=self.card_bg, fg=self.fg_color).grid(row=1, column=0, sticky=tk.W, pady=3)
        self.wellness_label = tk.Label(stats_grid, text="0",
                                       font=("Helvetica", 11),
                                       bg=self.card_bg, fg=self.accent_color)
        self.wellness_label.grid(row=1, column=1, sticky=tk.E, pady=3)
        
        # Focus Score
        tk.Label(stats_grid, text="Focus Score:",
                font=("Helvetica", 11, "bold"),
                bg=self.card_bg, fg=self.fg_color).grid(row=2, column=0, sticky=tk.W, pady=3)
        self.focus_score_label = tk.Label(stats_grid, text="0%",
                                          font=("Helvetica", 11),
                                          bg=self.card_bg, fg=self.accent_color)
        self.focus_score_label.grid(row=2, column=1, sticky=tk.E, pady=3)
        
        # Session Time
        tk.Label(stats_grid, text="Session Time:",
                font=("Helvetica", 11, "bold"),
                bg=self.card_bg, fg=self.fg_color).grid(row=3, column=0, sticky=tk.W, pady=3)
        self.session_time_label = tk.Label(stats_grid, text="0s",
                                           font=("Helvetica", 11),
                                           bg=self.card_bg, fg=self.accent_color)
        self.session_time_label.grid(row=3, column=1, sticky=tk.E, pady=3)
        
        stats_grid.grid_columnconfigure(1, weight=1)
        
        # Deep work meter
        self.deep_work_label = tk.Label(stats_content, text="⚡ Deep Work: 0%",
                                        font=("Helvetica", 11),
                                        bg=self.card_bg, fg=self.fg_color)
        self.deep_work_label.pack(pady=(10, 0))
        
        # Motivation/Coaching messages
        self.motivation_label = tk.Label(right_panel, text="",
                                        font=("Helvetica", 11, "italic"),
                                        bg=self.bg_color, fg=self.accent_color,
                                        wraplength=350, justify=tk.CENTER)
        self.motivation_label.pack(pady=15)
        
        # Start camera
        if not self.cap:
            self.cap = cv2.VideoCapture(0)
            self.update_camera()
    
    def toggle_offscreen_mode(self):
        """Handle paper mode toggle"""
        if self.offscreen_mode.get():
            self.update_motivation("✍️ Paper Mode ON - No judgment! You're still earning streak time. Face just needs to be in frame.")
        else:
            self.update_motivation("👀 Normal Mode - Back to eye tracking. Looking directly at screen required.")
    
    def setup_history_screen(self):
        """Session history screen with improved graph visibility - SCROLLABLE"""
        self.clear_screen()
        self.current_screen = "history"
        
        # Container with header
        container = tk.Frame(self.root, bg=self.bg_color)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Header frame (fixed at top)
        header_container = tk.Frame(container, bg=self.bg_color)
        header_container.pack(fill=tk.X, padx=40, pady=(30, 10))
        
        header_frame = tk.Frame(header_container, bg=self.bg_color)
        header_frame.pack(fill=tk.X)
        
        tk.Label(header_frame, text="📊 Session History",
                font=("Helvetica", 24, "bold"),
                bg=self.bg_color, fg=self.fg_color).pack(side=tk.LEFT)
        
        back_btn = tk.Button(header_frame, text="🏠 Home",
                            command=self.setup_home_screen,
                            font=("Helvetica", 12),
                            bg=self.card_bg, fg=self.fg_color,
                            padx=20, pady=8, relief=tk.SOLID,
                            borderwidth=1, cursor="hand2")
        back_btn.pack(side=tk.RIGHT)
        
        if not self.session_history:
            tk.Label(container, text="No sessions yet. Start your first session!",
                    font=("Helvetica", 14),
                    bg=self.bg_color, fg=self.text_secondary).pack(pady=50)
            return
        
        # Scrollable content
        canvas = tk.Canvas(container, bg=self.bg_color, highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.bg_color)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Mousewheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=40)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 40))
        
        # Add padding frame
        content_frame = tk.Frame(scrollable_frame, bg=self.bg_color)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Sessions list
        for i, session in enumerate(reversed(self.session_history)):
            self.create_session_card(content_frame, session, len(self.session_history) - i)
    
    def create_session_card(self, parent, session, session_num):
        """Create session card with detailed view button"""
        card = tk.Frame(parent, bg=self.card_bg, relief=tk.RAISED, borderwidth=1)
        card.pack(fill=tk.X, pady=10)
        
        content = tk.Frame(card, bg=self.card_bg)
        content.pack(padx=20, pady=15, fill=tk.X)
        
        # Header
        header = tk.Frame(content, bg=self.card_bg)
        header.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(header, text=f"Session {session_num}",
                font=("Helvetica", 14, "bold"),
                bg=self.card_bg, fg=self.fg_color).pack(side=tk.LEFT)
        
        tk.Label(header, text=session.get('timestamp', 'Unknown')[:10],
                font=("Helvetica", 11),
                bg=self.card_bg, fg=self.text_secondary).pack(side=tk.RIGHT)
        
        # Quick stats
        stats_frame = tk.Frame(content, bg=self.card_bg)
        stats_frame.pack(fill=tk.X)
        
        quick_stats = [
            ("Task", session.get('task', 'N/A')),
            ("Duration", f"{session.get('session_time', 0) // 60} min"),
            ("Focus", f"{session.get('focus_score', 0)}%"),
            ("Cycles", str(session.get('streak_count', 0)))
        ]
        
        for label, value in quick_stats:
            stat_frame = tk.Frame(stats_frame, bg=self.card_bg)
            stat_frame.pack(side=tk.LEFT, padx=15)
            
            tk.Label(stat_frame, text=label,
                    font=("Helvetica", 9),
                    bg=self.card_bg, fg=self.text_secondary).pack()
            tk.Label(stat_frame, text=value,
                    font=("Helvetica", 12, "bold"),
                    bg=self.card_bg, fg=self.accent_color).pack()
        
        # IMPROVED: "Click to view detailed stats and graph" button
        view_btn = tk.Button(content, text="📊 Click here to view detailed stats and graph",
                            command=lambda s=session: self.show_session_details(s),
                            font=("Helvetica", 12, "bold"),
                            bg=self.accent_color, fg="white",
                            padx=20, pady=10, relief=tk.FLAT,
                            cursor="hand2",
                            activebackground="#2563eb")
        view_btn.pack(pady=(10, 0))
    
    def show_session_details(self, session):
        """Show detailed session stats with focus timeline graph"""
        details_window = tk.Toplevel(self.root)
        details_window.title("Session Details")
        details_window.geometry("900x700")
        details_window.configure(bg=self.bg_color)
        
        # Header
        tk.Label(details_window, text="📈 Detailed Session Analysis",
                font=("Helvetica", 20, "bold"),
                bg=self.bg_color, fg=self.accent_color).pack(pady=20)
        
        # Stats grid
        stats_frame = tk.Frame(details_window, bg=self.bg_color)
        stats_frame.pack(pady=20, padx=30, fill=tk.X)
        
        stats_grid = tk.Frame(stats_frame, bg=self.bg_color)
        stats_grid.pack()
        
        detailed_stats = [
            ("Session Duration", f"{session.get('session_time', 0)} seconds", 
             f"{session.get('session_time', 0) // 60} minutes"),
            ("Focus Score", f"{session.get('focus_score', 0)}%",
             "Time spent focused"),
            ("Cycles Completed", f"{session.get('streak_count', 0)}",
             "Focus-break cycles"),
            ("Wellness Points", f"{session.get('wellness_points', 0)}",
             "Healthy breaks taken"),
            ("Longest Streak", f"{session.get('longest_streak', 0)}s",
             f"{session.get('longest_streak', 0) // 60} min"),
            ("Total Break Time", f"{session.get('break_time', 0)}s",
             f"{session.get('break_time', 0) // 60} min")
        ]
        
        for i, (label, value, subtitle) in enumerate(detailed_stats):
            row = i // 3
            col = i % 3
            
            stat_card = tk.Frame(stats_grid, bg=self.card_bg, relief=tk.RAISED, borderwidth=1)
            stat_card.grid(row=row, column=col, padx=10, pady=10)
            
            tk.Label(stat_card, text=label, font=("Helvetica", 10),
                    bg=self.card_bg, fg=self.text_secondary,
                    padx=15, pady=5).pack()
            
            tk.Label(stat_card, text=value, font=("Helvetica", 18, "bold"),
                    bg=self.card_bg, fg=self.accent_color,
                    padx=15).pack()
            
            tk.Label(stat_card, text=subtitle, font=("Helvetica", 9),
                    bg=self.card_bg, fg=self.text_secondary,
                    padx=15, pady=5).pack()
        
        # FIXED: Focus timeline graph - NOW VISIBLE
        if session.get('focus_timeline'):
            graph_frame = tk.Frame(details_window, bg=self.card_bg, relief=tk.RAISED, borderwidth=1)
            graph_frame.pack(padx=30, pady=20, fill=tk.BOTH, expand=True)
            
            tk.Label(graph_frame, text="📈 Focus Timeline Graph",
                    font=("Helvetica", 14, "bold"),
                    bg=self.card_bg, fg=self.fg_color).pack(pady=10)
            
            self.create_focus_graph(graph_frame, session['focus_timeline'])
        else:
            tk.Label(details_window, text="No timeline data available for this session",
                    font=("Helvetica", 12),
                    bg=self.bg_color, fg=self.text_secondary).pack(pady=20)
        
        # Close button - IMPROVED VISIBILITY
        close_btn = tk.Button(details_window, text="Close",
                             command=details_window.destroy,
                             font=("Helvetica", 13, "bold"),
                             bg=self.accent_color, fg="white",
                             padx=35, pady=12, relief=tk.FLAT,
                             cursor="hand2",
                             activebackground="#2563eb")
        close_btn.pack(pady=20)
    
    def create_focus_graph(self, parent, timeline_data):
        """Create focus timeline graph using matplotlib"""
        fig, ax = plt.subplots(figsize=(8, 3.5), facecolor=self.card_bg if self.dark_mode.get() else 'white')
        
        if self.dark_mode.get():
            ax.set_facecolor(self.bg_color)
        else:
            ax.set_facecolor('#f9fafb')
        
        # Prepare data
        time_points = list(range(len(timeline_data)))
        focus_values = timeline_data
        
        # Create the plot
        ax.fill_between(time_points, focus_values, alpha=0.3, color='#3b82f6')
        ax.plot(time_points, focus_values, color='#3b82f6', linewidth=2, marker='o', markersize=4)
        
        # Styling
        text_color = self.fg_color if self.dark_mode.get() else '#111827'
        ax.set_xlabel('Time (5-second intervals)', fontsize=11, color=text_color)
        ax.set_ylabel('Focus State', fontsize=11, color=text_color)
        ax.set_ylim(-0.1, 1.1)
        ax.set_yticks([0, 1])
        ax.set_yticklabels(['Away', 'Focused'])
        ax.grid(True, alpha=0.3)
        ax.tick_params(colors=text_color)
        
        # Dark mode spine colors
        if self.dark_mode.get():
            for spine in ax.spines.values():
                spine.set_edgecolor(text_color)
        
        plt.tight_layout()
        
        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.draw()
        canvas.get_tk_widget().pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
    
    def setup_achievements_screen(self):
        """NEW: Achievements screen - SCROLLABLE"""
        self.clear_screen()
        self.current_screen = "achievements"
        
        # Container
        container = tk.Frame(self.root, bg=self.bg_color)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Header (fixed)
        header_container = tk.Frame(container, bg=self.bg_color)
        header_container.pack(fill=tk.X, padx=40, pady=(30, 10))
        
        header_frame = tk.Frame(header_container, bg=self.bg_color)
        header_frame.pack(fill=tk.X)
        
        tk.Label(header_frame, text="🏆 Achievements",
                font=("Helvetica", 24, "bold"),
                bg=self.bg_color, fg=self.fg_color).pack(side=tk.LEFT)
        
        back_btn = tk.Button(header_frame, text="🏠 Home",
                            command=self.setup_home_screen,
                            font=("Helvetica", 12),
                            bg=self.card_bg, fg=self.fg_color,
                            padx=20, pady=8, relief=tk.SOLID,
                            borderwidth=1, cursor="hand2")
        back_btn.pack(side=tk.RIGHT)
        
        # Progress
        unlocked = sum(1 for a in self.achievements.values() if a["unlocked"])
        total = len(self.achievements)
        
        tk.Label(header_container, text=f"Unlocked: {unlocked}/{total}",
                font=("Helvetica", 14),
                bg=self.bg_color, fg=self.text_secondary).pack(pady=10)
        
        # Scrollable content
        canvas = tk.Canvas(container, bg=self.bg_color, highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.bg_color)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Mousewheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=40)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 40))
        
        # Achievement grid
        grid = tk.Frame(scrollable_frame, bg=self.bg_color)
        grid.pack(pady=20, fill=tk.BOTH, expand=True, padx=20)
        
        row, col = 0, 0
        for key, achievement in self.achievements.items():
            self.create_achievement_card(grid, achievement, row, col)
            col += 1
            if col >= 2:
                col = 0
                row += 1
    
    def create_achievement_card(self, parent, achievement, row, col):
        """Create achievement card"""
        unlocked = achievement["unlocked"]
        
        card = tk.Frame(parent, bg=self.card_bg if unlocked else "#3a3a3a",
                       relief=tk.RAISED, borderwidth=1)
        card.grid(row=row, column=col, padx=20, pady=15, ipadx=30, ipady=20, sticky="nsew")
        
        parent.grid_columnconfigure(col, weight=1)
        
        icon = "🏆" if unlocked else "🔒"
        tk.Label(card, text=icon, font=("Helvetica", 40),
                bg=card["bg"]).pack(pady=10)
        
        tk.Label(card, text=achievement["title"],
                font=("Helvetica", 14, "bold"),
                bg=card["bg"],
                fg=self.fg_color if unlocked else "#666666").pack()
        
        tk.Label(card, text=achievement["description"],
                font=("Helvetica", 11),
                bg=card["bg"],
                fg=self.text_secondary if unlocked else "#555555",
                wraplength=250, justify=tk.CENTER).pack(pady=8)
        
        if unlocked:
            tk.Label(card, text="✓ UNLOCKED",
                    font=("Helvetica", 10, "bold"),
                    bg=card["bg"], fg="#22c55e").pack(pady=5)
    
    def setup_settings_screen(self):
        """NEW: Settings screen - SCROLLABLE"""
        self.clear_screen()
        self.current_screen = "settings"
        
        # Container
        container = tk.Frame(self.root, bg=self.bg_color)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Header (fixed)
        header_container = tk.Frame(container, bg=self.bg_color)
        header_container.pack(fill=tk.X, padx=40, pady=(30, 10))
        
        header_frame = tk.Frame(header_container, bg=self.bg_color)
        header_frame.pack(fill=tk.X)
        
        tk.Label(header_frame, text="⚙️ Settings",
                font=("Helvetica", 24, "bold"),
                bg=self.bg_color, fg=self.fg_color).pack(side=tk.LEFT)
        
        back_btn = tk.Button(header_frame, text="🏠 Home",
                            command=self.setup_home_screen,
                            font=("Helvetica", 12),
                            bg=self.card_bg, fg=self.fg_color,
                            padx=20, pady=8, relief=tk.SOLID,
                            borderwidth=1, cursor="hand2")
        back_btn.pack(side=tk.RIGHT)
        
        # Scrollable content
        canvas = tk.Canvas(container, bg=self.bg_color, highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.bg_color)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Mousewheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=40)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 40))
        
        # Content frame
        main_frame = tk.Frame(scrollable_frame, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Coaching Style
        coaching_card = tk.Frame(main_frame, bg=self.card_bg, relief=tk.RAISED, borderwidth=1)
        coaching_card.pack(fill=tk.X, pady=15)
        
        coaching_content = tk.Frame(coaching_card, bg=self.card_bg)
        coaching_content.pack(padx=30, pady=20)
        
        tk.Label(coaching_content, text="🎯 Coaching Style",
                font=("Helvetica", 14, "bold"),
                bg=self.card_bg, fg=self.fg_color).pack(anchor=tk.W, pady=(0, 10))
        
        for style in ["Gentle", "Moderate", "Intense"]:
            tk.Radiobutton(coaching_content, text=style,
                          variable=self.coaching_style, value=style,
                          font=("Helvetica", 11),
                          bg=self.card_bg, fg=self.fg_color,
                          selectcolor=self.card_bg,
                          command=self.save_user_progress,
                          activebackground=self.card_bg).pack(anchor=tk.W, pady=3)
        
        # Privacy Settings
        privacy_card = tk.Frame(main_frame, bg=self.card_bg, relief=tk.RAISED, borderwidth=1)
        privacy_card.pack(fill=tk.X, pady=15)
        
        privacy_content = tk.Frame(privacy_card, bg=self.card_bg)
        privacy_content.pack(padx=30, pady=20)
        
        tk.Label(privacy_content, text="🔒 Privacy Settings",
                font=("Helvetica", 14, "bold"),
                bg=self.card_bg, fg=self.fg_color).pack(anchor=tk.W, pady=(0, 10))
        
        tk.Checkbutton(privacy_content,
                      text="Enable Privacy Shield (Blur video during breaks)",
                      variable=self.privacy_shield,
                      font=("Helvetica", 11),
                      bg=self.card_bg, fg=self.fg_color,
                      selectcolor=self.card_bg,
                      command=self.save_user_progress,
                      activebackground=self.card_bg).pack(anchor=tk.W, pady=5)
        
        tk.Label(privacy_content, text="✓ All processing is local on your device",
                font=("Helvetica", 10, "italic"),
                bg=self.card_bg, fg=self.text_secondary).pack(anchor=tk.W, pady=2)
        
        tk.Label(privacy_content, text="✓ No data sent to cloud or servers",
                font=("Helvetica", 10, "italic"),
                bg=self.card_bg, fg=self.text_secondary).pack(anchor=tk.W, pady=2)
        
        # Audio Settings
        audio_card = tk.Frame(main_frame, bg=self.card_bg, relief=tk.RAISED, borderwidth=1)
        audio_card.pack(fill=tk.X, pady=15)
        
        audio_content = tk.Frame(audio_card, bg=self.card_bg)
        audio_content.pack(padx=30, pady=20)
        
        tk.Label(audio_content, text="🔊 Audio Settings",
                font=("Helvetica", 14, "bold"),
                bg=self.card_bg, fg=self.fg_color).pack(anchor=tk.W, pady=(0, 10))
        
        tk.Checkbutton(audio_content,
                      text="Enable Audio Cues and Voice Coaching",
                      variable=self.audio_cues,
                      font=("Helvetica", 11),
                      bg=self.card_bg, fg=self.fg_color,
                      selectcolor=self.card_bg,
                      command=self.save_user_progress,
                      activebackground=self.card_bg).pack(anchor=tk.W, pady=5)
        
        # Display Settings
        display_card = tk.Frame(main_frame, bg=self.card_bg, relief=tk.RAISED, borderwidth=1)
        display_card.pack(fill=tk.X, pady=15)
        
        display_content = tk.Frame(display_card, bg=self.card_bg)
        display_content.pack(padx=30, pady=20)
        
        tk.Label(display_content, text="🎨 Display Settings",
                font=("Helvetica", 14, "bold"),
                bg=self.card_bg, fg=self.fg_color).pack(anchor=tk.W, pady=(0, 10))
        
        tk.Checkbutton(display_content,
                      text="🌙 Dark Mode",
                      variable=self.dark_mode,
                      font=("Helvetica", 11),
                      bg=self.card_bg, fg=self.fg_color,
                      selectcolor=self.card_bg,
                      activebackground=self.card_bg).pack(anchor=tk.W, pady=5)
    
    def check_achievements(self):
        """Check and unlock achievements"""
        if self.total_sessions >= 1 and not self.achievements["first_session"]["unlocked"]:
            self.achievements["first_session"]["unlocked"] = True
            self.show_achievement_notification("First Steps")
        
        if self.persistent_streak_count >= 10 and not self.achievements["focus_master"]["unlocked"]:
            self.achievements["focus_master"]["unlocked"] = True
            self.show_achievement_notification("Focus Master")
        
        if self.lifetime_wellness >= 500 and not self.achievements["wellness_warrior"]["unlocked"]:
            self.achievements["wellness_warrior"]["unlocked"] = True
            self.show_achievement_notification("Wellness Warrior")
        
        if self.level >= 5 and not self.achievements["level_5"]["unlocked"]:
            self.achievements["level_5"]["unlocked"] = True
            self.show_achievement_notification("Rising Star")
        
        if self.session_cycles >= 5 and not self.achievements["perfect_day"]["unlocked"]:
            self.achievements["perfect_day"]["unlocked"] = True
            self.show_achievement_notification("Perfect Day")
        
        if self.persistent_streak_count >= 20 and not self.achievements["streak_legend"]["unlocked"]:
            self.achievements["streak_legend"]["unlocked"] = True
            self.show_achievement_notification("Streak Legend")
        
        self.save_user_progress()
    
    def show_achievement_notification(self, title):
        """Show achievement unlock notification"""
        if hasattr(self, 'motivation_label'):
            self.update_motivation(f"🏆 Achievement Unlocked: {title}!")
    
    def clear_screen(self):
        """Clear all widgets from screen"""
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def start_session(self):
        """Start a new focus session"""
        self.session_active = True
        self.session_start_time = time.time()
        self.cycle_start_time = time.time()
        self.current_cycle_type = "focus"
        self.session_id = datetime.now().isoformat()
        
        # Reset session stats
        self.streak_time_sec = 0
        self.streak_count = 0
        self.longest_streak = 0
        self.wellness_points = 0
        self.focus_score = 0
        self.focused_frames = 0
        self.total_frames = 0
        self.deep_work_meter = 0
        self.total_break_time = 0
        self.focus_timeline = []
        self.cycles_completed = 0
        self.session_cycles = 0  # Reset session cycles
        self.reminder_count = 0
        self.last_reminder_time = None
        
        self.update_motivation("🎯 Session started! Stay focused!")
    
    def end_session(self):
        """End current session and save data"""
        if not self.session_active:
            return
        
        self.session_active = False
        session_duration = int(time.time() - self.session_start_time)
        
        # Calculate final stats
        session_data = {
            "timestamp": self.session_id,
            "task": self.session_task,
            "mood": self.session_mood,
            "session_time": session_duration,
            "focus_score": self.focus_score,
            "streak_count": self.session_cycles,  # Use session cycles
            "longest_streak": self.longest_streak,
            "wellness_points": self.wellness_points,
            "break_time": self.total_break_time,
            "focus_timeline": self.focus_timeline
        }
        
        # Save to history
        self.session_history.append(session_data)
        self.save_session_history()
        
        # Update lifetime stats
        self.total_sessions += 1
        self.lifetime_wellness += self.wellness_points
        
        # Award completion XP
        xp_earned = self.xp_rewards["complete_session"]
        self.add_xp(xp_earned, "Session completed!")
        
        # Perfect focus bonus
        if self.focus_score >= 90:
            bonus_xp = self.xp_rewards["perfect_focus"]
            self.add_xp(bonus_xp, "Perfect focus!")
            xp_earned += bonus_xp
        
        # Check achievements
        self.check_achievements()
        
        self.save_user_progress()
        
        # Generate AI coaching feedback based on performance
        ai_feedback = self.generate_session_feedback()
        
        # Show summary with AI feedback
        summary = f"""
Session Complete! 🎉

Task: {self.session_task}
Duration: {session_duration // 60} minutes {session_duration % 60} seconds
Focus Score: {self.focus_score}%
Cycles Completed: {self.session_cycles}
Wellness Points: {self.wellness_points}
Current Streak: {self.persistent_streak_count} cycles

💰 XP Earned: +{xp_earned}

🤖 AI Coach Says:
{ai_feedback}

Keep up the great work! 💪
        """
        
        messagebox.showinfo("Session Complete", summary)
        
        # Return to home
        self.setup_home_screen()
    
    def generate_session_feedback(self):
        """Generate AI coaching feedback based on session performance"""
        focus_score = self.focus_score
        cycles = self.session_cycles
        wellness = self.wellness_points
        
        # Excellent performance
        if focus_score >= 90 and cycles >= 3:
            messages = [
                "Outstanding! You were in the zone today. That level of focus is rare and impressive. Keep this momentum going!",
                "Wow! That was a masterclass in concentration. You crushed it! Your focus skills are seriously impressive.",
                "Incredible session! You maintained laser focus throughout. This is exactly the kind of deep work that leads to breakthroughs!"
            ]
        # Great performance
        elif focus_score >= 75 and cycles >= 2:
            messages = [
                "Great work! You stayed focused and got a lot done. Small improvements and you'll be at peak performance!",
                "Solid session! Your focus was strong and consistent. You're building excellent habits here.",
                "Well done! You maintained good focus and completed multiple cycles. This is sustainable productivity at its best!"
            ]
        # Good performance
        elif focus_score >= 60:
            messages = [
                "Good effort! You stayed on task and made progress. Every session helps build your focus muscle.",
                "Nice work! You showed up and put in the effort. Consistency beats perfection every time!",
                "Solid! You maintained decent focus despite distractions. That's growth right there."
            ]
        # Room for improvement
        else:
            messages = [
                "Progress, not perfection! Every session is practice. You'll do better next time - I believe in you!",
                "Hey, you showed up! That's what matters. Focus is a skill you're building, and you're on the right path.",
                "Tough session, but you finished! That takes commitment. Let's identify what distracted you and tackle it next time."
            ]
        
        # Add wellness-specific encouragement
        if wellness >= 30:
            wellness_msg = " Love that you're taking care of yourself with those breaks! Mental health = productivity."
        elif wellness >= 10:
            wellness_msg = " Good job taking breaks - keep balancing focus with rest!"
        else:
            wellness_msg = " Remember to take your breaks next time - they help you stay sharp!"
        
        import random
        return random.choice(messages) + wellness_msg
    
    def update_cycle_timer(self):
        """Update cycle timer display"""
        if not self.session_active or not self.cycle_start_time:
            return
        
        current_time = time.time()
        elapsed = int(current_time - self.cycle_start_time)
        
        if self.current_cycle_type == "focus":
            remaining = self.focus_cycle_duration - elapsed
            if remaining <= 0:
                # Focus cycle complete - only increment if actually focused OR in paper mode with face present
                is_paper_mode_focused = self.offscreen_mode.get() and self.cap and self.cap.isOpened()
                
                if self.current_state == "Focused" or is_paper_mode_focused:
                    self.cycles_completed += 1
                    self.session_cycles += 1
                    self.persistent_streak_count += 1  # Increment persistent streak
                    
                    self.add_xp(self.xp_rewards["complete_cycle"], "Cycle complete!")
                    self.update_motivation("🎉 Focus cycle complete! Take a break!")
                    
                    # Update displays
                    if hasattr(self, 'streak_counter_label'):
                        self.streak_counter_label.config(text=str(self.persistent_streak_count))
                    if hasattr(self, 'session_cycles_label'):
                        self.session_cycles_label.config(text=f"This session: {self.session_cycles} cycles")
                    
                    self.check_achievements()
                    self.save_user_progress()
                else:
                    self.update_motivation("⚠️ Cycle ended but focus was lost. No streak bonus.")
                
                # Switch to break
                self.current_cycle_type = "break"
                self.cycle_start_time = time.time()
                return
        else:  # break
            remaining = self.break_cycle_duration - elapsed
            if remaining <= 0:
                # Break complete!
                self.wellness_points += 10
                self.add_xp(self.xp_rewards["take_break"], "Break taken!")
                self.update_motivation("💪 Break over! Back to focus!")
                
                # Switch to focus
                self.current_cycle_type = "focus"
                self.cycle_start_time = time.time()
                return
        
        # Update display
        minutes = remaining // 60
        seconds = remaining % 60
        
        if hasattr(self, 'cycle_timer_label'):
            self.cycle_timer_label.config(text=f"{minutes:02d}:{seconds:02d}")
        
        if hasattr(self, 'cycle_type_label'):
            cycle_name = "🎯 FOCUS TIME" if self.current_cycle_type == "focus" else "☕ BREAK TIME"
            self.cycle_type_label.config(text=cycle_name)
    
    def detect_eye_gaze(self, frame, gray, face_rect):
        """Detect if eyes are looking at screen - enhanced to catch side-eyeing"""
        x, y, w, h = face_rect
        roi_gray = gray[y:y+h, x:x+w]
        
        # Detect eyes
        eyes = self.eye_cascade.detectMultiScale(roi_gray, scaleFactor=1.1, minNeighbors=5, minSize=(20, 20))
        
        if len(eyes) >= 2:
            eye_centers = []
            for (ex, ey, ew, eh) in eyes[:2]:  # Only use first 2 eyes detected
                # Get eye center
                cx = ex + ew // 2
                cy = ey + eh // 2
                eye_centers.append((cx, cy))
            
            # Add to history
            self.eye_history.append(eye_centers)
            if len(self.eye_history) > self.eye_history_length:
                self.eye_history.pop(0)
            
            # Analyze eye movement to detect side-eyeing
            if len(self.eye_history) >= 3:
                recent_positions = self.eye_history[-3:]
                deviations = []
                
                # Calculate deviation between consecutive frames
                for i in range(len(recent_positions) - 1):
                    for j in range(min(len(recent_positions[i]), len(recent_positions[i+1]))):
                        if j < len(recent_positions[i]) and j < len(recent_positions[i+1]):
                            dx = recent_positions[i+1][j][0] - recent_positions[i][j][0]
                            dy = recent_positions[i+1][j][1] - recent_positions[i][j][1]
                            deviation = np.sqrt(dx**2 + dy**2)
                            deviations.append(deviation)
                
                if deviations:
                    avg_deviation = np.mean(deviations)
                    
                    # Check for horizontal eye movement (side-eyeing)
                    # If eyes are moving horizontally a lot, user is looking away
                    horizontal_movements = []
                    for i in range(len(recent_positions) - 1):
                        for j in range(min(len(recent_positions[i]), len(recent_positions[i+1]))):
                            if j < len(recent_positions[i]) and j < len(recent_positions[i+1]):
                                dx = abs(recent_positions[i+1][j][0] - recent_positions[i][j][0])
                                horizontal_movements.append(dx)
                    
                    if horizontal_movements:
                        avg_horizontal = np.mean(horizontal_movements)
                        # If strong horizontal movement, they're side-eyeing
                        if avg_horizontal > 8:  # LOWERED threshold - stricter detection of side-eyeing
                            return True, False  # Eyes detected but not looking straight
                    
                    # Overall deviation check
                    looking_straight = avg_deviation < self.gaze_deviation_threshold
                    return True, looking_straight
            
            # Not enough history yet, assume looking straight
            return True, True
        
        # Eyes not detected
        return False, False
    
    def update_camera(self):
        """Update camera feed and process detection"""
        if not self.cap or not self.cap.isOpened():
            return
        
        ret, frame = self.cap.read()
        if not ret:
            self.root.after(33, self.update_camera)
            return
        
        frame = cv2.flip(frame, 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100))
        
        if self.session_active:
            self.process_face_detection(frame, faces, gray)
        else:
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (100, 100, 100), 2)
        
        # Update cycle timer
        self.update_cycle_timer()
        
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        imgtk = ImageTk.PhotoImage(image=img)
        self.video_canvas.imgtk = imgtk
        self.video_canvas.configure(image=imgtk)
        
        self.root.after(33, self.update_camera)
    
    def process_face_detection(self, frame, faces, gray):
        """Process face detection with enhanced buffer system and paper mode support"""
        current_time = time.time()
        self.total_frames += 1
        
        # Update timeline
        is_focused_state = (self.current_state == "Focused") or (self.offscreen_mode.get() and len(faces) > 0)
        if self.last_timeline_update is None or current_time - self.last_timeline_update >= self.timeline_interval:
            self.focus_timeline.append(1 if is_focused_state else 0)
            self.last_timeline_update = current_time
        
        eyes_detected = False
        looking_straight = False
        detected_state = "Away"
        
        # Paper mode handling
        if self.offscreen_mode.get():
            # In paper mode, just check if face is present anywhere in frame
            if len(faces) > 0:
                # Face detected = still working, treat as focused
                eyes_detected = True
                looking_straight = True
                detected_state = "Focused"  # Treat as focused in paper mode
            else:
                # No face at all = actually away
                detected_state = "Away"
        else:
            # Normal mode - check eye gaze and distance
            if len(faces) > 0:
                x, y, w, h = faces[0]
                
                # Check if too close first
                face_ratio = w / frame.shape[1]
                
                if face_ratio > self.TOO_CLOSE_THRESHOLD:
                    detected_state = "TooClose"
                    eyes_detected = False
                    looking_straight = False
                else:
                    # Not too close, check eye gaze
                    eyes_detected, looking_straight = self.detect_eye_gaze(frame, gray, (x, y, w, h))
                    
                    if eyes_detected and looking_straight:
                        self.eyes_detected_count += 1
                        self.no_eyes_count = 0
                        detected_state = "Focused"
                    else:
                        self.no_eyes_count += 1
                        # More forgiving - short glances away are okay
                        if self.no_eyes_count < self.eye_detection_threshold:
                            eyes_detected = True
                            looking_straight = True
                            detected_state = "Focused"
                        else:
                            self.eyes_detected_count = 0
                            detected_state = "Away"
            else:
                # No face detected at all
                self.eyes_detected_count = 0
                self.no_eyes_count += 1
                detected_state = "Away"
        
        # Apply distraction buffer - don't break streak immediately
        # SPECIAL HANDLING FOR PAPER MODE - if face present, never mark as Away
        if self.offscreen_mode.get() and len(faces) > 0:
            # In paper mode with face present, always treat as focused
            detected_state = "Focused"
            self.distraction_start_time = None  # Reset distraction timer
            
            if self.current_state == "Away":
                if self.return_buffer_start is None:
                    self.return_buffer_start = current_time
                elif current_time - self.return_buffer_start >= self.RETURN_BUFFER:
                    self.current_state = "Focused"
            else:
                self.current_state = "Focused"
                self.return_buffer_start = None
        elif detected_state == "Away":
            if self.distraction_start_time is None:
                self.distraction_start_time = current_time
            elif current_time - self.distraction_start_time >= self.distraction_buffer:
                # Been away for buffer period
                if self.current_state != "Away":
                    # Break streak ONLY during focus time
                    if self.current_cycle_type == "focus":
                        self.update_motivation("❌ Distracted! Streak broken.")
                        self.persistent_streak_count = 0  # Reset persistent streak
                        if hasattr(self, 'streak_counter_label'):
                            self.streak_counter_label.config(text="0")
                        self.save_user_progress()
                    
                    # Show reminder
                    if self.current_cycle_type == "focus":
                        self.show_unfocus_reminder()
                
                self.current_state = "Away"
                self.return_buffer_start = None
        elif detected_state == "TooClose":
            # Reset distraction buffer for too close
            self.distraction_start_time = None
            
            if self.current_state == "Away":
                if self.return_buffer_start is None:
                    self.return_buffer_start = current_time
                elif current_time - self.return_buffer_start >= self.RETURN_BUFFER:
                    self.current_state = "TooClose"
            else:
                self.current_state = "TooClose"
                self.return_buffer_start = None
        else:  # Focused
            # Reset distraction buffer
            self.distraction_start_time = None
            
            if self.current_state == "Away":
                if self.return_buffer_start is None:
                    self.return_buffer_start = current_time
                elif current_time - self.return_buffer_start >= self.RETURN_BUFFER:
                    self.current_state = "Focused"
            else:
                self.current_state = "Focused"
                self.return_buffer_start = None
        
        # Update focus tracking - count TooClose AND PAPER MODE as focused for stats
        if self.current_state in ["Focused", "TooClose"] or (self.offscreen_mode.get() and len(faces) > 0):
            self.focused_frames += 1
            
            if self.streak_start_time is None:
                self.streak_start_time = current_time
            
            self.streak_time_sec = int(current_time - self.streak_start_time)
            
            # Award XP for sustained focus
            if self.streak_time_sec > 0 and self.streak_time_sec % 600 == 0:  # Every 10 minutes
                self.add_xp(self.xp_rewards["maintain_focus_10min"], "10 min focus!")
        
        elif self.current_state == "Away" and not (self.offscreen_mode.get() and len(faces) > 0):
            if self.break_start_time is None:
                self.break_start_time = current_time
        
        # Update progress
        if self.last_state == "Away" and self.current_state in ["Focused", "TooClose"]:
            self.streak_start_time = current_time
            self.streak_time_sec = 0
            self.break_start_time = None
        
        self.last_state = self.current_state
        
        # Calculate focus score
        if self.total_frames > 0:
            self.focus_score = int((self.focused_frames / self.total_frames) * 100)
            self.deep_work_meter = self.focus_score
        
        self.draw_overlay(frame, faces, eyes_detected and looking_straight)
        self.update_stats_display()
    
    def draw_overlay(self, frame, faces, eyes_looking_straight):
        """Draw overlay with GREEN for focused, ORANGE for too close, RED for away"""
        for (x, y, w, h) in faces:
            # Color based on state
            if self.current_state == "Focused":
                color = (34, 197, 94)  # Green
                thickness = 3
            elif self.current_state == "TooClose":
                color = (251, 146, 60)  # Orange
                thickness = 3
            else:
                color = (239, 68, 68)  # Red
                thickness = 2
            
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, thickness)
        
        # Status text based on mode and state
        if self.offscreen_mode.get() and self.current_state == "Focused":
            status_text = "✍️ OFF-SCREEN WORK"
            status_color = (34, 197, 94)
        elif self.current_state == "Focused":
            status_text = "✓ FOCUSED"
            status_color = (34, 197, 94)
        elif self.current_state == "TooClose":
            status_text = "⚠ TOO CLOSE"
            status_color = (251, 146, 60)
        else:
            status_text = "✗ AWAY"
            status_color = (239, 68, 68)
        
        cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                   0.7, status_color, 2)
        
        # Cycle info
        cycle_text = "FOCUS TIME" if self.current_cycle_type == "focus" else "BREAK TIME"
        cv2.putText(frame, cycle_text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX,
                   0.6, (255, 255, 255), 2)
        
        # Paper mode indicator
        if self.offscreen_mode.get():
            cv2.putText(frame, "Paper Mode: No eye tracking", (10, 90), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (34, 197, 94), 2)
    
    def update_stats_display(self):
        """Update stats display - IMPROVED CLARITY with all states"""
        status_colors = {"Focused": "#22c55e", "TooClose": "#f59e0b", "Away": "#ef4444"}
        
        if self.offscreen_mode.get() and self.current_state == "Focused":
            status_text_display = "✍️ Off-Screen Work"
            status_color = "#22c55e"
        else:
            status_text_map = {
                "Focused": "✓ Focused", 
                "TooClose": "⚠ Too Close", 
                "Away": "✗ Away"
            }
            status_text_display = status_text_map.get(self.current_state, "Ready")
            status_color = status_colors.get(self.current_state, "#111827")
        
        if hasattr(self, 'status_label'):
            self.status_label.config(
                text=status_text_display,
                fg=status_color
            )
        
        if hasattr(self, 'streak_time_label'):
            self.streak_time_label.config(text=f"{self.streak_time_sec}s")
        
        if hasattr(self, 'wellness_label'):
            self.wellness_label.config(text=str(self.wellness_points))
        
        if hasattr(self, 'focus_score_label'):
            self.focus_score_label.config(text=f"{self.focus_score}%")
        
        if hasattr(self, 'session_time_label') and self.session_start_time:
            session_time = int(time.time() - self.session_start_time)
            self.session_time_label.config(text=f"{session_time}s")
        
        if hasattr(self, 'deep_work_label'):
            self.deep_work_label.config(text=f"⚡ Deep Work: {self.deep_work_meter}%")
        
        if hasattr(self, 'xp_label'):
            self.xp_label.config(text=f"XP: {self.xp}/{self.xp_to_next_level}")
            
        if hasattr(self, 'xp_progress'):
            self.xp_progress['value'] = (self.xp / self.xp_to_next_level) * 100
    
    def update_motivation(self, message):
        """Update motivation message"""
        if hasattr(self, 'motivation_label'):
            self.motivation_label.config(text=message)
            
            # Auto-clear after 3 seconds
            self.root.after(3000, lambda: self.motivation_label.config(text=""))
    
    def cleanup(self):
        """Cleanup resources"""
        if self.cap:
            self.cap.release()
        
        # Save progress before closing
        if self.session_active:
            self.end_session()
        
        self.root.destroy()

def main():
    root = tk.Tk()
    app = SeeMyFocusApp(root)
    root.protocol("WM_DELETE_WINDOW", app.cleanup)
    root.mainloop()

if __name__ == "__main__":
    main()