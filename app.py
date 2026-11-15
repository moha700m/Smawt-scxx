import os
import shutil
import subprocess
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime

class SMAETREC:
    def __init__(self, root):
        self.root=root; self.root.title('SMAET REC'); self.root.geometry('900x620'); self.root.minsize(760,520)
        self.root.configure(bg='#10131b'); self.proc=None; self.started_at=None; self.output_path=None; self.recording=False
        self.save_dir=os.path.join(os.path.expanduser('~'),'Videos','SMAET REC'); os.makedirs(self.save_dir,exist_ok=True)
        self._build(); self._tick()
    def _build(self):
        h=tk.Frame(self.root,bg='#171d2a',padx=24,pady=18); h.pack(fill='x')
        tk.Label(h,text='SMAET REC',bg='#171d2a',fg='white',font=('Segoe UI',23,'bold')).pack(anchor='e')
        tk.Label(h,text='استوديو تسجيل بسيط — كل شيء يبقى على جهازك',bg='#171d2a',fg='#9eabc1',font=('Segoe UI',11)).pack(anchor='e')
        body=tk.Frame(self.root,bg='#10131b',padx=24,pady=20); body.pack(fill='both',expand=True)
        p=tk.Frame(body,bg='#171d2a',padx=18,pady=18); p.pack(fill='both',expand=True)
        tk.Label(p,text='تسجيل شاشة الكمبيوتر',bg='#171d2a',fg='white',font=('Segoe UI',16,'bold')).pack(anchor='e')
        tk.Label(p,text='يتم التقاط سطح المكتب وحفظه كفيديو MP4.',bg='#171d2a',fg='#9eabc1',font=('Segoe UI',10)).pack(anchor='e',pady=(5,16))
        self.status=tk.Label(p,text='● جاهز للتسجيل',bg='#202a3a',fg='#82e0b0',font=('Segoe UI',12,'bold'),padx=14,pady=10); self.status.pack(fill='x')
        self.timer=tk.Label(p,text='00:00:00',bg='#171d2a',fg='white',font=('Consolas',30,'bold')); self.timer.pack(pady=18)
        c=tk.Frame(p,bg='#171d2a'); c.pack(fill='x',pady=10)
        tk.Label(c,text='معدل الإطارات',bg='#171d2a',fg='#dce4f2').pack(side='right',padx=8)
        self.fps=tk.StringVar(value='30'); ttk.Combobox(c,textvariable=self.fps,values=('30','60'),state='readonly',width=7).pack(side='right')
        self.start_btn=tk.Button(c,text='● بدء التسجيل',command=self.start,bg='#1e9b68',fg='white',relief='flat',padx=22,pady=12,font=('Segoe UI',11,'bold')); self.start_btn.pack(side='right',padx=10)
        self.stop_btn=tk.Button(c,text='■ إيقاف التسجيل',command=self.stop,bg='#a33c4b',fg='white',relief='flat',padx=22,pady=12,font=('Segoe UI',11,'bold'),state='disabled'); self.stop_btn.pack(side='right')
        f=tk.Frame(body,bg='#171d2a',padx=16,pady=14); f.pack(fill='x',pady=(14,0))
        tk.Label(f,text='مجلد الحفظ',bg='#171d2a',fg='white',font=('Segoe UI',11,'bold')).pack(anchor='e')
        row=tk.Frame(f,bg='#171d2a'); row.pack(fill='x',pady=8)
        tk.Button(row,text='اختيار مجلد',command=self.choose,bg='#293449',fg='white',relief='flat',padx=14,pady=8).pack(side='right')
        self.folder=tk.Label(row,text=self.save_dir,bg='#171d2a',fg='#9eabc1',anchor='e'); self.folder.pack(side='right',fill='x',expand=True,padx=12)
        tk.Label(body,text='محلي فقط • لا خادم شبكي • لا رفع سحابي',bg='#10131b',fg='#718098').pack(pady=14)
    def choose(self):
        p=filedialog.askdirectory(initialdir=self.save_dir)
        if p: self.save_dir=p; self.folder.config(text=p)
    def start(self):
        ff=shutil.which('ffmpeg')
        if not ff: messagebox.showerror('FFmpeg غير موجود','ثبّت FFmpeg وأضفه إلى PATH ثم أعد تشغيل التطبيق.'); return
        if self.recording:return
        self.output_path=os.path.join(self.save_dir,'SMAET_'+datetime.now().strftime('%Y-%m-%d_%H-%M-%S')+'.mp4')
        fps=self.fps.get(); cmd=[ff,'-y','-f','gdigrab','-framerate',fps,'-i','desktop','-an','-c:v','libx264','-preset','veryfast','-pix_fmt','yuv420p','-r',fps,'-movflags','+faststart',self.output_path]
        try:
            self.proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            time.sleep(.4)
            if self.proc.poll() is not None: raise RuntimeError('تعذر بدء الالتقاط. تحقق من توافق FFmpeg وصلاحيات سطح المكتب.')
            self.started_at=time.time(); self.recording=True; self.status.config(text='● جارٍ التسجيل',fg='#ff8d9a',bg='#3a202b'); self.start_btn.config(state='disabled'); self.stop_btn.config(state='normal')
        except Exception as e: self.proc=None; messagebox.showerror('تعذر بدء التسجيل',str(e))
    def stop(self):
        if not self.recording or not self.proc:return
        p=self.proc; self.proc=None; self.recording=False; self.stop_btn.config(state='disabled'); self.status.config(text='◌ جارٍ حفظ الفيديو...',fg='#f2c879',bg='#3a3322')
        def finish():
            try: p.stdin.write(b'q\n'); p.stdin.flush(); p.wait(timeout=25)
            except Exception:
                try:p.terminate();p.wait(timeout=5)
                except Exception:pass
            self.root.after(0,self.done)
        threading.Thread(target=finish,daemon=True).start()
    def done(self):
        self.start_btn.config(state='normal'); self.stop_btn.config(state='disabled'); self.timer.config(text='00:00:00'); self.status.config(text='● انتهى التسجيل',fg='#82e0b0',bg='#202a3a')
        if self.output_path and os.path.isfile(self.output_path) and os.path.getsize(self.output_path)>0: messagebox.showinfo('اكتمل التسجيل','تم حفظ الفيديو في:\n'+self.output_path)
        else: messagebox.showwarning('تنبيه','لم يتم إنشاء ملف فيديو صالح.')
    def _tick(self):
        if self.recording and self.started_at:
            s=int(time.time()-self.started_at); self.timer.config(text=f'{s//3600:02d}:{s%3600//60:02d}:{s%60:02d}')
        self.root.after(500,self._tick)
    def close(self):
        if self.recording:
            if messagebox.askyesno('إغلاق','يوجد تسجيل جارٍ. أوقفه قبل الإغلاق؟'): self.stop(); self.root.after(1200,self.root.destroy)
            return
        self.root.destroy()
if __name__=='__main__':
    root=tk.Tk(); app=SMAETREC(root); root.protocol('WM_DELETE_WINDOW',app.close); root.mainloop()
