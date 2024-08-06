OUT_DIR=".models"
# OUT_DIR=$1

mkdir -r $OUT_DIR
cd $OUT_DIR
wget https://huggingface.co/bartowski/gemma-2-2b-it-GGUF/resolve/main/gemma-2-2b-it-Q5_K_M.gguf
ln -s gemma-2-2b-it-Q5_K_M.gguf model.gguf