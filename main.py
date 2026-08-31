import os
import sys
import tempfile
import threading
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk
import yt_dlp

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

CORES = {
    "fundo": "#121212",
    "campo": "#1E1E1E",
    "borda": "#333333",
    "secundaria": "#2A2A2A",
    "hover": "#333333",
    "vermelho": "#E53935",
    "vermelho_hover": "#C62828",
    "verde": "#4CAF50",
    "amarelo": "#FFB300",
    "erro": "#FF5252",
    "texto": "#FFFFFF",
    "texto_secundario": "#AAAAAA",
}

def obter_caminho_recurso(caminho_relativo):
    """Retorna o caminho correto dos recursos, inclusive no .exe."""
    base = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base, caminho_relativo)


def obter_ffmpeg():
    """Retorna o caminho do FFmpeg."""
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return None


def criar_opcoes_download(
    pasta_destino,
    formato,
    qualidade,
    progress_hook
):
    """Monta as opções utilizadas pelo yt-dlp."""

    opcoes = {
        "progress_hooks": [progress_hook],
        "outtmpl": "%(title)s.%(ext)s",
        "paths": {
            "home": pasta_destino,
            "temp": tempfile.gettempdir(),
        },
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "nooverwrites": True,
    }

    ffmpeg = obter_ffmpeg()

    if ffmpeg:
        opcoes["ffmpeg_location"] = ffmpeg

    if formato == "MP3 (Áudio)":
        opcoes.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        })

        return opcoes

    opcoes["merge_output_format"] = "mp4"

    resolucoes = {
        "1080p": "1080",
        "720p": "720",
        "480p": "480",
        "360p": "360",
    }

    limite = resolucoes.get(qualidade)

    if limite:
        opcoes["format"] = (
            f"bestvideo[height<={limite}]+bestaudio/"
            f"best[height<={limite}]/best"
        )
    else:
        opcoes["format"] = "bestvideo+bestaudio/best"

    return opcoes


def baixar(url, opcoes):
    """Executa o download."""
    with yt_dlp.YoutubeDL(opcoes) as ytdl:
        ytdl.download([url])

