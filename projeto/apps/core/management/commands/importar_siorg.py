from django.core.management.base import BaseCommand
import os, time, zipfile, shutil
import pyautogui
from datetime import datetime
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ---------- parâmetros ----------
URL_DATASET = (
    "https://dados.gov.br/dados/conjuntos-dados/"
    "dados-da-estrutura-organizacional-do-poder-executivo-federal-sistema-siorg"
)
MESES_PT = {
    1:"janeiro",2:"fevereiro",3:"março",4:"abril",5:"maio",6:"junho",
    7:"julho",8:"agosto",9:"setembro",10:"outubro",11:"novembro",12:"dezembro"
}
VERSOES_MESES = {
    1:"Vjan",2:"Vfev",3:"Vmar",4:"Vabr",5:"Vmai",6:"Vjun",
    7:"Vjul",8:"Vago",9:"Vset",10:"Vout",11:"Vnov",12:"Vdez"
}
COL_FILTRAR = "nome_orgao_entidade"
OUT_BASENAME = "siorg_distribuicao_cargos_funcoes"
# ---------------------------------

def mes_ano():
    hoje = datetime.now()
    return MESES_PT[hoje.month], hoje.year

def versao_mes():
    hoje = datetime.now()
    return VERSOES_MESES[hoje.month]

def prepara_driver(download_dir):
    chrome_opts = webdriver.ChromeOptions()
    # chrome_opts.add_argument("--headless=new")          # REMOVENDO HEADLESS - PYAUTOGUI PRECISA VER A TELA
    chrome_opts.add_argument("--no-sandbox")
    chrome_opts.add_argument("--disable-gpu")
    chrome_prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    }
    chrome_opts.add_experimental_option("prefs", chrome_prefs)
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(
        service=service,
        options=chrome_opts
    )
    driver.set_page_load_timeout(60)
    return driver

def extrair_csv_do_zip(zip_path):
    with zipfile.ZipFile(zip_path) as z:
        csvs = [n for n in z.namelist() if n.lower().endswith(".csv")]
        if not csvs:
            raise RuntimeError("ZIP sem CSV interno.")
        with z.open(csvs[0]) as f:
            try:
                # Tenta separador ponto-e-vírgula primeiro
                return pd.read_csv(f, sep=";", encoding="latin1")
            except Exception:
                # Se der erro, tenta vírgula com UTF-8
                f.seek(0)  # Volta ao início do arquivo
                return pd.read_csv(f, sep=",", encoding="utf-8")

