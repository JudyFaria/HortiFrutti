#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <ctype.h>

// Procura produto Hortfrutti

#define M 1201 // O primeiro número primo após 1200.
#define LIVRE 0
#define OCUPADO 1
#define REMOVIDO 2

// constantes para o relatório
#define NOME_ARQUIVO "produtos_Hortifrutti.txt" 
#define MAX_CHAVES 1000
#define TAMANHO_LOTE 100

typedef struct item HashItem;
typedef struct produtoInfo ProdutoInfo;
typedef struct listaProdutos ListaProdutos;

struct produtoInfo{
    char nome[100];
    float preco;
};

struct listaProdutos{
    ProdutoInfo produto;
    ListaProdutos* proximo;
};

struct item{
    char* chave;
    ListaProdutos* lista_prod;
    int estado;
};

// --- VARIÁVEL GLOBAL "ESCONDIDA" ---
// A tabela agora vive aqui, escondida do Python.
static HashItem tabela[M];

// função h'(x) - calcula o indice inicial 

// função hash - Método de Dobra (XOR)
int f_hash_dobra(char* chave, int m){
    // 1. definir o tamanho do bloco
    int tam_bloco = 3;

    // 2. criar variável que guarda hash acumulado
    unsigned long hash_acumulado = 0;

    // 3. percorrer a chave
    int len_chave = strlen(chave);
    for (int i = 0; i < len_chave; i += tam_bloco){

        // 4.para cada caracter:
        // -> a) pega o bloco (str)
        char bloco_temp[tam_bloco + 1]; // para o terminador de string
        strncpy(bloco_temp, &chave[i], tam_bloco);
        bloco_temp[tam_bloco] = '\0'; // adicionando o terminador manualmente
        
        // -> b) transforma para numero (int)
        unsigned long bloco_num = strtoul(bloco_temp, NULL, 10);

        // -> c) combina com hash acumulado utilizando XOR
        hash_acumulado = hash_acumulado ^ bloco_num;
    }

    // 5. metodo da divisão com hash acumulado
    int indice = hash_acumulado % m;

    return indice;
}

// -> função h''(x) - calcula o pulo
int f_hash_pulo(char* chave, int m){
    unsigned long sum = 0;
    int len_chave = strlen(chave);

    for (int i = 0; i < len_chave; i++){
        sum += chave[i];
    }

    // formula que garante pulo != 0
    // -> 1 + ( x mod (m-1))
    return 1 + (sum % (m-1));
}

ListaProdutos* cria_no_produto(ProdutoInfo dados){
    ListaProdutos* novo_no = (ListaProdutos*) malloc(sizeof(ListaProdutos));
    if (novo_no == NULL) {
        perror("Erro de alocacao de memoria para o no da lista");
        exit(1); 
    }
    novo_no->produto = dados;
    novo_no->proximo = NULL;
    return novo_no;
}

// usando a formula de dispersão dupla

// -> inserção
int insere_dispersao_dupla(char* chave, ProdutoInfo novos_dados){

    int indice = f_hash_dobra(chave, M);
    int pulo = f_hash_pulo(chave, M);
    int primeiro_removido = -1;

    for ( int k = 0; k < M; k++){

        // formula dispersão dupla -> h(x, k) = (h'(x) + k * h''(x)) mod m
        int novo_indice = (indice + k * pulo) % M;

        if (tabela[novo_indice].estado == OCUPADO){
            // indice ocupado, a chave é a procurada?
            if (strcmp(tabela[novo_indice].chave, chave) == 0){
                ListaProdutos* novo_produto = cria_no_produto(novos_dados);

                //adiciona no na lista
                novo_produto->proximo = tabela[novo_indice].lista_prod;
                tabela[novo_indice].lista_prod = novo_produto;

                return k; // tentativas
            }
        }
        
        else if (tabela[novo_indice].estado == LIVRE){
            // chave não está na tabela

            // insere no primeiro removido (se houver) ou neste livre
            int indice_final = (primeiro_removido != -1) ? primeiro_removido : novo_indice;

            tabela[novo_indice].chave = strdup(chave); // copiando a string
            tabela[novo_indice].lista_prod = cria_no_produto(novos_dados);
            tabela[novo_indice].estado = OCUPADO;
            
            // Retorna k, se k=0, não houve colisão
            // Se k>0, k é o número de colisões (tentativa)
            
            return k; 
        }

        else if (tabela[novo_indice].estado == REMOVIDO){
            // marca o primeiro removido, caso precise depois para inserir
            if (primeiro_removido == -1){
                primeiro_removido = novo_indice;
            }
        }
    }

    // Tabela cheia - k = m
    printf("Tabela cheia! Chave %s nao pode ser inserida.\n", chave);
    return M; // Retorna 'm' para sinalizar falha
}

// -> Busca (Estudo)
ListaProdutos* busca_dispersao_dupla(char* chave){

    int indice = f_hash_dobra(chave, M);
    int pulo = f_hash_pulo(chave, M);

    for (int k = 0; k < M; k++){
        // -> h(x, k) = (h'(x) + k* h''(x)) mod m
        int novo_indice = (indice + k * pulo) % M;

        // -> indice inicial vazio, ou seja, não está na lista
        if (tabela[novo_indice].estado == LIVRE){
            return NULL;
        }

        // achou um local ocupado
        if (tabela[novo_indice].estado == OCUPADO){
            
            // compara a chave no índice com a chave procurada
            if (strcmp(tabela[novo_indice].chave, chave) == 0){
                
                // retorna um ponteiro para os dados
                return tabela[novo_indice].lista_prod;
            }
        }

        // se REMOVIDO, continua a busca
    }

    // fim da busca, k = m, não encontrou!
    return NULL;
}

// libera memória alocada para tabela
void libera_tabela(){
    for(int i = 0; i < M; i++){
        if(tabela[i].estado == OCUPADO){
            // libera a lista
            ListaProdutos* atual = tabela[i].lista_prod;
            while (atual != NULL){
                ListaProdutos* temp = atual;
                atual = atual->proximo;
                free(temp);
            }

            // libera a string da chave
            free(tabela[i].chave);
        }
    }
}


// FUNÇÕES DA API (o que o Python enxergará)

void inicializar_tabela(){
    for (int i = 0; i < M; i++){
        tabela[i].estado = LIVRE;
        tabela[i].chave = NULL;
        tabela[i].lista_prod = NULL;
    }
}

void add_prod_api(char* chave, char* nome, float preco){
    ProdutoInfo p;
    strncpy(p.nome, nome, 99);
    p.nome[99] = '\0';
    p.preco = preco;

    insere_dispersao_dupla(chave, p);
}

ListaProdutos* buscar_prod_api(char* chave){
    return busca_dispersao_dupla(chave);
}

void liberar_tabela_api(){
    libera_tabela();
}