class YouTubeDownloader(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.pasta_destino = str(Path.home() / "Downloads")
        self.download_em_andamento = False

        self.configurar_janela()
        self.criar_interface()

    def configurar_janela(self):
        self.title("YouTube Downloader")
        self.geometry("460x510")
        self.resizable(False, False)
        self.configure(fg_color=CORES["fundo"])

        icone = obter_caminho_recurso("logo.ico")

        if os.path.exists(icone):
            self.iconbitmap(icone)

    def criar_interface(self):

        ctk.CTkLabel(
            self,
            text="Downloader de vídeos do YouTube",
            font=("Helvetica", 18, "bold")
        ).pack(pady=(20, 10))

        # URL
        self.campo_url = ctk.CTkEntry(
            self,
            placeholder_text="Cole o link do vídeo aqui...",
            width=380,
            height=40,
            fg_color=CORES["campo"],
            border_color=CORES["borda"],
            text_color=CORES["texto"],
            placeholder_text_color="#666666",
            corner_radius=8,
        )
        self.campo_url.pack(pady=8)

        # Pasta
        container_pasta = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        container_pasta.pack(pady=5)

        self.campo_pasta = ctk.CTkEntry(
            container_pasta,
            width=290,
            height=35,
            fg_color=CORES["campo"],
            border_color=CORES["borda"],
            text_color=CORES["texto_secundario"],
            corner_radius=6,
        )
        self.campo_pasta.insert(0, self.pasta_destino)
        self.campo_pasta.configure(state="disabled")
        self.campo_pasta.pack(side="left", padx=(0, 5))

        ctk.CTkButton(
            container_pasta,
            text="Pasta",
            command=self.selecionar_pasta,
            width=85,
            height=35,
            fg_color=CORES["secundaria"],
            hover_color=CORES["hover"],
            text_color=CORES["texto"],
            corner_radius=6,
        ).pack(side="left")

        # Formato
        self.formato = ctk.StringVar(value="MP4 (Vídeo)")

        ctk.CTkSegmentedButton(
            self,
            values=["MP4 (Vídeo)", "MP3 (Áudio)"],
            variable=self.formato,
            command=self.mudar_formato,
            width=260,
            height=32,
            fg_color=CORES["campo"],
            selected_color="#D32F2F",
            selected_hover_color="#B71C1C",
            unselected_color=CORES["campo"],
            unselected_hover_color=CORES["secundaria"],
            text_color=CORES["texto"],
            corner_radius=6,
        ).pack(pady=10)

        # Qualidade
        container_qualidade = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        container_qualidade.pack(pady=5)

        ctk.CTkLabel(
            container_qualidade,
            text="Resolução:",
            font=("Helvetica", 12),
            text_color=CORES["texto_secundario"],
        ).pack(side="left", padx=(0, 10))

        self.qualidade = ctk.StringVar(
            value="Melhor Qualidade"
        )

        self.menu_qualidade = ctk.CTkOptionMenu(
            container_qualidade,
            values=[
                "Melhor Qualidade",
                "1080p",
                "720p",
                "480p",
                "360p",
            ],
            variable=self.qualidade,
            width=160,
            height=32,
            fg_color=CORES["campo"],
            button_color=CORES["secundaria"],
            button_hover_color=CORES["hover"],
            dropdown_fg_color=CORES["campo"],
            dropdown_hover_color=CORES["hover"],
            dropdown_text_color=CORES["texto"],
            text_color=CORES["texto"],
            corner_radius=6,
        )
        self.menu_qualidade.pack(side="left")

        # Progresso
        self.barra_progresso = ctk.CTkProgressBar(
            self,
            width=380,
            height=6,
            fg_color=CORES["campo"],
            progress_color=CORES["vermelho"],
            corner_radius=3,
        )
        self.barra_progresso.set(0)
        self.barra_progresso.pack(pady=(15, 5))

        self.texto_porcentagem = ctk.CTkLabel(
            self,
            text="0%",
            font=("Helvetica", 11),
            text_color="#888888",
        )
        self.texto_porcentagem.pack()

        # Download
        self.botao_baixar = ctk.CTkButton(
            self,
            text="BAIXAR AGORA",
            command=self.iniciar_download,
            width=200,
            height=42,
            fg_color=CORES["vermelho"],
            hover_color=CORES["vermelho_hover"],
            font=("Helvetica", 13, "bold"),
            corner_radius=8,
        )
        self.botao_baixar.pack(pady=15)

        # Status
        self.texto_status = ctk.CTkLabel(
            self,
            text="",
            font=("Helvetica", 11),
            text_color="#777777",
        )
        self.texto_status.pack(pady=5)

    def selecionar_pasta(self):
        pasta = filedialog.askdirectory(
            title="Selecione a pasta onde deseja salvar"
        )

        if not pasta:
            return

        self.pasta_destino = pasta

        self.campo_pasta.configure(state="normal")
        self.campo_pasta.delete(0, "end")
        self.campo_pasta.insert(0, pasta)
        self.campo_pasta.configure(state="disabled")

    def mudar_formato(self, formato):
        self.menu_qualidade.configure(
            state="disabled" if formato == "MP3 (Áudio)" else "normal"
        )

    def mostrar_status(self, mensagem, cor):
        self.texto_status.configure(
            text=mensagem,
            text_color=cor
        )

    def atualizar_progresso(self, dados):
        if dados["status"] == "downloading":

            total = (
                dados.get("total_bytes")
                or dados.get("total_bytes_estimate")
            )

            baixado = dados.get("downloaded_bytes", 0)

            if total:
                progresso = baixado / total

                self.after(
                    0,
                    self.atualizar_barra,
                    progresso
                )

        elif dados["status"] == "finished":
            self.after(
                0,
                self.atualizar_barra,
                1
            )

    def atualizar_barra(self, progresso):
        self.barra_progresso.set(progresso)
        self.texto_porcentagem.configure(
            text=f"{int(progresso * 100)}%"
        )

    def iniciar_download(self):

        if self.download_em_andamento:
            return

        url = self.campo_url.get().strip()

        if not url:
            self.mostrar_status(
                "Insira uma URL válida!",
                CORES["erro"]
            )
            return

        self.download_em_andamento = True

        self.botao_baixar.configure(
            state="disabled"
        )

        self.barra_progresso.set(0)
        self.texto_porcentagem.configure(text="0%")

        self.mostrar_status(
            "Iniciando download...",
            CORES["amarelo"]
        )

        threading.Thread(
            target=self.processar_download,
            args=(
                url,
                self.formato.get(),
                self.qualidade.get(),
            ),
            daemon=True
        ).start()

    def processar_download(
        self,
        url,
        formato,
        qualidade
    ):
        opcoes = criar_opcoes_download(
            self.pasta_destino,
            formato,
            qualidade,
            self.atualizar_progresso
        )

        try:
            baixar(url, opcoes)

            self.after(
                0,
                self.finalizar_download,
                "Download concluído com sucesso!",
                CORES["verde"]
            )

        except yt_dlp.utils.DownloadError as erro:

            self.after(
                0,
                self.finalizar_download,
                f"Erro no download: {erro}",
                CORES["erro"]
            )

        except Exception as erro:  # noqa: BLE001

            self.after(
                0,
                self.finalizar_download,
                f"Erro inesperado: {erro}",
                CORES["erro"]
            )

    def finalizar_download(self, mensagem, cor):
        self.mostrar_status(
            mensagem,
            cor
        )

        self.botao_baixar.configure(
            state="normal"
        )

        self.download_em_andamento = False

app = YouTubeDownloader()
app.mainloop()