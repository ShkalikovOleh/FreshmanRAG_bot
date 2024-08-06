# FreshmanRAG_bot
Ukrainian Telegram bot assistant for freshmen based on RAG with LLM.

Very often, first-year students have a lot of questions. But, unfortunately, they flatly refuse to read the pinned messages and guides. This forces us, those who help them, to answer the same questions many times. This bot aims to make the life of volunteers easier and provide answers or relevant links to the question to itself.

## Bot functionality

### Commands
There are two categories of bot commands: user commands and admin commands. Admin commands enable actions such as banning users, adding information, or publishing links to the knowledge base. These commands are found in the management handlers. User commands are intended for the bot’s users (freshmen) and include the following:
+ **/docs \<query\>** - return documents/facts relevant to the query
+ **/docs_rep** - return documents/facts relevant to the query from a replied message
+ **/ans \<question\>** - answer a question using RAG
+ **/ans_rep** - answer a question from a replied message using RAG
+ **/help** - show user's commands description
+ **/start** - show welcome message

### RAG pipeline types
Currently 3 different RAG pipelines are implemented. By default the bot uses the *Conditional RAG with question rewriting* pipeline, but you can change it to a desired one in the `config.json` file.

All pipelines support the ability to return only documents relevant to a question without LLM answer generation, it is implemented as a conditional edge which is depicted as `stop` on all diagrams below.

#### Simple RAG
The `Simple RAG` pipeline that uses the Sentence-BERT model (by default [*lang-uk/ukr-paraphrase-multilingual-mpnet-base*](lang-uk/ukr-paraphrase-multilingual-mpnet-base)) to extract embeddings and vector store (by default `pgvector`) to find the nearest documents from the knowledge base and then optionally use the retrieved information for generation.

![Simple RAG](assets/simple_rag.png)

#### Conditional RAG with document filtering
The `Conditional RAG with document filtering` pipeline adds an extra step to the `Simple RAG` that aims to filter out all documents irrelevant to a question. If all documents have been filtered out the pipeline generates a message (`giveup` node) that there is no relevant document in the knowledge base.

![Conditional RAG with document filtering](assets/rag_with_filtering.png)

#### Conditional RAG with question rewriting
The `Conditional RAG with document filtering pipeline` doesn’t give up immediately. Instead, it attempts to rephrase the question (up to a specified number of times) and uses the rewritten query for document search and question answering.

![Conditional RAG with question rewriting](assets/rag_with_question_rewriting.png)

## LLMs
This bot is currently using Gemma2-2B-it as an LLM. This is due to the fact that I do not have the money to host large models, let alone one on nodes with GPU. At the same time, even the smallest LLaMa-3.1-8b quantised into 4 bits takes 1 minute to run with llama.cpp. So I decided to use the new Gemma2-2B-it, which, according to the authors, is the best model in this size, and most importantly, more or less understands Ukrainian.

If I have time, I plan to fine-tune Gemma2-2B-it for better understanding of Ukrainian (including expanding the tokenizer dictionary) and especially for RAG. You will find corresponding training script in the `llms` directory.


## How to deploy
The easiest way to deploy the bot is to:
1. Clone the repository
```
git clone git@github.com:ShkalikovOleh/FreshmanRAG_bot.git
```
2. Load all desired models (please use scripts from [init_scripts](https://github.com/ShkalikovOleh/FreshmanRAG_bot/tree/master/init_scripts)) into the `.models` directory and check model paths in the `config.json`
3. Place `.env` file with your api keys and other variables (as in the example.env) in the repo directory
4. Run with docker-compose
```
docker compose up -d
```