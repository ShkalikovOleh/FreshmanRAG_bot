# FreshmanRAG_bot
Ukrainian Telegram bot assistant for freshmen based on RAG with LLM.

Very often, first-year students have a lot of questions. But, unfortunately, they flatly refuse to read the pinned messages and guides. This forces us, those who help them, to answer the same questions many times. This bot aims to make the life of volunteers easier by independently providing answers or relevant links to common questions.

## Bot functionality

### Commands
There are two categories of bot commands: user commands and admin commands. Admin commands implements actions such as banning users, adding information to the knowledge base, appending public links to private messages, etc. These commands can be found in the [management](./bot/handlers/management.py) handlers. User commands are intended for the bot’s users (freshmen) and they are the following:
+ **/docs \<query\>** - return documents/facts relevant to the query
+ **/docs_rep** - return documents/facts relevant to the query from a replied message
+ **/ans \<question\>** - answer a question using RAG
+ **/ans_rep** - answer a question from a replied message using RAG
+ **/help** - show user's commands description
+ **/start** - show welcome message

### RAG pipeline types
Currently 3 different RAG pipelines are implemented. By default the bot uses the *Conditional RAG with question rewriting* pipeline, but you can change in the [configs](#configuration).

All pipelines support the ability to return only documents relevant to a question without LLM answer generation, it is implemented as a conditional edge which is depicted as `stop` on all diagrams below.

#### Simple RAG
The `Simple RAG` pipeline that uses the provided [retriever](#retrievers) to find the relevant documents from the knowledge base and then optionally use this information for generation.

![Simple RAG](assets/simple_rag.png)

#### Conditional RAG with document filtering
The `Conditional RAG with document filtering` pipeline adds an extra step to the `Simple RAG` that aims to filter out all documents irrelevant to a question. If all documents have been filtered out the pipeline generates a message (`giveup` node) that there is no relevant document in the knowledge base. As of now it uses a LLM with a special prompt to grade documents, but I am open to PRs that will add an encoder only model for filtering (as a sentence classification task).

![Conditional RAG with document filtering](assets/rag_with_filtering.png)

#### Conditional RAG with question rewriting
The `Conditional RAG with document filtering pipeline` doesn’t give up immediately. Instead, it attempts to rephrase the question (up to a specified number of times) and uses the rewritten query for next iteration of document search and question answering.

![Conditional RAG with question rewriting](assets/rag_with_question_rewriting.png)

## LLMs
This bot is currently using Gemma2-2B-it (Q5-K quantized) as an LLM. This is due to the fact that I do not have money to host large models, let alone one on nodes with GPUs. At the same time, even the smallest LLaMa-3.1-8b quantized into 4 bits takes 1 minute to run with llama.cpp. So I decided to use the new Gemma2-2B-it, which, according to the authors, is the best model in this size, and most importantly, more or less understands Ukrainian.

If I have time, I plan to fine-tune Gemma2-2B-it for better understanding of Ukrainian (including expanding the tokenizer dictionary) and especially for RAG. You will find corresponding training script in the [llms](./llms/) directory.

## Retrievers
We support a variety of different retriever types, such as
- Dense vector retrievers using the Sentence BERT model [*lang-uk/ukr-paraphrase-multilingual-mpnet-base*](https://huggingface.co/lang-uk/ukr-paraphrase-multilingual-mpnet-base) to extract embeddings and `pgvector` as a vector store.
- Parent document retriever, which uses a dense vector retriever to find a relevant small document (since it is easy to make a search query), but passes all parent documents as context to an LLM so as not to lose relevant information.
- BM25 Sparse Retriever, which uses Elasticsearch as a store and allows us to do sparse searches (find keywords) using MB25 algorithm.
- [**Default**] Ensemble retriever fuses (using the Reciprocal Rank Fusion algorithm) the results from the parent document retriever and the BM25 retriever to find the most relevant information and take advantage of all the of both.

## Configuration
To configure the bot I use a reliable and flexible tool called Hydra. In the [configs](./configs/) directory you can find and add your own configs. Please read the [docs](https://hydra.cc/docs/1.3/intro/) to learn how to do it properly. By default (and especially inside a docker container), the bot will load the default config, so in addition to adding new configs, user will also need to modify the [default.yaml](./configs/default.yaml).

The overall structure of the configs is the following:
- llm - language model config
- retriever - retriever config
- prompts - prompts used  to query a language model
- pipeline - RAG pipeline config
- knowledge
    - loader - utility for loading documents from given URLs
    - transform - utility for pre-processing documents before uploading to a vector/elasticsearch store

## How to deploy
The easiest way to deploy the bot is to:
1. Download a release docker-compose file and optionally required scripts from the [init_scripts](./init_scripts/) directory
```
wget https://github.com/ShkalikovOleh/FreshmanRAG_bot/blob/master/docker-compose.release.yml
```
2. Load all desired models (please use scripts from [init_scripts](./init_scripts/)) into the `.models` directory and optionally place your own configs in the `configs` directory.
3. Place `.env` file with your api keys and other variables (as in the [example.env](./example.env)) in the repo directory
4. Prepare directories for mounting volumes via
```
bash init_scripts/prepare_data_volumes.sh
```
5. Run with docker-compose
```
docker compose up -d
```