from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="lang-uk/ukr-paraphrase-multilingual-mpnet-base",
    local_dir=".models/ukr-paraphrase-multilingual-mpnet-base",
)
