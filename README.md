# SeeMyFocus - AI-Powered Focus & Wellness Coach

> Transform your productivity with intelligent eye-tracking, personalized AI coaching, and mental health-focused features.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)

## Overview

SeeMyFocus is an intelligent productivity companion that combines real-time eye tracking, AI coaching, and gamification to help you maintain focus, build healthy work habits, and improve your productivity. Built with privacy in mind - everything runs locally on your device.

### Key Features

- **🎯 Real-Time Eye Tracking** - Detects focus, distractions, and posture using your webcam
- **🤖 AI Coaching** - Personalized focus strategies based on your task and mood
- **✍️ Paper Mode** - Work on handwritten tasks without breaking your streak
- **🎮 Gamification** - XP, levels, achievements, and persistent streaks
- **📊 Analytics** - Session history with focus graphs and detailed insights
- **💪 Wellness Focused** - Encourages healthy breaks and mental well-being
- **🔒 100% Private** - All processing happens locally, no data collection
- **🌙 Dark Mode** - Easy on the eyes for late-night sessions

## Demo

![SeeMyFocus Demo](https://www.youtube.com/watch?v=f0CX-8W_-y0)

*Real-time focus tracking with AI coaching*

## Quick Start

### Prerequisites

- Python 3.8 or higher
- Webcam
- Windows, macOS, or Linux

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/Asuresh07/CalHacks12.0.git
cd seemyfocus
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Run the app**
```bash
python seemyfocus_fixed.py
```

That's it! The app will launch and you can start your first focus session.

## Requirements

- `opencv-python` - Computer vision and eye tracking
- `Pillow` - Image processing
- `numpy` - Numerical computations
- `matplotlib` - Data visualization
- `pyttsx3` - Text-to-speech (optional)

Full list available in `requirements.txt`

## How It Works

### 1. Start a Session
- Enter what you're working on
- Select your current mood
- Get a personalized AI coaching plan

### 2. Two Modes

**Normal Mode (Eye Tracking)**
- Tracks eye gaze direction
- Detects side-eyeing and distractions
- Three states: Focused 🟢 | Too Close 🟠 | Away 🔴

**Paper Mode (Off-Screen Work)**
- Perfect for handwritten work
- Only checks face presence
- No eye tracking - full credit for focus time
- Great for: homework, notes, reading, drawing

### 3. Build Your Streak
- Complete 20-minute focus cycles
- Take 5-minute breaks for wellness points
- Earn XP and level up
- Unlock achievements
- Build persistent streaks across sessions

### 4. Track Progress
- View detailed session history
- Analyze focus patterns with graphs
- Get AI coaching feedback
- Monitor your improvement over time

## Core Features

### Eye Tracking
- **Strict Detection** - Catches side-eyeing at 8px movement
- **3 States** - Focused, Too Close, Away
- **5-Second Buffer** - Prevents accidental streak breaks
- **Real-Time Feedback** - Visual and status indicators

### Paper Mode
- **Face-Only Detection** - No eye tracking required
- **Full Credit** - Earns focus time, XP, and streaks
- **Visual Indicator** - " OFF-SCREEN WORK" status
- **Encouraging Message** - "No judgment! You're still earning streak time"

### Gamification
- **XP System** - Earn points for focus and breaks
- **Levels** - Progress and unlock new milestones
- **Achievements** - 6 achievements to unlock
- **Persistent Streaks** - Carry across sessions
- **Wellness Points** - Reward healthy break behavior

### AI Coaching
- **Personalized Plans** - Based on task and mood
- **Session Feedback** - Performance-based encouragement
- **Adaptive Messaging** - Supportive and motivating
- **Mental Health Focus** - Emphasizes balance and wellness

## Session Analytics

- **Focus Score** - Overall attention percentage
- **Cycle Completion** - Track Pomodoro-style cycles
- **Wellness Points** - Measure healthy break habits
- **Timeline Graph** - Visualize focus patterns
- **Streak History** - See your consistency over time

## Privacy & Security

✅ **100% Local Processing** - No cloud, no servers  
✅ **Zero Data Collection** - Everything stays on your device  
✅ **No Internet Required** - Works completely offline  
✅ **Open Source** - Transparent and auditable code  
✅ **Your Data, Your Control** - Delete anytime  

We respect your privacy. Period.

## Technical Details

### Architecture
- **Computer Vision** - OpenCV with Haar Cascades
- **Eye Tracking** - Multi-frame gaze analysis
- **UI Framework** - Tkinter with custom themes
- **Data Storage** - Local JSON files
- **Visualization** - Matplotlib integration

### Eye Tracking Algorithm
```python
# Strict gaze detection
gaze_deviation_threshold = 25  # pixels
horizontal_threshold = 8  # pixels for side-eye

# Multi-frame analysis prevents false positives
eye_history_length = 15  # frames
```

### Performance
- **Real-time tracking** - 30 FPS camera feed
- **Low CPU usage** - Optimized detection algorithms
- **Minimal memory** - < 100MB typical usage
- **Responsive UI** - Smooth scrolling and animations

## Customization

### Settings
- **Coaching Style** - Gentle, Moderate, or Intense
- **Audio Cues** - Voice coaching (optional)
- **Privacy Shield** - Blur video during breaks
- **Dark Mode** - Toggle light/dark themes
- **Cycle Duration** - Customize focus/break times (coming soon)

## Achievements

Unlock achievements by reaching milestones:

1. **First Steps** - Complete your first session
2. **Focus Master** - Reach 10 cycle streak
3. **Wellness Warrior** - Earn 500 wellness points
4. **Rising Star** - Reach level 5
5. **Perfect Day** - Complete 5 cycles in one session
6. **Streak Legend** - Maintain 20 cycle streak

## Use Cases

### Students
- Study sessions
- Homework and assignments
- Note-taking
- Reading textbooks

### Professionals
- Coding sprints
- Data analysis
- Writing reports
- Creative work

### Anyone Who Wants To
- Build focus habits
-  Practice time management
-  Reduce distractions
-  Track productivity
-  Improve concentration


## 📝 Roadmap

- [ ] Custom cycle durations
- [ ] Export session data (CSV, PDF)
- [ ] Statistics dashboard
- [ ] Mobile app version
- [ ] Team/group sessions
- [ ] Integration with task managers
- [ ] Advanced analytics
- [ ] Custom achievement system

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built for the Anthropic Claude Hackathon 2025
- Powered by Claude AI for intelligent coaching
- OpenCV community for computer vision tools
- All focus productivity enthusiasts

## Contact

- **GitHub Issues** - For bugs and feature requests
- **Email** - [adityasuresh@live.com]
- **LinkedIn** - [https://www.linkedin.com/in/adityasureshlive/]

## Star Us!

If SeeMyFocus helps you stay focused and productive, please give us a star! It helps others discover the project.

---

<div align="center">

[Report Bug](https://github.com/yourusername/seemyfocus/issues) · [Request Feature](https://github.com/yourusername/seemyfocus/issues) · [Documentation](https://github.com/yourusername/seemyfocus/wiki)

</div>
