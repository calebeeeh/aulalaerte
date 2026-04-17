import os
import time
import re
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from sqlalchemy import text
from database import engine


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


def executar_scraping(
    tipo: str = "ALUGUEL",
    tipos: str = "APARTAMENTO",
    estado: str = "DF",
    cidade: str = "TAGUATINGA",
    bairro: str = "TAGUATINGA NORTE",
    headless: bool = os.getenv("DOCKER", "false").lower() == "true",
) -> int:
    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

    driver = uc.Chrome(options=options, use_subprocess=True)
    wait = WebDriverWait(driver, 20)
    total = 0

    def selecionar_select2(campo_id, valor):
        campo = wait.until(EC.element_to_be_clickable((By.ID, campo_id)))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", campo)
        time.sleep(1)
        try:
            campo.click()
        except Exception:
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

        raise Exception(f"Não encontrou: {valor}")

    try:
        driver.get("https://www.dfimoveis.com.br/")
        time.sleep(2)

        try:
            botao_cookies = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "btn-lgpd"))
            )
            botao_cookies.click()
            time.sleep(1)
        except Exception:
            pass

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

        botao_busca = wait.until(EC.element_to_be_clickable((By.ID, "botaoDeBusca")))
        botao_busca.click()

        pagina = 1

        with engine.begin() as conn:
            while True:
                wait.until(
                    EC.presence_of_element_located((By.ID, "resultadoDaBuscaDeImoveis"))
                )

                cards = driver.find_elements(
                    By.XPATH,
                    "//div[@id='resultadoDaBuscaDeImoveis']//a[contains(@href, '/imovel/')]",
                )
                print(f"Página {pagina}: {len(cards)} anúncios encontrados")

                for card in cards:
                    try:
                        titulo = card.find_element(By.CLASS_NAME, "ellipse-text").text.strip()
                    except Exception:
                        titulo = ""
                    try:
                        preco = card.find_element(By.CLASS_NAME, "body-large").text.strip()
                    except Exception:
                        preco = ""
                    try:
                        quartos_txt = card.find_element(
                            By.XPATH, ".//div[contains(text(), 'Quarto')]"
                        ).text
                    except Exception:
                        quartos_txt = ""
                    try:
                        metragem_txt = card.find_element(
                            By.XPATH, ".//div[contains(text(), 'm²')]"
                        ).text
                    except Exception:
                        metragem_txt = ""
                    try:
                        vagas_txt = card.find_element(
                            By.XPATH, ".//div[contains(text(), 'Vaga')]"
                        ).text
                    except Exception:
                        vagas_txt = ""

                    id_tipo_imovel = get_or_create(conn, "tb_tipo_imovel", "nome_tipo_imovel", tipos)
                    id_operacao = get_or_create(conn, "tb_tipo_operacao", "nome_operacao", tipo)
                    id_imobiliaria = get_or_create(conn, "tb_imobiliaria", "nome_imobiliaria", "Não informada")

                    conn.execute(text("""
                        INSERT INTO tb_imoveis (
                            endereco, tamanho_m2, preco, quartos, vagas, suites,
                            id_operacao, id_imobiliaria, id_tipo_imovel
                        ) VALUES (
                            :endereco, :tamanho_m2, :preco, :quartos, :vagas, :suites,
                            :id_operacao, :id_imobiliaria, :id_tipo_imovel
                        )
                    """), {
                        "endereco": titulo,
                        "tamanho_m2": limpar_metragem(metragem_txt),
                        "preco": limpar_preco(preco),
                        "quartos": extrair_numero(quartos_txt),
                        "vagas": extrair_numero(vagas_txt),
                        "suites": None,
                        "id_operacao": id_operacao,
                        "id_imobiliaria": id_imobiliaria,
                        "id_tipo_imovel": id_tipo_imovel,
                    })
                    total += 1

                try:
                    proximo = wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "span.btn.next"))
                    )
                    if "disabled" in proximo.get_attribute("class"):
                        break
                    driver.execute_script("arguments[0].click();", proximo)
                    pagina += 1
                    time.sleep(2)
                except Exception:
                    break

    finally:
        try:
            driver.quit()
        except Exception:
            pass

    print(f"\nTotal coletado: {total} imóveis")
    return total
