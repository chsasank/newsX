set -e


wc -l /tmp/news.*

fasttext supervised \
    -input /tmp/news.train \
    -output news_model_cli \
    -loss ova \
    -epoch 10 \
    -lr 1 \
    -wordNgrams 2


echo "test on small validation set:"
fasttext test news_model_cli.bin /tmp/news.valid.small -1 0.5

fasttext quantize \
    -output news_model_cli \
    -input /tmp/news.train \
    -qnorm -retrain -epoch 1 -cutoff 100000

echo "test quantized on small validation set:"
fasttext test news_model_cli.bin /tmp/news.valid.small -1 0.5
