import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import threading
import re

# Dicionário com perfis: (resolução, perfil ProRes)
perfil_opcoes = {
    "Baixa (360p - Proxy)": ("640x360", "0"),
    "Média (720p - LT)":    ("1280x720", "1"),
    "Alta (1080p - 422)":   ("1920x1080", "2"),
    "Máxima (original - HQ)": (None, "3")
}

def selecionar_arquivo():
    caminho = filedialog.askopenfilename(filetypes=[("Vídeos", "*.mp4 *.mkv *.mov")])
    entrada_var.set(caminho)

def selecionar_saida():
    caminho = filedialog.asksaveasfilename(defaultextension=".mov", filetypes=[("MOV files", "*.mov")])
    saida_var.set(caminho)

def converter():
    entrada = entrada_var.get()
    saida = saida_var.get()
    perfil_nome = perfil_var.get()

    if not entrada or not saida or perfil_nome not in perfil_opcoes:
        messagebox.showerror("Erro", "Preencha todos os campos corretamente.")
        return

    log_text.delete(1.0, tk.END)
    progress_bar["value"] = 0
    percentual_label.config(text="0%")

    resolucao, perfil = perfil_opcoes[perfil_nome]

    duracao_cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", entrada
    ]
    try:
        duracao = float(subprocess.check_output(duracao_cmd).decode().strip())
    except Exception:
        messagebox.showerror("Erro", "Não foi possível obter a duração do vídeo.")
        return

    comando = [
        "ffmpeg", "-i", entrada,
        "-c:v", "prores_ks", "-profile:v", perfil,
        "-pix_fmt", "yuv422p10le",
        "-color_range", "tv", "-colorspace", "bt709",
        "-color_primaries", "bt709", "-color_trc", "bt709"
    ]
    if resolucao:
        comando += ["-s", resolucao]
    comando += ["-c:a", "pcm_s16le", saida]

    def executar_ffmpeg():
        try:
            processo = subprocess.Popen(
                comando, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True, bufsize=1
            )
            for linha in processo.stdout:
                log_text.insert(tk.END, linha)
                log_text.see(tk.END)

                match = re.search(r"time=(\d+):(\d+):([\d\.]+)", linha)
                if match:
                    h, m, s = map(float, match.groups())
                    segundos = h * 3600 + m * 60 + s
                    porcentagem = min(int((segundos / duracao) * 100), 100)
                    progress_bar["value"] = porcentagem
                    percentual_label.config(text=f"{porcentagem}%")

            processo.wait()
            if processo.returncode == 0:
                messagebox.showinfo("Sucesso", "Conversão concluída com sucesso!")
            else:
                messagebox.showerror("Erro", f"Ocorreu um erro. Código: {processo.returncode}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro durante execução: {e}")

    thread = threading.Thread(target=executar_ffmpeg)
    thread.start()

# Criação da janela
root = tk.Tk()
root.title("Conversor de video para DaVinci-Resolve Free")
root.resizable(False, False)
root.configure(padx=20, pady=20)

entrada_var = tk.StringVar()
saida_var = tk.StringVar()
perfil_var = tk.StringVar(value="Máxima (original - HQ)")

# Frame principal
main_frame = tk.Frame(root)
main_frame.pack(anchor="w")

# Entrada
entrada_frame = tk.Frame(main_frame)
entrada_frame.pack(pady=8, fill=tk.X)
tk.Label(entrada_frame, text="Arquivo de entrada:").pack(anchor='w')
entrada_inner = tk.Frame(entrada_frame)
entrada_inner.pack(fill=tk.X)
entrada_entry = tk.Entry(entrada_inner, textvariable=entrada_var, width=60)
entrada_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
tk.Button(entrada_inner, text="Selecionar...", command=selecionar_arquivo).pack(side=tk.RIGHT, padx=6)

# Saída
saida_frame = tk.Frame(main_frame)
saida_frame.pack(pady=8, fill=tk.X)
tk.Label(saida_frame, text="Arquivo de saída:").pack(anchor='w')
saida_inner = tk.Frame(saida_frame)
saida_inner.pack(fill=tk.X)
saida_entry = tk.Entry(saida_inner, textvariable=saida_var, width=60)
saida_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
tk.Button(saida_inner, text="Salvar como...", command=selecionar_saida).pack(side=tk.RIGHT, padx=6)

# Perfil de conversão
perfil_frame = tk.Frame(main_frame)
perfil_frame.pack(pady=(0,35), fill=tk.X)
tk.Label(perfil_frame, text="Qualidade de conversão:").pack(anchor='w')
perfil_inner = tk.Frame(perfil_frame)
perfil_inner.pack(fill=tk.X)
perfil_menu = ttk.OptionMenu(perfil_inner, perfil_var, perfil_var.get(), *perfil_opcoes.keys())
perfil_menu.pack(side=tk.LEFT, fill=tk.X, expand=True)

# Botão de conversão
tk.Button(
    root,
    text="Converter para ProRes",
    command=converter,
    bg="#3cb371",
    fg="white",
    activebackground="#2e8b57",
    cursor="hand2",
    font=("Arial", 13, "bold"),
    width=21,                    
    height=2
).pack(pady=(8, 23))


# Barra de progresso
progress_frame = tk.Frame(main_frame)
progress_frame.pack(fill=tk.X, pady=5)
progress_bar = ttk.Progressbar(progress_frame, length=400)
progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
percentual_label = tk.Label(progress_frame, text="0%")
percentual_label.pack(side=tk.RIGHT, padx=5)

# Log
tk.Label(main_frame, text="Log de execução do FFmpeg:").pack(anchor='w', pady=(8, 0))
log_text = tk.Text(main_frame, height=15, width=85)
log_text.pack(padx=2, pady=(0, 10))

root.mainloop()
