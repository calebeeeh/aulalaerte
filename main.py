import time
import re
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from sqlalchemy import create_engine, text

# ========================
# CONFIG BANCO MYSQL
# ========================
host = "127.0.0.1"
port = 3306
user = "root"
password = "Zen%402425"
banco_dados = "db_imoveis"

engine = create_engine(f"mysql+pymysql://{user}:{password}@{host}:{port}/{banco_dados}")

# ========================
# PARÂMETROS
# ========================
tipo = "ALUGUEL"
tipos = "APARTAMENTO"
estado = "DF"
cidade = "TAGUATINGA"
bairro = "TAGUATINGA NORTE"
url = "https://www.dfimoveis.com.br/"

# ========================
# FUNÇÕES AUXILIARES
# ========================
def limpar_preco(texto):
    if not texto:
        return None
    texto = texto.replace("R$", "").replace(".", "").replace(",", ".")
    return float(texto.strip())

def extrair_numero(texto):
    if not texto:
        return None
    match = re.search(r"\d+", texto)
    return int(match.group()) if match else None

def limpar_metragem(texto):
    if not texto:
        return None
    match = re.search(r"\d+", texto)
    return float(match.group()) if match else None

def get_or_create(conn, tabela, coluna, valor):
    result = conn.execute(
        text(f"SELECT id FROM {tabela} WHERE {coluna} = :valor"),
        {"valor": valor}
    ).fetchone()

    if result:
        return result[0]

    result = conn.execute(
        text(f"INSERT INTO {tabela} ({coluna}) VALUES (:valor)"),
        {"valor": valor}
    )
    return result.lastrowid

# ========================
# DRIVER
# ========================
options = uc.ChromeOptions()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--start-maximized")

driver = uc.Chrome(
    options=options,
    version_main=146,
    use_subprocess=True
)

wait = WebDriverWait(driver, 20)

# ========================
# SELECT2
# ========================
def selecionar_select2(campo_id, valor):
    campo = wait.until(EC.element_to_be_clickable((By.ID, campo_id)))

    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", campo)
    time.sleep(1)

    try:
        campo.click()
    except:
        driver.execute_script("arguments[0].click();", campo)

    busca = wait.until(
        EC.visibility_of_element_located((By.CLASS_NAME, "select2-search__field"))
    )

    busca.clear()
    busca.send_keys(valor)
    time.sleep(2)

    opcoes = wait.until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, "select2-results__option"))
    )

    for opcao in opcoes:
        if valor.upper() in opcao.text.upper():
            opcao.click()
            return

    print("Opções disponíveis:")
    for op in opcoes:
        print(op.text)

    raise Exception(f"Não encontrou: {valor}")

# ========================
# SCRAPING
# ========================
total = 0

try:
    driver.get(url)
    time.sleep(2)

    # cookies
    try:
        botao_cookies = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "btn-lgpd"))
        )
        botao_cookies.click()
        time.sleep(1)
    except:
        pass

    # filtros
    selecionar_select2("select2-negocios-container", tipo)
    time.sleep(2)

    selecionar_select2("select2-tipos-container", tipos)
    time.sleep(2)

    selecionar_select2("select2-estados-container", estado)
    time.sleep(3)

    selecionar_select2("select2-cidades-container", cidade)
    time.sleep(3)

    selecionar_select2("select2-bairros-container", bairro)
    time.sleep(3)

    # buscar
    botao_busca = wait.until(
        EC.element_to_be_clickable((By.ID, "botaoDeBusca"))
    )
    botao_busca.click()

    pagina = 1

    # conexão única (mais eficiente)
    with engine.begin() as conn:

        while True:
            wait.until(
                EC.presence_of_element_located(
                    (By.ID, "resultadoDaBuscaDeImoveis")
                )
            )

            cards = driver.find_elements(
                By.XPATH,
                "//div[@id='resultadoDaBuscaDeImoveis']//a[contains(@href, '/imovel/')]",
            )

            print(f"Página {pagina}: {len(cards)} anúncios encontrados")

            for card in cards:
                try:
                    titulo = card.find_element(By.CLASS_NAME, "ellipse-text").text.strip()
                except:
                    titulo = ""

                try:
                    preco = card.find_element(By.CLASS_NAME, "body-large").text.strip()
                except:
                    preco = ""

                try:
                    quartos_txt = card.find_element(
                        By.XPATH, ".//div[contains(text(), 'Quarto')]"
                    ).text
                except:
                    quartos_txt = ""

                try:
                    metragem_txt = card.find_element(
                        By.XPATH, ".//div[contains(text(), 'm²')]"
                    ).text
                except:
                    metragem_txt = ""

                try:
                    vagas_txt = card.find_element(
                        By.XPATH, ".//div[contains(text(), 'Vaga')]"
                    ).text
                except:
                    vagas_txt = ""

                # limpeza
                preco_limpo = limpar_preco(preco)
                quartos = extrair_numero(quartos_txt)
                metragem = limpar_metragem(metragem_txt)
                vagas = extrair_numero(vagas_txt)

                # FKs
                id_tipo_imovel = get_or_create(conn, "tb_tipo_imovel", "nome_tipo_imovel", tipos)
                id_operacao = get_or_create(conn, "tb_tipo_operacao", "nome_operacao", tipo)
                id_imobiliaria = get_or_create(conn, "tb_imobiliaria", "nome_imobiliaria", "Não informada")

                # insert
                conn.execute(text("""
                    INSERT INTO tb_imoveis (
                        endereco,
                        tamanho_m2,
                        preco,
                        quartos,
                        vagas,
                        suites,
                        id_operacao,
                        id_imobiliaria,
                        id_tipo_imovel
                    )
                    VALUES (
                        :endereco,
                        :tamanho_m2,
                        :preco,
                        :quartos,
                        :vagas,
                        :suites,
                        :id_operacao,
                        :id_imobiliaria,
                        :id_tipo_imovel
                    )
                """), {
                    "endereco": titulo,
                    "tamanho_m2": metragem,
                    "preco": preco_limpo,
                    "quartos": quartos,
                    "vagas": vagas,
                    "suites": None,
                    "id_operacao": id_operacao,
                    "id_imobiliaria": id_imobiliaria,
                    "id_tipo_imovel": id_tipo_imovel
                })

                total += 1

            # próxima página
            try:
                proximo = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "span.btn.next"))
                )

                if "disabled" in proximo.get_attribute("class"):
                    break

                driver.execute_script("arguments[0].click();", proximo)
                pagina += 1
                time.sleep(2)

            except:
                break

finally:
    driver.quit()

print(f"\nTotal coletado e salvo no MySQL: {total} imóveis")