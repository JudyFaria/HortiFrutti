import atexit
from ctypes import *
import platform # Para descobrir o sistema operacional
import os
import streamlit as st

# --- 1. FUNÇÕES AUXILIARES DE PYTHON ---

# Função para gerar a chave (primeira palavra, minúscula)
def gerar_chave(nome_completo):
    # Pega a primeira palavra
    chave = nome_completo.split(' ')[0]
    # Converte para minúscula e remove caracteres não-alfabéticos
    chave_limpa = "".join(c for c in chave if c.isalpha()).lower()
    return chave_limpa

# --- 2. CONFIGURAÇÃO DO CTYPES (A "Ponte" C <-> Python) ---

# Define o nome da biblioteca baseado no SO
if platform.system() == "Windows":
    lib_path = os.path.join(os.path.dirname(__file__), "tabelaHash.dll")
elif platform.system() == "Darwin": # Darwin é o nome do kernel do macOS
    lib_path = os.path.join(os.path.dirname(__file__), "libTabelaHash.dylib")
else: # Linux
    # --- MUDANÇA: Vamos forçar um caminho absoluto ---
    # Pega o diretório ONDE O SCRIPT ESTÁ
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Cria o caminho completo para a biblioteca
    lib_path = os.path.join(script_dir, "libTabelaHash.so")
    
# Carrega a biblioteca
try:
    lib = CDLL(lib_path)
except OSError as e:
    st.error(f"**Erro de Biblioteca:**\n\n"
             f"Nao foi possivel carregar a biblioteca C:\n{e}\n\n"
             "Verifique se voce compilou o .dll/.dylib/.so corretamente.")
    st.stop()

# Define as Structs em Python (devem ser IDÊNTICAS às do C)
class ProdutoInfo(Structure):
    _fields_ = [("nome", c_char * 100),
                ("preco", c_float)]

class ListaProdutos(Structure):
    pass # Definido primeiro para permitir o ponteiro recursivo

ListaProdutos._fields_ = [("produto", ProdutoInfo),
                          ("proximo", POINTER(ListaProdutos))]

# --- 3. MAPEAMENTO DAS FUNÇÕES DA API C ---
# Isso é CRUCIAL. Diz ao Python o que cada função C espera e retorna.

try:
    # void inicializar_tabela()
    lib.inicializar_tabela.argtypes = []
    lib.inicializar_tabela.restype = None

    # void add_prod_api(char* chave, char* nome, float preco)
    lib.add_prod_api.argtypes = [c_char_p, c_char_p, c_float]
    lib.add_prod_api.restype = None

    # ListaProdutos* buscar_prod_api(char* chave)
    lib.buscar_prod_api.argtypes = [c_char_p]
    lib.buscar_prod_api.restype = POINTER(ListaProdutos) 

    # void liberar_tabela_api()
    lib.liberar_tabela_api.argtypes = []
    lib.liberar_tabela_api.restype = None
except AttributeError as e:
    st.error(f"Erro de Mapeamento CTYPES: {e}")
    st.error("Símbolo indefinido. Verifique se o nome das funções no C "
             "(ex: 'add_prod_api') bate com o nome aqui no Python.")
    st.stop()

# --- 4. INICIALIZAÇÃO E CARGA (A NOVA FORMA) ---

# @st.cache_resource garante que este bloco só rode UMA VEZ
# e não a cada clique de botão.
@st.cache_resource
def inicializar_e_carregar():
    print("LOG: Chamando inicializar_tabela() do C...")
    lib.inicializar_tabela()

    # Registra a função de limpeza para ser chamada quando o
    # servidor Streamlit for parado (com Ctrl+C)
    atexit.register(lib.liberar_tabela_api)
    print("LOG: Tabela C inicializada e 'atexit' registrado.")

    # Carrega dados do arquivo (lógica movida do 'carregar_do_arquivo')
    try:
        count = 0
        with open("produtos.txt", "r") as f:
            for linha in f:
                try:
                    nome, preco_str = linha.strip().split(" - R$ ")
                    preco = float(preco_str.replace(",", "."))
                    
                    # Adiciona na tabela hash C
                    chave_str = gerar_chave(nome)
                    chave_c = chave_str.encode('utf-8')
                    nome_c = nome.encode('utf-8')
                    lib.add_prod_api(chave_c, nome_c, c_float(preco))
                    count += 1
                except ValueError:
                    pass # Ignora linhas mal formatadas
            
            print(f"LOG: {count} produtos carregados do arquivo.")
            return count # Retorna o número de produtos carregados
            
    except FileNotFoundError:
        print("LOG: 'produtos.txt' não encontrado.")
        return 0
    except Exception as e:
        print(f"LOG: Erro ao ler arquivo: {e}")
        return 0

# --- Executa a inicialização ---
num_produtos = inicializar_e_carregar()
st.success(f"Tabela Hash C carregada com {num_produtos} produtos do 'produtos.txt'.")


# --- 5. APLICAÇÃO GRÁFICA (Streamlit) ---
# Adeus, class AppHortifruti!

st.title("🛒 Hortifruti (Python + C)")
st.markdown("Interface Web com Streamlit controlando uma Tabela Hash em C.")

# --- Frame de Adição (Usando um expander e um formulário) ---
with st.expander("Adicionar Novo Produto"):
    # st.form impede a página de recarregar a cada tecla digitada
    with st.form(key="add_form"):
        # Widgets do Streamlit (substituem tk.Entry)
        nome_novo = st.text_input("Nome (ex: Uva Thompson (kg))")
        preco_novo = st.number_input("Preço (ex: 10.99)", min_value=0.01, format="%.2f")
        
        # Botão de submit do formulário
        submit_add = st.form_submit_button("Adicionar Produto")

        # Lógica de "adicionar_produto" (antes um método da classe)
        if submit_add:
            if not nome_novo:
                st.warning("Por favor, preencha o nome do produto.")
            else:
                # Lógica de 'adicionar_produto_na_lib'
                chave_str = gerar_chave(nome_novo)
                chave_c = chave_str.encode('utf-8')
                nome_c = nome_novo.encode('utf-8')
                
                lib.add_prod_api(chave_c, nome_c, c_float(preco_novo))
                
                st.success(f"ADICIONADO: {nome_novo} - R${preco_novo:.2f}")

# --- Frame de Busca ---
st.header("Buscar Produto")
termo_busca = st.text_input("Buscar por (ex: banana, maca, uva...)", 
                            placeholder="Digite o nome da fruta aqui...")

if st.button("Buscar"):
    # Lógica de "buscar_produto" (antes um método da classe)
    if not termo_busca:
        st.warning("Digite um termo para busca.")
    else:
        chave_str = gerar_chave(termo_busca)
        chave_c = chave_str.encode('utf-8')

        st.subheader(f"--- Buscando por '{chave_str}' ---")

        # Chama a função C
        ponteiro_lista = lib.buscar_prod_api(chave_c)

        # Processa o resultado (substitui o 'self._log')
        if not ponteiro_lista:
            st.info("Nenhum resultado encontrado.")
        else:
            # Percorre a lista ligada vinda do C
            atual = ponteiro_lista
            count = 0
            while atual:
                produto = atual.contents.produto
                
                nome_py = produto.nome.decode('utf-8')
                preco_py = produto.preco
                
                # st.write é o novo "print" para a tela
                st.write(f" -> **{nome_py}** - R${preco_py:.2f}")
                
                atual = atual.contents.proximo
                count += 1
            st.write(f"({count} resultado(s) encontrado(s))")

        st.write("--- Fim da busca ---")