# T5 Text Processing NVCF Task

This is an NVIDIA Cloud Functions (NVCF) task that uses the T5 model to process text for various NLP tasks including translation and summarization.


## Configuration

The task can be configured using the following environment variables:

- `MODEL_NAME`: T5 model to use (default: "t5-small")
  - Options: "translation", "summarization"
- `BATCH_SIZE`: Number of texts to process in each batch (default: 10)
- `MAX_TOKENS`: Maximum number of tokens in generated output (default: 1000)
- `TEMPERATURE`: Sampling temperature for text generation (default: 0.7)


### Translation
```
The house is wonderful.
The weather is nice today.
```

### Summarization
```
The quick brown fox jumps over the lazy dog. The quick brown fox jumps over the lazy dog.
Another long text to summarize...
```