class Command(BaseCommand):
    help = 'Baixa, processa e prepara a planilha SIORG para importação.'

    def handle(self, *args, **options):
        mes, ano = mes_ano()
        versao = versao_mes()
        tmp_dir = os.path.abspath("_tmp_siorg_download")

        # Limpa a pasta se ela já existir
        if os.path.exists(tmp_dir):
            try:
                shutil.rmtree(tmp_dir)
                self.stdout.write(self.style.WARNING(f"[DEBUG] Limpou pasta temporária existente"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"[DEBUG] Erro ao limpar pasta: {e}"))
        os.makedirs(tmp_dir, exist_ok=True)
        self.stdout.write(self.style.SUCCESS(f"[DEBUG] Pasta de download criada: {tmp_dir}"))

        # Inicia Chrome VISÍVEL
        driver = prepara_driver(tmp_dir)
        try:
            driver.get(URL_DATASET)
            driver.fullscreen_window()
            time.sleep(2)
            wait = WebDriverWait(driver, 30)
            recursos_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(.,'Recursos')]"))
            )
            recursos_btn.click()
            time.sleep(2)
            siorg_headers = wait.until(
                EC.presence_of_all_elements_located((By.XPATH, "//h4[contains(text(), 'SIORG')]"))
            )
            target_header = None
            for header in siorg_headers:
                if f"para o mês de {mes}/{ano}" in header.text:
                    target_header = header
                    break
            if not target_header and siorg_headers:
                target_header = siorg_headers[-1]
            if not target_header:
                raise RuntimeError("Não encontrou dataset")
            self.stdout.write(self.style.SUCCESS(f"[INFO] Dataset encontrado: {target_header.text}"))
            driver.execute_script("arguments[0].scrollIntoView(true);", target_header)
            time.sleep(2)
            self.stdout.write(self.style.SUCCESS(f"[INFO] Clicando na posição capturada: x=963, y=191"))
            pyautogui.click(963, 191)  # NOVA POSIÇÃO CORRETA
            self.stdout.write(self.style.SUCCESS("[INFO] Aguardando download..."))
            time.sleep(5)
            arquivos = os.listdir(tmp_dir)
            if not arquivos:
                downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
                if os.path.exists(downloads_path):
                    arquivos_downloads = [f for f in os.listdir(downloads_path) 
                                        if f.lower().endswith(('.zip', '.xlsx', '.csv'))]
                    arquivos_recentes = []
                    for arquivo in arquivos_downloads:
                        arquivo_path = os.path.join(downloads_path, arquivo)
                        if time.time() - os.path.getmtime(arquivo_path) < 30:
                            arquivos_recentes.append(arquivo)
                    if arquivos_recentes:
                        arquivo_recente = arquivos_recentes[0]
                        src = os.path.join(downloads_path, arquivo_recente)
                        dst = os.path.join(tmp_dir, arquivo_recente)
                        shutil.move(src, dst)
                        arquivos = [arquivo_recente]
            if not arquivos:
                raise RuntimeError("Nenhum arquivo foi baixado")
            zip_baixado = os.path.join(tmp_dir, arquivos[0])
            self.stdout.write(self.style.SUCCESS(f"[OK] Arquivo baixado: {zip_baixado}"))
        finally:
            driver.quit()
        # 7. ler CSV interno
        df = extrair_csv_do_zip(zip_baixado)
        self.stdout.write(self.style.SUCCESS(f"[OK] CSV: {len(df):,} linhas × {len(df.columns)} colunas"))
        # 8. filtrar "Ministério"
        if COL_FILTRAR not in df.columns:
            raise KeyError(f"Coluna '{COL_FILTRAR}' não encontrada. Colunas: {list(df.columns)}")
        df = df[df[COL_FILTRAR].astype(str).str.startswith("Ministério")]
        self.stdout.write(self.style.SUCCESS(f"[OK] Após filtro: {len(df):,} linhas"))
        self.stdout.write(self.style.WARNING(f"[DEBUG] Colunas disponíveis: {list(df.columns)}"))
        posicoes_remover = [4, 5, 6, 14, 15, 16, 17, 28, 37]  # E, F, G, O, P, Q, R, AC, AL
        colunas_remover = []
        for pos in posicoes_remover:
            if pos < len(df.columns):
                colunas_remover.append(df.columns[pos])
        if colunas_remover:
            df = df.drop(columns=colunas_remover)
            self.stdout.write(self.style.SUCCESS(f"[OK] Removidas {len(colunas_remover)} colunas: {colunas_remover}"))
        else:
            self.stdout.write(self.style.WARNING("[INFO] Nenhuma das colunas especificadas foi encontrada para remoção"))
        out_file = f"{OUT_BASENAME}_{versao}{ano}.xlsx"
        df.to_excel(out_file, index=False)
        self.stdout.write(self.style.SUCCESS(f"[OK] Salvou: {out_file}"))
        # Aqui será feita a importação para o banco de dados
        self.stdout.write(self.style.WARNING("[IMPORTAÇÃO] Adapte aqui para importar os dados para o banco de dados!"))
        # 10. limpeza tmp
        try:
            shutil.rmtree(tmp_dir)
            self.stdout.write(self.style.SUCCESS("[OK] Limpeza concluída"))
        except Exception:
            pass
        # 11. Deletar planilha após importação (adicione após importar para o banco)
        # os.remove(out_file)