import os
import math
import random
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import soundfile as sf
import pygame

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.widgets import SpanSelector
import numpy as np
import matplotlib.ticker as ticker
import tempfile
import subprocess
import imageio_ffmpeg


# Initialize pygame mixer for audio preview
pygame.mixer.init()

# Import our refactored modules
from enhance_audio import enhance_audio
from transcribe_elevenlabs import run_elevenlabs
from transcribe_groq_sdk import run_groq
from transcribe_local import run_local_whisper

# ── Design tokens ─────────────────────────────────────────────────
_C = {
    'void'   : '#03040A',
    'panel'  : '#060816',
    'panel2' : '#050912',
    'cyan'   : '#00F2FE',
    'mag'    : '#FF00AA',
    'violet' : '#9D00FF',
    'green'  : '#00FF88',
    'red'    : '#FF2244',
    'text'   : '#D8F0F8',
    'muted'  : '#5F98A7',
    'border' : '#102A45',
    'hot'    : '#0D2A3F',
}

W_WIN, H_WIN = 580, 680

class TranscriptionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ADVANCED AUDIO TRANSCRIPTION ENGINE")
        self.root.geometry(f"{W_WIN}x{H_WIN}")
        self.root.resizable(False, False)
        self.root.configure(bg=_C['void'])

        # State variables
        self.input_file = tk.StringVar()
        self.output_dir = tk.StringVar()
        
        self.cut_audio_var = tk.BooleanVar(value=False)
        self.start_time = tk.StringVar(value="00:00")
        self.end_time = tk.StringVar(value="01:00")
        
        self.language_var = tk.StringVar(value="Bengali")
        self.model_var = tk.StringVar(value="ElevenLabs (Accurate)")
        self.keywords_var = tk.StringVar(value="collection, adjust, MPO, dipo, practice, daily basis, message, amount, taka")
        
        self.is_playing = False
        self._t = 0.0
        self._scanline_y = 0.0
        self._stars = []
        self._after_id = None
        
        # Build UI
        self._build()
        self._seed_stars()
        self._tick()

    def _build(self):
        W, H = W_WIN, H_WIN
        self.cv = tk.Canvas(self.root, width=W, height=H, bg=_C['void'], highlightthickness=0, bd=0)
        self.cv.place(x=0, y=0)

        self._paint_gradient(W, H)
        self._paint_grid(W, H)

        self._sl = self.cv.create_line(0, 0, W, 0, fill='#00F2FE', width=1, stipple='gray12')

        self._paint_brackets(W, H)
        self._paint_title(W)

        # Build rows sequentially
        curr_y = 70
        curr_y = self._row_input(curr_y, W)
        curr_y = self._row_output(curr_y, W)
        curr_y = self._row_cut_options(curr_y, W)
        curr_y = self._row_config(curr_y, W)
        curr_y = self._row_keywords(curr_y, W)
        curr_y = self._row_progress(curr_y, W)
        curr_y = self._row_execute(curr_y, W)
        
        self._footer(W, H)

    # ── Painters ──────────────────────────────────────────────────
    def _paint_gradient(self, W, H):
        for y in range(H):
            t = y / H
            r = int(3  + t * 4)
            g = int(4  + t * 5)
            b = int(10 + t * 16)
            self.cv.create_line(0, y, W, y, fill=f'#{r:02x}{g:02x}{b:02x}', width=1)

    def _paint_grid(self, W, H):
        for x in range(0, W, 40):
            self.cv.create_line(x, 0, x, H, fill='#07091A', width=1)
        for y in range(0, H, 40):
            self.cv.create_line(0, y, W, y, fill='#07091A', width=1)

    def _paint_brackets(self, W, H, pad=10, sz=18):
        c = _C['cyan']
        self.cv.create_line(pad, pad, pad+sz, pad, fill=c, width=1)
        self.cv.create_line(pad, pad, pad, pad+sz, fill=c, width=1)
        self.cv.create_line(W-pad-sz, pad, W-pad, pad, fill=c, width=1)
        self.cv.create_line(W-pad, pad, W-pad, pad+sz, fill=c, width=1)
        self.cv.create_line(pad, H-pad, pad+sz, H-pad, fill=c, width=1)
        self.cv.create_line(pad, H-pad-sz, pad, H-pad, fill=c, width=1)
        self.cv.create_line(W-pad-sz, H-pad, W-pad, H-pad, fill=c, width=1)
        self.cv.create_line(W-pad, H-pad-sz, W-pad, H-pad, fill=c, width=1)

    def _paint_title(self, W):
        self.cv.create_oval(W//2-140, 8, W//2+140, 48, fill='#030B14', outline='')
        self.cv.create_text(W//2, 24, text='ADVANCED AUDIO TRANSCRIPTION', font=('Courier New', 12, 'bold'), fill=_C['cyan'])
        self.cv.create_text(W//2, 39, text='∞  N E U R A L   P I P E L I N E  ∞', font=('Courier New', 6), fill=_C['muted'])
        self.cv.create_line(28, 52, W-28, 52, fill=_C['border'], width=1)
        self.cv.create_oval(23, 47, 33, 57, fill=_C['cyan'], outline='')
        self.cv.create_oval(W-33, 47, W-23, 57, fill=_C['violet'], outline='')

    # ── Rows ──────────────────────────────────────────────────────
    def _row_input(self, y, W):
        self.cv.create_text(28, y, text='INPUT AUDIO FILE', font=('Courier New', 7, 'bold'), fill=_C['muted'], anchor='w')
        self._glass_rect(28, y+8, W-28, y+30, r=5, outline='#12304A')
        self.ent_in = tk.Entry(self.root, textvariable=self.input_file, bg=_C['panel2'], fg=_C['text'],
                               insertbackground=_C['cyan'], relief='flat', font=('Courier New', 9), highlightthickness=0, bd=0)
        self.cv.create_window(33, y+19, window=self.ent_in, width=W-108, height=18, anchor='w')
        self._mini_btn(W-56, y+19, 'BROWSE', self.browse_input)
        return y + 45

    def _row_output(self, y, W):
        self.cv.create_text(28, y, text='OUTPUT FOLDER', font=('Courier New', 7, 'bold'), fill=_C['muted'], anchor='w')
        self._glass_rect(28, y+8, W-28, y+30, r=5, outline='#12304A')
        self.ent_out = tk.Entry(self.root, textvariable=self.output_dir, bg=_C['panel2'], fg=_C['text'],
                                insertbackground=_C['cyan'], relief='flat', font=('Courier New', 9), highlightthickness=0, bd=0)
        self.cv.create_window(33, y+19, window=self.ent_out, width=W-108, height=18, anchor='w')
        self._mini_btn(W-56, y+19, 'BROWSE', self.browse_output)
        return y + 45

    def _row_cut_options(self, y, W):
        self._glass_rect(28, y, W-28, y+50, r=5, fill='#040A12', outline='#12304A')
        
        # Checkbox
        self.chk_cut = tk.Checkbutton(self.root, text="CUT AUDIO", variable=self.cut_audio_var, command=self.toggle_cut,
                                      bg='#040A12', fg=_C['cyan'], selectcolor='#040A12', activebackground='#040A12', activeforeground=_C['cyan'],
                                      font=('Courier New', 8, 'bold'), cursor="hand2", highlightthickness=0, bd=0)
        self.cv.create_window(35, y+25, window=self.chk_cut, anchor='w')

        # Start Time
        self.cv.create_text(160, y+25, text="START (MM:SS)", font=('Courier New', 7), fill=_C['muted'], anchor='e')
        self.ent_start = tk.Entry(self.root, textvariable=self.start_time, bg=_C['panel'], fg=_C['text'], insertbackground=_C['cyan'], width=5, font=('Courier New', 9), highlightthickness=1, highlightbackground=_C['border'], highlightcolor=_C['cyan'], bd=0)
        self.cv.create_window(170, y+25, window=self.ent_start, anchor='w')
        
        # End Time
        self.cv.create_text(290, y+25, text="END (MM:SS)", font=('Courier New', 7), fill=_C['muted'], anchor='e')
        self.ent_end = tk.Entry(self.root, textvariable=self.end_time, bg=_C['panel'], fg=_C['text'], insertbackground=_C['cyan'], width=5, font=('Courier New', 9), highlightthickness=1, highlightbackground=_C['border'], highlightcolor=_C['cyan'], bd=0)
        self.cv.create_window(300, y+25, window=self.ent_end, anchor='w')
        
        # Audio Control Button
        self.btn_play = tk.Button(self.root, text="▶ PREVIEW", command=self.toggle_playback, bg='#07152B', fg=_C['cyan'], font=('Courier New', 7, 'bold'), relief='flat', cursor='hand2')
        self.cv.create_window(W-70, y+25, window=self.btn_play, width=70, height=22)
        
        self.toggle_cut() # Initialize states
        
        # Waveform Canvas
        self.fig = Figure(figsize=(5.2, 1.5), dpi=100, facecolor='#060816')
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor('#060816')
        self.ax.tick_params(colors='#5F98A7', labelsize=7)
        for spine in self.ax.spines.values():
            spine.set_color('#102A45')
        self.fig.subplots_adjust(left=0.08, right=0.98, top=0.9, bottom=0.2)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.cv.create_window(W//2, y+140, window=self.canvas_widget, width=W-56, height=140)
        
        self.span = SpanSelector(self.ax, self.on_select_waveform, 'horizontal', useblit=True,
                                 props=dict(alpha=0.3, facecolor='#00F2FE'), interactive=True)
                                 
        self.canvas.mpl_connect('scroll_event', self.on_scroll)
        self.canvas.mpl_connect('button_press_event', self.on_mouse_press)
        self.canvas.mpl_connect('button_release_event', self.on_mouse_release)
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_motion)
        
        # Format X axis as HH:MM:SS
        def format_func(x, pos):
            h = int(x // 3600)
            m = int((x % 3600) // 60)
            s = int(x % 60)
            if h > 0: return f"{h:02d}:{m:02d}:{s:02d}"
            return f"{m:02d}:{s:02d}"
        self.ax.xaxis.set_major_formatter(ticker.FuncFormatter(format_func))

        # Crop Button
        self.btn_crop = tk.Button(self.root, text="✂ CROP", command=self.crop_waveform, bg='#07152B', fg=_C['cyan'], font=('Courier New', 7, 'bold'), relief='flat', cursor='hand2')
        self.cv.create_window(W-140, y+25, window=self.btn_crop, width=60, height=22)
        
        # Info Label
        self.lbl_cut_info = tk.Label(self.root, text="", bg=_C['void'], fg=_C['green'], font=('Courier New', 8, 'bold'))
        self.cv.create_window(W//2, y+215, window=self.lbl_cut_info)

        return y + 230

    def _safe_set_xlim(self, left, right):
        if hasattr(self, '_waveform_data'):
            max_t = self._waveform_data[0][-1]
            width = right - left
            if left < 0:
                left = 0
                right = left + width
            if right > max_t:
                right = max_t
                left = right - width
            if left < 0:
                left = 0
            self.ax.set_xlim(left, right)
        else:
            self.ax.set_xlim(left, right)


    def _row_config(self, y, W):
        # Engine dropdown
        self.cv.create_text(28, y, text="TRANSCRIPTION ENGINE", font=('Courier New', 7, 'bold'), fill=_C['muted'], anchor='w')
        self.model_menu = tk.OptionMenu(self.root, self.model_var, "ElevenLabs (Accurate)", "Groq (Fast)", "Local Whisper")
        self.model_menu.config(bg=_C['panel'], fg=_C['text'], activebackground=_C['hot'], activeforeground='#fff', font=('Courier New', 8), highlightthickness=1, highlightbackground=_C['border'], bd=0, indicatoron=0)
        self.model_menu["menu"].config(bg=_C['panel'], fg=_C['text'], font=('Courier New', 8))
        self.cv.create_window(30, y+10, window=self.model_menu, anchor='nw', width=240, height=24)

        # Language dropdown
        self.cv.create_text(W-28, y, text="LANGUAGE", font=('Courier New', 7, 'bold'), fill=_C['muted'], anchor='e')
        self.lang_menu = tk.OptionMenu(self.root, self.language_var, "Bengali", "English", "Auto-Detect")
        self.lang_menu.config(bg=_C['panel'], fg=_C['text'], activebackground=_C['hot'], activeforeground='#fff', font=('Courier New', 8), highlightthickness=1, highlightbackground=_C['border'], bd=0, indicatoron=0)
        self.lang_menu["menu"].config(bg=_C['panel'], fg=_C['text'], font=('Courier New', 8))
        self.cv.create_window(W-270, y+10, window=self.lang_menu, anchor='nw', width=240, height=24)
        
        return y + 55

    def _row_keywords(self, y, W):
        self.cv.create_text(28, y, text='KEYWORDS / PROMPT', font=('Courier New', 7, 'bold'), fill=_C['muted'], anchor='w')
        self._glass_rect(28, y+8, W-28, y+30, r=5, outline='#12304A')
        self.ent_keys = tk.Entry(self.root, textvariable=self.keywords_var, bg=_C['panel2'], fg=_C['text'],
                               insertbackground=_C['cyan'], relief='flat', font=('Courier New', 8), highlightthickness=0, bd=0)
        self.cv.create_window(33, y+19, window=self.ent_keys, width=W-60, height=18, anchor='w')
        return y + 45

    def _row_progress(self, y, W):
        self._lbl_status = self.cv.create_text(28, y, text='◉  SYSTEM READY', font=('Courier New', 7), fill=_C['cyan'], anchor='w')
        self._lbl_pct = self.cv.create_text(W-28, y, text='—', font=('Courier New', 7, 'bold'), fill=_C['cyan'], anchor='e')

        self._glass_rect(28, y+7, W-28, y+21, r=4, fill='#030610', outline='#09152A')

        STRIPS = 50
        track_px = W - 58
        sw = track_px / STRIPS
        self._strips = []
        for i in range(STRIPS):
            x1 = 29 + i * sw
            sid = self.cv.create_rectangle(x1, y+8, x1 + sw + 0.5, y+20, fill=_C['void'], outline='', state='hidden')
            self._strips.append(sid)

        self._tip = self.cv.create_oval(24, y+5, 35, y+23, fill=_C['cyan'], outline='', state='hidden')
        return y + 40

    def _row_execute(self, y, W):
        bx1, by1, bx2, by2 = 120, y, W-120, y+38
        self._exec_bg = self._glass_rect(bx1, by1, bx2, by2, r=9, fill='#030A1C', outline='#00F2FE')
        
        self.exec_btn = tk.Button(self.root, command=self.run_process, text='⟨  AUTOMATE TRANSCRIPTION  ⟩', font=('Courier New', 10, 'bold'), fg=_C['cyan'], bg='#030A1C', relief='flat', cursor='hand2', activebackground='#061C34', activeforeground='#FFFFFF', highlightthickness=0, bd=0)
        self.cv.create_window(W//2, (by1+by2)//2, window=self.exec_btn, width=(bx2-bx1)-2, height=(by2-by1)-2)

        def on_in(e):
            if self.exec_btn['state'] != 'disabled':
                self.cv.itemconfig(self._exec_bg, fill='#061C34', outline='#FFFFFF')
                self.exec_btn.configure(bg='#061C34', fg='#FFFFFF')
        def on_out(e):
            if self.exec_btn['state'] != 'disabled':
                self.cv.itemconfig(self._exec_bg, fill='#030A1C', outline='#00F2FE')
                self.exec_btn.configure(bg='#030A1C', fg=_C['cyan'])

        self.exec_btn.bind('<Enter>', on_in)
        self.exec_btn.bind('<Leave>', on_out)
        return y + 50

    def _footer(self, W, H):
        self.cv.create_text(W//2, H-11, text='AUDIO ENGINE  v2.0  ·  NEURAL CORE', font=('Courier New', 6), fill='#4F6880')

    # ── Helpers & Utils ───────────────────────────────────────────
    def _glass_rect(self, x1, y1, x2, y2, r=6, fill=None, outline=None):
        pts = [x1+r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y2-r, x2, y2, x2-r, y2, x1+r, y2, x1, y2, x1, y2-r, x1, y1+r, x1, y1]
        return self.cv.create_polygon(pts, smooth=True, fill=fill or _C['panel'], outline=outline or _C['border'], width=1)

    def _mini_btn(self, cx, cy, label, cmd, w=52, h=21):
        x1, y1, x2, y2 = cx-w//2, cy-h//2, cx+w//2, cy+h//2
        bg_id = self._glass_rect(x1, y1, x2, y2, r=4, fill='#07152B', outline='#00F2FE')
        btn = tk.Button(self.root, text=label, command=cmd, font=('Courier New', 7, 'bold'), fg='#00F2FE', bg='#07152B', relief='flat', cursor='hand2', activebackground='#0B2A4A', activeforeground='#FFFFFF', highlightthickness=0, bd=0)
        self.cv.create_window(cx, cy, window=btn, width=w-2, height=h-2)
        def on_in(e):
            self.cv.itemconfig(bg_id, fill=_C['hot'], outline='#FFFFFF')
            btn.configure(bg=_C['hot'], fg='#FFFFFF')
        def on_out(e):
            self.cv.itemconfig(bg_id, fill='#07152B', outline='#00F2FE')
            btn.configure(bg='#07152B', fg='#00F2FE')
        btn.bind('<Enter>', on_in)
        btn.bind('<Leave>', on_out)
        return btn

    def _seed_stars(self):
        colors = [_C['cyan'], '#FFFFFF', _C['violet'], '#4FACFE']
        for _ in range(35):
            x = random.randint(40, W_WIN-40)
            y = random.randint(60, H_WIN-40)
            sz = random.choice([1, 1, 1, 2])
            sid = self.cv.create_oval(x, y, x+sz, y+sz, fill=random.choice(colors), outline='', state='hidden')
            self._stars.append({'id': sid, 'ph': random.uniform(0, 2*math.pi), 'spd': random.uniform(0.025, 0.065)})

    def _tick(self):
        self._t += 0.045
        self._scanline_y = (self._scanline_y + 1.8) % H_WIN
        self.cv.coords(self._sl, 0, self._scanline_y, W_WIN, self._scanline_y)

        current_text = self.cv.itemcget(self._lbl_status, 'text')
        if 'READY' in current_text:
            v = int(184 + 56 * math.sin(self._t))
            self.cv.itemconfig(self._lbl_status, fill=f'#00{v:02x}{v//2:02x}')

        for s in self._stars:
            s['ph'] += s['spd']
            a = (math.sin(s['ph']) + 1) / 2
            self.cv.itemconfig(s['id'], state='normal' if a > 0.15 else 'hidden')

        self._after_id = self.root.after(50, self._tick)

    # ── Logic ─────────────────────────────────────────────────────
    def crop_waveform(self):
        s = self.time_to_sec(self.start_time.get())
        e = self.time_to_sec(self.end_time.get())
        if s is not None and e is not None and s < e:
            self.cut_audio_var.set(True)
            self.toggle_cut()
            self.lbl_cut_info.config(text=f"✔ Only the selected part ({self.start_time.get()} to {self.end_time.get()}) will be sent for transcription.")
            if hasattr(self, '_waveform_data'):
                times, data = self._waveform_data
                self.line_full.set_color('#2A3B4C') # Gray out unselected
                mask = (times >= s) & (times <= e)
                self.line_sel.set_data(times[mask], data[mask])
                self.canvas.draw()

    def on_mouse_press(self, event):
        if event.button == 3: # Right click
            self._is_panning = True
            self._pan_start_px = event.x
            self._pan_start_xlim = self.ax.get_xlim()

    def on_mouse_release(self, event):
        if event.button == 3:
            self._is_panning = False

    def on_mouse_motion(self, event):
        if getattr(self, '_is_panning', False) and event.x is not None:
            dx_px = event.x - self._pan_start_px
            width_px = self.ax.bbox.width
            cur_xlim = getattr(self, '_pan_start_xlim', None)
            if cur_xlim is None: return
            
            width_data = cur_xlim[1] - cur_xlim[0]
            dx_data = (dx_px / width_px) * width_data
            
            # Subtracted to drag "against" the mouse (like moving paper)
            self._safe_set_xlim(cur_xlim[0] - dx_data, cur_xlim[1] - dx_data)
            self.canvas.draw()

    def on_scroll(self, event):
        cur_xlim = self.ax.get_xlim()
        if event.key == 'control':
            base_scale = 1.2
            if event.button == 'up':
                scale_factor = 1 / base_scale
            elif event.button == 'down':
                scale_factor = base_scale
            else:
                return
            xdata = event.xdata
            if xdata is None: return
            cur_xlim = self.ax.get_xlim()
            new_width = (cur_xlim[1] - cur_xlim[0]) * scale_factor
            relx = (xdata - cur_xlim[0]) / (cur_xlim[1] - cur_xlim[0])
            self._safe_set_xlim(xdata - new_width * relx, xdata + new_width * (1 - relx))
            self.canvas.draw()
        elif event.key == 'shift':
            width = cur_xlim[1] - cur_xlim[0]
            shift = width * 0.1
            if event.button == 'up': # Scroll Left
                self._safe_set_xlim(cur_xlim[0] - shift, cur_xlim[1] - shift)
            elif event.button == 'down': # Scroll Right
                self._safe_set_xlim(cur_xlim[0] + shift, cur_xlim[1] + shift)
            self.canvas.draw()

    def on_select_waveform(self, xmin, xmax):
        self.cut_audio_var.set(True)
        self.toggle_cut()
        
        def fmt_time(sec):
            h = int(sec // 3600)
            m = int((sec % 3600) // 60)
            s = int(sec % 60)
            if h > 0: return f"{h:02d}:{m:02d}:{s:02d}"
            return f"{m:02d}:{s:02d}"
            
        self.start_time.set(fmt_time(xmin))
        self.end_time.set(fmt_time(xmax))
        
        self.lbl_cut_info.config(text=f"✔ Only the selected part ({fmt_time(xmin)} to {fmt_time(xmax)}) will be sent for transcription.")
        if hasattr(self, '_waveform_data'):
            times, data = self._waveform_data
            self.line_full.set_color('#2A3B4C') # Gray out unselected
            mask = (times >= xmin) & (times <= xmax)
            self.line_sel.set_data(times[mask], data[mask])
            self.canvas.draw()

    def plot_waveform(self, path):
        self.ax.clear()
        self.ax.set_facecolor('#060816')
        self.ax.tick_params(colors='#5F98A7', labelsize=7)
        for spine in self.ax.spines.values():
            spine.set_color('#102A45')
            
        def format_func(x, pos):
            h = int(x // 3600)
            m = int((x % 3600) // 60)
            s = int(x % 60)
            if h > 0: return f"{h:02d}:{m:02d}:{s:02d}"
            return f"{m:02d}:{s:02d}"
        self.ax.xaxis.set_major_formatter(ticker.FuncFormatter(format_func))
            
        try:
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            temp_wav = os.path.join(tempfile.gettempdir(), "waveform_temp.wav")
            # Downsample to 8000Hz mono for fast plotting
            cmd = [ffmpeg_exe, "-y", "-i", path, "-ac", "1", "-ar", "8000", temp_wav]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            data, rate = sf.read(temp_wav)
            os.remove(temp_wav)
            
            # Subsample for even faster plotting if huge
            if len(data) > 800000:
                step = len(data) // 800000
                data = data[::step]
                rate = rate / step
                
            times = np.arange(len(data)) / float(rate)
            
            def _update_gui():
                self._waveform_data = (times, data)
                self.line_full, = self.ax.plot(times, data, color='#00F2FE', linewidth=0.5)
                self.line_sel, = self.ax.plot([], [], color='#00F2FE', linewidth=0.5)
                self.ax.set_xlim(0, times[-1])
                self.canvas.draw()
                self.lbl_cut_info.config(text="✔ Waveform loaded. You can select a region if cutting is required.", fg='#00FF88')
                
            self.root.after(0, _update_gui)
            
        except Exception as e:
            print("Failed to plot waveform:", e)

    def browse_input(self):
        fp = filedialog.askopenfilename(filetypes=[("All Audio Files", "*.wav *.m4a *.mp3 *.flac *.ogg *.aac *.wma"), ("All Files", "*.*")])
        if fp:
            self.input_file.set(fp)
            if not self.output_dir.get():
                self.output_dir.set(os.path.dirname(fp))
            
            self.lbl_cut_info.config(text="⏳ Loading waveform... Please wait.", fg='#FFCC00')
            self.root.update_idletasks()
            
            threading.Thread(target=self.plot_waveform, args=(fp,), daemon=True).start()

    def browse_output(self):
        dp = filedialog.askdirectory()
        if dp:
            self.output_dir.set(dp)

    def toggle_cut(self):
        if self.cut_audio_var.get():
            self.ent_start.config(state='normal')
            self.ent_end.config(state='normal')
        else:
            self.ent_start.config(state='disabled')
            self.ent_end.config(state='disabled')

    def time_to_sec(self, time_str):
        try:
            parts = time_str.split(":")
            if len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            return int(time_str)
        except:
            return None

    def toggle_playback(self):
        import imageio_ffmpeg
        import subprocess
        import tempfile
        if self.is_playing:
            pygame.mixer.music.stop()
            self.btn_play.config(text="▶ PREVIEW")
            self.is_playing = False
        else:
            path = self.input_file.get()
            if not os.path.exists(path):
                messagebox.showerror("Error", "Please select a valid audio file.")
                return
            try:
                # Convert to temp wav to support ALL formats (m4a, etc) via embedded ffmpeg
                ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
                temp_wav = os.path.join(tempfile.gettempdir(), "preview_temp.wav")
                
                # To make preview loading fast, only extract the first 2 minutes
                cmd = [ffmpeg_exe, "-y", "-i", path, "-t", "120", temp_wav]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                pygame.mixer.music.load(temp_wav)
                
                # Check if cut is enabled
                start_sec = 0.0
                if self.cut_audio_var.get():
                    sec = self.time_to_sec(self.start_time.get())
                    if sec is not None: start_sec = float(sec)
                
                pygame.mixer.music.play(start=start_sec)
                self.btn_play.config(text="■ STOP")
                self.is_playing = True
            except Exception as e:
                messagebox.showerror("Error", f"Failed to play audio:\n{e}")

    def set_progress(self, pct: float, status: str = 'PROCESSING'):
        N = len(self._strips)
        filled = int(N * pct / 100)
        for i, sid in enumerate(self._strips):
            if i < filled:
                t = i / max(N - 1, 1)
                if t < 0.5:
                    u = t * 2
                    r = int(u * 157); g = int(242 * (1 - u)); b = 255
                else:
                    u = (t - 0.5) * 2
                    r = int(157 + u * 98); g = 0; b = int(255 * (1 - u * 0.42))
                self.cv.itemconfig(sid, fill=f'#{r:02x}{g:02x}{b:02x}', state='normal')
            else:
                self.cv.itemconfig(sid, state='hidden')

        if filled > 0:
            track_px = W_WIN - 58
            x = 29 + filled * (track_px / N)
            self.cv.coords(self._tip, x-7, self.cv.coords(self._tip)[1], x+7, self.cv.coords(self._tip)[3])
            self.cv.itemconfig(self._tip, state='normal')
        else:
            self.cv.itemconfig(self._tip, state='hidden')

        self.cv.itemconfig(self._lbl_pct, text=f'{int(pct)}%' if pct > 0 else '—')
        if pct == 0: self.cv.itemconfig(self._lbl_status, text='◉  SYSTEM READY', fill=_C['cyan'])
        elif pct >= 100: self.cv.itemconfig(self._lbl_status, text='◉  SEQUENCE COMPLETE', fill=_C['green'])
        else: self.cv.itemconfig(self._lbl_status, text=f'◉  {status}', fill=_C['cyan'])
        self.root.update_idletasks()

    def show_success_dialog(self, out_txt, cleaned_path, input_path):
        top = tk.Toplevel(self.root)
        top.title("Success")
        top.geometry("450x250")
        top.configure(bg=_C['panel'])
        top.resizable(False, False)
        top.geometry("+%d+%d" % (self.root.winfo_x() + 50, self.root.winfo_y() + 100))
        
        tk.Label(top, text="◉ PROCESSING COMPLETE", font=('Courier New', 12, 'bold'), fg=_C['green'], bg=_C['panel']).pack(pady=15)
        tk.Label(top, text=f"Saved to:\n{out_txt}", font=('Courier New', 8), fg=_C['text'], bg=_C['panel'], wraplength=400, justify='center').pack(pady=5)
        
        del_cropped_var = tk.BooleanVar(value=False)
        del_source_var = tk.BooleanVar(value=False)
        
        tk.Checkbutton(top, text="Delete cropped/cleaned audio file", variable=del_cropped_var, bg=_C['panel'], fg=_C['cyan'], selectcolor='#03040A', activebackground=_C['panel'], activeforeground=_C['cyan'], font=('Courier New', 9), highlightthickness=0, bd=0).pack(anchor='w', padx=40, pady=5)
        tk.Checkbutton(top, text="Delete original source file", variable=del_source_var, bg=_C['panel'], fg=_C['cyan'], selectcolor='#03040A', activebackground=_C['panel'], activeforeground=_C['cyan'], font=('Courier New', 9), highlightthickness=0, bd=0).pack(anchor='w', padx=40, pady=5)
        
        def on_ok():
            if del_cropped_var.get() and os.path.exists(cleaned_path):
                try: os.remove(cleaned_path)
                except Exception as e: print("Failed to delete cleaned audio:", e)
            if del_source_var.get() and os.path.exists(input_path):
                try: os.remove(input_path)
                except Exception as e: print("Failed to delete original audio:", e)
            top.destroy()
            
        tk.Button(top, text="OK", command=on_ok, font=('Courier New', 10, 'bold'), fg=_C['panel'], bg=_C['cyan'], relief='flat', cursor='hand2', width=15).pack(pady=15)

    def run_process(self):
        if not self.input_file.get():
            messagebox.showwarning("Input Missing", "Please select an input audio file.")
            return
            
        # Stop playback if running
        if self.is_playing:
            self.toggle_playback()
            
        self.exec_btn.config(state='disabled')
        self.btn_play.config(state='disabled')
        self.chk_cut.config(state='disabled')
        
        threading.Thread(target=self._process_thread, daemon=True).start()

    def _process_thread(self):
        try:
            input_path = self.input_file.get()
            out_dir = self.output_dir.get()
            base_name = os.path.splitext(os.path.basename(input_path))[0]
            
            # 1. CLEAN & CUT
            self.set_progress(10, "INITIALIZING ENHANCEMENT PIPELINE...")
            
            start_sec, end_sec = None, None
            if self.cut_audio_var.get():
                s = self.time_to_sec(self.start_time.get())
                e = self.time_to_sec(self.end_time.get())
                if s is not None and e is not None and s < e:
                    start_sec = s
                    end_sec = e
                    base_name += f"_cut_{s}-{e}"
            
            cleaned_path = os.path.join(out_dir, base_name + "_cleaned.wav")
            
            self.set_progress(25, "APPLYING NOISE GATING & EQ...")
            enhance_audio(input_path, cleaned_path, start_sec=start_sec, end_sec=end_sec)
            self.set_progress(50, "AUDIO ENHANCEMENT COMPLETE.")
            
            # 2. TRANSCRIBE
            self.set_progress(60, "CONNECTING TO NEURAL ENGINE...")
            
            lang = self.language_var.get()
            lang_code = "bn" if lang == "Bengali" else "en" if lang == "English" else None
            keywords = self.keywords_var.get()
            
            model_choice = self.model_var.get()
            transcript_text = ""
            
            self.set_progress(75, f"TRANSCRIBING ({model_choice.upper()})...")
            
            if "ElevenLabs" in model_choice:
                transcript_text = run_elevenlabs(cleaned_path, lang_code, keywords)
            elif "Groq" in model_choice:
                transcript_text = run_groq(cleaned_path, lang_code, keywords)
            else:
                transcript_text = run_local_whisper(cleaned_path, lang_code, keywords)
                
            self.set_progress(90, "FINALIZING TRANSCRIPT...")
            
            # Save Transcript
            engine_name = model_choice.split()[0].lower()
            out_txt = os.path.join(out_dir, f"{base_name}_{engine_name}.txt")
            with open(out_txt, "w", encoding="utf-8") as f:
                f.write(transcript_text)
                
            self.set_progress(100, "SEQUENCE COMPLETE")
            self.root.after(0, lambda o=out_txt, c=cleaned_path, i=input_path: self.show_success_dialog(o, c, i))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Pipeline Failed:\n{str(e)}"))
            self.set_progress(0, "SYSTEM READY")
        finally:
            self.root.after(0, lambda: self.exec_btn.config(state='normal'))
            self.root.after(0, lambda: self.btn_play.config(state='normal'))
            self.root.after(0, lambda: self.chk_cut.config(state='normal'))

if __name__ == "__main__":
    root = tk.Tk()
    app = TranscriptionApp(root)
    root.mainloop()
